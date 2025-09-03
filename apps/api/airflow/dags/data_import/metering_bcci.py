"""
BCCI (BlueCurrent Commercial & Industrial) Metering Data DAG

Individual DAG for BlueCurrent Commercial & Industrial metering provider with clear debugging steps:
1. Test Connection
2. Discover Files
3. Download Files (with duplicate detection)
4. Import DRR Data
5. Import HHR Data
6a. Load DRR to Database
6b. Load HHR to Database
7. Verify Database Load
8. Cleanup & Archive (with compression)

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
import csv
import hashlib
import gzip

# Add utils to path
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/metering/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))

# Simple SFTPDiscovery class to avoid import issues (consistent with SMCO/BCMM approach)
class SFTPDiscovery:
    """Simple SFTP discovery class for BCCI (matching SMCO/BCMM pattern)"""
    
    def __init__(self, connection_config):
        self.config = connection_config
        self.sftp_client = None
        self.ssh_client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def discover_files(self):
        """Discover files using paramiko SFTP"""
        try:
            import paramiko
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using the config
            ssh.connect(
                hostname=self.config['host'],
                port=self.config['port'],
                username=self.config['user'],
                password=self.config['password']
            )
            
            # Create SFTP client
            sftp = ssh.open_sftp()
            
            # List files in remote path
            remote_path = self.config['remote_path']
            files = sftp.listdir(remote_path)
            
            # Filter for TXT files and get file info
            discovered_files = []
            for filename in files:
                if filename.upper().endswith('.TXT'):
                    try:
                        stat = sftp.stat(f"{remote_path}/{filename}")
                        discovered_files.append({
                            'filename': filename,
                            'size': stat.st_size
                        })
                    except Exception as e:
                        logging.warning(f"⚠️ Could not get stats for {filename}: {e}")
                        discovered_files.append({
                            'filename': filename,
                            'size': 0
                        })
            
            sftp.close()
            ssh.close()
            
            return discovered_files
            
        except Exception as e:
            logging.error(f"❌ SFTP discovery error: {e}")
            return []
    
    def download_file(self, file_info, local_path):
        """Download a file using paramiko SFTP"""
        try:
            import paramiko
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using the config
            ssh.connect(
                hostname=self.config['host'],
                port=self.config['port'],
                username=self.config['user'],
                password=self.config['password']
            )
            
            # Create SFTP client
            sftp = ssh.open_sftp()
            
            # Download file
            remote_file_path = f"{self.config['remote_path']}/{file_info['filename']}"
            sftp.get(remote_file_path, str(local_path))
            
            sftp.close()
            ssh.close()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ SFTP download error for {file_info['filename']}: {e}")
            return False
    
    def close(self):
        """Close connections"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()

# Data processing directory (Corrected to use the /data volume mount)
DATA_DIR = Path('/data/imports/electricity/metering/bcci')
DAILY_DIR = DATA_DIR / 'daily'
INTERVAL_DIR = DATA_DIR / 'interval'

def ensure_directories():
    """Ensure processing directories exist"""
    for subdir in ['imported', 'archive', 'error']:
        (DAILY_DIR / subdir).mkdir(parents=True, exist_ok=True)
        (INTERVAL_DIR / subdir).mkdir(parents=True, exist_ok=True)

# Default arguments
default_args = {
    'owner': 'data_import',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 25),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

def get_timescale_connection():
    """Get TimescaleDB connection"""
# Import connection utility
import sys
sys.path.append('/app/airflow/utils')
from connection import get_connection

def get_timescale_connection():
    """DEPRECATED: Use get_connection() instead."""
    return get_connection()

def calculate_file_hash(file_path):
    """Calculate MD5 hash of file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of file (consistent with BCMM naming)"""
    try:
        return calculate_file_hash(file_path)
    except Exception as e:
        logging.warning(f"⚠️ Could not calculate hash for {file_path}: {e}")
        return ""

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

def test_bcci_connection(**context):
    """Step 1: Test BCCI SFTP connection"""
    logging.info("🔍 Step 1: Testing BCCI SFTP Connection")
    
    try:
        from connection_manager import ConnectionManager
        
        # Get BCCI connection config with ACTUAL folder structure from table
        conn_config = {
            'protocol': os.getenv('BLUECURRENT_CI_PROTOCOL'),
            'host': os.getenv('BLUECURRENT_CI_HOST'),
            'port': int(os.getenv('BLUECURRENT_CI_PORT')),
            'user': os.getenv('BLUECURRENT_CI_USER'),
            'password': os.getenv('BLUECURRENT_CI_PASS'),
            'remote_paths': {
                'daily_unvalidated': '/SFTP/C_I/Daily unvalidated',    # Daily unvalidated - FROM TABLE
                'monthly_validated': '/SFTP/C_I/Monthly validated',    # Monthly validated - FROM TABLE
                'drr': '/SFTP/C_I/Daily unvalidated',                  # Default to daily for DRR
                'monthly': '/SFTP/C_I/Monthly validated'               # Monthly data
            },
            'remote_path': '/SFTP/C_I/Daily unvalidated'  # Default to daily unvalidated - FROM TABLE
        }
        
        logging.info(f"Testing connection to {conn_config['host']}:{conn_config['port']}")
        
        if ConnectionManager.test_connection(conn_config):
            logging.info("✅ BCCI connection successful")
            context['ti'].xcom_push(key='connection_status', value='success')
            context['ti'].xcom_push(key='conn_config', value=conn_config)
            return True
        else:
            logging.error("❌ BCCI connection failed")
            context['ti'].xcom_push(key='connection_status', value='failed')
            raise Exception("BCCI connection test failed")
            
    except Exception as e:
        logging.error(f"❌ Connection test error: {e}")
        raise

def discover_bcci_files(**context):
    """Step 2: Discover BCCI EIEP3 files from SFTP"""
    logging.info("🔍 Step 2: Discovering BCCI EIEP3 Files")
    
    # Get connection status from previous task
    connection_status = context['ti'].xcom_pull(key='connection_status')
    
    # Connection config for BCCI EIEP3 files
    conn_config = {
        'protocol': os.getenv('BLUECURRENT_CI_PROTOCOL'),
        'host': os.getenv('BLUECURRENT_CI_HOST'),
        'port': int(os.getenv('BLUECURRENT_CI_PORT')),
        'user': os.getenv('BLUECURRENT_CI_USER'),
        'password': os.getenv('BLUECURRENT_CI_PASS'),
        'remote_paths': {
            'daily_unvalidated': '/SFTP/C_I/Daily unvalidated',    # Daily unvalidated EIEP3 files
            'monthly_validated': '/SFTP/C_I/Monthly validated',    # Monthly validated EIEP3 files
            'eiep3_daily': '/SFTP/C_I/Daily unvalidated',          # EIEP3 daily files
            'eiep3_monthly': '/SFTP/C_I/Monthly validated'         # EIEP3 monthly files
        },
        'remote_path': '/SFTP/C_I/Daily unvalidated'  # Default to daily unvalidated
    }

    # If connection status check failed and we have connection data, skip this task
    if connection_status == 'failed':
        raise Exception("Cannot discover files - connection test failed")
    
    try:
        # Use the local SFTPDiscovery class (consistent with SMCO/BCMM approach)
        # Discover EIEP3 files from all BCCI folders
        all_files = []

        with SFTPDiscovery(conn_config) as discovery:
            # Check Daily unvalidated folder (EIEP3 daily files)
            daily_config = conn_config.copy()
            daily_config['remote_path'] = conn_config['remote_paths']['eiep3_daily']
            logging.info(f"🔍 Checking Daily unvalidated folder: {daily_config['remote_path']}")
            daily_discovery = SFTPDiscovery(daily_config)
            daily_files = daily_discovery.discover_files()
            for f in daily_files:
                f['folder_type'] = 'eiep3_daily'
                f['data_type'] = 'daily_eiep3'
                f['source_folder'] = 'Daily unvalidated'
            all_files.extend(daily_files)
            logging.info(f"📊 Found {len(daily_files)} files in Daily unvalidated folder")

            # Check Monthly validated folder (EIEP3 monthly files)
            monthly_config = conn_config.copy()
            monthly_config['remote_path'] = conn_config['remote_paths']['eiep3_monthly']
            logging.info(f"🔍 Checking Monthly validated folder: {monthly_config['remote_path']}")
            monthly_discovery = SFTPDiscovery(monthly_config)
            monthly_files = monthly_discovery.discover_files()
            for f in monthly_files:
                f['folder_type'] = 'eiep3_monthly'
                f['data_type'] = 'monthly_eiep3'
                f['source_folder'] = 'Monthly validated'
            all_files.extend(monthly_files)
            logging.info(f"📊 Found {len(monthly_files)} files in Monthly validated folder")

            # Filter for EIEP3 data files (TXT extensions)
            eiep3_files = [f for f in all_files if f['filename'].upper().endswith('.TXT')]

            # Log file distribution by folder
            daily_txt_files = [f for f in eiep3_files if f['folder_type'] == 'eiep3_daily']
            monthly_txt_files = [f for f in eiep3_files if f['folder_type'] == 'eiep3_monthly']
            logging.info(f"📊 EIEP3 Files found - Daily: {len(daily_txt_files)}, Monthly: {len(monthly_txt_files)}")

            for f in daily_txt_files:
                logging.info(f"  📄 Daily EIEP3: {f['filename']}")
            for f in monthly_txt_files:
                logging.info(f"  📄 Monthly EIEP3: {f['filename']}")

            logging.info(f"📊 Found {len(eiep3_files)} BCCI EIEP3 files")
            for file_info in eiep3_files:
                logging.info(f"  - {file_info['filename']} ({file_info['size']} bytes)")
            
            context['ti'].xcom_push(key='discovered_files', value=eiep3_files)
            context['ti'].xcom_push(key='files_count', value=len(eiep3_files))
            context['ti'].xcom_push(key='conn_config', value=conn_config)  # Store config for later tasks
            
            return eiep3_files
            
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def download_bcci_files(**context):
    """Step 3: Download BCCI files with duplicate checking"""
    logging.info("⬇️ Step 3: Downloading BCCI Files (with duplicate detection)")
    
    files = context['ti'].xcom_pull(key='discovered_files')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    # If no files from discovery, try to discover them first
    if not files:
        logging.info("ℹ️ No files from discovery, attempting to discover files first")
        try:
            files = discover_bcci_files(**context)
            conn_config = context['ti'].xcom_pull(key='conn_config')
        except Exception as e:
            logging.info(f"ℹ️ No files to download - discovery failed: {e}")
        return []
    
    # If no connection config, create it
    if not conn_config:
        logging.info("ℹ️ No connection config from previous tasks, creating new config")
        conn_config = {
            'protocol': os.getenv('BLUECURRENT_CI_PROTOCOL'),
            'host': os.getenv('BLUECURRENT_CI_HOST'),
            'port': int(os.getenv('BLUECURRENT_CI_PORT')),
            'user': os.getenv('BLUECURRENT_CI_USER'),
            'password': os.getenv('BLUECURRENT_CI_PASS'),
            'remote_paths': {
                'daily_unvalidated': '/SFTP/C_I/Daily unvalidated',    # Daily unvalidated - FROM TABLE
                'monthly_validated': '/SFTP/C_I/Monthly validated',    # Monthly validated - FROM TABLE
                'drr': '/SFTP/C_I/Daily unvalidated',                  # Default to daily for DRR
                'monthly': '/SFTP/C_I/Monthly validated'               # Monthly data
            },
            'remote_path': '/SFTP/C_I/Daily unvalidated'  # Default to daily unvalidated - FROM TABLE
        }
    
    try:
        # Use the local SFTPDiscovery class (consistent with SMCO/BCMM approach)
        
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
                    """SELECT file_name FROM metering_raw.import_log 
                       WHERE mep_provider = 'BCCI' AND status = 'completed' AND import_type = 'EIEP3'"""
                )
                processed_files = {row[0] for row in cur.fetchall()}
                logging.info(f"Found {len(processed_files)} already processed EIEP3 files for BCCI.")

                for file_info in files:
                    filename = file_info['filename']
                    
                    # All BCCI files are EIEP3 format
                    import_type = 'EIEP3'
                    
                    if filename in processed_files:
                        skipped_files.append(filename) # Simpler logging
                    else:
                        files_to_download.append(file_info)
        
        logging.info(f"📊 Download Summary: {len(files_to_download)} new files, {len(skipped_files)} already processed")
        
        if len(skipped_files) > 0:
            logging.info("🔄 Skipped files (already processed):")
            for filename in skipped_files:
                logging.info(f"  - {filename}")
        
        if len(files_to_download) == 0:
            logging.info("ℹ️ No new files to download - all discovered files have been processed already")
            context['ti'].xcom_push(key='downloaded_files', value=[])
            context['ti'].xcom_push(key='skipped_files', value=skipped_files)
            context['ti'].xcom_push(key='skipped_files_count', value=len(skipped_files))
            return []
        
        downloaded_files = []
        
        for file_info in files_to_download:
            logging.info(f"⬇️ Downloading {file_info['filename']} from {file_info.get('source_folder', 'unknown')} folder")
            
            # Create appropriate connection config for this file's source folder
            file_conn_config = conn_config.copy()
            
            # Determine target directory, file type, and remote path based on source folder (EIEP3 format)
            if file_info.get('folder_type') == 'eiep3_daily' or file_info.get('source_folder') == 'Daily unvalidated':
                target_dir = DAILY_DIR / 'imported'
                file_type = 'daily_eiep3'
                file_conn_config['remote_path'] = conn_config['remote_paths']['daily_unvalidated']
                logging.info(f"  📊 Classifying as DAILY EIEP3 file (from Daily unvalidated folder: {file_conn_config['remote_path']})")
            elif file_info.get('folder_type') == 'eiep3_monthly' or file_info.get('source_folder') == 'Monthly validated':
                target_dir = INTERVAL_DIR / 'imported'
                file_type = 'monthly_eiep3'
                file_conn_config['remote_path'] = conn_config['remote_paths']['monthly_validated']
                logging.info(f"  📈 Classifying as MONTHLY EIEP3 file (from Monthly validated folder: {file_conn_config['remote_path']})")
            else:
                # Fallback to filename-based classification for EIEP3
                if 'daily' in file_info['filename'].lower() or file_info['filename'].upper().endswith('.TXT'):
                    target_dir = DAILY_DIR / 'imported'
                    file_type = 'daily_eiep3'
                    file_conn_config['remote_path'] = conn_config['remote_paths']['daily_unvalidated']
                    logging.info(f"  📊 Classifying as DAILY EIEP3 file (filename pattern)")
                else:
                    target_dir = INTERVAL_DIR / 'imported'
                    file_type = 'monthly_eiep3'
                    file_conn_config['remote_path'] = conn_config['remote_paths']['monthly_validated']
                    logging.info(f"  📈 Classifying as MONTHLY EIEP3 file (filename pattern)")
            
            local_path = target_dir / file_info['filename']
            
            # Use the appropriate connection config for this file
            with SFTPDiscovery(file_conn_config) as file_discovery:
                if file_discovery.download_file(file_info, local_path):
                    downloaded_files.append({
                        'filename': file_info['filename'],
                        'local_path': str(local_path),
                        'size': file_info.get('size', 0),
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

def import_bcci_eiep3(**context):
    """Step 4: Import BCCI EIEP3 data from downloaded files"""
    logging.info("📊 Step 4: Importing BCCI EIEP3 Data")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No files to import")
        return {'eiep3_records': 0, 'eiep3_data': [], 'file_line_counts': {}}
    
    eiep3_data = []
    total_records = 0
    file_line_counts = {}
    
    for file_info in downloaded_files:
        file_path = file_info['local_path']
        filename = file_info['filename']
        
        logging.info(f"📄 Processing EIEP3 file: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_records = 0
                header_info = {}
                total_lines = 0
                
                for line_num, line in enumerate(file, 1):
                    total_lines = line_num
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(',')
                    
                    if line.startswith('HDR'):
                        # Parse header: HDR,ICPHH,11.0,AMCI,YESP,,18/01/2024,15:29:07,0001,1632,202401,E,I
                        if len(parts) >= 13:
                            header_info = {
                                'record_type': parts[1] if len(parts) > 1 else '',      # ICPHH
                                'version': parts[2] if len(parts) > 2 else '',          # 11.0
                                'from_participant': parts[3] if len(parts) > 3 else '', # AMCI
                                'to_participant': parts[4] if len(parts) > 4 else '',   # YESP
                                'via_participant': parts[5] if len(parts) > 5 else '',  # Via
                                'creation_date': parts[6] if len(parts) > 6 else '',    # 18/01/2024
                                'creation_time': parts[7] if len(parts) > 7 else '',    # 15:29:07
                                'file_sequence': parts[8] if len(parts) > 8 else '',    # 0001
                                'record_count': parts[9] if len(parts) > 9 else '',     # 1632
                                'period': parts[10] if len(parts) > 10 else '',         # 202401
                                'data_type': parts[11] if len(parts) > 11 else '',      # E
                                'process_flag': parts[12] if len(parts) > 12 else ''    # I
                            }
                            logging.info(f"  📋 Header: {header_info['record_type']} from {header_info['from_participant']} to {header_info['to_participant']}, Period: {header_info['period']}")
                    
                    elif line.startswith('DET'):
                        # Parse detail: DET,0000438016MP0FD,215504779,F,01/01/2024,1,0.000,0.312,,I,
                        if len(parts) >= 10:
                            # Get process flag to determine record type
                            process_flag = parts[9].strip() if len(parts) > 9 else ''
                            
                            # Process both Import (I) and Export (X) records
                            if process_flag in ['I', 'X']:
                                # Safely get parts, defaulting to '0' for numeric fields if empty or missing
                                import_value = parts[6].strip() if len(parts) > 6 and parts[6].strip() else '0'
                                export_value = parts[7].strip() if len(parts) > 7 and parts[7].strip() else '0'

                                record = {
                                    'filename': filename,
                                    'line_number': line_num,
                                    'record_type': 'DET',
                                    'icp': parts[1] if len(parts) > 1 else '',              # ICP
                                    'meter_serial': parts[2] if len(parts) > 2 else '',     # Meter Serial
                                    'channel': parts[3] if len(parts) > 3 else '',          # Channel (F, G, etc.)
                                    'read_date': parts[4] if len(parts) > 4 else '',        # Date
                                    'period': parts[5] if len(parts) > 5 else '',           # Period (1-48 for HH)
                                    'import_value': import_value,    # Import kWh
                                    'export_value': export_value,    # Export kWh
                                    'units': parts[8] if len(parts) > 8 else '',            # Units
                                    'process_flag': process_flag,                           # Process flag (I or X)
                                    'source_folder': file_info.get('source_folder', ''),
                                    'folder_type': file_info.get('folder_type', ''),
                                    # Include header info
                                    'header_from': header_info.get('from_participant', ''),
                                    'header_to': header_info.get('to_participant', ''),
                                    'header_period': header_info.get('period', ''),
                                    'header_data_type': header_info.get('data_type', ''),
                                    'header_version': header_info.get('version', '')
                                }
                                
                                eiep3_data.append(record)
                                file_records += 1
                
                total_records += file_records
                file_line_counts[filename] = total_lines
                logging.info(f"  ✅ Imported {file_records} EIEP3 records from {filename} ({total_lines} source lines)")
        
        except Exception as e:
            logging.error(f"❌ Error processing EIEP3 file {filename}: {e}")
            continue
    
    logging.info(f"📊 Total EIEP3 records imported: {total_records}")
    
    # Store results for next step
    results = {
        'eiep3_records': total_records,
        'eiep3_data': eiep3_data,
        'file_line_counts': file_line_counts
    }
    
    context['ti'].xcom_push(key='eiep3_results', value=results)
    return results

def load_bcci_eiep3_to_db(**context):
    """Step 5: Load BCCI EIEP3 data to existing BlueCurrent EIEP3 table"""
    logging.info("💾 Step 5: Loading BCCI EIEP3 to Database")
    
    eiep3_results = context['ti'].xcom_pull(key='eiep3_results')
    if not eiep3_results or eiep3_results['eiep3_records'] == 0:
        logging.info("ℹ️ No EIEP3 data to load")
        return {'loaded_eiep3': 0}
    
    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Create schema and table if not exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS metering_raw")
                
                # Ensure the target table exists with the correct schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_raw.bluecurrent_eiep3 (
                        id SERIAL PRIMARY KEY,
                        record_type VARCHAR(10),
                        icp_identifier VARCHAR(50),
                        data_stream_identifier VARCHAR(50),
                        reading_type VARCHAR(20),
                        date_field TEXT,
                        trading_period INTEGER,
                        active_energy NUMERIC,
                        reactive_energy NUMERIC,
                        apparent_energy NUMERIC,
                        energy_flow_direction VARCHAR(10),
                        data_stream_type VARCHAR(10),
                        extra_field_1 TEXT,
                        extra_field_2 TEXT,
                        extra_field_3 TEXT,
                        extra_field_4 TEXT,
                        extra_field_5 TEXT,
                        file_name VARCHAR(255),
                        row_number INTEGER,
                        imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Add unique constraint if it doesn't exist (include energy_flow_direction for I/X records)
                cur.execute("""
                    DO $$ 
                    BEGIN
                        -- Drop old constraint if it exists
                        IF EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'bluecurrent_eiep3_unique_constraint'
                        ) THEN
                            ALTER TABLE metering_raw.bluecurrent_eiep3 
                            DROP CONSTRAINT bluecurrent_eiep3_unique_constraint;
                        END IF;
                        
                        -- Add new constraint that includes energy_flow_direction
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'bluecurrent_eiep3_unique_constraint_with_flow'
                        ) THEN
                            ALTER TABLE metering_raw.bluecurrent_eiep3 
                            ADD CONSTRAINT bluecurrent_eiep3_unique_constraint_with_flow 
                            UNIQUE (icp_identifier, date_field, trading_period, data_stream_identifier, energy_flow_direction);
                        END IF;
                    END $$;
                """)

                # Group records by filename for processing and duplicate detection
                files_to_process = {}
                files_processed = {}
                
                # Group records by filename first
                for record in eiep3_results['eiep3_data']:
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
                    file_path = f"/data/imports/electricity/metering/bcci/daily/imported/{filename}"
                    file_hash = ""
                    file_size = 0
                    
                    if Path(file_path).exists():
                        file_hash = get_file_hash(file_path)
                        file_size = Path(file_path).stat().st_size
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/bcci/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_hash = get_file_hash(file_path)
                            file_size = Path(file_path).stat().st_size
                    
                    # Check if this file was already successfully processed
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'EIEP3' 
                           AND status = 'completed' AND mep_provider = 'BCCI'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"🔄 Skipping file {filename} - already processed successfully")
                        files_processed[filename]['duplicates'] = len(records)
                        duplicate_count += len(records)
                        continue
                    
                    # Process all records from this file (not duplicate)
                    for record in records:
                        # Create tuple matching existing bluecurrent_eiep3 schema
                        row_data = (
                            record['record_type'],           # record_type (DET)
                            record['icp'],                   # icp_identifier
                            record['meter_serial'],          # data_stream_identifier
                            record['channel'],               # reading_type
                            record['read_date'],             # date_field
                            record['period'],                # trading_period
                            record['import_value'],          # active_energy
                            record['export_value'],          # reactive_energy
                            None,                            # apparent_energy (use None for NULL)
                            record['process_flag'],          # energy_flow_direction (I or X)
                            record.get('header_data_type', 'E'),  # data_stream_type
                            record['source_folder'],         # extra_field_1
                            record['folder_type'],           # extra_field_2
                            record['header_from'],           # extra_field_3
                            record['header_to'],             # extra_field_4
                            record['header_period'],         # extra_field_5
                            record['filename'],              # file_name
                            record['line_number']            # row_number
                        )
                        data_to_insert.append(row_data)
                
                # Bulk insert new records only
                if data_to_insert:
                    execute_values(
                        cur,
                        """
                        INSERT INTO metering_raw.bluecurrent_eiep3 
                        (record_type, icp_identifier, data_stream_identifier, reading_type, 
                         date_field, trading_period, active_energy, reactive_energy, apparent_energy,
                         energy_flow_direction, data_stream_type, extra_field_1, extra_field_2, 
                         extra_field_3, extra_field_4, extra_field_5, file_name, row_number)
                        VALUES %s
                        ON CONFLICT (icp_identifier, date_field, trading_period, data_stream_identifier, energy_flow_direction) 
                        DO NOTHING
                        """,
                        data_to_insert
                    )
                
                loaded_count = len(data_to_insert)
                logging.info(f"✅ Loaded {loaded_count} new EIEP3 records to metering_raw.bluecurrent_eiep3")
                if duplicate_count > 0:
                    logging.info(f"🔄 Skipped {duplicate_count} duplicate EIEP3 records")
                
                # Update files_processed with actual database rows loaded per file
                for record in data_to_insert:
                    filename = record[16]  # file_name is at index 16
                    if filename in files_processed:
                        files_processed[filename]['loaded'] += 1
                
                # Log each file's import status with duplicate prevention
                for filename, counts in files_processed.items():
                    # Get file info for logging - check both directories
                    file_path = f"/data/imports/electricity/metering/bcci/daily/imported/{filename}"
                    file_size = 0
                    file_hash = ""
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = get_file_hash(file_path)
                    else:
                        # Try interval path
                        file_path = f"/data/imports/electricity/metering/bcci/interval/imported/{filename}"
                        if Path(file_path).exists():
                            file_size = Path(file_path).stat().st_size
                            file_hash = get_file_hash(file_path)
                    
                    # Check if this file was already processed (duplicate prevention)
                    cur.execute(
                        """SELECT COUNT(*) FROM metering_raw.import_log 
                           WHERE file_name = %s AND file_hash = %s AND import_type = 'EIEP3' 
                           AND status = 'completed'""",
                        (filename, file_hash)
                    )
                    
                    if cur.fetchone()[0] > 0:
                        logging.info(f"📋 File {filename} already logged as completed, updating counts")
                    
                    # Log import with comprehensive details
                    source_records = eiep3_results.get('file_line_counts', {}).get(filename, 0)
                    log_import(
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        mep_provider='BCCI',
                        file_name=filename,
                        file_size=file_size,
                        file_hash=file_hash,
                        import_type='EIEP3',
                        status='completed',
                        source_records=source_records,
                        records_parsed=counts['parsed'],
                        intervals_loaded=counts['loaded'],
                        error_message=f"Duplicates skipped: {counts['duplicates']}" if counts['duplicates'] > 0 else None
                    )
                
                context['ti'].xcom_push(key='loaded_eiep3', value=loaded_count)
                context['ti'].xcom_push(key='duplicate_eiep3', value=duplicate_count)
                return {'loaded_eiep3': loaded_count, 'duplicate_eiep3': duplicate_count}
            
    except Exception as e:
        logging.error(f"❌ EIEP3 database load error: {e}")
        
        # Log error for each file
        if 'eiep3_results' in locals() and eiep3_results.get('eiep3_data'):
            filenames = set(record['filename'] for record in eiep3_results['eiep3_data'])
            for filename in filenames:
                # Get file info for error logging - check both directories
                file_path = f"/data/imports/electricity/metering/bcci/daily/imported/{filename}"
                file_size = 0
                file_hash = ""
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    file_hash = get_file_hash(file_path)
                else:
                    # Try interval path
                    file_path = f"/data/imports/electricity/metering/bcci/interval/imported/{filename}"
                    if Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size
                        file_hash = calculate_file_hash(file_path)
                
                log_import(
                    dag_id=dag_id,
                    task_id=task_id,
                    run_id=run_id,
                    mep_provider='BCCI',
                    file_name=filename,
                    file_size=file_size,
                    file_hash=file_hash,
                    import_type='EIEP3',
                    status='failed',
                    source_records=0,
                    records_parsed=0,
                    intervals_loaded=0,
                    error_message=str(e)
                )
        
        raise

def verify_bcci_database_load(**context):
    """Step 6: Verify database load with comprehensive audit"""
    logging.info("🔍 Step 6: Verifying BCCI EIEP3 Database Load")
    
    try:
        eiep3_results = context['ti'].xcom_pull(key='eiep3_results') or {'eiep3_records': 0}
        loaded_eiep3 = context['ti'].xcom_pull(key='loaded_eiep3') or 0
        duplicate_eiep3 = context['ti'].xcom_pull(key='duplicate_eiep3') or 0
        
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Count records in EIEP3 table
                cur.execute("SELECT COUNT(*) FROM metering_raw.bluecurrent_eiep3 WHERE extra_field_3 = 'AMCI' OR extra_field_4 = 'YESP'")
                db_eiep3_count = cur.fetchone()[0]
                
                # Get import log summary for this run
                run_id = context['run_id']
                cur.execute(
                    """SELECT import_type, status, COUNT(*) as file_count, 
                       SUM(records_parsed) as total_parsed, SUM(intervals_loaded) as total_loaded
                       FROM metering_raw.import_log 
                       WHERE run_id = %s AND mep_provider = 'BCCI'
                       GROUP BY import_type, status
                       ORDER BY import_type, status""",
                    (run_id,)
                )
                import_log_summary = cur.fetchall()
                
                # Get recent import activity
                cur.execute(
                    """SELECT file_name, import_type, status, intervals_loaded, completed_at
                       FROM metering_raw.import_log 
                       WHERE mep_provider = 'BCCI' AND completed_at >= NOW() - INTERVAL '24 hours'
                       ORDER BY completed_at DESC LIMIT 10""",
                    ()
                )
                recent_imports = cur.fetchall()
                
                logging.info("📊 BCCI EIEP3 Import Verification Results:")
                logging.info(f"  📄 Files processed this run: {eiep3_results['eiep3_records']} records")
                logging.info(f"  💾 Records loaded to DB: {loaded_eiep3}")
                logging.info(f"  🔄 Duplicate records skipped: {duplicate_eiep3}")
                logging.info(f"  📋 Total EIEP3 records in DB: {db_eiep3_count}")
                
                # Import efficiency calculation
                total_processed = eiep3_results['eiep3_records']
                if total_processed > 0:
                    efficiency = (loaded_eiep3 / total_processed) * 100
                    duplicate_rate = (duplicate_eiep3 / total_processed) * 100
                    logging.info(f"  📈 Import Efficiency: {efficiency:.1f}%")
                    logging.info(f"  🔄 Duplicate Rate: {duplicate_rate:.1f}%")
                
                # Import log summary
                if import_log_summary:
                    logging.info("📋 Import Log Summary (this run):")
                    for log_entry in import_log_summary:
                        import_type, status, file_count, total_parsed, total_loaded = log_entry
                        logging.info(f"  {import_type} - {status}: {file_count} files, {total_parsed or 0} parsed, {total_loaded or 0} loaded")
                
                # Recent import activity
                if recent_imports:
                    logging.info("🕒 Recent Import Activity (24h):")
                    for recent in recent_imports[:5]:  # Show top 5
                        file_name, import_type, status, intervals_loaded, completed_at = recent
                        logging.info(f"  {completed_at}: {file_name} ({import_type}) - {status} - {intervals_loaded or 0} records")
                
                # Store verification success for cleanup step
                context['ti'].xcom_push(key='verification_success', value=True)
                
                return {
                    'verification_status': 'completed',
                    'total_eiep3_records': db_eiep3_count,
                    'loaded_this_run': loaded_eiep3,
                    'duplicates_skipped': duplicate_eiep3,
                    'efficiency': efficiency if total_processed > 0 else 0
                }
                
    except Exception as e:
        logging.error(f"❌ Database verification error: {e}")
        # Store verification failure for cleanup step
        context['ti'].xcom_push(key='verification_success', value=False)
        return {'verification_status': 'failed', 'error': str(e)}

def cleanup_bcci_files(**context):
    """Step 8: Cleanup and archive processed files with gzip compression"""
    logging.info("🧹 Step 8: Cleanup and Archive BCCI Files with Compression")
    
    try:
        downloaded_files = context['ti'].xcom_pull(key='downloaded_files') or []
        verification = context['ti'].xcom_pull(key='verification_success', default=False)
        
        archived_count = 0
        error_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        # Process files that were downloaded in this run
        for file_info in downloaded_files:
            source_path = Path(file_info['local_path'])
            
            if not source_path.exists():
                logging.warning(f"⚠️ Source file not found: {source_path}")
                continue
                
            original_size = source_path.stat().st_size
            total_original_size += original_size
            
            if verification:
                # Compress and archive on success
                if file_info['type'] in ['daily', 'daily_eiep3']:
                    target_dir = DAILY_DIR / 'archive'
                    archived_count += 1
                else:
                    target_dir = INTERVAL_DIR / 'archive'
                    archived_count += 1
            else:
                # Compress and move to error on failure
                if file_info['type'] in ['daily', 'daily_eiep3']:
                    target_dir = DAILY_DIR / 'error'
                    error_count += 1
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
        
        # Also archive any remaining files in imported directories that weren't processed in this run
        additional_files_processed = 0
        for import_dir in [DAILY_DIR / 'imported', INTERVAL_DIR / 'imported']:
            if import_dir.exists():
                for file_path in import_dir.glob('*.TXT'):
                    logging.info(f"🔍 Found additional file to archive: {file_path.name}")
                    
                    original_size = file_path.stat().st_size
                    total_original_size += original_size
                    
                    # Determine target directory based on source directory
                    if import_dir == DAILY_DIR / 'imported':
                        target_dir = DAILY_DIR / 'archive' if verification else DAILY_DIR / 'error'
                    else:
                        target_dir = INTERVAL_DIR / 'archive' if verification else INTERVAL_DIR / 'error'
                    
                    # Ensure target directory exists
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Compress file with gzip maximum compression (level 9)
                    compressed_filename = f"{file_path.name}.gz"
                    target_path = target_dir / compressed_filename
                    
                    try:
                        with open(file_path, 'rb') as f_in:
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
                        file_path.unlink()
                        
                        if verification:
                            archived_count += 1
                        else:
                            error_count += 1
                        additional_files_processed += 1
                        
                        logging.info(f"🗜️ Compressed additional file {file_path.name} → {compressed_filename}")
                        logging.info(f"   📊 Size: {original_size:,} bytes → {compressed_size:,} bytes ({compression_ratio:.1f}% reduction)")
                        logging.info(f"   📁 Archived to: {target_path.parent.name}")
                        
                    except Exception as e:
                        logging.error(f"❌ Failed to compress additional file {file_path.name}: {e}")
                        # Fallback: move file without compression
                        fallback_target = target_dir / file_path.name
                        file_path.rename(fallback_target)
                        if verification:
                            archived_count += 1
                        else:
                            error_count += 1
                        additional_files_processed += 1
                        logging.info(f"📁 Moved additional file {file_path.name} to {target_dir.name} (uncompressed fallback)")
        
        # Calculate overall compression statistics
        overall_compression = (1 - total_compressed_size / total_original_size) * 100 if total_original_size > 0 else 0
        
        logging.info(f"🧹 Cleanup complete: {archived_count} archived, {error_count} moved to error")
        if additional_files_processed > 0:
            logging.info(f"   📁 Additional files processed: {additional_files_processed}")
        logging.info(f"🗜️ Compression summary:")
        logging.info(f"   Original size: {total_original_size:,} bytes")
        logging.info(f"   Compressed size: {total_compressed_size:,} bytes")
        logging.info(f"   Overall compression: {overall_compression:.1f}% reduction")
        
        # Final summary
        logging.info("📋 BCCI Import Complete - Final Summary:")
        logging.info(f"  Files processed: {len(downloaded_files) + additional_files_processed}")
        logging.info(f"  Files archived (compressed): {archived_count}")
        logging.info(f"  Files in error (compressed): {error_count}")
        logging.info(f"  Space saved: {total_original_size - total_compressed_size:,} bytes")
        logging.info(f"  Import status: {'✅ SUCCESS' if verification else '❌ FAILED'}")
        
        return {
            'files_processed': len(downloaded_files) + additional_files_processed,
            'files_archived': archived_count,
            'files_error': error_count,
            'import_success': verification,
            'original_size_bytes': total_original_size,
            'compressed_size_bytes': total_compressed_size,
            'compression_ratio_percent': overall_compression
        }
            
    except Exception as e:
        logging.error(f"❌ Cleanup error: {e}")
        logging.warning("⚠️ Continuing despite cleanup errors")

# Create the DAG
dag = DAG(
    'metering_bcci',
    default_args=default_args,
    description='BCCI (BlueCurrent Commercial & Industrial) Metering Data Pipeline with Clear Debugging Steps',
    schedule_interval='0 6 * * *',  # 6 AM daily
    max_active_runs=1,
    catchup=False,  # Explicitly disable catchup to prevent backfill
    tags=['metering', 'bcci', 'bluecurrent-ci', 'commercial', 'industrial', 'daily', 'debug']
)

# Define tasks with clear dependencies
task_1_connection = PythonOperator(
    task_id='01_test_connection',
    python_callable=test_bcci_connection,
    dag=dag
)

task_2_discover = PythonOperator(
    task_id='02_discover_files',
    python_callable=discover_bcci_files,
    dag=dag
)

task_3_download = PythonOperator(
    task_id='03_download_files',
    python_callable=download_bcci_files,
    dag=dag
)

task_4_import_eiep3 = PythonOperator(
    task_id='04_import_eiep3',
    python_callable=import_bcci_eiep3,
    dag=dag
)

task_5_load_eiep3_db = PythonOperator(
    task_id='05_load_eiep3_database',
    python_callable=load_bcci_eiep3_to_db,
    dag=dag
)

task_6_verify_db = PythonOperator(
    task_id='06_verify_database',
    python_callable=verify_bcci_database_load,
    dag=dag
)

task_7_cleanup = PythonOperator(
    task_id='07_cleanup_archive',
    python_callable=cleanup_bcci_files,
    dag=dag
)

# Set task dependencies - clear linear flow for debugging
task_1_connection >> task_2_discover >> task_3_download
task_3_download >> task_4_import_eiep3
task_4_import_eiep3 >> task_5_load_eiep3_db
task_5_load_eiep3_db >> task_6_verify_db >> task_7_cleanup 
task_5_load_eiep3_db >> task_6_verify_db >> task_7_cleanup 