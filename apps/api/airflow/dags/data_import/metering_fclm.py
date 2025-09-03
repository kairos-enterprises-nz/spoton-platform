"""
FCLM (Financial Corporation Limited) Metering Data Import DAG

Individual DAG for Financial Corporation Limited metering provider with clear debugging steps:
1. Test Connection
2. Discover Files
3. Download Files
4. Import DRR Data
5. Import HHR Data
6a. Load DRR to Database
6b. Load HHR to Database
7. Verify Database Load
8. Cleanup & Archive

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
sys.path.append("/app/airflow/dags/metering/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))
sys.path.append("/app/airflow/dags/metering/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

# Default arguments
default_args = {
    'owner': 'data_import',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 25),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'catchup': False
}

# Data processing directory
DATA_DIR = Path('/data/imports/electricity/metering/fclm')
DAILY_DIR = DATA_DIR / 'daily'
INTERVAL_DIR = DATA_DIR / 'interval'

def ensure_directories():
    """Ensure processing directories exist"""
    for subdir in ['imported', 'archive', 'error']:
        (DAILY_DIR / subdir).mkdir(parents=True, exist_ok=True)
        (INTERVAL_DIR / subdir).mkdir(parents=True, exist_ok=True)

# Import connection utility
import sys
sys.path.append('/app/airflow/utils')
from connection import get_connection

def get_timescale_connection():
    """DEPRECATED: Use get_connection() instead."""
    return get_connection()

def test_fclm_connection(**context):
    """Step 1: Test FCLM SFTP connection"""
    logging.info("🔍 Step 1: Testing FCLM SFTP Connection")
    
    try:
        from connection_manager import ConnectionManager
        
        # Get FCLM connection config with ACTUAL folder structure
        conn_config = {
            'protocol': os.getenv('FCLM_PROTOCOL'),
            'host': os.getenv('FCLM_HOST'),
            'port': int(os.getenv('FCLM_PORT')),
            'user': os.getenv('FCLM_USER'),
            'password': os.getenv('FCLM_PASS'),
            'private_key_path': os.getenv('FCLM_PRIVATE_KEY_PATH'),
            'private_key_passphrase': os.getenv('FCLM_PRIVATE_KEY_PASSPHRASE'),
            'remote_paths': {
                'drr': '/out/rr',      # Daily Register Reads - FCLM RR folder
                'hhr': '/out/hhr',     # Half-Hourly Reads - FCLM HHR folder
            },
            'remote_path': '/out/rr'   # Default to RR folder
        }
        
        logging.info(f"Testing connection to {conn_config['host']}:{conn_config['port']}")
        
        if ConnectionManager.test_connection(conn_config):
            logging.info("✅ FCLM connection successful")
            context['ti'].xcom_push(key='connection_status', value='success')
            context['ti'].xcom_push(key='conn_config', value=conn_config)
            return True
        else:
            logging.error("❌ FCLM connection failed")
            context['ti'].xcom_push(key='connection_status', value='failed')
            raise Exception("FCLM connection test failed")
            
    except Exception as e:
        logging.error(f"❌ Connection test error: {e}")
        raise

def discover_fclm_files(**context):
    """Step 2: Discover available FCLM files"""
    logging.info("📁 Step 2: Discovering FCLM Files")
    
    # Check connection status from previous task
    connection_status = context['ti'].xcom_pull(key='connection_status')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    # If no connection config, create it
    if not conn_config:
        logging.info("ℹ️ No connection data from previous task, creating new connection config")
        conn_config = {
            'protocol': os.getenv('FCLM_PROTOCOL'),
            'host': os.getenv('FCLM_HOST'),
            'port': int(os.getenv('FCLM_PORT')),
            'user': os.getenv('FCLM_USER'),
            'password': os.getenv('FCLM_PASS'),
            'private_key_path': os.getenv('FCLM_PRIVATE_KEY_PATH'),
            'private_key_passphrase': os.getenv('FCLM_PRIVATE_KEY_PASSPHRASE'),
            'remote_paths': {
                'drr': '/out/rr',      # Daily Register Reads
                'hhr': '/out/hhr',     # Half-Hourly Reads
            },
            'remote_path': '/out/rr'   # Default to RR folder
        }
    
    # If connection status check failed, skip this task
    if connection_status == 'failed':
        raise Exception("Cannot discover files - connection test failed")
    
    try:
        try:
            from utils.sftp_discovery import SFTPDiscovery
        except ImportError:
            from metering_etl import SFTPDiscovery
        
        # Discover files from all FCLM folders (RR and HHR)
        all_files = []
        
        with SFTPDiscovery(conn_config) as discovery:
            # Check RR folder (Daily Register Reads)
            drr_config = conn_config.copy()
            drr_config['remote_path'] = conn_config['remote_paths']['drr']
            logging.info(f"🔍 Checking RR folder: {drr_config['remote_path']}")
            drr_discovery = SFTPDiscovery(drr_config)
            drr_files = drr_discovery.discover_files()
            # Filter for CSV files in RR folder
            for f in drr_files:
                if f['filename'].lower().endswith('.csv'):
                    f['folder_type'] = 'drr'
                    f['data_type'] = 'daily_register_reads'
                    f['source_folder'] = 'RR'
                    all_files.append(f)
            logging.info(f"📊 Found {len([f for f in drr_files if f['filename'].lower().endswith('.csv')])} CSV files in RR folder")
            
            # Check HHR folder (Half-Hourly Reads)
            hhr_config = conn_config.copy()
            hhr_config['remote_path'] = conn_config['remote_paths']['hhr']
            logging.info(f"🔍 Checking HHR folder: {hhr_config['remote_path']}")
            hhr_discovery = SFTPDiscovery(hhr_config)
            hhr_files = hhr_discovery.discover_files()
            # Filter for NEW files in HHR folder
            for f in hhr_files:
                if f['filename'].lower().endswith('.new'):
                    f['folder_type'] = 'hhr'
                    f['data_type'] = 'half_hourly_reads'
                    f['source_folder'] = 'HHR'
                    all_files.append(f)
            logging.info(f"📊 Found {len([f for f in hhr_files if f['filename'].lower().endswith('.new')])} NEW files in HHR folder")
            
            # Filter for FCLM data files (CSV and NEW extensions)
            fclm_files = all_files
            
            # Log file distribution by folder
            drr_csv_files = [f for f in fclm_files if f['folder_type'] == 'drr']
            hhr_new_files = [f for f in fclm_files if f['folder_type'] == 'hhr']
            logging.info(f"📊 Data Files found - RR: {len(drr_csv_files)}, HHR: {len(hhr_new_files)}")
            
            for f in drr_csv_files:
                logging.info(f"  📄 RR: {f['filename']}")
            for f in hhr_new_files:
                logging.info(f"  📄 HHR: {f['filename']}")
            
            logging.info(f"📊 Found {len(fclm_files)} FCLM data files")
            for file_info in fclm_files:
                logging.info(f"  - {file_info['filename']} ({file_info['size']} bytes)")
            
            context['ti'].xcom_push(key='discovered_files', value=fclm_files)
            context['ti'].xcom_push(key='files_count', value=len(fclm_files))
            context['ti'].xcom_push(key='conn_config', value=conn_config)  # Store config for later tasks
            
            return fclm_files
            
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def download_fclm_files(**context):
    """Step 3: Download FCLM files with duplicate checking"""
    logging.info("⬇️ Step 3: Downloading FCLM Files (with duplicate detection)")
    
    files = context['ti'].xcom_pull(key='discovered_files')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    # If no files from discovery, try to discover them first
    if not files:
        logging.info("ℹ️ No files from discovery, attempting to discover files first")
        try:
            files = discover_fclm_files(**context)
            conn_config = context['ti'].xcom_pull(key='conn_config')
        except Exception as e:
            logging.info(f"ℹ️ No files to download - discovery failed: {e}")
        return []
    
    # If no connection config, create it
    if not conn_config:
        logging.info("ℹ️ No connection config from previous tasks, creating new config")
        conn_config = {
            'protocol': os.getenv('FCLM_PROTOCOL'),
            'host': os.getenv('FCLM_HOST'),
            'port': int(os.getenv('FCLM_PORT')),
            'user': os.getenv('FCLM_USER'),
            'password': os.getenv('FCLM_PASS'),
            'private_key_path': os.getenv('FCLM_PRIVATE_KEY_PATH'),
            'private_key_passphrase': os.getenv('FCLM_PRIVATE_KEY_PASSPHRASE'),
            'remote_paths': {
                'drr': '/out/rr',      # Daily Register Reads
                'hhr': '/out/hhr',     # Half-Hourly Reads
            },
            'remote_path': '/out/rr'   # Default to RR folder
        }
    
    try:
        try:
            from utils.sftp_discovery import SFTPDiscovery
        except ImportError:
            from metering_etl import SFTPDiscovery
        
        ensure_directories()
        
        # Pre-filter files to exclude already processed ones
        logging.info(f"🔍 Checking {len(files)} discovered files for duplicates...")
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
                       WHERE mep_provider = 'FCLM' AND status = 'completed'"""
                )
                processed_files = {(row[0], row[1]) for row in cur.fetchall()}
                logging.info(f"Found {len(processed_files)} already processed files for FCLM.")

                for file_info in files:
                    filename = file_info['filename']
                    
                    # Determine file type for import log lookup
                    if file_info.get('folder_type') == 'drr' or file_info.get('source_folder') == 'RR':
                        import_type = 'RR'
                    elif file_info.get('folder_type') == 'hhr' or file_info.get('source_folder') == 'HHR':
                        import_type = 'HHR'
                    else:
                        # Fallback to filename-based classification
                        import_type = 'RR' if 'daily' in filename.lower() or 'rr' in filename.lower() else 'HHR'
                    
                    if (filename, import_type) in processed_files:
                        skipped_files.append(f"{filename} ({import_type})")
                    else:
                        files_to_download.append(file_info)
        
        logging.info(f"📊 Download Summary: {len(files_to_download)} new files, {len(skipped_files)} already processed")
        
        if len(skipped_files) > 0:
            logging.info("🔄 Skipped files (already processed):")
            for skipped_info in skipped_files:
                logging.info(f"  - {skipped_info}")
        
        if len(files_to_download) == 0:
            logging.info("ℹ️ No new files to download - all discovered files have been processed already")
            context['ti'].xcom_push(key='downloaded_files', value=[])
            context['ti'].xcom_push(key='skipped_files', value=skipped_files)
            return []
        
        downloaded_files = []
        
        for file_info in files_to_download:
            logging.info(f"⬇️ Downloading {file_info['filename']} from {file_info.get('source_folder', 'unknown')} folder")
            
            # Create appropriate connection config for this file's source folder
            file_conn_config = conn_config.copy()
            
            # Determine target directory, file type, and remote path based on source folder
            if file_info.get('folder_type') == 'drr' or file_info.get('source_folder') == 'RR':
                target_dir = DAILY_DIR / 'imported'
                file_type = 'daily'
                file_conn_config['remote_path'] = conn_config['remote_paths']['drr']
                logging.info(f"  📊 Classifying as DAILY file (from RR folder: {file_conn_config['remote_path']})")
            elif file_info.get('folder_type') == 'hhr' or file_info.get('source_folder') == 'HHR':
                target_dir = INTERVAL_DIR / 'imported'
                file_type = 'interval'
                file_conn_config['remote_path'] = conn_config['remote_paths']['hhr']
                logging.info(f"  📈 Classifying as INTERVAL file (from HHR folder: {file_conn_config['remote_path']})")
            else:
                # Fallback to filename-based classification
                if 'daily' in file_info['filename'].lower() or 'rr' in file_info['filename'].lower():
                    target_dir = DAILY_DIR / 'imported'
                    file_type = 'daily'
                    file_conn_config['remote_path'] = conn_config['remote_paths']['drr']
                    logging.info(f"  📊 Classifying as DAILY file (filename pattern, from RR folder)")
                else:
                    target_dir = INTERVAL_DIR / 'imported'
                    file_type = 'interval'
                    file_conn_config['remote_path'] = conn_config['remote_paths']['hhr']
                    logging.info(f"  📈 Classifying as INTERVAL file (filename pattern, from HHR folder)")
            
            local_path = target_dir / file_info['filename']
            
            # Use SFTPDiscovery for file download (consistent with BCMM pattern)
            with SFTPDiscovery(file_conn_config) as file_discovery:
                if file_discovery.download_file(file_info, local_path):
                    downloaded_files.append({
                        'filename': file_info['filename'],
                        'local_path': str(local_path),
                        'size': file_info['size'],
                        'type': file_type,
                        'source_folder': file_info.get('source_folder', 'unknown')
                    })
                    logging.info(f"✅ Downloaded to {local_path} as {file_type} file")
                else:
                    logging.warning(f"⚠️ Failed to download {file_info['filename']}")
        
        logging.info(f"📥 Downloaded {len(downloaded_files)}/{len(files_to_download)} new files")
        logging.info(f"📊 Total files discovered: {len(files)}, New: {len(files_to_download)}, Already processed: {len(skipped_files)}")
        
        context['ti'].xcom_push(key='downloaded_files', value=downloaded_files)
        context['ti'].xcom_push(key='skipped_files', value=skipped_files)
        context['ti'].xcom_push(key='total_discovered', value=len(files))
        context['ti'].xcom_push(key='new_files_count', value=len(files_to_download))
        context['ti'].xcom_push(key='skipped_files_count', value=len(skipped_files))
        
        return downloaded_files
        
    except Exception as e:
        logging.error(f"❌ Download error: {e}")
        raise

def import_fclm_drr(**context):
    """Step 4: Import FCLM DRR (Daily Register Reads) data - RAW IMPORT"""
    logging.info("📊 Step 4: Importing FCLM DRR Data (RAW IMPORT)")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to process for RR")
        return {'rr_records': 0, 'rr_files': 0}
    
    try:
        rr_files = [f for f in downloaded_files if f['type'] == 'daily']
        rr_records = []
        file_line_counts = {}
        
        for file_info in rr_files:
            logging.info(f"📊 Processing RR file: {file_info['filename']}")
            
            # RAW IMPORT - Parse CSV file exactly as it comes
            import csv
            import gzip
            
            # Handle both .gz and regular files
            if file_info['local_path'].endswith('.gz'):
                file_obj = gzip.open(file_info['local_path'], 'rt', encoding='utf-8')
            else:
                file_obj = open(file_info['local_path'], 'r', encoding='utf-8')
            
            try:
                csv_reader = csv.reader(file_obj)
                file_records = 0
                total_lines = 0
                
                for row_num, row in enumerate(csv_reader, 1):
                    total_lines += 1
                    if len(row) == 0:  # Skip empty rows
                        continue
                    
                    # RAW IMPORT - capture ALL columns as they are in the CSV file
                    # Actual CSV format: ICP, ReadDate, empty, Register, Reading, ReadType, empty, ReadTime, empty, empty, SerialNumber
                    record = {
                        'icp': row[0].strip() if len(row) > 0 else None,
                        'read_date': row[1].strip() if len(row) > 1 else None,
                        'register_id': row[3].strip() if len(row) > 3 else None,
                        'reading': row[4].strip() if len(row) > 4 else None,
                        'read_type': row[5].strip() if len(row) > 5 else None,
                        'read_time': row[7].strip() if len(row) > 7 else None,
                        'meter_serial': row[10].strip() if len(row) > 10 else None,
                        'extra_col_5': row[2].strip() if len(row) > 2 else None,  # empty field
                        'extra_col_6': row[6].strip() if len(row) > 6 else None,  # empty field
                        'extra_col_7': row[8].strip() if len(row) > 8 else None,  # empty field
                        'extra_col_8': row[9].strip() if len(row) > 9 else None,  # empty field
                        'extra_col_9': row[11].strip() if len(row) > 11 else None, # any additional fields
                        'filename': file_info['filename']
                    }
                    
                    rr_records.append(record)
                    file_records += 1
                    
                    if row_num <= 5:  # Log first 5 records
                        logging.info(f"  Row {row_num}: ICP={record['icp']}, Date={record['read_date']}, Register={record['register_id']}, Reading={record['reading']}")
                
                file_line_counts[file_info['filename']] = total_lines
                logging.info(f"✅ Parsed {file_records} RR records from {file_info['filename']} ({total_lines} source lines)")
                
            finally:
                file_obj.close()
        
        logging.info(f"📊 Total RR: {len(rr_records)} records from {len(rr_files)} files")
        
        result = {
            'rr_records': len(rr_records), 
            'rr_files': len(rr_files), 
            'rr_data': rr_records,
            'file_line_counts': file_line_counts
        }
        context['ti'].xcom_push(key='rr_results', value=result)
        
        return result
        
    except Exception as e:
        logging.error(f"❌ RR import error: {e}")
        raise

def import_fclm_hhr(**context):
    """Step 5: Import FCLM HHR (Half-Hourly Reads) data"""
    logging.info("📈 Step 5: Importing FCLM HHR Data")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to process for HHR")
        return {'hhr_records': 0, 'hhr_files': 0}
    
    try:
        hhr_files = [f for f in downloaded_files if f['type'] == 'interval']
        logging.info(f"🔍 Found {len(hhr_files)} interval files to process:")
        for f in hhr_files:
            logging.info(f"  📈 {f['filename']} (from {f.get('source_folder', 'unknown')} folder)")
        
        hhr_records = []
        file_line_counts = {}
        
        for file_info in hhr_files:
            logging.info(f"📈 Processing HHR file: {file_info['filename']}")
            
            file_records = 0
            total_lines = 0
            
            # Parse FCLM HHR file format (special format with multiple readings per row)
            import csv
            from datetime import datetime, timedelta
            
            with open(file_info['local_path'], 'r') as csvfile:
                reader = csv.reader(csvfile)
                
                for row_num, row in enumerate(reader, 1):
                    total_lines += 1
                    # Skip header line (HERM,1,FCLM,YESP,NZDT,151)
                    if row_num == 1 and len(row) > 0 and row[0] == 'HERM':
                        logging.info(f"📋 Skipping FCLM header line: {row}")
                        continue
                    
                    if len(row) < 8:  # Minimum: ICP, MeterSerial, RegisterID, Type, Channel, Units, Date, Status
                        logging.warning(f"⚠️ Row {row_num}: Too few columns ({len(row)})")
                        continue
                    
                    try:
                        # RAW IMPORT - capture ALL columns as they are in the file
                        # FCLM HHR format: ICP,MeterSerial,RegisterID,Type,Channel,Units,Date,Status,Reading1...Reading48
                        
                        # Create interval data (up to 50 intervals) - null values should be NULL
                        intervals = {}
                        for i in range(1, 51):  # interval_01 to interval_50
                            col_idx = 7 + i  # readings start at column 8 (index 7)
                            if col_idx < len(row):
                                value = row[col_idx].strip() if row[col_idx] else ''
                                # Handle null values properly - intervals 49/50 should be null when not applicable
                                if value == '' or value.upper() in ['NULL', 'N/A', 'NA']:
                                    intervals[f'interval_{i:02d}'] = None
                                else:
                                    intervals[f'interval_{i:02d}'] = value
                            else:
                                # Intervals beyond available data should be null (especially 49/50)
                                intervals[f'interval_{i:02d}'] = None
                        
                        # Parse intervals correctly - readings start from position 9
                        intervals = []
                        for i in range(48):  # 48 half-hourly intervals
                            interval_pos = 9 + i  # Start from position 9
                            if interval_pos < len(row):
                                interval_value = row[interval_pos].strip() if row[interval_pos] else None
                                intervals.append(interval_value)
                            else:
                                intervals.append(None)
                        
                        record = {
                            'icp': row[0].strip() if len(row) > 0 else None,
                            'meter_serial': row[1].strip() if len(row) > 1 else None,
                            'asset_number': row[2].strip() if len(row) > 2 else None,
                            'reading_type': row[3].strip() if len(row) > 3 else None,
                            'channel': row[4].strip() if len(row) > 4 else None,
                            'register_code': row[5].strip() if len(row) > 5 else None,
                            'reading_date': row[6].strip() if len(row) > 6 else None,
                            'read_type': row[7].strip() if len(row) > 7 else None,
                            'midnight_read': row[8].strip() if len(row) > 8 else None,
                            'intervals': intervals,
                            'extra_field_1': row[57].strip() if len(row) > 57 else None,  # Position after 48 intervals
                            'extra_field_2': row[58].strip() if len(row) > 58 else None,
                            'extra_field_3': row[59].strip() if len(row) > 59 else None,
                            'extra_field_4': row[60].strip() if len(row) > 60 else None,
                            'extra_field_5': row[61].strip() if len(row) > 61 else None,
                            'filename': file_info['filename']
                        }
                        hhr_records.append(record)
                        file_records += 1
                    
                    except Exception as e:
                        logging.warning(f"⚠️ Row {row_num}: Parse error - {e}")
                        continue
                
                file_line_counts[file_info['filename']] = total_lines
                logging.info(f"✅ Parsed {file_records} HHR rows from {file_info['filename']} ({total_lines} source lines)")
        
        logging.info(f"📈 Total HHR: {len(hhr_records)} rows from {len(hhr_files)} files")
        
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

def load_fclm_drr_to_db(**context):
    """Step 6a: Load FCLM DRR data to existing FCLM DRR table"""
    logging.info("💾 Step 6a: Loading FCLM DRR to Database")
    
    rr_results = context['ti'].xcom_pull(key='rr_results')
    if not rr_results or rr_results['rr_records'] == 0:
        logging.info("ℹ️ No RR data to load")
        return {'loaded_rr': 0}
    
    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Create schema and table if not exists for FCLM DRR
                cur.execute("CREATE SCHEMA IF NOT EXISTS metering_raw")
                
                # Drop and recreate FCLM DRR table to match file structure exactly
                logging.info("Dropping and recreating fclm_drr table to match file structure")
                cur.execute("DROP TABLE IF EXISTS metering_raw.fclm_drr CASCADE")
                
                # Create table based on FCLM DRR file format matching user requirements
                cur.execute("""
                    CREATE TABLE metering_raw.fclm_drr (
                        id SERIAL PRIMARY KEY,
                        icp VARCHAR(50),
                        read_date VARCHAR(20),
                        register_id VARCHAR(10),
                        reading VARCHAR(20),
                        read_type VARCHAR(20),
                        read_time VARCHAR(20),
                        meter_serial VARCHAR(50),
                        extra_field_1 VARCHAR(100),
                        extra_field_2 VARCHAR(100),
                        extra_field_3 VARCHAR(100),
                        extra_field_4 VARCHAR(100),
                        extra_field_5 VARCHAR(100),
                        filename VARCHAR(255),
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Group records by filename for processing and duplicate detection
                files_to_process = {}
                files_processed = {}
                
                # Group records by filename first
                for record in rr_results['rr_data']:
                    filename = record['filename']
                    if filename not in files_to_process:
                        files_to_process[filename] = []
                        files_processed[filename] = {'parsed': 0, 'loaded': 0, 'duplicates': 0}
                    files_to_process[filename].append(record)
                    files_processed[filename]['parsed'] += 1
                
                # File-based duplicate detection using import logs
                data_to_insert = []
                duplicate_count = 0
                
                for filename, records in files_to_process.items():
                    # Get file info for duplicate checking
                    file_path = f"/data/imports/electricity/metering/fclm/daily/imported/{filename}"
                    file_hash = ""
                    file_size = 0
                    
                    if Path(file_path).exists():
                        file_hash = get_file_hash(file_path)
                        file_size = Path(file_path).stat().st_size
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/fclm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_hash = get_file_hash(file_path)
                            file_size = Path(file_path).stat().st_size
                    
                    # Check if this file was already successfully processed
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'RR' 
                           AND status = 'completed' AND mep_provider = 'FCLM'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                        files_processed[filename]['duplicates'] = len(records)
                        duplicate_count += len(records)
                        continue
                    
                    # Process all records from this file (not duplicate) - RAW IMPORT
                    for record in records:
                        # Create tuple matching fclm_drr schema - RAW IMPORT all columns
                        row_data = (
                            record['icp'],                    # icp
                            record['read_date'],              # read_date
                            record['register_id'],            # register_id
                            record['reading'],                # reading
                            record.get('read_type'),          # read_type
                            record.get('read_time'),          # read_time
                            record['meter_serial'],           # meter_serial
                            record.get('extra_col_5'),        # extra_field_1
                            record.get('extra_col_6'),        # extra_field_2
                            record.get('extra_col_7'),        # extra_field_3
                            record.get('extra_col_8'),        # extra_field_4
                            record.get('extra_col_9'),        # extra_field_5
                            record['filename']                # filename
                        )
                        data_to_insert.append(row_data)
                
                # Bulk insert new records only
                if data_to_insert:
                    execute_values(
                        cur,
                        """
                        INSERT INTO metering_raw.fclm_drr 
                        (icp, read_date, register_id, reading, read_type, read_time, meter_serial,
                         extra_field_1, extra_field_2, extra_field_3, extra_field_4, extra_field_5, filename)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                        """,
                        data_to_insert
                    )
                
                loaded_count = len(data_to_insert)
                logging.info(f"✅ Loaded {loaded_count} new DRR records to metering_raw.fclm_drr")
                if duplicate_count > 0:
                    logging.info(f"🔄 Skipped {duplicate_count} duplicate RR records")
                
                # Update files_processed with loaded counts
                for record in data_to_insert:
                    filename = record[-1]  # file_name is the last column
                    if filename in files_processed:
                        files_processed[filename]['loaded'] += 1
                
                # Log each file's import status
                for filename, counts in files_processed.items():
                    # Get file info for logging
                    file_path = f"/data/imports/electricity/metering/fclm/daily/imported/{filename}"
                    file_size = 0
                    file_hash = ""
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/fclm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_size = Path(file_path).stat().st_size
                            file_hash = get_file_hash(file_path)
                    
                    # Log import with comprehensive details
                    source_records = rr_results.get('file_line_counts', {}).get(filename, 0)
                    log_import(
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        mep_provider='FCLM',
                        file_name=filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        import_type='RR',
                        status='completed',
                        source_records=source_records,
                        records_parsed=counts['parsed'],
                        intervals_loaded=counts['loaded'],
                        error_message=f"Duplicates skipped: {counts['duplicates']}" if counts['duplicates'] > 0 else None
                    )
                
                context['ti'].xcom_push(key='loaded_rr', value=loaded_count)
                context['ti'].xcom_push(key='duplicate_rr', value=duplicate_count)
                return {'loaded_rr': loaded_count, 'duplicate_rr': duplicate_count}
                
    except Exception as e:
        logging.error(f"❌ RR database load error: {e}")
        
        # Log error for each file
        if 'rr_results' in locals() and rr_results.get('rr_data'):
            filenames = set(record['filename'] for record in rr_results['rr_data'])
            for filename in filenames:
                log_import(
                    dag_id=dag_id,
                    task_id=task_id,
                    run_id=run_id,
                    mep_provider='FCLM',
                    file_name=filename,
                    file_size=0,
                    file_hash="",
                    import_type='RR',
                    status='failed',
                    records_parsed=0,
                    intervals_loaded=0,
                    error_message=str(e)
                )
        
        raise 

def load_fclm_hhr_to_db(**context):
    """Step 6b: Load FCLM HHR data with interval columns (like BCMM) - no transformation"""
    logging.info("💾 Step 6b: Loading FCLM HHR to Database")
    
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
                # Drop and recreate FCLM HHR table to match file structure exactly
                logging.info("Dropping and recreating fclm_hhr table to match file structure")
                cur.execute("DROP TABLE IF EXISTS metering_raw.fclm_hhr CASCADE")
                
                # Create table based on FCLM HHR file format - standardized schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_raw.fclm_hhr (
                        id SERIAL PRIMARY KEY,
                        icp VARCHAR(50),
                        meter_serial VARCHAR(50),
                        asset_number VARCHAR(50),
                        reading_type VARCHAR(20),
                        channel VARCHAR(10),
                        register_code VARCHAR(50),
                        read_date VARCHAR(20),
                        read_type VARCHAR(10),
                        midnight_read VARCHAR(20),
                        -- 48 half-hourly intervals (30-minute periods) - NULL instead of default
                        interval_01 VARCHAR(20),
                        interval_02 VARCHAR(20),
                        interval_03 VARCHAR(20),
                        interval_04 VARCHAR(20),
                        interval_05 VARCHAR(20),
                        interval_06 VARCHAR(20),
                        interval_07 VARCHAR(20),
                        interval_08 VARCHAR(20),
                        interval_09 VARCHAR(20),
                        interval_10 VARCHAR(20),
                        interval_11 VARCHAR(20),
                        interval_12 VARCHAR(20),
                        interval_13 VARCHAR(20),
                        interval_14 VARCHAR(20),
                        interval_15 VARCHAR(20),
                        interval_16 VARCHAR(20),
                        interval_17 VARCHAR(20),
                        interval_18 VARCHAR(20),
                        interval_19 VARCHAR(20),
                        interval_20 VARCHAR(20),
                        interval_21 VARCHAR(20),
                        interval_22 VARCHAR(20),
                        interval_23 VARCHAR(20),
                        interval_24 VARCHAR(20),
                        interval_25 VARCHAR(20),
                        interval_26 VARCHAR(20),
                        interval_27 VARCHAR(20),
                        interval_28 VARCHAR(20),
                        interval_29 VARCHAR(20),
                        interval_30 VARCHAR(20),
                        interval_31 VARCHAR(20),
                        interval_32 VARCHAR(20),
                        interval_33 VARCHAR(20),
                        interval_34 VARCHAR(20),
                        interval_35 VARCHAR(20),
                        interval_36 VARCHAR(20),
                        interval_37 VARCHAR(20),
                        interval_38 VARCHAR(20),
                        interval_39 VARCHAR(20),
                        interval_40 VARCHAR(20),
                        interval_41 VARCHAR(20),
                        interval_42 VARCHAR(20),
                        interval_43 VARCHAR(20),
                        interval_44 VARCHAR(20),
                        interval_45 VARCHAR(20),
                        interval_46 VARCHAR(20),
                        interval_47 VARCHAR(20),
                        interval_48 VARCHAR(20),
                        -- Intervals 49 and 50 for daylight savings (null when not applicable)
                        interval_49 VARCHAR(20),
                        interval_50 VARCHAR(20),
                        filename VARCHAR(255),
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Group records by filename for processing and duplicate detection
                files_to_process = {}
                files_processed = {}
                
                # Group records by filename first
                for record in hhr_results['hhr_data']:
                    filename = record['filename']
                    if filename not in files_to_process:
                        files_to_process[filename] = []
                        files_processed[filename] = {'parsed': 0, 'loaded': 0, 'duplicates': 0}
                    files_to_process[filename].append(record)
                    files_processed[filename]['parsed'] += 1
                
                # File-based duplicate detection using import logs
                data_to_insert = []
                duplicate_count = 0
                
                for filename, records in files_to_process.items():
                    # Get file info for duplicate checking
                    file_path = f"/data/imports/electricity/metering/fclm/daily/imported/{filename}"
                    file_hash = ""
                    file_size = 0
                    
                    if Path(file_path).exists():
                        file_hash = get_file_hash(file_path)
                        file_size = Path(file_path).stat().st_size
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/fclm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_hash = get_file_hash(file_path)
                            file_size = Path(file_path).stat().st_size
                    
                    # Check if this file was already successfully processed
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'HHR' 
                           AND status = 'completed' AND mep_provider = 'FCLM'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                        files_processed[filename]['duplicates'] = len(records)
                        duplicate_count += len(records)
                        continue
                    
                    # Process all records from this file (not duplicate) - RAW IMPORT
                    for record in records:
                        # Create tuple matching fclm_hhr schema - RAW IMPORT all columns
                        # Prepare interval values - intervals is now a list
                        intervals_list = record['intervals']
                        interval_values = []
                        for i in range(50):  # 50 intervals total
                            if i < len(intervals_list):
                                interval_values.append(intervals_list[i])
                            else:
                                interval_values.append(None)
                        
                        row_data = (
                            record['icp'],                    # icp
                            record['meter_serial'],           # meter_serial
                            record.get('asset_number'),       # asset_number (register_id from file)
                            record['reading_type'],           # reading_type
                            record['channel'],                # channel
                            record.get('register_code'),      # register_code (units from file)
                            record['reading_date'],           # read_date
                            record.get('read_type'),          # read_type (status from file)
                            record.get('midnight_read'),      # midnight_read
                            # 50 interval values (interval_01 through interval_50)
                            *interval_values,
                            record['filename']                # filename
                        )
                        data_to_insert.append(row_data)
                
                # Bulk insert new records only
                if data_to_insert:
                    interval_columns = ', '.join([f'interval_{i:02d}' for i in range(1, 51)])
                    
                    execute_values(
                        cur,
                        f"""
                        INSERT INTO metering_raw.fclm_hhr 
                        (icp, meter_serial, asset_number, reading_type, channel, register_code, read_date, read_type, midnight_read,
                         {interval_columns}, filename)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                        """,
                        data_to_insert
                    )
                
                loaded_count = len(data_to_insert)
                logging.info(f"✅ Loaded {loaded_count} new HHR rows to metering_raw.fclm_hhr")
                if duplicate_count > 0:
                    logging.info(f"🔄 Skipped {duplicate_count} duplicate HHR rows")
                
                # Update files_processed with loaded counts
                for record in data_to_insert:
                    filename = record[-1]  # file_name is the last column
                    if filename in files_processed:
                        files_processed[filename]['loaded'] += 1
                
                # Log each file's import status
                for filename, counts in files_processed.items():
                    # Get file info for logging
                    file_path = f"/data/imports/electricity/metering/fclm/daily/imported/{filename}"
                    file_size = 0
                    file_hash = ""
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/fclm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_size = Path(file_path).stat().st_size
                            file_hash = get_file_hash(file_path)
                    
                    # Calculate intervals loaded (exclude midnight read, count only HHR intervals)
                    # FCLM format: 48 HHR intervals per row (exclude midnight read at position 9)
                    rows_processed = sum(1 for row_data in data_to_insert if row_data[-1] == filename)
                    actual_intervals_loaded = rows_processed * 48  # 48 HHR intervals per row
                    
                    # For detailed statistics (will move to processing log later)
                    null_intervals = 0
                    zero_intervals = 0
                    total_possible_intervals = rows_processed * 48
                    
                    for row_data in data_to_insert:
                        if row_data[-1] == filename:  # Match this filename
                            # Count intervals by type (intervals are positions 10-57: interval_01 to interval_48, excluding midnight)
                            hhr_intervals = row_data[10:58]  # interval_01 to interval_48 (48 HHR intervals, exclude midnight at pos 9)
                            
                            for interval in hhr_intervals:
                                if interval is None or interval == '' or interval == 'NULL':
                                    null_intervals += 1
                                elif interval == '0' or interval == 0:
                                    zero_intervals += 1
                    
                    # Calculate data quality percentages
                    valid_percentage = (actual_intervals_loaded / total_possible_intervals * 100) if total_possible_intervals > 0 else 0
                    null_percentage = (null_intervals / total_possible_intervals * 100) if total_possible_intervals > 0 else 0
                    zero_percentage = (zero_intervals / total_possible_intervals * 100) if total_possible_intervals > 0 else 0
                    
                    # Log with clear three-column semantics plus data quality statistics:
                    # source_records = Raw records/rows from file 
                    # records_parsed = Individual interval readings extracted
                    # intervals_loaded = Total intervals stored in database (DST-aware)
                    logging.info(f"📊 Import Summary for {filename}:")
                    logging.info(f"  📄 Source records/rows from file: {counts['loaded']}")
                    logging.info(f"  🔍 Individual intervals parsed: {counts['parsed']}")
                    logging.info(f"  💾 Total intervals stored: {actual_intervals_loaded}")
                    logging.info(f"  📈 Data Quality Statistics:")
                    logging.info(f"    • Total possible intervals: {total_possible_intervals}")
                    logging.info(f"    • Valid intervals (non-null): {actual_intervals_loaded} ({valid_percentage:.1f}%)")
                    logging.info(f"    • Null/missing intervals: {null_intervals} ({null_percentage:.1f}%)")
                    logging.info(f"    • Zero value intervals: {zero_intervals} ({zero_percentage:.1f}%)")
                    
                    # Prepare detailed error message with data quality info
                    quality_stats = f"Valid: {actual_intervals_loaded}, Null: {null_intervals}, Zero: {zero_intervals}"
                    error_message = f"Duplicates skipped: {counts['duplicates']}, Data quality: {quality_stats}" if counts['duplicates'] > 0 else f"Data quality: {quality_stats}"
                    
                    source_records = hhr_results.get('file_line_counts', {}).get(filename, 0)
                    log_import(
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        mep_provider='FCLM',
                        file_name=filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        import_type='HHR',
                        status='completed',
                        source_records=source_records,  # Raw records/rows from file
                        records_parsed=counts['parsed'],  # Individual interval readings extracted
                        intervals_loaded=actual_intervals_loaded,  # Total intervals stored (DST-aware)
                        error_message=error_message
                    )
                
                context['ti'].xcom_push(key='loaded_hhr', value=loaded_count)
                context['ti'].xcom_push(key='duplicate_hhr', value=duplicate_count)
                return {'loaded_hhr': loaded_count, 'duplicate_hhr': duplicate_count}
                
    except Exception as e:
        logging.error(f"❌ HHR database load error: {e}")
        
        # Log error for each file
        if 'hhr_results' in locals() and hhr_results.get('hhr_data'):
            filenames = set(record['filename'] for record in hhr_results['hhr_data'])
            for filename in filenames:
                log_import(
                    dag_id=dag_id,
                    task_id=task_id,
                    run_id=run_id,
                    mep_provider='FCLM',
                    file_name=filename,
                    file_size=0,
                    file_hash="",
                    import_type='HHR',
                    status='failed',
                    records_parsed=0,
                    intervals_loaded=0,
                    error_message=str(e)
                )
        
        raise

def verify_fclm_database_load(**context):
    """Step 7: Verify database load with comprehensive audit"""
    logging.info("🔍 Step 7: Verifying FCLM Database Load")
    
    try:
        rr_results = context['ti'].xcom_pull(key='rr_results') or {'rr_records': 0}
        hhr_results = context['ti'].xcom_pull(key='hhr_results') or {'hhr_records': 0}
        loaded_rr = context['ti'].xcom_pull(key='loaded_rr') or 0
        loaded_hhr = context['ti'].xcom_pull(key='loaded_hhr') or 0
        duplicate_rr = context['ti'].xcom_pull(key='duplicate_rr') or 0
        duplicate_hhr = context['ti'].xcom_pull(key='duplicate_hhr') or 0
        
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Count records in FCLM tables
                cur.execute("SELECT COUNT(*) FROM metering_raw.fclm_drr")
                db_rr_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metering_raw.fclm_hhr")
                db_hhr_count = cur.fetchone()[0]
                
                # Get import log summary for this run
                run_id = context['run_id']
                cur.execute(
                    """SELECT import_type, status, COUNT(*) as file_count, 
                       SUM(records_parsed) as total_parsed, SUM(intervals_loaded) as total_loaded
                       FROM metering_raw.import_log 
                       WHERE run_id = %s AND mep_provider = 'FCLM'
                       GROUP BY import_type, status
                       ORDER BY import_type, status""",
                    (run_id,)
                )
                import_log_summary = cur.fetchall()
                
                # Get recent import activity (last 24 hours)
                cur.execute(
                    """SELECT import_type, COUNT(*) as files, SUM(intervals_loaded) as records,
                       MIN(started_at) as first_import, MAX(completed_at) as last_import
                       FROM metering_raw.import_log 
                       WHERE mep_provider = 'FCLM' AND started_at >= NOW() - INTERVAL '24 hours'
                       GROUP BY import_type
                       ORDER BY import_type""",
                )
                recent_imports = cur.fetchall()
        
        # Get download statistics for comprehensive summary
        total_discovered = context['ti'].xcom_pull(key='total_discovered') or 0
        new_files_count = context['ti'].xcom_pull(key='new_files_count') or 0
        skipped_files_count = context['ti'].xcom_pull(key='skipped_files_count') or 0
        
        logging.info("📊 FCLM Import Verification Summary:")
        logging.info(f"  📁 Files - Discovered: {total_discovered}, New: {new_files_count}, Skipped: {skipped_files_count}")
        logging.info(f"  📊 RR - Parsed: {rr_results['rr_records']}, Loaded: {loaded_rr}, Duplicates: {duplicate_rr}, In DB: {db_rr_count}")
        logging.info(f"  📈 HHR - Parsed: {hhr_results['hhr_records']}, Loaded: {loaded_hhr}, Duplicates: {duplicate_hhr}, In DB: {db_hhr_count}")
        
        # Import log summary
        if import_log_summary:
            logging.info("📋 Import Log Summary for this run:")
            for row in import_log_summary:
                import_type, status, file_count, total_parsed, total_loaded = row
                logging.info(f"  {import_type} - {status.upper()}: {file_count} files, {total_parsed or 0} parsed, {total_loaded or 0} loaded")
        
        # Recent import activity
        if recent_imports:
            logging.info("📈 Recent Import Activity (24h):")
            for row in recent_imports:
                import_type, files, records, first_import, last_import = row
                logging.info(f"  {import_type}: {files} files, {records} records ({first_import} to {last_import})")
        
        # Verification checks
        success = True
        expected_loaded_rr = max(0, rr_results['rr_records'] - duplicate_rr)
        expected_loaded_hhr = max(0, hhr_results['hhr_records'] - duplicate_hhr)
        
        if loaded_rr != expected_loaded_rr:
            if expected_loaded_rr == 0 and duplicate_rr == rr_results['rr_records']:
                logging.info(f"✅ RR verification passed: All {rr_results['rr_records']} records were duplicates")
            else:
                logging.warning(f"⚠️ RR mismatch: Expected {expected_loaded_rr} but loaded {loaded_rr}")
                success = False
            
        if loaded_hhr != expected_loaded_hhr:
            if expected_loaded_hhr == 0 and duplicate_hhr == hhr_results['hhr_records']:
                logging.info(f"✅ HHR verification passed: All {hhr_results['hhr_records']} records were duplicates")
            else:
                logging.warning(f"⚠️ HHR mismatch: Expected {expected_loaded_hhr} but loaded {loaded_hhr}")
                success = False
        
        # Calculate efficiency metrics
        total_processed_records = rr_results['rr_records'] + hhr_results['hhr_records']
        total_loaded_records = loaded_rr + loaded_hhr
        total_duplicate_records = duplicate_rr + duplicate_hhr
        
        if total_processed_records > 0:
            load_efficiency = (total_loaded_records / (total_processed_records - total_duplicate_records)) * 100 if (total_processed_records - total_duplicate_records) > 0 else 0
            duplicate_rate = (total_duplicate_records / total_processed_records) * 100
            
            logging.info(f"📈 Import Efficiency: {load_efficiency:.1f}% ({total_loaded_records}/{total_processed_records - total_duplicate_records} records)")
            logging.info(f"🔄 Duplicate Rate: {duplicate_rate:.1f}% ({total_duplicate_records}/{total_processed_records} records)")
        
        if success:
            logging.info("✅ Database verification successful")
        else:
            logging.error("❌ Database verification failed")
            
        context['ti'].xcom_push(key='verification_success', value=success)
            
        return {
            'verification_success': success,
            'rr_parsed': rr_results['rr_records'],
            'rr_loaded': loaded_rr,
            'rr_duplicates': duplicate_rr,
            'rr_in_db': db_rr_count,
            'hhr_parsed': hhr_results['hhr_records'],
            'hhr_loaded': loaded_hhr,
            'hhr_duplicates': duplicate_hhr,
            'hhr_in_db': db_hhr_count,
            'total_processed_records': total_processed_records,
            'total_loaded_records': total_loaded_records,
            'total_duplicate_records': total_duplicate_records
        }
        
    except Exception as e:
        logging.error(f"❌ Verification error: {e}")
        raise

def cleanup_fclm_files(**context):
    """Step 8: Cleanup and archive processed files with gzip compression"""
    logging.info("🧹 Step 8: Cleanup and Archive FCLM Files with Compression")
    
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
        logging.info("📋 FCLM Import Complete - Final Summary:")
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

def log_import(dag_id: str, task_id: str, run_id: str, mep_provider: str, 
               file_name: str, file_size: int, file_hash: str, import_type: str, 
               status: str, records_parsed: int = 0, intervals_loaded: int = 0, 
               source_records: int = 0, error_message: str = None):
    """Log import activity to metering_raw.import_log table"""
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Create schema and table if not exists
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
                
                # Insert or update import log record
                if status == 'completed':
                    cur.execute(
                        """INSERT INTO metering_raw.import_log 
                           (dag_id, task_id, run_id, mep_provider, file_name, file_size, file_hash, 
                            import_type, status, records_parsed, intervals_loaded, source_records, error_message, completed_at) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) 
                           ON CONFLICT (file_name, file_hash, import_type) DO UPDATE SET
                               status = EXCLUDED.status,
                               records_parsed = EXCLUDED.records_parsed,
                               intervals_loaded = EXCLUDED.intervals_loaded,
                               source_records = EXCLUDED.source_records,
                               error_message = EXCLUDED.error_message,
                               completed_at = EXCLUDED.completed_at""",
                        [dag_id, task_id, run_id, mep_provider, file_name, file_size, file_hash, 
                         import_type, status, records_parsed, intervals_loaded, source_records, error_message]
                    )
                else:
                    cur.execute(
                        """INSERT INTO metering_raw.import_log 
                           (dag_id, task_id, run_id, mep_provider, file_name, file_size, file_hash, 
                            import_type, status, records_parsed, intervals_loaded, source_records, error_message) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                           ON CONFLICT (file_name, file_hash, import_type) DO UPDATE SET
                               status = EXCLUDED.status,
                               records_parsed = EXCLUDED.records_parsed,
                               intervals_loaded = EXCLUDED.intervals_loaded,
                               source_records = EXCLUDED.source_records,
                               error_message = EXCLUDED.error_message""",
                        [dag_id, task_id, run_id, mep_provider, file_name, file_size, file_hash, 
                         import_type, status, records_parsed, intervals_loaded, source_records, error_message]
                    )
                
                logging.info(f"📝 Logged import: {file_name} - {status} ({source_records} source records, {records_parsed} parsed, {intervals_loaded} loaded)")
                
    except Exception as e:
        logging.error(f"❌ Failed to log import for {file_name}: {e}")

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

# Create the DAG
dag = DAG(
    'metering_fclm',
    default_args=default_args,
    description='FCLM (Financial Corporation Limited) Metering Data Import',
    schedule_interval='0 6 * * *',  # 6 AM daily
    tags=['fclm','financial_corporation_limited' ,'data-import', 'metering'],
    catchup=False
)

# Define tasks
task_1_test_connection = PythonOperator(
    task_id='1_test_fclm_connection',
    python_callable=test_fclm_connection,
    dag=dag
)

task_2_discover_files = PythonOperator(
    task_id='2_discover_fclm_files',
    python_callable=discover_fclm_files,
    dag=dag
)

task_3_download_files = PythonOperator(
    task_id='3_download_fclm_files',
    python_callable=download_fclm_files,
    dag=dag
)

task_4_import_drr = PythonOperator(
    task_id='4_import_fclm_drr',
    python_callable=import_fclm_drr,
    dag=dag
)

task_5_import_hhr = PythonOperator(
    task_id='5_import_fclm_hhr',
    python_callable=import_fclm_hhr,
    dag=dag
)

task_6a_load_drr = PythonOperator(
    task_id='6a_load_fclm_drr_to_db',
    python_callable=load_fclm_drr_to_db,
    dag=dag
)

task_6b_load_hhr = PythonOperator(
    task_id='6b_load_fclm_hhr_to_db',
    python_callable=load_fclm_hhr_to_db,
    dag=dag
)

task_7_verify_database = PythonOperator(
    task_id='7_verify_fclm_database_load',
    python_callable=verify_fclm_database_load,
    dag=dag
)

task_8_cleanup = PythonOperator(
    task_id='8_cleanup_fclm_files',
    python_callable=cleanup_fclm_files,
    dag=dag
)

# Define task dependencies
task_1_test_connection >> task_2_discover_files >> task_3_download_files
task_3_download_files >> [task_4_import_drr, task_5_import_hhr]
task_4_import_drr >> task_6a_load_drr
task_5_import_hhr >> task_6b_load_hhr
[task_6a_load_drr, task_6b_load_hhr] >> task_7_verify_database >> task_8_cleanup 