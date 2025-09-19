"""
Switching Files Import DAG

Downloads ALL switching files from SFTP /fromreg/ folder and imports them RAW into database tables.
Follows the same philosophy as metering_bcmm.py and registry_information_files.py:
- Download all switching files (not selective)
- Import raw into database tables
- Simple file-based duplicate detection
- Comprehensive logging

Author: SpotOn Data Team
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import logging
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import hashlib
import gzip

# Add utils to path
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/switching/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))

# Default arguments
default_args = {
    'owner': 'switching_import',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 25),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),  # Add timeout
    'catchup': False
}

# Data processing directories - Create nested structure by file type
DATA_DIR = Path('/data/imports/electricity/switching')

def ensure_directories():
    """Ensure processing directories exist with proper nested structure by file type"""
    # Create nested directories by switching file type first, then by status
    switching_types = ['NT', 'AN', 'CS', 'RR', 'AC', 'NW', 'AW']
    status_dirs = ['imported', 'archive', 'error']
    
    for switch_type in switching_types:
        for status_dir in status_dirs:
            (DATA_DIR / switch_type / status_dir).mkdir(parents=True, exist_ok=True)
    
    logging.info("✅ Created nested directory structure: {TYPE}/{STATUS} format")

def get_timescale_connection():
    """Get TimescaleDB connection"""
# Import connection utility
import sys
sys.path.append('/app/airflow/utils')
from connection import get_connection

def get_timescale_connection():
    """DEPRECATED: Use get_connection() instead."""
    return get_connection()

def test_registry_connection(**context):
    """Step 1: Test Registry SFTP connection (switching files use same registry source)"""
    logging.info("🔍 Step 1: Testing Registry SFTP Connection for Switching Files")
    
    try:
        from connection_manager import ConnectionManager
        
        # Use ConnectionManager for consistency with registry DAG
        conn_config = ConnectionManager.get_connection_config(
            protocol='SFTP',
            prefix='REGISTRY',
            default_host=None,
            default_port=22,
            default_user=None
        )
        # Override remote path for registry files (switching files come from same source)
        conn_config['remote_path'] = '/fromreg/'
        
        logging.info(f"Testing connection to {conn_config['host']}:{conn_config['port']}")
        
        if ConnectionManager.test_connection(conn_config):
            logging.info("✅ Registry connection successful")
            context['ti'].xcom_push(key='connection_status', value='success')
            context['ti'].xcom_push(key='conn_config', value=conn_config)
            return True
        else:
            logging.error("❌ Registry connection failed")
            context['ti'].xcom_push(key='connection_status', value='failed')
            raise Exception("Registry connection test failed")
            
    except Exception as e:
        logging.error(f"❌ Connection test error: {e}")
        raise

def discover_switching_files(**context):
    """Step 2: Discover ALL switching files (following metering philosophy)"""
    logging.info("📁 Step 2: Discovering ALL Switching Files")
    
    conn_config = context['ti'].xcom_pull(key='conn_config')
    if not conn_config:
        logging.info("ℹ️ No connection data from previous task, creating new connection config")
        from connection_manager import ConnectionManager
        # Use ConnectionManager for consistency with registry DAG
        conn_config = ConnectionManager.get_connection_config(
            protocol='SFTP',
            prefix='REGISTRY',
            default_host=None,
            default_port=22,
            default_user=None
        )
        # Override remote path for registry files (switching files come from same source)
        conn_config['remote_path'] = '/fromreg/'
    
    try:
        from connection_manager import ConnectionManager
        
        # Get ALL files and filter for switching files
        logging.info("🔍 Scanning for ALL files and filtering for switching files...")
        all_files = ConnectionManager.list_remote_files(conn_config, r'^.*$')  # Get ALL files
        
        # Filter for switching file types
        switching_files = []
        for filename in all_files:
            file_type = classify_switching_file_type(filename)
            if file_type.startswith('SWITCHING-'):
                switching_files.append({
                    'filename': filename,
                    'file_type': file_type,
                    'size': 0  # Size will be determined during download
                })
        
        logging.info(f"📊 Found {len(switching_files)} switching files out of {len(all_files)} total files:")
        
        # Group by file type for summary
        type_counts = {}
        for file_info in switching_files:
            file_type = file_info['file_type']
            if file_type not in type_counts:
                type_counts[file_type] = []
            type_counts[file_type].append(file_info['filename'])
        
        for file_type, files in type_counts.items():
            logging.info(f"  📄 {file_type}: {len(files)} files")
            for filename in files:
                logging.info(f"    - {filename}")
        
        context['ti'].xcom_push(key='discovered_files', value=switching_files)
        context['ti'].xcom_push(key='conn_config', value=conn_config)
        context['ti'].xcom_push(key='total_files', value=len(switching_files))
        
        return switching_files
        
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def classify_switching_file_type(filename: str) -> str:
    """Classify switching file type based on filename patterns - ONLY switching files"""
    filename_lower = filename.lower()
    
    # Only classify actual switching files (NT, AN, CS, RR, AC, NW, AW)
    if filename_lower.startswith('nt') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-NT-REQUEST'
    elif filename_lower.startswith('an') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-AN-ACKNOWLEDGE'
    elif filename_lower.startswith('cs') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-CS-COMPLETE'
    elif filename_lower.startswith('rr') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-RR-REPLACE'
    elif filename_lower.startswith('ac') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-AC-READACK'
    elif filename_lower.startswith('nw') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-NW-WITHDRAWAL'
    elif filename_lower.startswith('aw') and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-AW-WITHACK'
    else:
        return 'OTHER'  # Not a switching file

def download_switching_files(**context):
    """Step 3: Download ALL switching files with duplicate checking and organize by file type"""
    logging.info("⬇️ Step 3: Downloading ALL Switching Files")
    
    discovered_files = context['ti'].xcom_pull(key='discovered_files')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    if not discovered_files:
        logging.info("ℹ️ No switching files discovered")
        return []
    
    if not conn_config:
        logging.info("ℹ️ No connection config, creating new one")
        from connection_manager import ConnectionManager
        # Use ConnectionManager for consistency with registry DAG
        conn_config = ConnectionManager.get_connection_config(
            protocol='SFTP',
            prefix='REGISTRY',
            default_host=None,
            default_port=22,
            default_user=None
        )
        # Override remote path for registry files (switching files come from same source)
        conn_config['remote_path'] = '/fromreg/'
    
    try:
        from connection_manager import ConnectionManager
        
        # Ensure directories exist
        ensure_directories()
        
        # Create switching tables before checking import log
        conn = get_timescale_connection()
        cur = conn.cursor()
        create_switching_tables(cur)
        conn.commit()
        
        # Get already processed files from import_log
        cur.execute("""
            SELECT file_name, file_hash 
            FROM switching.import_log 
            WHERE status = 'success'
        """)
        processed_files = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
        conn.close()
        
        downloaded_files = []
        skipped_files = []
        
        for file_info in discovered_files:
            filename = file_info['filename']
            file_type = file_info['file_type']
            
            # Extract file type prefix for folder organization
            file_type_prefix = get_file_type_prefix(file_type)
            
            if not file_type_prefix:
                logging.warning(f"⚠️ Unknown file type for {filename}, skipping")
                continue
            
            # Create nested path based on file type: {TYPE}/{STATUS}
            local_file_path = DATA_DIR / file_type_prefix / 'imported' / filename
            
            try:
                # Download file
                if ConnectionManager.download_file(conn_config, filename, local_file_path):
                    # Calculate hash
                    file_hash = calculate_file_hash(local_file_path)
                    file_size = local_file_path.stat().st_size
                    
                    # Check if already processed
                    if filename in processed_files and processed_files[filename] == file_hash:
                        logging.info(f"⏭️ Skipping already processed file: {filename}")
                        skipped_files.append({
                            'filename': filename,
                            'file_type': file_type,
                            'reason': 'already_processed',
                            'local_path': str(local_file_path)
                        })
                        # Move to archive: {TYPE}/archive/
                        archive_path = DATA_DIR / file_type_prefix / 'archive' / filename
                        archive_path.parent.mkdir(parents=True, exist_ok=True)
                        local_file_path.rename(archive_path)
                        continue
                    
                    downloaded_files.append({
                        'filename': filename,
                        'file_type': file_type,
                        'file_type_prefix': file_type_prefix,
                        'local_path': str(local_file_path),
                        'file_size': file_size,
                        'file_hash': file_hash
                    })
                    
                    logging.info(f"✅ Downloaded: {filename} -> {file_type_prefix}/ ({file_size} bytes)")
                else:
                    logging.error(f"❌ Failed to download: {filename}")
                    
            except Exception as e:
                logging.error(f"❌ Error downloading {filename}: {e}")
                # Move to error folder if it exists: {TYPE}/error/
                if local_file_path.exists():
                    error_path = DATA_DIR / file_type_prefix / 'error' / filename
                    error_path.parent.mkdir(parents=True, exist_ok=True)
                    local_file_path.rename(error_path)
        
        logging.info(f"📊 Download Summary:")
        logging.info(f"  ✅ Downloaded: {len(downloaded_files)} files")
        logging.info(f"  ⏭️ Skipped: {len(skipped_files)} files")
        
        # Group by file type for summary
        type_counts = {}
        for file_info in downloaded_files:
            file_type_prefix = file_info['file_type_prefix']
            if file_type_prefix not in type_counts:
                type_counts[file_type_prefix] = []
            type_counts[file_type_prefix].append(file_info['filename'])
        
        for file_type_prefix, files in type_counts.items():
            logging.info(f"  📁 {file_type_prefix}/: {len(files)} files")
        
        context['ti'].xcom_push(key='downloaded_files', value=downloaded_files)
        context['ti'].xcom_push(key='skipped_files', value=skipped_files)
        context['ti'].xcom_push(key='total_downloaded', value=len(downloaded_files))
        
        return downloaded_files
        
    except Exception as e:
        logging.error(f"❌ Download error: {e}")
        raise

def get_file_type_prefix(file_type: str) -> str:
    """Extract file type prefix for folder organization"""
    if file_type.startswith('SWITCHING-'):
        # Extract the file type code (NT, AN, CS, RR, AC, NW, AW)
        parts = file_type.split('-')
        if len(parts) >= 2:
            return parts[1]  # NT, AN, CS, RR, AC, NW, AW
    return None

def import_switching_files_raw(**context):
    """Step 4: Import ALL switching files with comprehensive CSV parsing"""
    logging.info("💾 Step 4: Importing ALL Switching Files with Functional Spec Parsing")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No switching files to import")
        return {'imported_files': 0, 'total_records': 0}

    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Create the schema and all tables
                create_switching_tables(cur)
                
                imported_count = 0
                total_records = 0
                
                for i, file_info in enumerate(downloaded_files, 1):
                    filename = file_info['filename']
                    file_path = Path(file_info['local_path'])
                    file_size = file_info['file_size']
                    file_type = file_info['file_type']
                    
                    logging.info(f"📄 Processing file {i}/{len(downloaded_files)}: {filename} ({file_type})")
                    
                    try:
                        # Check if file exists
                        if not file_path.exists():
                            logging.error(f"❌ File not found: {file_path}")
                            continue
                        
                        # Calculate file hash with progress logging
                        logging.info(f"🔍 Calculating file hash for {filename}...")
                        file_hash = calculate_file_hash(file_path)
                        logging.info(f"✅ File hash calculated")
                        
                        # Check if already imported by looking in import_log
                        logging.info(f"🔍 Checking for duplicates: {filename}")
                        cur.execute(
                            """SELECT COUNT(*) FROM switching.import_log 
                               WHERE file_name = %s AND file_hash = %s AND status = 'completed'""",
                            (filename, file_hash)
                        )
                        
                        if cur.fetchone()[0] > 0:
                            logging.info(f"🔄 Skipping {filename} - already imported")
                            continue
                        
                        # Parse file based on type and import into specific tables
                        logging.info(f"📖 Parsing file: {filename}")
                        parsed_records = parse_switching_file(file_path, file_type, filename)
                        logging.info(f"✅ Parsed {len(parsed_records)} records from {filename}")
                        
                        if not parsed_records:
                            logging.warning(f"⚠️ No records found in {filename}")
                            continue
                        
                        # Import parsed records into specific tables
                        logging.info(f"💾 Importing {len(parsed_records)} records for {filename}")
                        loaded_records = import_parsed_switching_records(cur, file_type, filename, parsed_records, file_hash)
                        logging.info(f"✅ Imported {loaded_records} records")
                        
                        imported_count += 1
                        total_records += len(parsed_records)
                        
                        # Commit after each file to prevent long transactions
                        conn.commit()
                        logging.info(f"💾 Committed changes for {filename}")
                        
                        # Log import
                        log_import(
                            dag_id=dag_id,
                            task_id=task_id,
                            run_id=run_id,
                            source_group='SWITCHING',
                            file_name=filename,
                            file_type=file_type,
                            file_size=file_size,
                            file_hash=file_hash,
                            status='completed',
                            records_parsed=len(parsed_records),
                            records_loaded=loaded_records
                        )
                        
                        logging.info(f"✅ Completed processing {filename}: {len(parsed_records)} records")
                        
                    except Exception as file_error:
                        logging.error(f"❌ Failed to import {filename}: {file_error}")
                        import traceback
                        logging.error(f"📋 Error details: {traceback.format_exc()}")
                        
                        # Log failed import and continue with next file
                        try:
                            log_import(
                                dag_id=dag_id,
                                task_id=task_id,
                                run_id=run_id,
                                source_group='SWITCHING',
                                file_name=filename,
                                file_type=file_type,
                                file_size=file_size,
                                file_hash=file_hash if 'file_hash' in locals() else '',
                                status='failed',
                                records_parsed=0,
                                records_loaded=0,
                                error_message=str(file_error)
                            )
                            conn.commit()
                        except Exception as log_error:
                            logging.error(f"❌ Failed to log error for {filename}: {log_error}")
                        
                        # Continue with next file instead of failing entire import
                        continue
                
                conn.commit()
                
                logging.info(f"📊 Import Summary: {imported_count} files, {total_records} total records")
                
                context['ti'].xcom_push(key='imported_files', value=imported_count)
                context['ti'].xcom_push(key='total_records', value=total_records)
                
                return {'imported_files': imported_count, 'total_records': total_records}
        
    except Exception as e:
        logging.error(f"❌ Import error: {e}")
        
        # Log errors for each file
        if downloaded_files:
            for file_info in downloaded_files:
                log_import(
                    dag_id=dag_id,
                    task_id=task_id,
                    run_id=run_id,
                    source_group='SWITCHING',
                    file_name=file_info['filename'],
                    file_type=file_info['file_type'],
                    file_size=file_info['file_size'],
                    file_hash='',
                    status='failed',
                    records_parsed=0,
                    records_loaded=0,
                    error_message=str(e)
                )
        
        raise

def create_switching_tables(cur):
    """Create switching tables based on FS1.txt functional specifications
    
    Each file type gets its own table with:
    - Header information as columns (HDR record)
    - Detail records (P, I, M, R) as separate rows with their specific fields
    """
    
    # Create schema
    cur.execute("CREATE SCHEMA IF NOT EXISTS switching;")
    
    # NT Request table (New Trader Request) - RS-010 - ONLY P records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.nt_requests (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P only
            
            -- P record fields (Premises/Point record)
            icp VARCHAR(50),
            requesting_trader VARCHAR(10),
            confirmation_address_unit VARCHAR(50),
            confirmation_address_number VARCHAR(75),
            confirmation_address_street VARCHAR(100),
            confirmation_address_suburb VARCHAR(100),
            confirmation_address_town VARCHAR(100),
            confirmation_address_postcode VARCHAR(20),
            confirmation_address_region VARCHAR(50),
            confirmation_property_name VARCHAR(200),
            proposed_transfer_date DATE,
            switch_type VARCHAR(10),
            proposed_profiles VARCHAR(75),
            proposed_anzsic VARCHAR(20),
            user_reference VARCHAR(100),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # AN Acknowledge table (Acknowledgment) - RS-020 - ONLY P records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.an_acknowledges (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P only
            
            -- P record fields
            icp VARCHAR(50),
            trader VARCHAR(10),
            response_code VARCHAR(10),
            expected_transfer_date DATE,
            user_reference VARCHAR(100),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # CS Complete table (Completion) - RS-050 - P, I, M, R records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.cs_completions (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P, I, M, R
            
            -- P record fields (Premises record)
            icp VARCHAR(50),
            trader VARCHAR(10),
            actual_transfer_date DATE,
            user_reference VARCHAR(100),
            metering_installation_number INTEGER,
            
            -- Installation record fields (I record)
            installation_number INTEGER,
            average_daily_consumption DECIMAL(12,2),
            key_held_indicator VARCHAR(1),
            
            -- Meter record fields (M record)
            meter_serial_number VARCHAR(75),
            last_read_date DATE,
            meter_reader_notes VARCHAR(150),
            
            -- Register/Channel record fields (R record)
            channel_number INTEGER,
            reading DECIMAL(15,3),
            actual_or_estimate VARCHAR(1),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # RR Replace table (Replacement) - RS-050 - P and R records only
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.rr_replacements (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P, R only
            
            -- P record fields (Premises record)
            icp VARCHAR(50),
            trader VARCHAR(10),
            actual_transfer_date DATE,
            user_reference VARCHAR(100),
            metering_installation_number INTEGER,
            
            -- Register/Channel record fields (R record)
            meter_serial_number VARCHAR(75),
            channel_number INTEGER,
            reading DECIMAL(15,3),
            actual_or_estimate VARCHAR(1),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # AC ReadAck table (Read Acknowledgment) - RC-020 - ONLY P records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.ac_readacks (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P only
            
            -- P record fields
            icp VARCHAR(50),
            trader VARCHAR(10),
            actual_transfer_date DATE,
            switch_read_acknowledgement VARCHAR(1),
            user_reference VARCHAR(100),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # NW Withdrawal table (Withdrawal) - RW-010 - ONLY P records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.nw_withdrawals (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P only
            
            -- P record fields
            icp VARCHAR(50),
            trader VARCHAR(10),
            withdrawal_advisory_code VARCHAR(10),
            user_reference VARCHAR(100),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # AW WithAck table (Withdrawal Acknowledgment) - RW-020 - ONLY P records
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.aw_withacks (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- Header information (HDR record)
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_user_reference VARCHAR(100),
            
            -- Detail record information
            record_type VARCHAR(10),  -- P only
            
            -- P record fields
            icp VARCHAR(50),
            trader VARCHAR(10),
            withdrawal_transfer_status VARCHAR(10),
            user_reference VARCHAR(100),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Import log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS switching.import_log (
            id SERIAL PRIMARY KEY,
            dag_id VARCHAR(100),
            task_id VARCHAR(100),
            run_id VARCHAR(100),
            source_group VARCHAR(50),
            file_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(100),
            file_size BIGINT,
            file_hash VARCHAR(64),
            status VARCHAR(20),
            records_parsed INTEGER DEFAULT 0,
            records_loaded INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
    """)
    
    # Create indexes for performance
    index_commands = [
        "CREATE INDEX IF NOT EXISTS idx_nt_requests_file_name ON switching.nt_requests(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_nt_requests_file_hash ON switching.nt_requests(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_nt_requests_icp ON switching.nt_requests(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_an_acknowledges_file_name ON switching.an_acknowledges(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_an_acknowledges_file_hash ON switching.an_acknowledges(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_an_acknowledges_icp ON switching.an_acknowledges(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_cs_completions_file_name ON switching.cs_completions(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_cs_completions_file_hash ON switching.cs_completions(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_cs_completions_icp ON switching.cs_completions(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_rr_replacements_file_name ON switching.rr_replacements(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_rr_replacements_file_hash ON switching.rr_replacements(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_rr_replacements_icp ON switching.rr_replacements(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_ac_readacks_file_name ON switching.ac_readacks(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_ac_readacks_file_hash ON switching.ac_readacks(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_ac_readacks_icp ON switching.ac_readacks(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_nw_withdrawals_file_name ON switching.nw_withdrawals(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_nw_withdrawals_file_hash ON switching.nw_withdrawals(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_nw_withdrawals_icp ON switching.nw_withdrawals(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_aw_withacks_file_name ON switching.aw_withacks(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_aw_withacks_file_hash ON switching.aw_withacks(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_aw_withacks_icp ON switching.aw_withacks(icp);",
        
        "CREATE INDEX IF NOT EXISTS idx_import_log_file_name ON switching.import_log(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_import_log_file_hash ON switching.import_log(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_import_log_status ON switching.import_log(status);"
    ]
    
    for cmd in index_commands:
        cur.execute(cmd)
    
    logging.info("✅ All switching tables created successfully with proper FS1.txt schema")

def parse_switching_file(file_path: Path, file_type: str, filename: str):
    """Parse switching file based on type and return structured records"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    
        if file_type == 'SWITCHING-NT-REQUEST':
            return parse_nt_request(lines, filename)
        elif file_type == 'SWITCHING-AN-ACKNOWLEDGE':
            return parse_an_acknowledge(lines, filename)
        elif file_type == 'SWITCHING-CS-COMPLETE':
            return parse_cs_completion(lines, filename)
        elif file_type == 'SWITCHING-RR-REPLACE':
            return parse_rr_replacement(lines, filename)
        elif file_type == 'SWITCHING-AC-READACK':
            return parse_ac_readack(lines, filename)
        elif file_type == 'SWITCHING-NW-WITHDRAWAL':
            return parse_nw_withdrawal(lines, filename)
        elif file_type == 'SWITCHING-AW-WITHACK':
            return parse_aw_withack(lines, filename)
        else:
            # Generic parsing for unknown switching file types
            return parse_generic_switching_file(lines, filename)
            
    except Exception as e:
        logging.error(f"Error parsing {filename}: {e}")
        return []

def parse_nt_request(lines, filename):
    """Parse NT (New Trader Request) files according to FS1.txt RS-010 specification"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            # Parse header record: HDR,process_id,sender,recipient,date,time,count,user_ref
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # Parse P record: P,ICP,Requesting_Trader,Address_Unit,Address_Number,Address_Street,
            # Address_Suburb,Address_Town,Address_Postcode,Address_Region,Property_Name,
            # Proposed_Transfer_Date,Switch_Type,Proposed_Profiles,Proposed_ANZSIC,User_Reference
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else '',
                'requesting_trader': fields[2] if len(fields) > 2 else '',
                'confirmation_address_unit': fields[3] if len(fields) > 3 else '',
                'confirmation_address_number': fields[4] if len(fields) > 4 else '',
                'confirmation_address_street': fields[5] if len(fields) > 5 else '',
                'confirmation_address_suburb': fields[6] if len(fields) > 6 else '',
                'confirmation_address_town': fields[7] if len(fields) > 7 else '',
                'confirmation_address_postcode': fields[8] if len(fields) > 8 else '',
                'confirmation_address_region': fields[9] if len(fields) > 9 else '',
                'confirmation_property_name': fields[10] if len(fields) > 10 else '',
                'proposed_transfer_date': parse_date(fields[11]) if len(fields) > 11 else None,
                'switch_type': fields[12] if len(fields) > 12 else '',
                'proposed_profiles': fields[13] if len(fields) > 13 else '',
                'proposed_anzsic': fields[14] if len(fields) > 14 else '',
                'user_reference': fields[15] if len(fields) > 15 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_an_acknowledge(lines, filename):
    """Parse AN (Acknowledge) files according to FS1.txt RS-020 specification"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # Parse P record: P,ICP,Trader,Response_Code,Expected_Transfer_Date,User_Reference
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else '',
                'trader': fields[2] if len(fields) > 2 else '',
                'response_code': fields[3] if len(fields) > 3 else '',
                'expected_transfer_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'user_reference': fields[5] if len(fields) > 5 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_cs_completion(lines, filename):
    """Parse CS (Completion) files according to FS1.txt RS-050 specification
    
    CS files can have P, I, M, R record types in sequence
    """
    records = []
    header_info = None
    current_icp = None
    current_installation = None
    current_meter = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # P record: P,ICP,Trader,Actual_Transfer_Date,User_Reference,Metering_Installation_Number
            current_icp = fields[1] if len(fields) > 1 else ''
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': current_icp,
                'trader': fields[2] if len(fields) > 2 else '',
                'actual_transfer_date': parse_date(fields[3]) if len(fields) > 3 else None,
                'user_reference': fields[4] if len(fields) > 4 else '',
                'metering_installation_number': parse_int(fields[5]) if len(fields) > 5 else None,
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
        elif line.startswith('I'):
            # I record: I,ICP,Metering_Installation_Number,Average_Daily_Consumption,Key_Held_Indicator
            current_installation = parse_int(fields[2]) if len(fields) > 2 else None
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else current_icp,
                'installation_number': current_installation,
                'average_daily_consumption': parse_decimal(fields[3]) if len(fields) > 3 else None,
                'key_held_indicator': fields[4] if len(fields) > 4 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
        elif line.startswith('M'):
            # M record: M,ICP,Metering_Installation_Number,Metering_Component_Serial_Number,Last_Read_Date,Meter_Reader_Notes
            current_meter = fields[3] if len(fields) > 3 else ''
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else current_icp,
                'installation_number': parse_int(fields[2]) if len(fields) > 2 else current_installation,
                'meter_serial_number': current_meter,
                'last_read_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'meter_reader_notes': fields[5] if len(fields) > 5 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
        elif line.startswith('R'):
            # R record: R,ICP,Metering_Installation_Number,Metering_Component_Serial_Number,Channel_Number,Reading,Actual_or_Estimate
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else current_icp,
                'installation_number': parse_int(fields[2]) if len(fields) > 2 else current_installation,
                'meter_serial_number': fields[3] if len(fields) > 3 else current_meter,
                'channel_number': parse_int(fields[4]) if len(fields) > 4 else None,
                'reading': parse_decimal(fields[5]) if len(fields) > 5 else None,
                'actual_or_estimate': fields[6] if len(fields) > 6 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_rr_replacement(lines, filename):
    """Parse RR (Replacement) files according to FS1.txt RS-050 specification
    
    RR files have P and R record types only
    """
    records = []
    header_info = None
    current_icp = None
    current_installation = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # P record: P,ICP,Trader,Actual_Transfer_Date,User_Reference,Metering_Installation_Number
            current_icp = fields[1] if len(fields) > 1 else ''
            current_installation = parse_int(fields[5]) if len(fields) > 5 else None
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': current_icp,
                'trader': fields[2] if len(fields) > 2 else '',
                'actual_transfer_date': parse_date(fields[3]) if len(fields) > 3 else None,
                'user_reference': fields[4] if len(fields) > 4 else '',
                'metering_installation_number': current_installation,
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
        elif line.startswith('R'):
            # R record: R,ICP,Metering_Installation_Number,Metering_Component_Serial_Number,Channel_Number,Reading,Actual_or_Estimate
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else current_icp,
                'installation_number': parse_int(fields[2]) if len(fields) > 2 else current_installation,
                'meter_serial_number': fields[3] if len(fields) > 3 else '',
                'channel_number': parse_int(fields[4]) if len(fields) > 4 else None,
                'reading': parse_decimal(fields[5]) if len(fields) > 5 else None,
                'actual_or_estimate': fields[6] if len(fields) > 6 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_ac_readack(lines, filename):
    """Parse AC (Read Acknowledgment) files according to FS1.txt RC-020 specification"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # P record: P,ICP,Trader,Actual_Transfer_Date,Switch_Read_Acknowledgement,User_Reference
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else '',
                'trader': fields[2] if len(fields) > 2 else '',
                'actual_transfer_date': parse_date(fields[3]) if len(fields) > 3 else None,
                'switch_read_acknowledgement': fields[4] if len(fields) > 4 else '',
                'user_reference': fields[5] if len(fields) > 5 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_nw_withdrawal(lines, filename):
    """Parse NW (Withdrawal) files according to FS1.txt RW-010 specification"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # P record: P,ICP,Trader,Withdrawal_Advisory_Code,User_Reference
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else '',
                'trader': fields[2] if len(fields) > 2 else '',
                'withdrawal_advisory_code': fields[3] if len(fields) > 3 else '',
                'user_reference': fields[4] if len(fields) > 4 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_aw_withack(lines, filename):
    """Parse AW (Withdrawal Acknowledgment) files according to FS1.txt RW-020 specification"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_user_reference': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            # P record: P,ICP,Trader,Withdrawal_Transfer_Status,User_Reference
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp': fields[1] if len(fields) > 1 else '',
                'trader': fields[2] if len(fields) > 2 else '',
                'withdrawal_transfer_status': fields[3] if len(fields) > 3 else '',
                'user_reference': fields[4] if len(fields) > 4 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_generic_switching_file(lines, filename):
    """Generic parser for unknown switching file types"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            header_info = {
                'record_type': fields[0] if len(fields) > 0 else '',
                'process_identifier': fields[1] if len(fields) > 1 else '',
                'sender': fields[2] if len(fields) > 2 else '',
                'recipient': fields[3] if len(fields) > 3 else '',
                'creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'creation_time': fields[5] if len(fields) > 5 else '',
                'record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'description': fields[7] if len(fields) > 7 else ''
            }
        elif line.startswith('P'):
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'data_fields': fields[1:] if len(fields) > 1 else [],
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_date(date_str):
    """Parse date string to DATE format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        from datetime import datetime
        # Handle various date formats
        date_str = date_str.strip()
        if len(date_str) == 8:  # YYYYMMDD
            return datetime.strptime(date_str, '%Y%m%d').date()
        elif len(date_str) == 10 and '-' in date_str:  # YYYY-MM-DD
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        elif len(date_str) == 10 and '/' in date_str:  # DD/MM/YYYY
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        else:
            return None
    except:
        return None

def parse_time(time_str):
    """Parse time string to TIME format"""
    if not time_str or time_str.strip() == '':
        return None
    try:
        from datetime import datetime
        # Handle various time formats
        time_str = time_str.strip()
        if len(time_str) == 4:  # HHMM
            return datetime.strptime(time_str, '%H%M').time()
        elif len(time_str) == 5 and ':' in time_str:  # HH:MM
            return datetime.strptime(time_str, '%H:%M').time()
        elif len(time_str) == 8 and ':' in time_str:  # HH:MM:SS
            return datetime.strptime(time_str, '%H:%M:%S').time()
        else:
            return None
    except:
        return None

def parse_int(int_str):
    """Parse integer string"""
    if not int_str or int_str.strip() == '':
        return None
    try:
        return int(int_str.strip())
    except:
        return None

def parse_decimal(decimal_str):
    """Parse decimal string"""
    if not decimal_str or decimal_str.strip() == '':
        return None
    try:
        return float(decimal_str.strip())
    except:
        return None

def import_parsed_switching_records(cur, file_type, filename, records, file_hash):
    """Import parsed records into appropriate switching tables"""
    if file_type == 'SWITCHING-NT-REQUEST':
        return import_nt_request_records(cur, filename, records, file_hash)
    elif file_type == 'SWITCHING-AN-ACKNOWLEDGE':
        return import_an_acknowledge_records(cur, filename, records, file_hash)
    elif file_type == 'SWITCHING-CS-COMPLETE':
        return import_cs_completion_records(cur, filename, records, file_hash)
    elif file_type == 'SWITCHING-RR-REPLACE':
        return import_rr_replacement_records(cur, filename, records, file_hash)
    elif file_type == 'SWITCHING-AC-READACK':
        return import_ac_readack_records(cur, filename, records, file_hash)
    elif file_type == 'SWITCHING-NW-WITHDRAWAL':
        return import_nw_withdrawal_records(cur, filename, records, file_hash)
    elif file_type == 'SWITCHING-AW-WITHACK':
        return import_aw_withack_records(cur, filename, records, file_hash)
    else:
        logging.warning(f"Unknown switching file type: {file_type}")
        return 0

def import_nt_request_records(cur, filename, records, file_hash):
    """Import NT Request records with proper FS1.txt schema"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.nt_requests (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, requesting_trader, confirmation_address_unit,
            confirmation_address_number, confirmation_address_street, confirmation_address_suburb,
            confirmation_address_town, confirmation_address_postcode, confirmation_address_region,
            confirmation_property_name, proposed_transfer_date, switch_type,
            proposed_profiles, proposed_anzsic, user_reference,
            total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('requesting_trader'),
            record.get('confirmation_address_unit'), record.get('confirmation_address_number'),
            record.get('confirmation_address_street'), record.get('confirmation_address_suburb'),
            record.get('confirmation_address_town'), record.get('confirmation_address_postcode'),
            record.get('confirmation_address_region'), record.get('confirmation_property_name'),
            record.get('proposed_transfer_date'), record.get('switch_type'),
            record.get('proposed_profiles'), record.get('proposed_anzsic'),
            record.get('user_reference'), record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_an_acknowledge_records(cur, filename, records, file_hash):
    """Import AN Acknowledge records with proper FS1.txt schema"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.an_acknowledges (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, trader, response_code, expected_transfer_date, user_reference,
            total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('trader'),
            record.get('response_code'), record.get('expected_transfer_date'),
            record.get('user_reference'), record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_cs_completion_records(cur, filename, records, file_hash):
    """Import CS Completion records with proper FS1.txt schema (handles P, I, M, R records)"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.cs_completions (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, trader, actual_transfer_date, user_reference,
            metering_installation_number, installation_number, average_daily_consumption,
            key_held_indicator, meter_serial_number, last_read_date, meter_reader_notes,
            channel_number, reading, actual_or_estimate,
            total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('trader'),
            record.get('actual_transfer_date'), record.get('user_reference'),
            record.get('metering_installation_number'), record.get('installation_number'),
            record.get('average_daily_consumption'), record.get('key_held_indicator'),
            record.get('meter_serial_number'), record.get('last_read_date'),
            record.get('meter_reader_notes'), record.get('channel_number'),
            record.get('reading'), record.get('actual_or_estimate'),
            record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_rr_replacement_records(cur, filename, records, file_hash):
    """Import RR Replacement records with proper FS1.txt schema (handles P, R records)"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.rr_replacements (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, trader, actual_transfer_date, user_reference,
            metering_installation_number, meter_serial_number, channel_number,
            reading, actual_or_estimate,
            total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('trader'),
            record.get('actual_transfer_date'), record.get('user_reference'),
            record.get('metering_installation_number'), record.get('meter_serial_number'),
            record.get('channel_number'), record.get('reading'), record.get('actual_or_estimate'),
            record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_ac_readack_records(cur, filename, records, file_hash):
    """Import AC ReadAck records with proper FS1.txt schema"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.ac_readacks (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, trader, actual_transfer_date, switch_read_acknowledgement,
            user_reference, total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('trader'),
            record.get('actual_transfer_date'), record.get('switch_read_acknowledgement'),
            record.get('user_reference'), record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_nw_withdrawal_records(cur, filename, records, file_hash):
    """Import NW Withdrawal records with proper FS1.txt schema"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.nw_withdrawals (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, trader, withdrawal_advisory_code, user_reference,
            total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('trader'),
            record.get('withdrawal_advisory_code'), record.get('user_reference'),
            record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_aw_withack_records(cur, filename, records, file_hash):
    """Import AW WithAck records with proper FS1.txt schema"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO switching.aw_withacks (
            file_name, file_hash, line_number,
            hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
            hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_user_reference,
            record_type, icp, trader, withdrawal_transfer_status, user_reference,
            total_fields, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        header = record.get('header_info', {})
        values.append((
            filename, file_hash, record.get('line_number'),
            header.get('hdr_record_type'), header.get('hdr_process_identifier'),
            header.get('hdr_sender'), header.get('hdr_recipient'),
            header.get('hdr_creation_date'), header.get('hdr_creation_time'),
            header.get('hdr_record_count'), header.get('hdr_user_reference'),
            record.get('record_type'), record.get('icp'), record.get('trader'),
            record.get('withdrawal_transfer_status'), record.get('user_reference'),
            record.get('total_fields'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def verify_switching_import(**context):
    """Step 5: Verify import with comprehensive audit"""
    logging.info("🔍 Step 5: Verifying Switching Import")
    
    try:
        imported_files = context['ti'].xcom_pull(key='imported_files') or 0
        total_records = context['ti'].xcom_pull(key='total_records') or 0
        
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Count records across all switching tables
                table_counts = {}
                tables = ['nt_requests', 'an_acknowledges', 'cs_completions', 'rr_replacements', 
                         'ac_readacks', 'nw_withdrawals', 'aw_withacks']
                
                total_db_records = 0
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM switching.{table}")
                    count = cur.fetchone()[0]
                    table_counts[table] = count
                    total_db_records += count
                
                # Get file type breakdown from import_log
                cur.execute("""
                    SELECT file_type, COUNT(DISTINCT file_name) as file_count, 
                           SUM(records_loaded) as total_records
                    FROM switching.import_log 
                    WHERE status = 'completed'
                    GROUP BY file_type 
                    ORDER BY file_count DESC
                """)
                type_breakdown = cur.fetchall()
                
                # Get recent import activity
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM switching.import_log 
                    WHERE started_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY status
                """)
                recent_imports = cur.fetchall()
        
        logging.info("📊 Switching Import Verification:")
        logging.info(f"  📁 Files - This run: {imported_files}")
        logging.info(f"  📄 Records - This run: {total_records}, Total in DB: {total_db_records}")
        
        logging.info("📋 Table Record Counts:")
        for table, count in table_counts.items():
            if count > 0:
                logging.info(f"  {table}: {count} records")
        
        if type_breakdown:
            logging.info("📋 File Type Breakdown:")
            for file_type, file_count, total_records_type in type_breakdown:
                logging.info(f"  {file_type}: {file_count} files, {total_records_type or 0} records")
        
        if recent_imports:
            logging.info("📈 Recent Import Activity (24h):")
            for status, count in recent_imports:
                logging.info(f"  {status.upper()}: {count} files")
        
        # Verification logic
        success = True
        if imported_files > 0:
            if total_db_records >= total_records:
                logging.info("✅ Import verification successful")
            else:
                logging.warning("⚠️ Record count mismatch in database")
                success = False
        else:
            logging.info("ℹ️ No new switching files imported (all were duplicates)")
        
        context['ti'].xcom_push(key='verification_success', value=success)
        
        return {
            'verification_success': success,
            'imported_files': imported_files,
            'total_records': total_records,
            'total_db_records': total_db_records,
            'table_counts': table_counts
        }
        
    except Exception as e:
        logging.error(f"❌ Verification error: {e}")
        raise

def cleanup_switching_files(**context):
    """Step 6: Cleanup and archive processed files with compression"""
    logging.info("🧹 Step 6: Cleanup and Archive Switching Files")
    
    try:
        downloaded_files = context['ti'].xcom_pull(key='downloaded_files') or []
        verification_success = context['ti'].xcom_pull(key='verification_success', default=False)
        
        if not downloaded_files:
            logging.info("ℹ️ No switching files to cleanup")
            return {'files_processed': 0}
        
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
            
            # Determine target directory based on verification success
            if verification_success:
                target_dir = DATA_DIR / 'archive'
                archived_count += 1
            else:
                target_dir = DATA_DIR / 'error'
                error_count += 1
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Compress file with gzip
            compressed_filename = f"{source_path.name}.gz"
            target_path = target_dir / compressed_filename
            
            try:
                with open(source_path, 'rb') as f_in:
                    with gzip.open(target_path, 'wb', compresslevel=9) as f_out:
                        while True:
                            chunk = f_in.read(65536)  # 64KB chunks
                            if not chunk:
                                break
                            f_out.write(chunk)
                
                compressed_size = target_path.stat().st_size
                total_compressed_size += compressed_size
                compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                
                # Remove original file
                source_path.unlink()
                
                logging.info(f"🗜️ Compressed {source_path.name} → {compressed_filename}")
                logging.info(f"   📊 Size: {original_size:,} → {compressed_size:,} bytes ({compression_ratio:.1f}% reduction)")
                
            except Exception as e:
                logging.error(f"❌ Failed to compress {source_path.name}: {e}")
                # Fallback: move without compression
                fallback_target = target_dir / source_path.name
                source_path.rename(fallback_target)
        
        overall_compression = (1 - total_compressed_size / total_original_size) * 100 if total_original_size > 0 else 0
        
        logging.info(f"🧹 Cleanup Summary:")
        logging.info(f"  Files archived: {archived_count}")
        logging.info(f"  Files in error: {error_count}")
        logging.info(f"  Compression: {overall_compression:.1f}% reduction")
        logging.info(f"  Space saved: {total_original_size - total_compressed_size:,} bytes")
        
        return {
            'files_processed': len(downloaded_files),
            'files_archived': archived_count,
            'files_error': error_count,
            'compression_ratio': overall_compression
        }
        
    except Exception as e:
        logging.error(f"❌ Cleanup error: {e}")
        raise

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file with progress logging"""
    hash_sha256 = hashlib.sha256()
    file_size = file_path.stat().st_size
    bytes_read = 0
    
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)  # 64KB chunks for faster processing
            if not chunk:
                break
            hash_sha256.update(chunk)
            bytes_read += len(chunk)
            
            # Log progress for large files
            if file_size > 1024*1024 and bytes_read % (1024*1024) == 0:  # Every 1MB
                progress = (bytes_read / file_size) * 100
                logging.info(f"   📊 Hash progress: {progress:.1f}% ({bytes_read:,}/{file_size:,} bytes)")
    
    return hash_sha256.hexdigest()

def log_import(dag_id: str, task_id: str, run_id: str, source_group: str, 
               file_name: str, file_type: str, file_size: int, file_hash: str, 
               status: str, records_parsed: int = 0, records_loaded: int = 0, 
               error_message: str = None):
    """Log import activity to switching.import_log table"""
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                if status == 'completed':
                    cur.execute("""
                        INSERT INTO switching.import_log 
                        (dag_id, task_id, run_id, source_group, file_name, file_type, 
                         file_size, file_hash, status, records_parsed, records_loaded, completed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (dag_id, task_id, run_id, source_group, file_name, file_type,
                          file_size, file_hash, status, records_parsed, records_loaded))
                else:
                    cur.execute("""
                        INSERT INTO switching.import_log 
                        (dag_id, task_id, run_id, source_group, file_name, file_type, 
                         file_size, file_hash, status, records_parsed, records_loaded, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (dag_id, task_id, run_id, source_group, file_name, file_type,
                          file_size, file_hash, status, records_parsed, records_loaded, error_message))
                
                conn.commit()
    except Exception as e:
        logging.error(f"Failed to log import: {e}")

# Create DAG
dag = DAG(
    'switching_files',
    default_args=default_args,
    description='Switching Files Import DAG - Raw Import Philosophy. Handles NT (New Connection), AN (Acknowledgement), CS (Customer Switch), RR (Reading Request), AC (Acknowledgement Confirmation), NW (New Withdrawal), AW (Acknowledgement Withdrawal) switch types.',
    schedule_interval='*/30 * * * *',  # Every 30 minutes (less frequent)
    max_active_runs=1,  # Prevent multiple concurrent runs
    catchup=False,  # Explicitly disable catchup to prevent backfill
    tags=['switching', 'import', 'electricity', 'raw', 'NT', 'AN', 'CS', 'RR', 'AC', 'NW', 'AW']
)

# Define tasks (simplified workflow following metering philosophy)
test_connection_task = PythonOperator(
    task_id='1_test_registry_connection',
    python_callable=test_registry_connection,
    dag=dag
)

discover_files_task = PythonOperator(
    task_id='2_discover_switching_files',
    python_callable=discover_switching_files,
    dag=dag
)

download_files_task = PythonOperator(
    task_id='3_download_switching_files',
    python_callable=download_switching_files,
    dag=dag
)

import_files_task = PythonOperator(
    task_id='4_import_switching_files_raw',
    python_callable=import_switching_files_raw,
        dag=dag
    )

verify_import_task = PythonOperator(
    task_id='5_verify_switching_import',
    python_callable=verify_switching_import,
    dag=dag
)

cleanup_files_task = PythonOperator(
    task_id='6_cleanup_switching_files',
    python_callable=cleanup_switching_files,
    dag=dag
)

# Set task dependencies (linear workflow like metering)
test_connection_task >> discover_files_task >> download_files_task >> import_files_task >> verify_import_task >> cleanup_files_task
