"""
NZX Wholesale Prices Import DAG

Runs daily at 06:00 NZT (18:00 UTC) to import wholesale nodal spot-prices
from NZX SFTP/FTPS server into TimescaleDB.

Supports both SFTP and FTPS protocols with robust connection handling.

Author: SpotOn Data Team
"""

import gzip
import logging
import os
import re
import shutil
import ssl
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import psycopg2
from airflow import DAG
from airflow.decorators import dag, task, task_group
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import Variable
from airflow.operators.python import get_current_context
from airflow.utils.dates import days_ago
from ftplib import FTP_TLS
from pydantic import BaseModel, ValidationError, validator
import paramiko

# Configure logging
logger = logging.getLogger(__name__)

# Import the new connection manager utility
import sys
import os
sys.path.append("/app/airflow/dags/wits/utils")
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/wits/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    # Try importing from airflow utils first
    from connection_manager import ConnectionManager, DataSourceConfig
    try:
        from audit_logger import get_dag_audit_logger
    except ImportError:
        # audit_logger might not exist, create a simple fallback
        def get_dag_audit_logger(dag_id):
            return logging.getLogger(dag_id)
except ImportError:
    try:
        # Try importing from utils directory
        from utils.connection_manager import ConnectionManager, DataSourceConfig
        from audit_logger import get_dag_audit_logger
    except ImportError:
        # Final fallback for development
        import logging
        logging.warning("⚠️ Connection manager not available - using mock implementation")
        
        class ConnectionManager:
            @staticmethod
            def get_connection_config(*args, **kwargs):
                return {'host': 'mock', 'port': 22, 'user': 'mock'}
            
            @staticmethod
            def test_connection(*args, **kwargs):
                return False
        
        class DataSourceConfig:
            WITS_NZX_PRICES = {
                'protocol': 'SFTP',
                'prefix': 'NZX',
                'default_host': None,  # Use NZX_HOST env var
                'default_port': None,  # Use NZX_PORT env var
                'default_user': None,  # Use NZX_USER env var
                'remote_path': '/wits/prices',
                'file_pattern': r'^final(\d{14})\.csv$'
            }
        
        def get_dag_audit_logger(dag_id):
            return logging.getLogger(dag_id)


# Configuration
DEFAULT_ARGS = {
    "owner": "nzx_import",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
    "catchup": False,
    "task_timeout": timedelta(minutes=10),  # 10 minute timeout per task
    "execution_timeout": timedelta(minutes=30),  # 30 minute total timeout
}

# File paths - Use flexible directory structure
# Use a simple, direct path that relies on the Docker volume mapping
BASE_PATH = Path('/data/imports/electricity/nzx/prices')
IMPORTED_PATH = BASE_PATH / "imported"
ERROR_PATH = BASE_PATH / "error" 
ARCHIVE_PATH = BASE_PATH / "archive"

# Database configuration - using Django models
# Tables are managed by Django migrations:
# - energy_marketprice (MarketPrice model)
# - energy_nzx_import_log (NZXImportLog model)


class WholesalePriceRecord(BaseModel):
    """Pydantic model for wholesale price validation - matches WITS specification exactly."""
    
    gip_gxp: str  # GIPGXP - Grid Injection Point or Grid Exit Point (Varchar 7)
    trading_date: datetime  # Trading date (DD/MM/YYYY)
    trading_period: int  # Trading period (Number 2) - 1 to 50
    price_type: str  # Price type (Char 1) - F=Final, I=Interim  
    price: float  # Price (Number 8,5) - Format: 99999.99999.00
    publish_time: datetime  # Publish time (DD/MM/YYYY HH:MM:SS)
    
    @validator('gip_gxp')
    def validate_gip_gxp(cls, v):
        if not v or not v.strip():
            raise ValueError('gip_gxp cannot be empty')
        if len(v.strip()) > 7:
            raise ValueError(f'gip_gxp must be 7 characters or less, got {len(v.strip())}')
        return v.strip()
    
    @validator('trading_period')
    def validate_trading_period(cls, v):
        if not 1 <= v <= 50:
            raise ValueError(f'trading_period must be between 1 and 50, got {v}')
        return v
    
    @validator('price_type')
    def validate_price_type(cls, v):
        if v not in ['F', 'I']:
            raise ValueError(f'price_type must be F (Final) or I (Interim), got {v}')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError(f'price cannot be negative, got {v}')
        # Check format: 99999.99999 (8 digits total, 5 decimal places)
        if v >= 1000:  # More than 3 digits before decimal
            raise ValueError(f'price exceeds maximum format 999.99999, got {v}')
        return round(v, 5)
    
    def to_wits_data(self) -> Dict:
        """Convert to WITS database format."""
        return {
            'gip_gxp': self.gip_gxp,
            'trading_date': self.trading_date.date(),
            'trading_period': self.trading_period,
            'price_type': self.price_type,
            'price': self.price,
            'publish_time': self.publish_time,
            'source': 'WITS_NZX',
        }


def get_connection_config() -> Dict[str, str]:
    """Get NZX connection configuration using the centralized connection manager."""
    source_config = DataSourceConfig.WITS_NZX_PRICES
    
    config = ConnectionManager.get_connection_config(
        protocol=source_config['protocol'],
        prefix=source_config['prefix'],
        default_host=source_config['default_host'],
        default_port=source_config['default_port'],
        default_user=source_config['default_user']
    )
    
    # Add remote path for WITS prices
    config['remote_path'] = source_config['remote_path']
    
    return config


def ensure_directories():
    """Ensure all required directories exist."""
    for path in [IMPORTED_PATH, ERROR_PATH, ARCHIVE_PATH]:
        path.mkdir(parents=True, exist_ok=True)


# Connection functions are now handled by ConnectionManager utility


def parse_csv_row(row: List[str], filename: str) -> WholesalePriceRecord:
    """Parse and validate a CSV row according to actual file format."""
    if len(row) != 6:
        raise ValueError(f"Expected 6 columns, got {len(row)}")
    
    # Actual format: node_code, trading_date, trading_period, price, file_generated_at, status
    node_code, trading_date_str, trading_period_str, price_str, file_generated_str, status = row
    
    # Convert all values to strings first (pandas might have converted some to int/float)
    node_code = str(node_code).strip()
    trading_date_str = str(trading_date_str).strip()
    trading_period_str = str(trading_period_str).strip()
    price_str = str(price_str).strip()
    file_generated_str = str(file_generated_str).strip()
    status = str(status).strip()
    
    # Parse dates
    trading_date = datetime.strptime(trading_date_str, '%d/%m/%Y')
    publish_time = datetime.strptime(file_generated_str, '%d/%m/%Y %H:%M:%S')
    
    return WholesalePriceRecord(
        gip_gxp=node_code,
        trading_date=trading_date,
        trading_period=int(trading_period_str),
        price_type=status,  # 'F' for Final
        price=float(price_str),
        publish_time=publish_time
    )


def validate_file_data(file_path: Path) -> Tuple[List[WholesalePriceRecord], List[str]]:
    """Validate CSV file data and return records and errors."""
    records = []
    errors = []
    seen_keys = set()
    
    try:
        df = pd.read_csv(file_path, header=None)
        
        for idx, row in df.iterrows():
            try:
                record = parse_csv_row(row.tolist(), file_path.name)
                
                # Check for duplicates within file
                key = (record.trading_date.date(), record.trading_period, record.gip_gxp, record.price_type)
                if key in seen_keys:
                    errors.append(f"Row {idx + 1}: Duplicate key {key}")
                    continue
                
                seen_keys.add(key)
                records.append(record)
                
            except (ValueError, ValidationError) as e:
                errors.append(f"Row {idx + 1}: {e}")
    
    except Exception as e:
        errors.append(f"File parsing error: {e}")
    
    return records, errors


# Import connection utility
import sys
sys.path.append('/app/airflow/utils')
from connection import get_connection

def get_timescale_connection():
    """DEPRECATED: Use get_connection() instead."""
    return get_connection()


def bulk_upsert_records(records: List[WholesalePriceRecord]) -> int:
    """Bulk upsert records into WITS nodal price hypertable (TimescaleDB)."""
    import uuid
    
    if not records:
        return 0
    
    # Convert to WITS database format
    data = []
    import_batch_id = str(uuid.uuid4())
    
    for record in records:
        wits_data = record.to_wits_data()
        data.append((
            wits_data['gip_gxp'],
            wits_data['trading_date'],
            wits_data['trading_period'],
            wits_data['price_type'],
            wits_data['price'],
            wits_data['publish_time'],
            wits_data['source'],
            import_batch_id,
        ))
    
    upsert_sql = """
    INSERT INTO wits.nodal_price 
    (gip_gxp, trading_date, trading_period, price_type, price, 
     publish_time, source, import_batch_id, created_at)
    VALUES %s
    ON CONFLICT (gip_gxp, trading_date, trading_period, price_type)
    DO UPDATE SET
        price = EXCLUDED.price,
        publish_time = EXCLUDED.publish_time,
        import_batch_id = EXCLUDED.import_batch_id,
        created_at = NOW()
    """
    
    # Use execute_values for bulk insert
    conn = get_timescale_connection()
    try:
        with conn.cursor() as cursor:
            # Ensure schema and table exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS wits")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wits.nodal_price (
                    id BIGSERIAL PRIMARY KEY,
                    gip_gxp VARCHAR(10) NOT NULL,
                    trading_date DATE NOT NULL,
                    trading_period SMALLINT NOT NULL,
                    price_type CHAR(1) NOT NULL,
                    price NUMERIC(10, 5) NOT NULL,
                    publish_time TIMESTAMP WITH TIME ZONE,
                    source VARCHAR(50),
                    import_batch_id UUID,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT nodal_price_unique UNIQUE (gip_gxp, trading_date, trading_period, price_type)
                );
            """)
            # Consider creating a hypertable if this is a large, time-series table
            # cursor.execute("SELECT create_hypertable('wits.nodal_price', 'trading_date', if_not_exists => TRUE);")
            
            from psycopg2.extras import execute_values
            
            # Add created_at timestamp to each record
            data_with_timestamp = [
                row + (datetime.now(),) for row in data
            ]
            
            execute_values(
                cursor,
                upsert_sql,
                data_with_timestamp,
                template=None,
                page_size=1000
            )
            conn.commit()
            return len(data)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def detect_file_type(filename: str) -> str:
    """Detect file type from filename."""
    filename_lower = filename.lower()
    if 'final' in filename_lower:
        return 'final'
    elif 'provisional' in filename_lower:
        return 'provisional'
    elif 'forecast' in filename_lower:
        return 'forecast'
    else:
        return 'final'  # Default


def log_import(filename: str, records_count: int = 0, file_size: int = 0):
    """Log successful import to prevent reprocessing."""
    file_type = detect_file_type(filename)
    conn = get_timescale_connection()
    try:
        with conn.cursor() as cursor:
            # Create schema if it doesn't exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS wits")
            
            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wits.import_log (
                    id SERIAL PRIMARY KEY,
                    file_name VARCHAR(255) UNIQUE NOT NULL,
                    file_type VARCHAR(50),
                    records_imported INTEGER DEFAULT 0,
                    file_size BIGINT DEFAULT 0,
                    imported_at TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Insert import log record
            cursor.execute(
                """INSERT INTO wits.import_log 
                   (file_name, file_type, records_imported, file_size, imported_at) 
                   VALUES (%s, %s, %s, %s, NOW()) 
                   ON CONFLICT (file_name) DO UPDATE SET
                       records_imported = EXCLUDED.records_imported,
                       file_size = EXCLUDED.file_size,
                       imported_at = EXCLUDED.imported_at""",
                [filename, file_type, records_count, file_size]
            )
            
            logger.info(f"📝 Logged import: {filename} ({records_count} records, {file_size} bytes)")
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to log import for {filename}: {e}")
        conn.rollback()
    finally:
        conn.close()


def is_file_already_imported(filename: str) -> bool:
    """Check if file has already been imported."""
    conn = get_timescale_connection()
    try:
        with conn.cursor() as cursor:
            # Create schema and table if they don't exist (idempotent)
            cursor.execute("CREATE SCHEMA IF NOT EXISTS wits")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wits.import_log (
                    id SERIAL PRIMARY KEY,
                    file_name VARCHAR(255) UNIQUE NOT NULL,
                    file_type VARCHAR(50),
                    records_imported INTEGER DEFAULT 0,
                    file_size BIGINT DEFAULT 0,
                    imported_at TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cursor.execute(
                "SELECT 1 FROM wits.import_log WHERE file_name = %s",
                [filename]
            )
            result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.warning(f"⚠️  Could not check import status for {filename}: {e}")
        return False  # Assume not imported if we can't check
    finally:
        conn.close()


def compress_and_archive_file(file_path: Path):
    """Compress file with gzip and move to archive."""
    archive_file = ARCHIVE_PATH / f"{file_path.name}.gz"
    
    with open(file_path, 'rb') as f_in:
        with gzip.open(archive_file, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    file_path.unlink()  # Remove original file


def move_to_error(file_path: Path, error_msg: str):
    """Move file to error directory with error log."""
    error_file = ERROR_PATH / file_path.name
    shutil.move(str(file_path), str(error_file))
    
    # Write error log
    error_log = ERROR_PATH / f"{file_path.stem}.error.txt"
    with open(error_log, 'w') as f:
        f.write(f"Error processing {file_path.name}:\n{error_msg}\n")


@dag(
    dag_id="wits_prices_nzx",
    description="Import WITS nodal spot-prices from NZX into TimescaleDB",
    schedule="0 18 * * *",  # 06:00 NZT (UTC+12) = 18:00 UTC
    default_args=DEFAULT_ARGS,
    tags=["wits", "nzx", "prices", "timescaledb"],
    catchup=False,
    max_active_runs=1,
)
def wits_prices_nzx_dag():
    """WITS Nodal Prices Import DAG."""
    
    @task_group(group_id="wits_prices")
    def wits_prices_group():
        """TaskGroup for WITS nodal prices processing."""
        
        @task
        def initialize_audit_logging() -> str:
            """Initialize audit logging for the DAG run."""
            context = get_current_context()
            audit_logger = get_dag_audit_logger('wits_prices_nzx', context)
            audit_logger.log_dag_start(task_count=4, context=context)
            return audit_logger.batch_id
        
        @task
        def test_connection() -> bool:
            """Test connection to NZX server before processing."""
            try:
                config = get_connection_config()
                logger.info(f"🔗 Testing {config['protocol']} connection to {config['host']}:{config['port']}")
                
                # Check if we have real credentials
                if config['password'] in ['your-password-here', '']:
                    logger.error("❌ NZX_PASS is not configured with real credentials")
                    raise ValueError("Missing NZX SFTP credentials - please update .env file")
                
                if not ConnectionManager.test_connection(config):
                    logger.error("❌ SFTP connection test failed")
                    raise ConnectionError(f"Cannot connect to NZX SFTP server at {config['host']}:{config['port']}")
                
                logger.info("✅ SFTP connection test successful")
                return True
                
            except Exception as e:
                logger.error(f"❌ Connection test failed: {e}")
                raise  # Re-raise to fail the task
        
        @task
        def fetch_files(batch_id: str) -> List[str]:
            """Fetch new files from NZX server."""
            ensure_directories()
            config = get_connection_config()
            source_config = DataSourceConfig.WITS_NZX_PRICES
            audit_logger = get_dag_audit_logger('wits_prices_nzx')
            audit_logger.batch_id = batch_id  # Use the same batch ID
            
            # Enhanced validation with better error messages
            missing_config = []
            if not config.get('host') or config['host'] == 'mock-host':
                missing_config.append('NZX_HOST')
            if not config.get('user') or config['user'] == 'mock':
                missing_config.append('NZX_USER')
            if not config.get('password') and not config.get('private_key_path'):
                missing_config.append('NZX_PASS or NZX_PRIVATE_KEY_PATH')
            
            if missing_config:
                error_msg = f"Missing NZX connection configuration: {', '.join(missing_config)}"
                logger.error(f"❌ {error_msg}")
                logger.error("💡 Please set the following environment variables in your Airflow configuration:")
                for var in missing_config:
                    logger.error(f"   - {var}")
                raise ValueError(error_msg)
            
            logger.info(f"🔗 Connecting to NZX server: {config['host']}:{config['port']}")
            
            # Add timeout protection for file listing
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"SFTP operation timed out after {config.get('timeout', 30)} seconds")
            
            try:
                # Set timeout for the entire operation
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(120)  # 2 minute timeout for file discovery
                
                # Get list of remote files using the file pattern from source config
                logger.info(f"📁 Looking for files matching pattern: {source_config['file_pattern']}")
                remote_files = ConnectionManager.list_remote_files(config, source_config['file_pattern'])
                
                signal.alarm(0)  # Cancel timeout
                logger.info(f"Found {len(remote_files)} files on remote server")
                
            except TimeoutError as e:
                signal.alarm(0)  # Cancel timeout
                logger.error(f"⏰ {e}")
                logger.error("💡 This usually indicates network connectivity issues or server problems")
                raise
            except Exception as e:
                signal.alarm(0)  # Cancel timeout
                logger.error(f"❌ Failed to list remote files: {e}")
                logger.error("💡 Check network connectivity and SFTP credentials")
                raise
            
            # Check which files are new
            new_files = []
            
            for filename in remote_files:
                if not is_file_already_imported(filename):
                    # Download file
                    local_path = IMPORTED_PATH / filename
                    start_time = datetime.now()
                    
                    if ConnectionManager.download_file(config, filename, local_path):
                        new_files.append(filename)
                        logger.info(f"✅ Downloaded: {filename}")
                        
                        # Log successful download
                        file_size = local_path.stat().st_size if local_path.exists() else None
                        audit_logger.log_file_operation(
                            filename=filename,
                            operation='sftp_download',
                            status='completed',
                            file_path=str(local_path),
                            source_path=f"{config['remote_path']}/{filename}",
                            destination_path=str(local_path),
                            file_size=file_size,
                            started_at=start_time,
                            completed_at=datetime.now()
                        )
                    else:
                        logger.error(f"❌ Failed to download: {filename}")
                        
                        # Log failed download
                        audit_logger.log_file_operation(
                            filename=filename,
                            operation='sftp_download',
                            status='failed',
                            source_path=f"{config['remote_path']}/{filename}",
                            error_message=f"Failed to download {filename}",
                            started_at=start_time,
                            completed_at=datetime.now()
                        )
                else:
                    logger.info(f"⏭️  Skipping already imported: {filename}")
            
            logger.info(f"Downloaded {len(new_files)} new files")
            return new_files
        
        @task
        def validate_and_load(filenames: List[str], batch_id: str) -> Dict[str, any]:
            """Validate files and load into TimescaleDB."""
            audit_logger = get_dag_audit_logger('wits_prices_nzx')
            audit_logger.batch_id = batch_id  # Use the same batch ID
            
            results = {
                "processed": 0,
                "loaded_records": 0,
                "failed_files": [],
                "successful_files": []
            }
            
            for filename in filenames:
                file_path = IMPORTED_PATH / filename
                
                if not file_path.exists():
                    logger.error(f"❌ File not found: {filename}")
                    continue
                
                try:
                    start_time = datetime.now()
                    logger.info(f"🔍 Validating: {filename}")
                    records, errors = validate_file_data(file_path)
                    
                    if errors:
                        error_msg = "\n".join(errors)
                        logger.error(f"❌ Validation failed for {filename}:\n{error_msg}")
                        move_to_error(file_path, error_msg)
                        results["failed_files"].append(filename)
                        
                        # Log validation failure
                        audit_logger.log_data_validation(
                            check_name=f"File validation: {filename}",
                            check_type='file_integrity',
                            result='fail',
                            records_checked=0,
                            issues_found=len(errors),
                            error_message=error_msg,
                            check_parameters={'filename': filename},
                            check_results={'errors': errors}
                        )
                        
                        # Log file processing failure
                        audit_logger.log_file_operation(
                            filename=filename,
                            operation='process',
                            status='failed',
                            file_path=str(file_path),
                            error_message=error_msg,
                            started_at=start_time,
                            completed_at=datetime.now()
                        )
                        continue
                    
                    if not records:
                        logger.warning(f"⚠️  No valid records in {filename}")
                        move_to_error(file_path, "No valid records found")
                        results["failed_files"].append(filename)
                        
                        # Log empty file
                        audit_logger.log_file_operation(
                            filename=filename,
                            operation='process',
                            status='failed',
                            file_path=str(file_path),
                            error_message="No valid records found",
                            started_at=start_time,
                            completed_at=datetime.now()
                        )
                        continue
                    
                    # Load records
                    logger.info(f"💾 Loading {len(records)} records from {filename}")
                    loaded_count = bulk_upsert_records(records)
                    
                    # Log successful import with metrics
                    file_size = file_path.stat().st_size
                    log_import(filename, loaded_count, file_size)
                    
                    results["loaded_records"] += loaded_count
                    results["successful_files"].append(filename)
                    logger.info(f"✅ Successfully loaded {loaded_count} records from {filename}")
                    
                    # Log successful validation and processing
                    audit_logger.log_data_validation(
                        check_name=f"File validation: {filename}",
                        check_type='file_integrity',
                        result='pass',
                        records_checked=len(records),
                        issues_found=0,
                        check_parameters={'filename': filename},
                        check_results={'records_validated': len(records)}
                    )
                    
                    audit_logger.log_file_operation(
                        filename=filename,
                        operation='process',
                        status='completed',
                        file_path=str(file_path),
                        file_size=file_size,
                        records_processed=len(records),
                        records_successful=loaded_count,
                        records_failed=0,
                        started_at=start_time,
                        completed_at=datetime.now()
                    )
                
                except Exception as e:
                    error_msg = f"Processing error: {str(e)}"
                    logger.error(f"❌ Error processing {filename}: {error_msg}")
                    move_to_error(file_path, error_msg)
                    results["failed_files"].append(filename)
                    
                    # Log processing exception
                    audit_logger.log_file_operation(
                        filename=filename,
                        operation='process',
                        status='failed',
                        file_path=str(file_path),
                        error_message=error_msg,
                        started_at=start_time,
                        completed_at=datetime.now()
                    )
                
                results["processed"] += 1
            
            return results
        
        @task
        def archive_or_error(results: Dict[str, any], batch_id: str):
            """Archive successful files or move failed ones to error directory."""
            audit_logger = get_dag_audit_logger('wits_prices_nzx')
            audit_logger.batch_id = batch_id  # Use the same batch ID
            
            for filename in results["successful_files"]:
                file_path = IMPORTED_PATH / filename
                if file_path.exists():
                    try:
                        start_time = datetime.now()
                        compress_and_archive_file(file_path)
                        logger.info(f"📦 Archived: {filename}")
                        
                        # Log successful archiving
                        audit_logger.log_file_operation(
                            filename=filename,
                            operation='archive',
                            status='completed',
                            source_path=str(file_path),
                            destination_path=str(ARCHIVE_PATH / f"{filename}.gz"),
                            started_at=start_time,
                            completed_at=datetime.now()
                        )
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to archive {filename}: {e}")
                        
                        # Log archiving failure
                        audit_logger.log_file_operation(
                            filename=filename,
                            operation='archive',
                            status='failed',
                            source_path=str(file_path),
                            error_message=str(e),
                            started_at=start_time,
                            completed_at=datetime.now()
                        )
            
            logger.info(f"📊 Processing complete:")
            logger.info(f"  - Files processed: {results['processed']}")
            logger.info(f"  - Records loaded: {results['loaded_records']}")
            logger.info(f"  - Successful files: {len(results['successful_files'])}")
            logger.info(f"  - Failed files: {len(results['failed_files'])}")
            
            # Determine overall success
            success = len(results["failed_files"]) == 0
            
            if results["failed_files"]:
                error_msg = f"Failed to process {len(results['failed_files'])} files: {', '.join(results['failed_files'])}"
                logger.error(f"❌ {error_msg}")
                
                # Log final DAG completion as failure
                audit_logger.log_dag_completion(
                    success=False,
                    summary={
                        'files_processed': results['processed'],
                        'records_loaded': results['loaded_records'],
                        'successful_files': results['successful_files'],
                        'failed_files': results['failed_files']
                    },
                    error_msg=error_msg
                )
                
                # Fail the DAG if any files failed to process
                raise ValueError(error_msg)
            else:
                # Log successful DAG completion
                logger.info("✅ All files processed successfully")
                audit_logger.log_dag_completion(
                    success=True,
                    summary={
                        'files_processed': results['processed'],
                        'records_loaded': results['loaded_records'],
                        'successful_files': results['successful_files'],
                        'failed_files': results['failed_files']
                    },
                    error_msg=None
                )
        
        # Define task dependencies
        audit_init = initialize_audit_logging()
        connection_test = test_connection()
        files = fetch_files(audit_init)
        load_results = validate_and_load(files, audit_init)
        final_task = archive_or_error(load_results, audit_init)
        
        # Set dependencies
        audit_init >> connection_test >> files >> load_results >> final_task
    
    # Main DAG flow - just run the WITS group
    wits_group = wits_prices_group()


# Instantiate the DAG
dag_instance = wits_prices_nzx_dag() 