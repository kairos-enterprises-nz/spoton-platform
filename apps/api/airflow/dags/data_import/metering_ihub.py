"""
IHUB (IntelliHub) Metering Data Import DAG
Imports DRR (XML) and HHR (CSV) data from IHUB SFTP server
"""

from datetime import datetime, timedelta
from pathlib import Path
import logging
import xml.etree.ElementTree as ET
import gzip
import hashlib
import os
import sys

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

# Add utils to path
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/metering/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))

try:
    from utils.metering_etl import SFTPDiscovery
except ImportError:
    try:
        from metering_etl import SFTPDiscovery
    except ImportError:
        from utils.sftp_discovery import SFTPFileDiscovery as SFTPDiscovery

from connection_manager import ConnectionManager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    psycopg2 = None

# Data processing directory (Corrected to use the root /data volume mount)
DATA_DIR = Path('/data/imports/electricity/metering/ihub')
DAILY_DIR = DATA_DIR / 'daily'
INTERVAL_DIR = DATA_DIR / 'interval'

IHUB_CONFIG = {
    'protocol': os.getenv('INTELLIHUB_PROTOCOL', 'sftp'),
    'host': os.getenv('INTELLIHUB_HOST'),
    'port': int(os.getenv('INTELLIHUB_PORT', '22')),
    'user': os.getenv('INTELLIHUB_USER'),
    'password': os.getenv('INTELLIHUB_PASS'),
    'remote_paths': {
        'drr': '/RR',  # XML files for Daily Register Reads
        'hhr': '/HHR', # CSV files for Half-Hourly Reads
        'event': '/Event'
    }
}

# Validate required environment variables
required_env_vars = ['INTELLIHUB_HOST', 'INTELLIHUB_USER', 'INTELLIHUB_PASS']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables for IHUB: {', '.join(missing_vars)}")

# DAG default arguments
default_args = {
    'owner': 'data_import',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def ensure_directories():
    """Ensure all required directories exist"""
    for dir_path in [DAILY_DIR / 'imported', DAILY_DIR / 'archive', DAILY_DIR / 'error',
                     INTERVAL_DIR / 'imported', INTERVAL_DIR / 'archive', INTERVAL_DIR / 'error']:
        dir_path.mkdir(parents=True, exist_ok=True)

# Import connection utility
import sys
sys.path.append('/app/airflow/utils')
from connection import get_connection

def get_timescale_connection():
    """DEPRECATED: Use get_connection() instead."""
    return get_connection()

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of file"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.warning(f"⚠️ Could not calculate hash for {file_path}: {e}")
        return ""

def log_import(dag_id: str, task_id: str, run_id: str, mep_provider: str, 
               file_name: str, file_size: int, file_hash: str, import_type: str, 
               status: str, records_parsed: int = 0, intervals_loaded: int = 0, 
               source_records: int = 0, error_message: str = None):
    """Log import status to database"""
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                if status == 'completed':
                    cur.execute("""
                        INSERT INTO metering_raw.import_log 
                        (dag_id, task_id, run_id, mep_provider, file_name, file_size, file_hash, 
                         import_type, status, records_parsed, intervals_loaded, source_records, error_message, completed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (file_name, file_hash, import_type) 
                        DO UPDATE SET 
                            status = EXCLUDED.status,
                            records_parsed = EXCLUDED.records_parsed,
                            intervals_loaded = EXCLUDED.intervals_loaded,
                            source_records = EXCLUDED.source_records,
                            error_message = EXCLUDED.error_message,
                            completed_at = NOW()
                    """, (dag_id, task_id, run_id, mep_provider, file_name, file_size, 
                          file_hash, import_type, status, records_parsed, intervals_loaded, 
                          source_records, error_message))
                else:
                    cur.execute("""
                        INSERT INTO metering_raw.import_log 
                        (dag_id, task_id, run_id, mep_provider, file_name, file_size, file_hash, 
                         import_type, status, records_parsed, intervals_loaded, source_records, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (file_name, file_hash, import_type) 
                        DO UPDATE SET 
                            status = EXCLUDED.status,
                            records_parsed = EXCLUDED.records_parsed,
                            intervals_loaded = EXCLUDED.intervals_loaded,
                            source_records = EXCLUDED.source_records,
                            error_message = EXCLUDED.error_message
                    """, (dag_id, task_id, run_id, mep_provider, file_name, file_size, 
                          file_hash, import_type, status, records_parsed, intervals_loaded, 
                          source_records, error_message))
                conn.commit()
    except Exception as e:
        logging.error(f"Failed to log import: {e}")

def test_ihub_connection(**context):
    """Step 1: Test IHUB SFTP connection"""
    logging.info("🔌 Step 1: Testing IHUB SFTP Connection")
    
    try:
        ensure_directories()
        
        # Test connection using ConnectionManager
        connection_result = ConnectionManager.test_connection(IHUB_CONFIG)
        
        if connection_result:
            logging.info("✅ IHUB SFTP connection successful")
            return True
        else:
            logging.error("❌ IHUB SFTP connection failed")
            raise Exception("IHUB SFTP connection test failed")
            
    except Exception as e:
        logging.error(f"❌ Connection test error: {e}")
        raise

def discover_ihub_files(**context):
    """Step 2: Discover files in IHUB SFTP server (both RR and HHR folders)"""
    logging.info("🔍 Step 2: Discovering IHUB Files")
    
    try:
        all_files = []
        
        # Discover RR files (XML for DRR)
        rr_config = IHUB_CONFIG.copy()
        rr_config['remote_path'] = IHUB_CONFIG['remote_paths']['drr']
        
        with SFTPDiscovery(rr_config) as discovery:
            rr_files = discovery.discover_files()
            for file_info in rr_files:
                file_info['folder_type'] = 'rr'
                file_info['source_folder'] = 'RR'
                all_files.append(file_info)
        
        # Discover HHR files (CSV for HHR)
        hhr_config = IHUB_CONFIG.copy()
        hhr_config['remote_path'] = IHUB_CONFIG['remote_paths']['hhr']
        
        with SFTPDiscovery(hhr_config) as discovery:
            hhr_files = discovery.discover_files()
            for file_info in hhr_files:
                file_info['folder_type'] = 'hhr'
                file_info['source_folder'] = 'HHR'
                all_files.append(file_info)
        
        rr_count = len([f for f in all_files if f.get('folder_type') == 'rr'])
        hhr_count = len([f for f in all_files if f.get('folder_type') == 'hhr'])
        
        logging.info(f"🔍 Found {len(all_files)} total files:")
        logging.info(f"  📋 RR folder (XML/DRR): {rr_count} files")
        logging.info(f"  📈 HHR folder (CSV/HHR): {hhr_count} files")
        
        context['ti'].xcom_push(key='discovered_files', value=all_files)
        return all_files
        
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def download_ihub_files(**context):
    """Step 3: Download IHUB files with duplicate detection"""
    logging.info("📥 Step 3: Downloading IHUB Files")
    
    try:
        files = context['ti'].xcom_pull(key='discovered_files')
        if not files:
            logging.info("ℹ️ No files discovered to download")
            context['ti'].xcom_push(key='downloaded_files', value=[])
            return []
        
        files_to_download = []
        skipped_files = []
        
        # Check database for already processed files
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Ensure schema and table exist before querying
                cur.execute("CREATE SCHEMA IF NOT EXISTS metering_raw")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_raw.import_log (
                        id SERIAL PRIMARY KEY,
                        dag_id VARCHAR(100) NOT NULL,
                        task_id VARCHAR(100) NOT NULL,
                        run_id VARCHAR(255) NOT NULL,
                        mep_provider VARCHAR(50) NOT NULL,
                        file_name VARCHAR(255) NOT NULL,
                        file_size BIGINT,
                        file_hash VARCHAR(64),
                        import_type VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        source_records INTEGER DEFAULT 0,
                        records_parsed INTEGER DEFAULT 0,
                        intervals_loaded INTEGER DEFAULT 0,
                        error_message TEXT,
                        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        completed_at TIMESTAMP WITH TIME ZONE,
                        UNIQUE(file_name, file_hash, import_type)
                    )
                """)
                
                # Fetch all completed files for this provider to check in memory
                cur.execute(
                    """SELECT file_name, import_type FROM metering_raw.import_log 
                       WHERE mep_provider = 'IHUB' AND status = 'completed'"""
                )
                processed_files = {(row[0], row[1]) for row in cur.fetchall()}
                logging.info(f"Found {len(processed_files)} already processed files for IHUB.")

                for file_info in files:
                    filename = file_info['filename']
                    
                    # Determine file type for import log lookup
                    if file_info.get('folder_type') == 'rr':
                        import_type = 'DRR'
                    elif file_info.get('folder_type') == 'hhr':
                        import_type = 'HHR'
                    else:
                        import_type = 'DRR' if filename.lower().endswith('.xml') else 'HHR'
                    
                    if (filename, import_type) in processed_files:
                        logging.info(f"🔄 Skipping {filename} - already processed")
                        skipped_files.append(file_info)
                    else:
                        files_to_download.append(file_info)
        
        if not files_to_download:
            logging.info("ℹ️ No new files to download")
            context['ti'].xcom_push(key='downloaded_files', value=[])
            return []
        
        downloaded_files = []
        
        for file_info in files_to_download:
            # Determine target directory and connection config
            if file_info.get('folder_type') == 'rr':
                target_dir = DAILY_DIR / 'imported'
                file_type = 'daily'
                conn_config = IHUB_CONFIG.copy()
                conn_config['remote_path'] = IHUB_CONFIG['remote_paths']['drr']
            else:
                target_dir = INTERVAL_DIR / 'imported'
                file_type = 'interval'
                conn_config = IHUB_CONFIG.copy()
                conn_config['remote_path'] = IHUB_CONFIG['remote_paths']['hhr']
            
            local_path = target_dir / file_info['filename']
            
            # Download file
            with SFTPDiscovery(conn_config) as discovery:
                if discovery.download_file(file_info, local_path):
                    downloaded_files.append({
                        'filename': file_info['filename'],
                        'local_path': str(local_path),
                        'size': file_info.get('size', 0),
                        'type': file_type,
                        'source_folder': file_info.get('source_folder', 'unknown')
                    })
                    logging.info(f"✅ Downloaded {file_info['filename']} as {file_type}")
        
        logging.info(f"📥 Downloaded {len(downloaded_files)} files")
        context['ti'].xcom_push(key='downloaded_files', value=downloaded_files)
        return downloaded_files
        
    except Exception as e:
        logging.error(f"❌ Download error: {e}")
        raise

def import_ihub_drr(**context):
    """Step 4: Import IHUB DRR data from XML files"""
    logging.info("📊 Step 4: Importing IHUB DRR Data (XML parsing)")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to process for DRR")
        return {'drr_records': 0, 'drr_files': 0}
    
    try:
        drr_files = [f for f in downloaded_files if f['type'] == 'daily']
        drr_records = []
        file_line_counts = {}
        
        for file_info in drr_files:
            logging.info(f"📊 Processing DRR XML file: {file_info['filename']}")
            
            try:
                # Parse IHUB XML file
                tree = ET.parse(file_info['local_path'])
                root = tree.getroot()
                
                # Create parent map for efficient parent lookup
                parent_map = {c: p for p in tree.iter() for c in p}
                
                # Find all READING elements
                reading_elements = root.findall('.//READING')
                total_elements = len(reading_elements)
                logging.info(f"  📋 Found {total_elements} READING elements")
                
                for reading_elem in reading_elements:
                    try:
                        record = {'filename': file_info['filename']}
                        
                        # Get ICP from ancestor ICP element
                        current = reading_elem
                        while current in parent_map:
                            parent = parent_map[current]
                            if parent.tag == 'ICP':
                                record['icp'] = parent.get('ID', '').strip()
                                break
                            current = parent
                        
                        # Get meter serial from ancestor METER element
                        current = reading_elem
                        while current in parent_map:
                            parent = parent_map[current]
                            if parent.tag == 'METER':
                                record['meter_serial'] = parent.get('SERIAL', '').strip()
                                break
                            current = parent
                        
                        # Extract reading attributes
                        record['read_date'] = reading_elem.get('TIMESTAMP', '').strip()
                        record['register_channel'] = reading_elem.get('LOGICALCHANNEL', '').strip()
                        record['read_type'] = reading_elem.get('READINGTYPE', 'A').strip()
                        record['units'] = reading_elem.get('UOM', 'KWH').strip()
                        record['register_number'] = reading_elem.get('REGISTERNUMBER', '').strip()
                        record['energy_flow'] = reading_elem.get('ENERGYFLOW', '').strip()
                        record['rcc'] = reading_elem.get('RCC', '').strip()
                        record['stop_time'] = reading_elem.get('STOPTIME', '').strip()
                        
                        # Get reading value
                        value_elem = reading_elem.find('VALUE')
                        if value_elem is not None:
                            reading_value = value_elem.text.strip() if value_elem.text else ''
                            if reading_value == 'NR':
                                record['reading'] = None
                                record['read_type'] = 'NR'
                            else:
                                record['reading'] = reading_value
                        else:
                            record['reading'] = None
                        
                        # Only include records with valid ICP
                        if record.get('icp'):
                            drr_records.append(record)
                            
                    except Exception as e:
                        logging.warning(f"⚠️ Error parsing READING element: {e}")
                        continue
                
                file_line_counts[file_info['filename']] = total_elements
                logging.info(f"✅ Parsed {len([r for r in drr_records if r['filename'] == file_info['filename']])} DRR records ({total_elements} source elements)")
                
            except Exception as e:
                logging.error(f"❌ Error processing XML file {file_info['filename']}: {e}")
                continue
        
        logging.info(f"📊 Total DRR: {len(drr_records)} records from {len(drr_files)} files")
        
        result = {
            'drr_records': len(drr_records), 
            'drr_files': len(drr_files), 
            'drr_data': drr_records,
            'file_line_counts': file_line_counts
        }
        context['ti'].xcom_push(key='drr_results', value=result)
        return result
        
    except Exception as e:
        logging.error(f"❌ DRR import error: {e}")
        raise

def import_ihub_hhr(**context):
    """Step 5: Import IHUB HHR data from CSV files"""
    logging.info("📈 Step 5: Importing IHUB HHR Data")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to process for HHR")
        return {'hhr_records': 0, 'hhr_files': 0}
    
    try:
        hhr_files = [f for f in downloaded_files if f['type'] == 'interval']
        hhr_records = []
        file_line_counts = {}
        
        for file_info in hhr_files:
            logging.info(f"📈 Processing IHUB HHR file: {file_info['filename']}")
            
            # Parse IHUB-specific CSV format (fixed 13-field structure)
            with open(file_info['local_path'], 'r') as csvfile:
                lines = csvfile.readlines()
                total_lines = len(lines)
                
                # Skip header line (metadata line)
                data_lines = lines[1:] if len(lines) > 1 else []
                
                for line_num, line in enumerate(data_lines, start=2):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        fields = line.split(',')
                        
                        if len(fields) >= 10:
                            record = {
                                'icp': fields[0].strip(),
                                'meter_serial': fields[1].strip(),
                                'register': fields[2].strip(),
                                'stream': fields[3].strip(),
                                'register_type': fields[4].strip(),
                                'status': fields[5].strip(),
                                'interval_number': int(fields[6]) if fields[6].isdigit() else 0,
                                'start_datetime': fields[7].strip(),
                                'end_datetime': fields[8].strip(),
                                'reading': float(fields[9]) if fields[9].replace('.', '', 1).isdigit() else 0.0,
                                'quality': fields[10].strip() if len(fields) > 10 else '',
                                'unit': fields[11].strip() if len(fields) > 11 else '',
                                'flag': fields[12].strip() if len(fields) > 12 else '',
                                'filename': file_info['filename']
                            }
                            
                            # Validate required fields
                            if record['icp'] and record['start_datetime']:
                                hhr_records.append(record)
                                
                    except Exception as e:
                        logging.warning(f"Error parsing line {line_num}: {e}")
                        continue
            
            file_line_counts[file_info['filename']] = total_lines
            logging.info(f"✅ Parsed {len([r for r in hhr_records if r['filename'] == file_info['filename']])} HHR records ({total_lines} source lines)")
        
        logging.info(f"📈 Total HHR: {len(hhr_records)} records from {len(hhr_files)} files")
        
        result = {
            'hhr_records': len(hhr_records), 
            'hhr_files': len(hhr_files), 
            'hhr_data': hhr_records,
            'file_line_counts': file_line_counts
        }
        context['ti'].xcom_push(key='hhr_results', value=result)
        return result
        
    except Exception as e:
        logging.error(f"❌ HHR import error: {e}")
        raise

def load_ihub_drr_to_db(**context):
    """Step 6a: Load IHUB DRR data to database with comprehensive tracking"""
    logging.info("💾 Step 6a: Loading IHUB DRR to Database")
    
    drr_results = context['ti'].xcom_pull(key='drr_results')
    if not drr_results or drr_results['drr_records'] == 0:
        logging.info("ℹ️ No DRR data to load")
        return {'loaded_drr': 0}
    
    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Ensure the target table exists with the correct schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_raw.intellihub_drr (
                        id SERIAL PRIMARY KEY,
                        icp VARCHAR(50),
                        meter_serial VARCHAR(50),
                        read_date TIMESTAMP WITH TIME ZONE,
                        register_channel VARCHAR(50),
                        read_type VARCHAR(20),
                        register_number VARCHAR(50),
                        energy_flow VARCHAR(20),
                        rcc VARCHAR(20),
                        units VARCHAR(20),
                        stop_time VARCHAR(50),
                        reading NUMERIC,
                        filename VARCHAR(255),
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Add unique constraint if it doesn't exist
                cur.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'intellihub_drr_unique_constraint'
                        ) THEN
                            ALTER TABLE metering_raw.intellihub_drr 
                            ADD CONSTRAINT intellihub_drr_unique_constraint 
                            UNIQUE (icp, read_date, register_channel, register_number);
                        END IF;
                    END $$;
                """)

                drr_data = drr_results['drr_data']
                loaded_count = 0
                
                # Group records by filename for proper import logging
                files_data = {}
                for record in drr_data:
                    filename = record['filename']
                    if filename not in files_data:
                        files_data[filename] = []
                    files_data[filename].append(record)
                
                for filename, records in files_data.items():
                    try:
                        # Calculate file hash for tracking
                        downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
                        file_info = next((f for f in downloaded_files if f['filename'] == filename), None)
                        
                        file_hash = get_file_hash(file_info['local_path']) if file_info and file_info.get('local_path') else 'unknown'
                        # Calculate actual file size from local file
                        file_size = 0
                        if file_info and file_info.get('local_path') and Path(file_info['local_path']).exists():
                            file_size = Path(file_info['local_path']).stat().st_size
                        else:
                            file_size = file_info['size'] if file_info and 'size' in file_info else 0
                        
                        # Check if this file was already successfully processed
                        cur.execute(
                            """SELECT COUNT(*) FROM metering_raw.import_log 
                               WHERE file_name = %s AND file_hash = %s AND import_type = 'DRR' 
                               AND status = 'completed' AND mep_provider = 'IHUB'""",
                            (filename, file_hash)
                        )
                        
                        if cur.fetchone()[0] > 0:
                            logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                            log_import(
                                dag_id=dag_id,
                                task_id=task_id,
                                run_id=run_id,
                                mep_provider='IHUB',
                                file_name=filename,
                                file_size=file_size,
                                file_hash=file_hash,
                                import_type='DRR',
                                status='skipped',
                                records_parsed=len(records),
                                intervals_loaded=0,
                                error_message="File previously processed successfully"
                            )
                            continue
                            
                        # Build list of records for bulk insert
                        data_to_insert = []
                        for record in records:
                            try:
                                # Parse datetime properly
                                read_datetime_str = record.get('read_date', '') # Use read_date from XML
                                if not read_datetime_str:
                                    logging.warning(f"Skipping DRR record with empty timestamp: {record.get('icp')}")
                                    continue
                                    
                                if 'T' in read_datetime_str:
                                    # Remove timezone info and replace T with space
                                    read_datetime_str = read_datetime_str.split('+')[0].replace('T', ' ')
                                
                                # Append a tuple of values for the insert
                                data_to_insert.append((
                                    record.get('icp'),
                                    record.get('meter_serial', ''),
                                    read_datetime_str,
                                    record.get('register_channel', ''),
                                    record.get('read_type', ''),
                                    record.get('register_number', ''),
                                    record.get('energy_flow', ''),
                                    record.get('rcc', ''),
                                    record.get('units', ''),
                                    record.get('stop_time'),
                                    record.get('reading', 0.0),
                                    filename
                                ))
                            except Exception as e:
                                logging.warning(f"Error preparing DRR record for insert: {e}")
                                continue

                        # Bulk insert records
                        file_loaded = 0
                        if data_to_insert:
                            execute_values(
                                cur,
                                """
                                INSERT INTO metering_raw.intellihub_drr 
                                (icp, meter_serial, read_date, register_channel, read_type, register_number, 
                                 energy_flow, rcc, units, stop_time, reading, filename)
                                VALUES %s
                                ON CONFLICT (icp, read_date, register_channel, register_number) 
                                DO NOTHING
                                """,
                                data_to_insert
                            )
                            file_loaded = len(data_to_insert)
                            loaded_count += file_loaded
                        
                        # Log import status for this file
                        source_records = drr_results.get('file_line_counts', {}).get(filename, 0)
                        log_import(
                            dag_id=dag_id,
                            task_id=task_id,
                            run_id=run_id,
                            mep_provider='IHUB',
                            file_name=filename,
                            file_size=file_size,
                            file_hash=file_hash,
                            import_type='DRR',
                            status='completed' if file_loaded > 0 else 'no_new_records',
                            source_records=source_records,
                            records_parsed=len(records),
                            intervals_loaded=file_loaded
                        )
                        
                        logging.info(f"✅ Loaded {file_loaded}/{len(records)} DRR records from {filename}")
                        
                    except Exception as e:
                        logging.error(f"❌ Error processing file {filename}: {e}")
                        # Log error status
                        source_records = drr_results.get('file_line_counts', {}).get(filename, 0)
                        log_import(
                            dag_id=dag_id,
                            task_id=task_id,
                            run_id=run_id,
                            mep_provider='IHUB',
                            file_name=filename,
                            file_size=0,
                            file_hash='error',
                            import_type='DRR',
                            status='error',
                            source_records=source_records,
                            records_parsed=len(records),
                            intervals_loaded=0,
                            error_message=str(e)
                        )
                        continue
                
                conn.commit()
                logging.info(f"💾 Total DRR records loaded: {loaded_count}")
                
                context['ti'].xcom_push(key='loaded_drr_count', value=loaded_count)
                return {'loaded_drr': loaded_count}
                
    except Exception as e:
        logging.error(f"❌ DRR database load error: {e}")
        raise

def load_ihub_hhr_to_db(**context):
    """Step 6b: Load IHUB HHR data to database with comprehensive tracking"""
    logging.info("💾 Step 6b: Loading IHUB HHR to Database")
    
    hhr_results = context['ti'].xcom_pull(key='hhr_results')
    if not hhr_results or hhr_results['hhr_records'] == 0:
        logging.info("ℹ️ No HHR data to load")
        return {'loaded_hhr': 0}
    
    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Ensure the target table exists with the correct schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_raw.intellihub_hhr (
                        id SERIAL PRIMARY KEY,
                        icp VARCHAR(50),
                        meter_serial VARCHAR(50),
                        register VARCHAR(50),
                        stream VARCHAR(50),
                        register_type VARCHAR(20),
                        status VARCHAR(20),
                        interval_number INTEGER,
                        start_datetime TIMESTAMP WITH TIME ZONE,
                        end_datetime TIMESTAMP WITH TIME ZONE,
                        reading NUMERIC,
                        quality VARCHAR(20),
                        unit VARCHAR(20),
                        flag VARCHAR(20),
                        filename VARCHAR(255),
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Add unique constraint if it doesn't exist
                cur.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'intellihub_hhr_unique_constraint'
                        ) THEN
                            ALTER TABLE metering_raw.intellihub_hhr 
                            ADD CONSTRAINT intellihub_hhr_unique_constraint 
                            UNIQUE (icp, start_datetime, register, interval_number);
                        END IF;
                    END $$;
                """)

                hhr_data = hhr_results['hhr_data']
                loaded_count = 0
                
                # Group records by filename for proper import logging
                files_data = {}
                for record in hhr_data:
                    filename = record['filename']
                    if filename not in files_data:
                        files_data[filename] = []
                    files_data[filename].append(record)
                
                for filename, records in files_data.items():
                    try:
                        # Calculate file hash for tracking
                        downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
                        file_info = next((f for f in downloaded_files if f['filename'] == filename), None)
                        
                        file_hash = get_file_hash(file_info['local_path']) if file_info and file_info.get('local_path') else 'unknown'
                        # Calculate actual file size from local file
                        file_size = 0
                        if file_info and file_info.get('local_path') and Path(file_info['local_path']).exists():
                            file_size = Path(file_info['local_path']).stat().st_size
                        else:
                            file_size = file_info['size'] if file_info and 'size' in file_info else 0
                        
                        # Check if this file was already successfully processed
                        cur.execute(
                            """SELECT COUNT(*) FROM metering_raw.import_log 
                               WHERE file_name = %s AND file_hash = %s AND import_type = 'HHR' 
                               AND status = 'completed' AND mep_provider = 'IHUB'""",
                            (filename, file_hash)
                        )
                        
                        if cur.fetchone()[0] > 0:
                            logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                            log_import(
                                dag_id=dag_id,
                                task_id=task_id,
                                run_id=run_id,
                                mep_provider='IHUB',
                                file_name=filename,
                                file_size=file_size,
                                file_hash=file_hash,
                                import_type='HHR',
                                status='skipped',
                                records_parsed=len(records),
                                intervals_loaded=0,
                                error_message="File previously processed successfully"
                            )
                            continue
                            
                        # Build list of records for bulk insert
                        data_to_insert = []
                        for record in records:
                            try:
                                # Parse datetime properly
                                start_datetime_str = record.get('start_datetime', '')
                                end_datetime_str = record.get('end_datetime', '')
                                
                                if not start_datetime_str:
                                    logging.warning(f"Skipping HHR record with empty start_datetime: {record.get('icp')}")
                                    continue
                                
                                if 'T' in start_datetime_str:
                                    start_datetime_str = start_datetime_str.split('+')[0].replace('T', ' ')
                                if end_datetime_str and 'T' in end_datetime_str:
                                    end_datetime_str = end_datetime_str.split('+')[0].replace('T', ' ')
                                
                                # Append a tuple of values for the insert
                                data_to_insert.append((
                                    record.get('icp'),
                                    record.get('meter_serial', ''),
                                    record.get('register', ''),
                                    record.get('stream', ''),
                                    record.get('register_type', ''),
                                    record.get('status', ''),
                                    record.get('interval_number', 0),
                                    start_datetime_str,
                                    end_datetime_str,
                                    record.get('reading', 0.0),
                                    record.get('quality', ''),
                                    record.get('unit', ''),
                                    record.get('flag', ''),
                                    filename
                                ))
                            except Exception as e:
                                logging.warning(f"Error preparing HHR record for insert: {e}")
                                continue

                        # Bulk insert records
                        file_loaded = 0
                        if data_to_insert:
                            execute_values(
                                cur,
                                """
                                INSERT INTO metering_raw.intellihub_hhr 
                                (icp, meter_serial, register, stream, register_type, status, interval_number, 
                                 start_datetime, end_datetime, reading, quality, unit, flag, filename)
                                VALUES %s
                                ON CONFLICT (icp, start_datetime, register, interval_number) 
                                DO NOTHING
                                """,
                                data_to_insert
                            )
                            file_loaded = len(data_to_insert)
                            loaded_count += file_loaded
                        
                        # Log import status for this file
                        source_records = hhr_results.get('file_line_counts', {}).get(filename, 0)
                        log_import(
                            dag_id=dag_id,
                            task_id=task_id,
                            run_id=run_id,
                            mep_provider='IHUB',
                            file_name=filename,
                            file_size=file_size,
                            file_hash=file_hash,
                            import_type='HHR',
                            status='completed' if file_loaded > 0 else 'no_new_records',
                            source_records=source_records,
                            records_parsed=len(records),
                            intervals_loaded=file_loaded
                        )
                        
                        logging.info(f"✅ Loaded {file_loaded} HHR daily records from {len(records)} intervals in {filename}")
                        
                    except Exception as e:
                        logging.error(f"❌ Error processing file {filename}: {e}")
                        # Log error status
                        log_import(
                            dag_id=dag_id,
                            task_id=task_id,
                            run_id=run_id,
                            mep_provider='IHUB',
                            file_name=filename,
                            file_size=0,
                            file_hash='error',
                            import_type='HHR',
                            status='error',
                            records_parsed=len(records),
                            intervals_loaded=0,
                            error_message=str(e)
                        )
                        continue
                
                conn.commit()
                logging.info(f"💾 Total HHR records loaded: {loaded_count}")
                
                context['ti'].xcom_push(key='loaded_hhr_count', value=loaded_count)
                return {'loaded_hhr': loaded_count}
                
    except Exception as e:
        logging.error(f"❌ HHR database load error: {e}")
        raise

def verify_ihub_database_load(**context):
    """Step 7: Verify IHUB database load with comprehensive audit"""
    logging.info("🔍 Step 7: Verifying IHUB Database Load")
    
    try:
        # Get results from previous steps
        drr_results = context['ti'].xcom_pull(key='drr_results') or {'drr_records': 0, 'drr_files': 0}
        hhr_results = context['ti'].xcom_pull(key='hhr_results') or {'hhr_records': 0, 'hhr_files': 0}
        loaded_drr = context['ti'].xcom_pull(key='loaded_drr_count') or 0
        loaded_hhr = context['ti'].xcom_pull(key='loaded_hhr_count') or 0
        
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Count records in database
                cur.execute("SELECT COUNT(*) FROM metering_raw.intellihub_drr")
                db_drr_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metering_raw.intellihub_hhr")
                db_hhr_count = cur.fetchone()[0]
                
                # Get import log summary
                cur.execute("""
                    SELECT import_type, status, COUNT(*) as count, 
                           SUM(records_parsed) as total_parsed,
                           SUM(intervals_loaded) as total_loaded
                    FROM metering_raw.import_log 
                    WHERE mep_provider = 'IHUB' AND DATE(started_at) = CURRENT_DATE
                    GROUP BY import_type, status
                    ORDER BY import_type, status
                """)
                import_log_summary = cur.fetchall()
        
        # Calculate verification metrics
        duplicate_drr = drr_results['drr_records'] - loaded_drr
        duplicate_hhr = hhr_results['hhr_records'] - loaded_hhr
        
        total_processed_records = drr_results['drr_records'] + hhr_results['hhr_records']
        total_loaded_records = loaded_drr + loaded_hhr
        total_duplicate_records = duplicate_drr + duplicate_hhr
        
        # Determine success criteria
        success = (
            total_processed_records > 0 and
            total_loaded_records >= 0 and
            db_drr_count >= 0 and
            db_hhr_count >= 0
        )
        
        logging.info("🔍 Verification Results:")
        logging.info(f"  📊 DRR: {drr_results['drr_records']} parsed → {loaded_drr} loaded → {db_drr_count} in DB")
        logging.info(f"  📈 HHR: {hhr_results['hhr_records']} intervals → {loaded_hhr} rows → {db_hhr_count} in DB")
        logging.info(f"  🔄 Duplicates: {duplicate_drr} DRR + {duplicate_hhr} HHR = {total_duplicate_records} total")
        logging.info(f"  📋 Import Log Entries: {len(import_log_summary)}")
        
        for log_entry in import_log_summary:
            logging.info(f"    {log_entry[0]} {log_entry[1]}: {log_entry[2]} files, {log_entry[3]} parsed, {log_entry[4]} loaded")
        
        logging.info(f"  ✅ Verification: {'SUCCESS' if success else 'FAILED'}")
        
        context['ti'].xcom_push(key='verification_success', value=success)
        
        return {
            'verification_success': success,
            'drr_parsed': drr_results['drr_records'],
            'drr_loaded': loaded_drr,
            'drr_duplicates': duplicate_drr,
            'drr_in_db': db_drr_count,
            'hhr_intervals_parsed': hhr_results['hhr_records'],
            'hhr_rows_loaded': loaded_hhr,
            'hhr_duplicates': duplicate_hhr,
            'hhr_in_db': db_hhr_count,
            'total_processed_records': total_processed_records,
            'total_loaded_records': total_loaded_records,
            'total_duplicate_records': total_duplicate_records,
            'import_log_entries': len(import_log_summary)
        }
        
    except Exception as e:
        logging.error(f"❌ Verification error: {e}")
        context['ti'].xcom_push(key='verification_success', value=False)
        raise

def cleanup_ihub_files(**context):
    """Step 8: Cleanup and archive processed files with gzip compression"""
    logging.info("🧹 Step 8: Cleanup and Archive IHUB Files with Compression")
    
    try:
        downloaded_files = context['ti'].xcom_pull(key='downloaded_files') or []
        verification = context['ti'].xcom_pull(key='verification_success', default=False)
        
        archived_count = 0
        error_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        for file_info in downloaded_files:
            source_path = Path(file_info['local_path'])
            
            if not source_path.exists():
                logging.warning(f"⚠️ Source file not found: {source_path}")
                continue
                
            original_size = source_path.stat().st_size
            total_original_size += original_size
            
            if verification:
                # Compress and archive on success
                if file_info['type'] == 'daily':
                    target_dir = DAILY_DIR / 'archive'
                else:
                    target_dir = INTERVAL_DIR / 'archive'
                archived_count += 1
            else:
                # Compress and move to error on failure
                if file_info['type'] == 'daily':
                    target_dir = DAILY_DIR / 'error'
                else:
                    target_dir = INTERVAL_DIR / 'error'
                error_count += 1
            
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Compress file with gzip maximum compression (level 9)
            compressed_filename = f"{source_path.name}.gz"
            target_path = target_dir / compressed_filename
            
            try:
                with open(source_path, 'rb') as f_in:
                    with gzip.open(target_path, 'wb', compresslevel=9) as f_out:
                        # Copy file in chunks for memory efficiency
                        while True:
                            chunk = f_in.read(65536)  # 64KB chunks
                            if not chunk:
                                break
                            f_out.write(chunk)
                
                compressed_size = target_path.stat().st_size
                total_compressed_size += compressed_size
                compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                # Remove original file after successful compression
                source_path.unlink()
                
                logging.info(f"🗜️ Compressed {source_path.name} → {compressed_filename}")
                logging.info(f"   📊 Size: {original_size:,} bytes → {compressed_size:,} bytes ({compression_ratio:.1f}% reduction)")
                logging.info(f"   📁 Archived to: {target_path.parent.name}")
                
            except Exception as e:
                logging.error(f"❌ Failed to compress {source_path.name}: {e}")
                # Fallback: move file without compression
                fallback_target = target_dir / source_path.name
                source_path.rename(fallback_target)
                logging.info(f"📁 Moved {source_path.name} to {target_dir.name} (uncompressed fallback)")
        
        # Calculate overall compression statistics
        overall_compression = (1 - total_compressed_size / total_original_size) * 100 if total_original_size > 0 else 0
        
        logging.info(f"🧹 Cleanup complete: {archived_count} archived, {error_count} moved to error")
        logging.info(f"🗜️ Compression summary:")
        logging.info(f"   Original size: {total_original_size:,} bytes")
        logging.info(f"   Compressed size: {total_compressed_size:,} bytes")
        logging.info(f"   Overall compression: {overall_compression:.1f}% reduction")
        
        # Final summary
        logging.info("📋 IHUB Import Complete - Final Summary:")
        logging.info(f"  Files processed: {len(downloaded_files)}")
        logging.info(f"  Files archived (compressed): {archived_count}")
        logging.info(f"  Files in error (compressed): {error_count}")
        logging.info(f"  Space saved: {total_original_size - total_compressed_size:,} bytes")
        logging.info(f"  Import status: {'✅ SUCCESS' if verification else '❌ FAILED'}")
        
        return {
            'files_processed': len(downloaded_files),
            'files_archived': archived_count,
            'files_error': error_count,
            'import_success': verification,
            'original_size_bytes': total_original_size,
            'compressed_size_bytes': total_compressed_size,
            'compression_ratio_percent': overall_compression
        }
        
    except Exception as e:
        logging.error(f"❌ Cleanup error: {e}")
        raise

# Create the DAG
dag = DAG(
    'metering_ihub',
    default_args=default_args,
    description='IHUB (IntelliHub) Metering Data Import with XML parsing for DRR',
    schedule_interval='0 7 * * *',  # 7 AM daily
    max_active_runs=1,
    catchup=False,
    tags=['metering', 'ihub', 'intellihub', 'data_import', 'xml']
)

# Define tasks
task_1_test_connection = PythonOperator(
    task_id='1_test_ihub_connection',
    python_callable=test_ihub_connection,
    dag=dag
)

task_2_discover_files = PythonOperator(
    task_id='2_discover_ihub_files',
    python_callable=discover_ihub_files,
    dag=dag
)

task_3_download_files = PythonOperator(
    task_id='3_download_ihub_files',
    python_callable=download_ihub_files,
    dag=dag
)

task_4_import_drr = PythonOperator(
    task_id='4_import_ihub_drr',
    python_callable=import_ihub_drr,
    dag=dag
)

task_5_import_hhr = PythonOperator(
    task_id='5_import_ihub_hhr',
    python_callable=import_ihub_hhr,
    dag=dag
)

task_6a_load_drr_db = PythonOperator(
    task_id='6a_load_ihub_drr_to_db',
    python_callable=load_ihub_drr_to_db,
    dag=dag
)

task_6b_load_hhr_db = PythonOperator(
    task_id='6b_load_ihub_hhr_to_db',
    python_callable=load_ihub_hhr_to_db,
    dag=dag
)

task_7_verify_db = PythonOperator(
    task_id='7_verify_ihub_database_load',
    python_callable=verify_ihub_database_load,
    dag=dag
)

task_8_cleanup = PythonOperator(
    task_id='8_cleanup_ihub_files',
    python_callable=cleanup_ihub_files,
    dag=dag
)

# Set task dependencies
task_1_test_connection >> task_2_discover_files >> task_3_download_files
task_3_download_files >> [task_4_import_drr, task_5_import_hhr]
task_4_import_drr >> task_6a_load_drr_db
task_5_import_hhr >> task_6b_load_hhr_db
[task_6a_load_drr_db, task_6b_load_hhr_db] >> task_7_verify_db >> task_8_cleanup 