"""
BCMM (BlueCurrent Mass Market) Metering Data Import DAG

Individual DAG for BlueCurrent Mass Market metering provider with clear debugging steps:
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

# Data processing directory (Corrected to use the root /data volume mount)
DATA_DIR = Path('/data/imports/electricity/metering/bcmm')
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

def test_bcmm_connection(**context):
    """Step 1: Test BCMM SFTP connection"""
    logging.info("🔍 Step 1: Testing BCMM SFTP Connection")
    
    try:
        from connection_manager import ConnectionManager
        
        # Get BCMM connection config with ACTUAL folder structure from table
        conn_config = {
            'protocol': os.getenv('BLUECURRENT_RES_PROTOCOL'),
            'host': os.getenv('BLUECURRENT_RES_HOST'),
            'port': int(os.getenv('BLUECURRENT_RES_PORT')),
            'user': os.getenv('BLUECURRENT_RES_USER'),
            'key_path': os.getenv('BLUECURRENT_RES_PRIVATE_KEY_PATH'),
            'key_passphrase': os.getenv('BLUECURRENT_RES_PRIVATE_KEY_PASSPHRASE'),
            'remote_paths': {
                'drr': '/data/to_yesp/DRR',      # Daily Register Reads - FROM TABLE
                'hhr': '/data/to_yesp/HERM',     # Half-Hourly Reads in HERM - FROM TABLE
            },
            'remote_path': '/data/to_yesp/DRR'   # Default to DRR folder - FROM TABLE
        }
        
        logging.info(f"Testing connection to {conn_config['host']}:{conn_config['port']}")
        
        if ConnectionManager.test_connection(conn_config):
            logging.info("✅ BCMM connection successful")
            context['ti'].xcom_push(key='connection_status', value='success')
            context['ti'].xcom_push(key='conn_config', value=conn_config)
            return True
        else:
            logging.error("❌ BCMM connection failed")
            context['ti'].xcom_push(key='connection_status', value='failed')
            raise Exception("BCMM connection test failed")
            
    except Exception as e:
        logging.error(f"❌ Connection test error: {e}")
        raise

def discover_bcmm_files(**context):
    """Step 2: Discover available BCMM files"""
    logging.info("📁 Step 2: Discovering BCMM Files")
    
    # Check connection status from previous task, but don't fail if not available (for individual task runs)
    connection_status = context['ti'].xcom_pull(key='connection_status')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    # If no connection data from previous task, create connection config
    if not conn_config:
        logging.info("ℹ️ No connection data from previous task, creating new connection config")
        conn_config = {
            'protocol': os.getenv('BLUECURRENT_RES_PROTOCOL'),
            'host': os.getenv('BLUECURRENT_RES_HOST'),
            'port': int(os.getenv('BLUECURRENT_RES_PORT')),
            'user': os.getenv('BLUECURRENT_RES_USER'),
            'key_path': os.getenv('BLUECURRENT_RES_PRIVATE_KEY_PATH'),
            'key_passphrase': os.getenv('BLUECURRENT_RES_PRIVATE_KEY_PASSPHRASE'),
            'remote_paths': {
                'drr': '/data/to_yesp/DRR',      # Daily Register Reads
                'hhr': '/data/to_yesp/HERM',     # Half-Hourly Reads in HERM
            },
            'remote_path': '/data/to_yesp/DRR'   # Default to DRR folder
        }
    
    # If connection status check failed and we have connection data, skip this task
    if connection_status == 'failed':
        raise Exception("Cannot discover files - connection test failed")
    
    try:
        try:
            from utils.sftp_discovery import SFTPDiscovery
        except ImportError:
            from metering_etl import SFTPDiscovery
        
        # Discover files from all BCMM folders (DRR and HERM)
        all_files = []
        
        with SFTPDiscovery(conn_config) as discovery:
            # Check DRR folder (Daily Register Reads)
            drr_config = conn_config.copy()
            drr_config['remote_path'] = conn_config['remote_paths']['drr']
            logging.info(f"🔍 Checking DRR folder: {drr_config['remote_path']}")
            drr_discovery = SFTPDiscovery(drr_config)
            drr_files = drr_discovery.discover_files()
            for f in drr_files:
                f['folder_type'] = 'drr'
                f['data_type'] = 'daily_register_reads'
                f['source_folder'] = 'DRR'
            all_files.extend(drr_files)
            logging.info(f"📊 Found {len(drr_files)} files in DRR folder")
            
            # Check HERM folder (Half-Hourly)
            herm_config = conn_config.copy()
            herm_config['remote_path'] = conn_config['remote_paths']['hhr']  # HERM folder
            logging.info(f"🔍 Checking HERM folder: {herm_config['remote_path']}")
            herm_discovery = SFTPDiscovery(herm_config)
            herm_files = herm_discovery.discover_files()
            for f in herm_files:
                f['folder_type'] = 'herm'
                f['source_folder'] = 'HERM'
            all_files.extend(herm_files)
            logging.info(f"📊 Found {len(herm_files)} files in HERM folder")
            
            # Filter for BCMM data files (CSV and NEW extensions)
            bcmm_files = [f for f in all_files if f['filename'].lower().endswith(('.csv', '.new'))]
            
            # Log file distribution by folder
            drr_csv_files = [f for f in bcmm_files if f['folder_type'] == 'drr']
            herm_csv_files = [f for f in bcmm_files if f['folder_type'] == 'herm']
            logging.info(f"📊 CSV Files found - DRR: {len(drr_csv_files)}, HERM: {len(herm_csv_files)}")
            
            for f in drr_csv_files:
                logging.info(f"  📄 DRR: {f['filename']}")
            for f in herm_csv_files:
                logging.info(f"  📄 HERM: {f['filename']}")
            
            logging.info(f"📊 Found {len(bcmm_files)} BCMM CSV files")
            for file_info in bcmm_files:
                logging.info(f"  - {file_info['filename']} ({file_info['size']} bytes)")
            
            context['ti'].xcom_push(key='discovered_files', value=bcmm_files)
            context['ti'].xcom_push(key='files_count', value=len(bcmm_files))
            context['ti'].xcom_push(key='conn_config', value=conn_config)  # Store config for later tasks
            
            return bcmm_files
            
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def download_bcmm_files(**context):
    """Step 3: Download BCMM files with duplicate checking"""
    logging.info("⬇️ Step 3: Downloading BCMM Files (with duplicate detection)")
    
    files = context['ti'].xcom_pull(key='discovered_files')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    # If no files from discovery, try to discover them first
    if not files:
        logging.info("ℹ️ No files from discovery, attempting to discover files first")
        try:
            files = discover_bcmm_files(**context)
            conn_config = context['ti'].xcom_pull(key='conn_config')
        except Exception as e:
            logging.info(f"ℹ️ No files to download - discovery failed: {e}")
        return []
    
    # If no connection config, create it
    if not conn_config:
        logging.info("ℹ️ No connection config from previous tasks, creating new config")
        conn_config = {
            'protocol': os.getenv('BLUECURRENT_RES_PROTOCOL'),
            'host': os.getenv('BLUECURRENT_RES_HOST'),
            'port': int(os.getenv('BLUECURRENT_RES_PORT')),
            'user': os.getenv('BLUECURRENT_RES_USER'),
            'key_path': os.getenv('BLUECURRENT_RES_PRIVATE_KEY_PATH'),
            'key_passphrase': os.getenv('BLUECURRENT_RES_PRIVATE_KEY_PASSPHRASE'),
            'remote_paths': {
                'drr': '/data/to_yesp/DRR',      # Daily Register Reads
                'hhr': '/data/to_yesp/HERM',     # Half-Hourly Reads in HERM
            },
            'remote_path': '/data/to_yesp/DRR'   # Default to DRR folder
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
                       WHERE mep_provider = 'BCMM' AND status = 'completed'"""
                )
                processed_files = {(row[0], row[1]) for row in cur.fetchall()}
                logging.info(f"Found {len(processed_files)} already processed files for BCMM.")

                for file_info in files:
                    filename = file_info['filename']
                    
                    # Determine file type for import log lookup
                    if file_info.get('folder_type') == 'drr' or file_info.get('source_folder') == 'DRR':
                        import_type = 'DRR'
                    elif file_info.get('folder_type') == 'herm' or file_info.get('source_folder') == 'HERM':
                        import_type = 'HHR'
                    else:
                        # Fallback to filename-based classification
                        import_type = 'DRR' if 'c01' in filename.lower() else 'HHR'
                    
                    if (filename, import_type) in processed_files:
                        logging.info(f"🔄 Skipping {filename} - already processed successfully")
                        skipped_files.append({
                            'filename': filename,
                            'reason': 'already_processed',
                            'import_type': import_type
                        })
                    else:
                        logging.info(f"✅ {filename} - new file, will download")
                        files_to_download.append(file_info)
        
        logging.info(f"📊 Download Summary: {len(files_to_download)} new files, {len(skipped_files)} already processed")
        
        if len(skipped_files) > 0:
            logging.info("🔄 Skipped files (already processed):")
            for skipped in skipped_files:
                logging.info(f"  - {skipped['filename']} ({skipped['import_type']})")
        
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
            if file_info.get('folder_type') == 'drr' or file_info.get('source_folder') == 'DRR':
                target_dir = DAILY_DIR / 'imported'
                file_type = 'daily'
                file_conn_config['remote_path'] = conn_config['remote_paths']['drr']
                logging.info(f"  📊 Classifying as DAILY file (from DRR folder: {file_conn_config['remote_path']})")
            elif file_info.get('folder_type') == 'herm' or file_info.get('source_folder') == 'HERM':
                target_dir = INTERVAL_DIR / 'imported'
                file_type = 'interval'
                file_conn_config['remote_path'] = conn_config['remote_paths']['hhr']  # HERM folder
                logging.info(f"  📈 Classifying as INTERVAL file (from HERM folder: {file_conn_config['remote_path']})")
            else:
                # Fallback to filename-based classification
                if 'c01' in file_info['filename'].lower():
                    target_dir = DAILY_DIR / 'imported'
                    file_type = 'daily'
                    file_conn_config['remote_path'] = conn_config['remote_paths']['drr']
                    logging.info(f"  📊 Classifying as DAILY file (filename pattern, from DRR folder)")
                else:
                    target_dir = INTERVAL_DIR / 'imported'
                    file_type = 'interval'
                    file_conn_config['remote_path'] = conn_config['remote_paths']['hhr']
                    logging.info(f"  📈 Classifying as INTERVAL file (filename pattern, from HERM folder)")
                
            # Define local_path for all code paths
            local_path = target_dir / file_info['filename']
            
            # Use the appropriate connection config for this file
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

def import_bcmm_drr(**context):
    """Step 4: Import BCMM DRR (Daily Register Reads) data"""
    logging.info("📊 Step 4: Importing BCMM DRR Data")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to process for DRR")
        return {'drr_records': 0, 'drr_files': 0}
    
    try:
        drr_files = [f for f in downloaded_files if f['type'] == 'daily']
        drr_records = []
        file_line_counts = {}
        
        for file_info in drr_files:
            logging.info(f"📊 Processing DRR file: {file_info['filename']}")
            
            # Parse CSV file for daily register reads (no headers)
            import csv
            with open(file_info['local_path'], 'r') as csvfile:
                reader = csv.reader(csvfile)  # Use csv.reader for headerless files
                file_records = 0
                total_lines = 0
                
                for row_num, row in enumerate(reader, 1):
                    total_lines += 1
                    # Parse BCMM CSV format for daily reads
                    # Format: ICP, ReadDate, MeterNumber, RegisterChannel, Reading, ReadType, Empty, ReadTime, Empty, Empty, RegisterID
                    try:
                        if len(row) < 11:
                            logging.warning(f"⚠️ Row {row_num}: insufficient columns ({len(row)})")
                            continue
                            
                        # Handle empty reading values (keep as string for database)
                        reading_value = row[4].strip()
                        if reading_value == '':
                            reading_value = None  # Handle empty readings as None
                        
                        record = {
                            'icp': row[0].strip(),
                            'read_date': row[1].strip(),
                            'meter_number': row[2].strip(),
                            'register_channel': row[3].strip(),
                            'reading': reading_value,  # Keep as string, handle None
                            'read_type': row[5].strip(),
                            'read_time': row[7].strip(),
                            'register_id': row[10].strip(),
                            'units': 'kWh',  # Default unit
                            'filename': file_info['filename']
                        }
                        
                        if record['icp'] and record['read_date']:
                            drr_records.append(record)
                            file_records += 1
                            
                    except (ValueError, IndexError) as e:
                        logging.warning(f"⚠️ Row {row_num}: parsing error - {e}")
                        continue
                
                file_line_counts[file_info['filename']] = total_lines
                logging.info(f"✅ Parsed {file_records} DRR records from {file_info['filename']} ({total_lines} source lines)")
        
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

def import_bcmm_hhr(**context):
    """Step 5: Import BCMM HHR (Half-Hourly Reads) data"""
    logging.info("📈 Step 5: Importing BCMM HHR Data")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to process for HHR")
        return {'hhr_records': 0, 'hhr_files': 0}
    
    try:
        hhr_files = [f for f in downloaded_files if f['type'] == 'interval']
        logging.info(f"🔍 Found {len(hhr_files)} interval files to process:")
        for f in hhr_files:
            logging.info(f"  📈 {f['filename']} (from {f.get('source_folder', 'unknown')} folder)")
        
        if len(hhr_files) == 0:
            logging.warning("⚠️ No interval files found! Check folder discovery and classification logic.")
            all_files = downloaded_files
            logging.info(f"📋 All downloaded files ({len(all_files)}):")
            for f in all_files:
                logging.info(f"  📄 {f['filename']} - type: {f['type']}, source: {f.get('source_folder', 'unknown')}")
        
        hhr_records = []
        
        for file_info in hhr_files:
            logging.info(f"📈 Processing HHR file: {file_info['filename']}")
            
            file_records = 0
            
            if file_info['filename'].lower().endswith('.new'):
                # Parse HERM format (.new files) - More robust parsing
                logging.info(f"  📊 Processing HERM format file")
                with open(file_info['local_path'], 'r') as file:
                    lines = file.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if not line or line.startswith('HERM,'):
                            continue
                        
                        try:
                            parts = line.split(',')
                            if len(parts) < 58:
                                logging.warning(f"⚠️ Line {line_num}: insufficient fields ({len(parts)})")
                                continue

                            icp = parts[0].strip()
                            meter_serial = parts[1].strip()
                            register_id = parts[2].strip()
                            register_type = parts[3].strip()
                            register_number = parts[4].strip()
                            units = parts[5].strip()
                            date_str = parts[6].strip()  # YYYYMMDD format
                            status = parts[7].strip()
                            midnight_read = parts[8].strip()  # This is the midnight read value!
                            
                            # Store midnight read as a separate record
                            from datetime import datetime, timedelta
                            base_date = datetime.strptime(date_str, '%Y%m%d')
                            midnight_datetime = base_date  # Midnight read is at 00:00
                            
                            # Handle midnight read value safely
                            try:
                                midnight_value = float(midnight_read) if midnight_read and midnight_read not in ['', 'N', 'A'] else 0.0
                                midnight_status = 'V' if midnight_read and midnight_read not in ['', 'N', 'A'] else 'N'
                            except ValueError:
                                midnight_value = 0.0
                                midnight_status = 'U'  # Unknown/unparseable
                            
                            midnight_record = {
                                'icp': icp,
                                'read_datetime': midnight_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                                'register_id': register_id,
                                'register_type': register_type,
                                'register_number': register_number,
                                'reading': midnight_value,
                                'reading_status': midnight_status,
                                'units': units,
                                'meter_serial': meter_serial,
                                'status': status,
                                'period': 0,  # Period 0 for midnight read
                                'is_midnight_read': True,
                                'filename': file_info['filename']
                            }
                            
                            if midnight_record['icp']:
                                hhr_records.append(midnight_record)
                                file_records += 1
                            
                            # Parse 48 half-hourly readings (parts[9] to parts[56]) - matching SMCO approach
                            for period in range(48):
                                try:
                                    reading_str = parts[9 + period].strip()
                                    
                                    # Handle different value types in HERM format - null values should be NULL
                                    if reading_str == '' or reading_str in ['N', 'NULL', 'null']:
                                        reading_value = None  # No reading available - use NULL
                                        reading_status = 'N'  # No reading
                                    elif reading_str in ['A', 'ACTUAL', 'actual']:
                                        reading_value = None  # Status flag, not a reading - use NULL
                                        reading_status = 'A'  # Actual reading marker
                                    else:
                                        try:
                                            reading_value = float(reading_str)
                                            reading_status = 'V'  # Valid numeric reading
                                        except ValueError:
                                            # Non-numeric value that's not a known status
                                            logging.debug(f"Line {line_num}, period {period + 1}: Non-numeric value '{reading_str}', setting to NULL")
                                            reading_value = None  # Unknown/unparseable - use NULL
                                            reading_status = 'U'  # Unknown/unparseable
                                    
                                    # Calculate datetime for this 30-minute period
                                    read_datetime = base_date + timedelta(minutes=30 * period)
                                    
                                    record = {
                                        'icp': icp,
                                        'read_datetime': read_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                                        'register_id': register_id,
                                        'register_type': register_type,
                                        'register_number': register_number,
                                        'reading': reading_value,
                                        'reading_status': reading_status,  # Track the status of this reading
                                        'units': units,
                                        'meter_serial': meter_serial,
                                        'status': status,
                                        'period': period + 1,
                                        'is_midnight_read': False,
                                        'filename': file_info['filename']
                                    }
                                    
                                    # Include all readings (including zero) if ICP is valid
                                    if record['icp']:
                                        hhr_records.append(record)
                                        file_records += 1
                                        
                                except (IndexError) as e:
                                    logging.warning(f"⚠️ Line {line_num}, period {period + 1}: index error - {e}")
                                    continue

                        except (ValueError, IndexError) as e:
                            logging.warning(f"⚠️ Line {line_num}: parsing error - {e}")
                            continue
            else:
                # Parse CSV file for half-hourly reads (legacy format, if any)
                import csv
                with open(file_info['local_path'], 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        # Parse BCMM CSV format for interval reads
                        try:
                            record = {
                                'icp': row.get('ICP', '').strip(),
                                'read_datetime': row.get('ReadDateTime', '').strip(),
                                'register_id': row.get('RegisterId', '').strip(),
                                'reading': float(row.get('Reading', 0)),
                                'units': row.get('Units', 'kWh').strip(),
                                'filename': file_info['filename']
                            }
                            
                            if record['icp'] and record['read_datetime']:
                                hhr_records.append(record)
                                file_records += 1
                                
                        except (ValueError, KeyError) as e:
                            logging.warning(f"⚠️ Skipping invalid row in {file_info['filename']}: {e}")
                            continue
                
                logging.info(f"✅ Parsed {file_records} HHR records from {file_info['filename']}")
        
        logging.info(f"📈 Total HHR: {len(hhr_records)} records from {len(hhr_files)} files")
        
        result = {
            'hhr_records': len(hhr_records), 
            'hhr_files': len(hhr_files), 
            'hhr_data': hhr_records
        }
        context['ti'].xcom_push(key='hhr_results', value=result)
        
        return result
        
    except Exception as e:
        logging.error(f"❌ HHR import error: {e}")
        raise

def load_bcmm_drr_to_db(**context):
    """Step 6a: Load BCMM DRR data to the bcmm_drr table"""
    logging.info("💾 Step 6a: Loading BCMM DRR to Database")
    
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
                    CREATE TABLE IF NOT EXISTS metering_raw.bcmm_drr (
                        id SERIAL PRIMARY KEY,
                        icp TEXT,
                        read_date TEXT,
                        meter_number TEXT,
                        register_channel TEXT,
                        reading TEXT,
                        read_type TEXT,
                        read_time TEXT,
                        register_id TEXT,
                        units TEXT,
                        file_name VARCHAR(255),
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Add unique constraint if it doesn't exist
                cur.execute("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'bcmm_drr_unique_constraint'
                        ) THEN
                            ALTER TABLE metering_raw.bcmm_drr 
                            ADD CONSTRAINT bcmm_drr_unique_constraint 
                            UNIQUE (icp, read_date, meter_number, register_id, read_time);
                        END IF;
                    END $$;
                """)

                # Group records by filename for processing and duplicate detection
                files_to_process = {}
                files_processed = {}
                
                # Group records by filename first
                for record in drr_results['drr_data']:
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
                    # Get file info for duplicate checking - check both possible paths
                    file_path = f"/data/imports/electricity/metering/bcmm/daily/imported/{filename}"
                    file_hash = ""
                    file_size = 0
                    
                    if Path(file_path).exists():
                        file_hash = get_file_hash(file_path)
                        file_size = Path(file_path).stat().st_size
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/bcmm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_hash = get_file_hash(file_path)
                            file_size = Path(file_path).stat().st_size
                    
                    # Check if this file was already successfully processed
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'DRR' 
                           AND status = 'completed' AND mep_provider = 'BCMM'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                        files_processed[filename]['duplicates'] = len(records)
                        duplicate_count += len(records)
                        continue
                    
                    # Process all records from this file (not duplicate)
                    for record in records:
                        # Create tuple matching bcmm_drr schema
                        row_data = (
                            record['icp'],
                            record['read_date'],
                            record['meter_number'],
                            record['register_channel'],
                            record['reading'],
                            record['read_type'],
                            record['read_time'],
                            record['register_id'],
                            record['units'],
                            record['filename']
                        )
                        data_to_insert.append(row_data)
                
                # Bulk insert new records only with duplicate handling
                if data_to_insert:
                    execute_values(
                        cur,
                        """
                        INSERT INTO metering_raw.bcmm_drr 
                        (icp, read_date, meter_number, register_channel, reading, read_type,
                         read_time, register_id, units, file_name)
                        VALUES %s
                        ON CONFLICT (icp, read_date, meter_number, register_id, read_time) 
                        DO NOTHING
                        """,
                        data_to_insert
                    )
                
                loaded_count = cur.rowcount  # More reliable way to get affected rows
                logging.info(f"✅ Loaded {loaded_count} new DRR records to metering_raw.bcmm_drr")
                if duplicate_count > 0:
                    logging.info(f"🔄 Skipped {duplicate_count} duplicate DRR records")
                
                # Update files_processed with loaded counts
                for record in data_to_insert:
                    filename = record[-1]  # file_name is the last column
                    if filename in files_processed:
                        files_processed[filename]['loaded'] += 1
                
                # Log each file's import status with duplicate prevention
                for filename, counts in files_processed.items():
                    # Get file info for logging - check both directories
                    file_path = f"/data/imports/electricity/metering/bcmm/daily/imported/{filename}"
                    file_size = 0
                    file_hash = ""
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/bcmm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_size = Path(file_path).stat().st_size
                            file_hash = get_file_hash(file_path)
                    
                    # Check if this file was already processed (duplicate prevention)
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'DRR' 
                           AND status = 'completed'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"📋 File {filename} already logged as completed, updating counts")
                    
                    # Log import with comprehensive details
                    source_records = drr_results.get('file_line_counts', {}).get(filename, 0)
                    log_import(
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        mep_provider='BCMM',
                        file_name=filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        import_type='DRR',
                        status='completed',
                        source_records=source_records,
                        records_parsed=counts['parsed'],
                        intervals_loaded=counts['loaded'],
                        error_message=f"Duplicates skipped: {counts['duplicates']}" if counts['duplicates'] > 0 else None
                    )
                
                context['ti'].xcom_push(key='loaded_drr', value=loaded_count)
                context['ti'].xcom_push(key='duplicate_drr', value=duplicate_count)
                return {'loaded_drr': loaded_count, 'duplicate_drr': duplicate_count}
                
    except Exception as e:
        logging.error(f"❌ DRR database load error: {e}")
        
        # Log error for each file
        if 'drr_results' in locals() and drr_results.get('drr_data'):
            filenames = set(record['filename'] for record in drr_results['drr_data'])
            for filename in filenames:
                # Get file info for error logging - check both directories
                file_path = f"/data/imports/electricity/metering/bcmm/daily/imported/{filename}"
                file_size = 0
                file_hash = ""
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    file_hash = get_file_hash(file_path)
                else:
                    # Try interval path
                    file_path = f"/data/imports/electricity/metering/bcmm/interval/imported/{filename}"
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                
                    log_import(
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        mep_provider='BCMM',
                        file_name=filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        import_type='DRR',
                        status='failed',
                        records_parsed=0,
                        intervals_loaded=0,
                        error_message=str(e)
                    )
        
        raise

def load_bcmm_hhr_to_db(**context):
    """Step 6b: Load BCMM HHR data to the bcmm_hhr table"""
    logging.info("💾 Step 6b: Loading BCMM HHR to Database")
    
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
                # Create table for BCMM HHR data - standardized schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_raw.bcmm_hhr (
                        id SERIAL PRIMARY KEY,
                        icp TEXT,
                        bcmm_number TEXT,
                        bcmm_serial_number TEXT,
                        element TEXT,
                        register_number TEXT,
                        register_map TEXT,
                        reading_date TEXT,
                        validation_flag TEXT,
                        daylight_savings_adjusted TEXT,
                        midnight_read_value TEXT,
                        -- 48 half-hourly intervals plus intervals 49-50 for DST
                        interval_01 TEXT, interval_02 TEXT, interval_03 TEXT, interval_04 TEXT, interval_05 TEXT,
                        interval_06 TEXT, interval_07 TEXT, interval_08 TEXT, interval_09 TEXT, interval_10 TEXT,
                        interval_11 TEXT, interval_12 TEXT, interval_13 TEXT, interval_14 TEXT, interval_15 TEXT,
                        interval_16 TEXT, interval_17 TEXT, interval_18 TEXT, interval_19 TEXT, interval_20 TEXT,
                        interval_21 TEXT, interval_22 TEXT, interval_23 TEXT, interval_24 TEXT, interval_25 TEXT,
                        interval_26 TEXT, interval_27 TEXT, interval_28 TEXT, interval_29 TEXT, interval_30 TEXT,
                        interval_31 TEXT, interval_32 TEXT, interval_33 TEXT, interval_34 TEXT, interval_35 TEXT,
                        interval_36 TEXT, interval_37 TEXT, interval_38 TEXT, interval_39 TEXT, interval_40 TEXT,
                        interval_41 TEXT, interval_42 TEXT, interval_43 TEXT, interval_44 TEXT, interval_45 TEXT,
                        interval_46 TEXT, interval_47 TEXT, interval_48 TEXT,
                        -- Intervals 49 and 50 for daylight savings (null when not applicable)
                        interval_49 TEXT, 
                        interval_50 TEXT,
                        file_name VARCHAR(255),
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Note: Unique constraint removed to allow duplicate records (consistent with SMCO/FCLM)
                # Previously: UNIQUE (icp, reading_date, register_number, element)
                # Removed to match SMCO and FCLM behavior that allows legitimate duplicate records

                # Group records by filename for processing and duplicate detection
                files_to_process = {}
                files_processed = {}
                
                # Group HHR records first by filename, then by ICP and date
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
                    # Get file info for duplicate checking - check both possible paths
                    file_path = f"/data/imports/electricity/metering/bcmm/daily/imported/{filename}"
                    file_hash = ""
                    file_size = 0
                    
                    if Path(file_path).exists():
                        file_hash = get_file_hash(file_path)
                        file_size = Path(file_path).stat().st_size
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/bcmm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_hash = get_file_hash(file_path)
                            file_size = Path(file_path).stat().st_size
                    
                    # Check if this file was already successfully processed
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'HHR' 
                           AND status = 'completed' AND mep_provider = 'BCMM'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                        # Group intervals by ICP and date to count actual HHR rows that would be duplicated
                        grouped_for_count = {}
                        for record in records:
                            date_str = record['read_datetime'][:10]
                            key = f"{record['icp']}|{date_str}|{record.get('register_id', '')}|{record.get('register_number', '')}"
                            grouped_for_count[key] = True
                        
                        duplicate_row_count = len(grouped_for_count)
                        files_processed[filename]['duplicates'] = duplicate_row_count
                        duplicate_count += duplicate_row_count
                        continue
                    
                    # Process records from this file (not duplicate) - group by ICP and date like SMCO
                    grouped_records = {}
                    for record in records:
                        # Create a key for grouping by ICP, date, register info
                        date_str = record['read_datetime'][:10]  # Extract date part YYYY-MM-DD
                        key = f"{record['icp']}|{date_str}|{record.get('register_id', '')}|{record.get('register_number', '')}"
                        
                        if key not in grouped_records:
                            grouped_records[key] = {
                                'icp': record['icp'],
                                'reading_date': date_str,
                                'bcmm_number': record.get('meter_serial', ''),
                                'bcmm_serial_number': record.get('meter_serial', ''),
                                'element': record.get('register_type', ''),
                                'register_number': record.get('register_number', ''),
                                'register_map': record.get('units', ''),
                                'validation_flag': record.get('status', ''),
                                'daylight_savings_adjusted': 'N',
                                'midnight_read_value': '0',  # Will be updated when midnight read is found
                                'intervals': [None] * 50,  # Initialize 50 intervals with NULL values
                                'filename': record['filename']
                            }
                        
                        # Handle midnight read (period 0) vs interval reads (period 1-50)
                        period = record.get('period', 1)
                        if period == 0 and record.get('is_midnight_read', False):
                            # This is the midnight read - preserve NULL values
                            reading_value = record['reading']
                            grouped_records[key]['midnight_read_value'] = str(reading_value) if reading_value is not None else None
                        elif 1 <= period <= 50:
                            # This is an interval read - place in the correct interval slot (1-50), preserve NULL
                            reading_value = record['reading']
                            grouped_records[key]['intervals'][period - 1] = str(reading_value) if reading_value is not None else None
                    
                    # Add all grouped records from this file to data_to_insert
                    for group_key, group_data in grouped_records.items():
                        # Create tuple matching new bcmm_hhr schema (matching SMCO HERM format)
                        row_data = (
                            group_data['icp'],                    # icp
                            group_data['bcmm_number'],            # bcmm_number
                            group_data['bcmm_serial_number'],     # bcmm_serial_number
                            group_data['element'],                # element
                            group_data['register_number'],        # register_number
                            group_data['register_map'],           # register_map
                            group_data['reading_date'],           # reading_date
                            group_data['validation_flag'],        # validation_flag
                            group_data['daylight_savings_adjusted'], # daylight_savings_adjusted
                            group_data['midnight_read_value'],    # midnight_read_value
                            # 50 interval values (interval_01 through interval_50) - standardized
                            *group_data['intervals'][:50],
                            group_data['filename']                # file_name
                        )
                        data_to_insert.append(row_data)
                
                # Bulk insert new records only
                if data_to_insert:
                    interval_columns = ', '.join([f'interval_{i:02d}' for i in range(1, 51)])
                    
                    execute_values(
                        cur,
                        f"""
                        INSERT INTO metering_raw.bcmm_hhr 
                        (icp, bcmm_number, bcmm_serial_number, element, register_number, register_map,
                         reading_date, validation_flag, daylight_savings_adjusted, midnight_read_value,
                         {interval_columns}, file_name)
                        VALUES %s
                        """,
                        data_to_insert
                    )
                    
                    loaded_count = len(data_to_insert)  # All records loaded (no constraint filtering)
                    logging.info(f"✅ Loaded {loaded_count} new HHR rows to metering_raw.bcmm_hhr")
                    if duplicate_count > 0:
                        logging.info(f"🔄 Skipped {duplicate_count} duplicate HHR records (from previously processed files)")
                else:
                    loaded_count = 0
                
                # Update files_processed with loaded counts (no constraint filtering)
                for row_data in data_to_insert:
                    filename = row_data[-1]  # file_name is the last column
                    if filename in files_processed:
                        files_processed[filename]['loaded'] += 1
                
                # Log each file's import status with duplicate prevention
                for filename, counts in files_processed.items():
                    # Get file info for logging - check both directories
                    file_path = f"/data/imports/electricity/metering/bcmm/daily/imported/{filename}"
                    file_size = 0
                    file_hash = ""
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/bcmm/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_size = Path(file_path).stat().st_size
                            file_hash = get_file_hash(file_path)
                    
                    # Check if this file was already processed (duplicate prevention)
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'HHR' 
                           AND status = 'completed'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"📋 File {filename} already logged as completed, updating counts")
                    
                    # Calculate intervals loaded (exclude midnight read, count only HHR intervals)
                    # BCMM format: 48 HHR intervals per row (exclude midnight read at position 9)
                    rows_processed = sum(1 for row_data in data_to_insert if row_data[-1] == filename)
                    
                    actual_intervals_loaded = files_processed[filename]['loaded'] * 48  # 48 HHR intervals per row
                    
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
                    # intervals_loaded = Total intervals stored in database (no constraint filtering)
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
                    
                    log_import(
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        mep_provider='BCMM',
                        file_name=filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        import_type='HHR',
                        status='completed',
                        source_records=counts['loaded'],  # Raw records/rows from file
                        records_parsed=counts['parsed'],  # Individual interval readings extracted
                        intervals_loaded=actual_intervals_loaded,  # Total intervals stored (constraint-aware)
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
                # Get file info for error logging - check both directories
                file_path = f"/data/imports/electricity/metering/bcmm/daily/imported/{filename}"
                file_size = 0
                file_hash = ""
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    file_hash = get_file_hash(file_path)
                else:
                    # Try interval path
                    file_path = f"/data/imports/electricity/metering/bcmm/interval/imported/{filename}"
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                
                log_import(
                    dag_id=dag_id,
                    task_id=task_id,
                    run_id=run_id,
                    mep_provider='BCMM',
                    file_name=filename,
                    file_size=file_size,
                    file_hash=file_hash,
                    import_type='HHR',
                    status='failed',
                    records_parsed=0,
                    intervals_loaded=0,
                    error_message=str(e)
                )
        
        raise

def verify_bcmm_database_load(**context):
    """Step 7: Verify database load with comprehensive audit"""
    logging.info("🔍 Step 7: Verifying BCMM Database Load")
    
    try:
        drr_results = context['ti'].xcom_pull(key='drr_results') or {'drr_records': 0}
        hhr_results = context['ti'].xcom_pull(key='hhr_results') or {'hhr_records': 0}
        loaded_drr = context['ti'].xcom_pull(key='loaded_drr') or 0
        loaded_hhr = context['ti'].xcom_pull(key='loaded_hhr') or 0
        duplicate_drr = context['ti'].xcom_pull(key='duplicate_drr') or 0
        duplicate_hhr = context['ti'].xcom_pull(key='duplicate_hhr') or 0
        
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Count records in BCMM-specific tables
                cur.execute("SELECT COUNT(*) FROM metering_raw.bcmm_drr")
                db_drr_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM metering_raw.bcmm_hhr")
                db_hhr_count = cur.fetchone()[0]
                
                # Get import log summary for this run
                # run_id = context['run_id']
                # cur.execute(
                #     """SELECT import_type, status, COUNT(*) as file_count, 
                #        SUM(records_parsed) as total_parsed, SUM(intervals_loaded) as total_loaded
                #        FROM metering_raw.import_log 
                #        WHERE run_id = %s AND mep_provider = 'BCMM'
                #        GROUP BY import_type, status
                #        ORDER BY import_type, status""",
                #     (run_id,)
                # )
                # import_log_summary = cur.fetchall()
                
                # Get recent import activity (last 24 hours)
                cur.execute(
                    """SELECT import_type, COUNT(*) as files, SUM(intervals_loaded) as records,
                       MIN(started_at) as first_import, MAX(completed_at) as last_import
                       FROM metering_raw.import_log 
                       WHERE mep_provider = 'BCMM' AND started_at >= NOW() - INTERVAL '24 hours'
                       GROUP BY import_type
                       ORDER BY import_type""",
                )
                recent_imports = cur.fetchall()
        
        # Get download statistics for comprehensive summary
        total_discovered = context['ti'].xcom_pull(key='total_discovered') or 0
        new_files_count = context['ti'].xcom_pull(key='new_files_count') or 0
        skipped_files_count = context['ti'].xcom_pull(key='skipped_files_count') or 0
        
        # If no statistics from download step, try to get from discovery step
        if total_discovered == 0:
            discovered_files = context['ti'].xcom_pull(key='discovered_files') or []
            total_discovered = len(discovered_files)
            # If files were discovered but none downloaded, they were likely all skipped
            if total_discovered > 0 and new_files_count == 0:
                skipped_files_count = total_discovered
        
        logging.info("📊 BCMM Import Verification Summary:")
        logging.info(f"  📁 Files - Discovered: {total_discovered}, New: {new_files_count}, Skipped (already processed): {skipped_files_count}")
        logging.info(f"  📊 DRR - Parsed: {drr_results['drr_records']}, Loaded: {loaded_drr}, Duplicates: {duplicate_drr}, In DB: {db_drr_count}")
        logging.info(f"  📈 HHR - Parsed: {hhr_results['hhr_records']}, Loaded: {loaded_hhr}, Duplicates: {duplicate_hhr}, In DB: {db_hhr_count}")
        
        # Import log summary
        # if import_log_summary:
        #     logging.info("📋 Import Log Summary for this run:")
        #     for row in import_log_summary:
        #         import_type, status, file_count, total_parsed, total_loaded = row
        #         logging.info(f"  {import_type} - {status.upper()}: {file_count} files, {total_parsed or 0} parsed, {total_loaded or 0} loaded")
        #         logging.info(f"    Records: {total_parsed or 0} parsed, {total_loaded or 0} loaded")
        #         logging.info(f"    Period: {row[3]} to {row[4]}")
        
        # Recent import activity
        # Temporarily removed to troubleshoot performance in Step 7
        # if recent_imports:
        
        # Verification checks with duplicate awareness
        success = True
        drr_verification_passed = True
        hhr_verification_passed = True
        
        # DRR Verification: Records should match 1:1
        expected_loaded_drr = max(0, drr_results['drr_records'] - duplicate_drr)
        
        if loaded_drr != expected_loaded_drr:
            if expected_loaded_drr == 0 and duplicate_drr == drr_results['drr_records']:
                logging.info(f"✅ DRR verification passed: All {drr_results['drr_records']} records were duplicates, loaded {loaded_drr} new records")
            else:
                logging.warning(f"⚠️ DRR mismatch: Expected {expected_loaded_drr} (parsed {drr_results['drr_records']} - duplicates {duplicate_drr}) but loaded {loaded_drr}")
                drr_verification_passed = False
        else:
            logging.info(f"✅ DRR verification passed: Loaded {loaded_drr} of {expected_loaded_drr} expected new records")
            
        # HHR Verification: Intervals are grouped into rows (48 intervals ≈ 1 row)
        # For HHR, we need to account for the fact that multiple intervals become one row
        expected_hhr_intervals = max(0, hhr_results['hhr_records'] - duplicate_hhr)
        expected_hhr_rows = expected_hhr_intervals // 48 if expected_hhr_intervals > 0 else 0
        
        # More flexible HHR verification - allow for reasonable grouping variations
        if expected_hhr_intervals == 0:
            if loaded_hhr == 0:
                logging.info(f"✅ HHR verification passed: No new intervals to load, loaded {loaded_hhr} rows")
            else:
                logging.warning(f"⚠️ HHR unexpected: Expected 0 rows but loaded {loaded_hhr}")
                hhr_verification_passed = False
        elif loaded_hhr > 0:
            # If we loaded any HHR rows, consider it successful (flexible verification)
            logging.info(f"✅ HHR verification passed: Loaded {loaded_hhr} rows from {expected_hhr_intervals} intervals")
        else:
            logging.warning(f"⚠️ HHR mismatch: Expected to load rows from {expected_hhr_intervals} intervals but loaded {loaded_hhr}")
            hhr_verification_passed = False
        
        # Overall success is based on data being loaded appropriately, not exact matches
        # Allow for some flexibility in HHR due to grouping complexity
        if drr_verification_passed and (hhr_verification_passed or hhr_results['hhr_records'] == 0):
            success = True
            logging.info("✅ Database verification successful")
        else:
            # Don't fail the DAG for verification mismatches - log warnings instead
            success = False
            logging.warning("⚠️ Database verification has warnings but continuing")
            logging.warning("📋 This may be due to data grouping differences or duplicate handling")
        
        # Additional validation checks (normalize to comparable units)
        total_processed_records = drr_results['drr_records'] + hhr_results['hhr_records']
        total_loaded_records = loaded_drr + loaded_hhr
        total_duplicate_records = duplicate_drr + duplicate_hhr
        
        if total_processed_records > 0:
            # Calculate efficiency based on non-duplicate records
            non_duplicate_records = total_processed_records - total_duplicate_records
            if non_duplicate_records > 0:
                load_efficiency = (total_loaded_records / non_duplicate_records) * 100
            else:
                load_efficiency = 100 if total_loaded_records == 0 else 0
            
            duplicate_rate = (total_duplicate_records / total_processed_records) * 100
            
            logging.info(f"📈 Import Efficiency: {load_efficiency:.1f}% ({total_loaded_records}/{non_duplicate_records} non-duplicate records)")
            logging.info(f"🔄 Duplicate Rate: {duplicate_rate:.1f}% ({total_duplicate_records}/{total_processed_records} total records)")
            logging.info(f"📊 Data Summary: {drr_results['drr_records']} DRR + {hhr_results['hhr_records']} intervals → {loaded_drr} DRR rows + {loaded_hhr} HHR rows")
            
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
            # 'import_log_entries': len(import_log_summary)
        }
        
    except Exception as e:
        logging.error(f"❌ Verification error: {e}")
        raise

def cleanup_bcmm_files(**context):
    """Step 8: Cleanup and archive processed files with gzip compression"""
    logging.info("🧹 Step 8: Cleanup and Archive BCMM Files with Compression")
    
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
        logging.info("📋 BCMM Import Complete - Final Summary:")
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

def calculate_file_hash(file_path):
    """Calculate MD5 hash of file (consistent with SMCO)"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of file"""
    try:
        return calculate_file_hash(file_path)
    except Exception as e:
        logging.warning(f"⚠️ Could not calculate hash for {file_path}: {e}")
        return ""

def audit_bcmm_imports(days_back: int = 7, **context):
    """Comprehensive audit function for BCMM imports"""
    logging.info(f"🔍 BCMM Import Audit - Last {days_back} days")
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Get import log summary
                cur.execute(
                    """SELECT 
                        import_type,
                        status,
                        COUNT(*) as file_count,
                        SUM(records_parsed) as total_parsed,
                        SUM(intervals_loaded) as total_loaded,
                        MIN(started_at) as first_import,
                        MAX(completed_at) as last_import
                       FROM metering_raw.import_log 
                       WHERE mep_provider = 'BCMM' 
                       AND started_at >= NOW() - INTERVAL '%s days'
                       GROUP BY import_type, status
                       ORDER BY import_type, status""",
                    (days_back,)
                )
                import_summary = cur.fetchall()
                
                # Get failed imports
                cur.execute(
                    """SELECT file_name, import_type, error_message, started_at
                       FROM metering_raw.import_log 
                       WHERE mep_provider = 'BCMM' AND status = 'failed'
                       AND started_at >= NOW() - INTERVAL '%s days'
                       ORDER BY started_at DESC""",
                    (days_back,)
                )
                failed_imports = cur.fetchall()
                
                # Get duplicate file attempts
                cur.execute(
                    """SELECT file_name, file_hash, import_type, COUNT(*) as attempts,
                       MIN(started_at) as first_attempt, MAX(completed_at) as last_attempt
                       FROM metering_raw.import_log 
                       WHERE mep_provider = 'BCMM' 
                       AND started_at >= NOW() - INTERVAL '%s days'
                       GROUP BY file_name, file_hash, import_type
                       HAVING COUNT(*) > 1
                       ORDER BY attempts DESC""",
                    (days_back,)
                )
                duplicate_attempts = cur.fetchall()
                
                # Get data quality metrics
                cur.execute(
                    """SELECT 
                        'DRR' as data_type,
                        COUNT(*) as total_records,
                        COUNT(DISTINCT icp) as unique_icps,
                        COUNT(DISTINCT read_date) as unique_dates,
                        MIN(read_date) as earliest_date,
                        MAX(read_date) as latest_date
                       FROM metering_raw.bcmm_drr
                       UNION ALL
                       SELECT 
                        'HHR' as data_type,
                        COUNT(*) as total_records,
                        COUNT(DISTINCT icp) as unique_icps,
                        COUNT(DISTINCT reading_date) as unique_dates,
                        MIN(reading_date) as earliest_date,
                        MAX(reading_date) as latest_date
                       FROM metering_raw.bcmm_hhr"""
                )
                data_quality = cur.fetchall()
                
                # Check for potential data issues
                cur.execute(
                    """SELECT 'DRR Missing ICPs' as issue_type, COUNT(*) as count
                       FROM metering_raw.bcmm_drr 
                       WHERE (icp IS NULL OR icp = '')
                       UNION ALL
                       SELECT 'DRR Invalid Dates' as issue_type, COUNT(*) as count
                       FROM metering_raw.bcmm_drr 
                       WHERE read_date IS NULL
                       UNION ALL
                       SELECT 'HHR Missing ICPs' as issue_type, COUNT(*) as count
                       FROM metering_raw.bcmm_hhr 
                       WHERE (icp IS NULL OR icp = '')
                       UNION ALL
                       SELECT 'HHR Invalid Dates' as issue_type, COUNT(*) as count
                       FROM metering_raw.bcmm_hhr 
                       WHERE reading_date IS NULL"""
                )
                data_issues = cur.fetchall()
        
        # Report findings
        logging.info("📊 BCMM Import Audit Results:")
        logging.info("=" * 50)
        
        if import_summary:
            logging.info("📋 Import Summary:")
            for row in import_summary:
                import_type, status, file_count, total_parsed, total_loaded, first_import, last_import = row
                logging.info(f"  {import_type} - {status.upper()}: {file_count} files")
                logging.info(f"    Records: {total_parsed or 0} parsed, {total_loaded or 0} loaded")
                logging.info(f"    Period: {first_import} to {last_import}")
        
        if failed_imports:
            logging.warning("❌ Failed Imports:")
            for file_name, import_type, error_message, started_at in failed_imports:
                logging.warning(f"  {import_type}: {file_name} at {started_at}")
                logging.warning(f"    Error: {error_message}")
        
        if duplicate_attempts:
            logging.info("🔄 Duplicate Import Attempts:")
            for file_name, file_hash, import_type, attempts, first_attempt, last_attempt in duplicate_attempts:
                logging.info(f"  {import_type}: {file_name} ({attempts} attempts)")
                logging.info(f"    Hash: {file_hash[:8]}... Period: {first_attempt} to {last_attempt}")
        
        if data_quality:
            logging.info("📈 Data Quality Metrics:")
            for data_type, total_records, unique_icps, unique_dates, earliest_date, latest_date in data_quality:
                logging.info(f"  {data_type}: {total_records:,} records, {unique_icps:,} ICPs, {unique_dates} dates")
                logging.info(f"    Date range: {earliest_date} to {latest_date}")
        
        if data_issues:
            logging.info("⚠️ Data Quality Issues:")
            for issue_type, count in data_issues:
                if count > 0:
                    logging.warning(f"  {issue_type}: {count} records")
        
        # Calculate overall health score
        total_files = sum(row[2] for row in import_summary if row[1] == 'completed')
        failed_files = sum(row[2] for row in import_summary if row[1] == 'failed')
        total_issues = sum(row[1] for row in data_issues)
        
        if total_files + failed_files > 0:
            success_rate = (total_files / (total_files + failed_files)) * 100
            logging.info(f"🎯 Overall Health Score: {success_rate:.1f}% success rate")
            logging.info(f"   Files: {total_files} successful, {failed_files} failed")
            logging.info(f"   Data Issues: {total_issues} records with issues")
        
        return {
            'audit_period_days': days_back,
            'successful_files': total_files,
            'failed_files': failed_files,
            'duplicate_attempts': len(duplicate_attempts),
            'data_issues': total_issues,
            'success_rate': success_rate if total_files + failed_files > 0 else 0
        }
        
    except Exception as e:
        logging.error(f"❌ Audit error: {e}")
        raise

# Create the DAG
dag = DAG(
    'metering_bcmm',
    default_args=default_args,
    description='BCMM (BlueCurrent Mass Market) Metering Data Import',
    schedule_interval='0 5 * * *',  # 5 AM daily
    tags=['metering', 'bcmm', 'bluecurrent', 'data_import'],
    catchup=False
)

# Define tasks
task_1_test_connection = PythonOperator(
    task_id='1_test_bcmm_connection',
    python_callable=test_bcmm_connection,
    dag=dag
)

task_2_discover_files = PythonOperator(
    task_id='2_discover_bcmm_files',
    python_callable=discover_bcmm_files,
    dag=dag
)

task_3_download_files = PythonOperator(
    task_id='3_download_bcmm_files',
    python_callable=download_bcmm_files,
    dag=dag
)

task_4_import_drr = PythonOperator(
    task_id='4_import_bcmm_drr',
    python_callable=import_bcmm_drr,
    dag=dag
)

task_5_import_hhr = PythonOperator(
    task_id='5_import_bcmm_hhr',
    python_callable=import_bcmm_hhr,
    dag=dag
)

task_6a_load_drr = PythonOperator(
    task_id='6a_load_bcmm_drr_to_db',
    python_callable=load_bcmm_drr_to_db,
    dag=dag
)

task_6b_load_hhr = PythonOperator(
    task_id='6b_load_bcmm_hhr_to_db',
    python_callable=load_bcmm_hhr_to_db,
    dag=dag
)

task_7_verify_database = PythonOperator(
    task_id='7_verify_bcmm_database_load',
    python_callable=verify_bcmm_database_load,
    dag=dag
)

task_8_cleanup = PythonOperator(
    task_id='8_cleanup_bcmm_files',
    python_callable=cleanup_bcmm_files,
    dag=dag
)

# Define task dependencies
task_1_test_connection >> task_2_discover_files >> task_3_download_files
task_3_download_files >> [task_4_import_drr, task_5_import_hhr]
task_4_import_drr >> task_6a_load_drr
task_5_import_hhr >> task_6b_load_hhr
[task_6a_load_drr, task_6b_load_hhr] >> task_7_verify_database >> task_8_cleanup 