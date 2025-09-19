"""
NZX GR Reports Import DAG

Downloads ALL GR report files from NZX SFTP /nzx/*.gz folder and imports them RAW into database tables.
Follows the same philosophy as switching_files.py:
- Download all GR report files (not selective)
- Extract and parse gz files containing multiple report types
- Import raw into database tables with proper schema
- Simple file-based duplicate detection
- Comprehensive logging

Supported GR Report Types:
- GR-170: Purchaser's Submission Accuracy (HHR/NHH)
- GR-130: Report Electricity Supplied or Submitted Comparison
- GR-100: ICP Days Comparison
- GR-150: ICP Days Comparison Summary
- GR-090: Missing HHR ICPs
- GR-140: Missing HHR ICPs Summary

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
import zipfile
import tempfile
import shutil

# Add utils to path
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/nzx/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))

# Default arguments
default_args = {
    'owner': 'nzx_import',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 25),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=45),  # Longer timeout for gz extraction
    'catchup': False
}

# Data processing directories - Create nested structure by report type
DATA_DIR = Path('/data/imports/electricity/nzx/gr_reports')

def ensure_directories():
    """Ensure processing directories exist with proper nested structure by GR report type"""
    # Create nested directories by GR report type first, then by status
    gr_types = ['GR-170', 'GR-130', 'GR-100', 'GR-150', 'GR-090', 'GR-140', 'MULTI-GR']
    status_dirs = ['imported', 'archive', 'error', 'extracted']
    
    for gr_type in gr_types:
        for status_dir in status_dirs:
            (DATA_DIR / gr_type / status_dir).mkdir(parents=True, exist_ok=True)
    
    logging.info("✅ Created nested directory structure: {GR_TYPE}/{STATUS} format (including MULTI-GR)")

def get_timescale_connection():
    """Get TimescaleDB connection"""
# Import connection utility
import sys
sys.path.append('/app/airflow/utils')
from connection import get_connection

def get_timescale_connection():
    """DEPRECATED: Use get_connection() instead."""
    return get_connection()

def test_nzx_connection(**context):
    """Step 1: Test NZX SFTP connection for GR reports"""
    logging.info("🔍 Step 1: Testing NZX SFTP Connection for GR Reports")
    
    try:
        from connection_manager import ConnectionManager
        
        conn_config = {
            'protocol': os.getenv('NZX_PROTOCOL', 'SFTP'),
            'host': os.getenv('NZX_HOST'),
            'port': int(os.getenv('NZX_PORT', 22)),
            'user': os.getenv('NZX_USER'),
            'password': os.getenv('NZX_PASS'),
            'key_path': os.getenv('NZX_PRIVATE_KEY_PATH'),
            'key_passphrase': os.getenv('NZX_PRIVATE_KEY_PASSPHRASE'),
            'remote_path': '/nzx/',
            'timeout': 30
        }
        
        logging.info(f"Testing connection to {conn_config['host']}:{conn_config['port']}")
        
        if ConnectionManager.test_connection(conn_config):
            logging.info("✅ NZX connection successful")
            context['ti'].xcom_push(key='connection_status', value='success')
            context['ti'].xcom_push(key='conn_config', value=conn_config)
            return True
        else:
            logging.error("❌ NZX connection failed")
            context['ti'].xcom_push(key='connection_status', value='failed')
            raise Exception("NZX connection test failed")
            
    except Exception as e:
        logging.error(f"❌ Connection test error: {e}")
        raise

def discover_gr_files(**context):
    """Step 2: Discover ALL GR report gz files"""
    logging.info("📁 Step 2: Discovering ALL GR Report Files")
    
    conn_config = context['ti'].xcom_pull(key='conn_config')
    if not conn_config:
        logging.info("ℹ️ No connection data from previous task, creating new connection config")
        conn_config = {
            'protocol': os.getenv('NZX_PROTOCOL', 'SFTP'),
            'host': os.getenv('NZX_HOST'),
            'port': int(os.getenv('NZX_PORT', 22)),
            'user': os.getenv('NZX_USER'),
            'password': os.getenv('NZX_PASS'),
            'key_path': os.getenv('NZX_PRIVATE_KEY_PATH'),
            'key_passphrase': os.getenv('NZX_PRIVATE_KEY_PASSPHRASE'),
            'remote_path': '/nzx/',
            'timeout': 30
        }
    
    try:
        from connection_manager import ConnectionManager
        
        # Get ALL .zip and .gz files from /nzx/ directory
        logging.info("🔍 Scanning for ALL .zip and .gz files...")
        all_files = ConnectionManager.list_remote_files(conn_config, r'.*\.(zip|gz)$')
        
        # Filter for GR report files
        gr_files = []
        for filename in all_files:
            file_type = classify_gr_file_type(filename)
            if file_type.startswith('GR-') or file_type == 'MULTI-GR-REPORTS':
                gr_files.append({
                    'filename': filename,
                    'file_type': file_type,
                    'size': 0  # Size will be determined during download
                })
        
        logging.info(f"📊 Found {len(gr_files)} GR report files out of {len(all_files)} total .zip/.gz files:")
        
        # Group by file type for summary
        type_counts = {}
        for file_info in gr_files:
            file_type = file_info['file_type']
            if file_type not in type_counts:
                type_counts[file_type] = []
            type_counts[file_type].append(file_info['filename'])
        
        for file_type, files in type_counts.items():
            logging.info(f"  📄 {file_type}: {len(files)} files")
            for filename in files:
                logging.info(f"    - {filename}")
        
        context['ti'].xcom_push(key='discovered_files', value=gr_files)
        context['ti'].xcom_push(key='conn_config', value=conn_config)
        context['ti'].xcom_push(key='total_files', value=len(gr_files))
        
        return gr_files
        
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def classify_gr_file_type(filename: str) -> str:
    """Classify GR report file type based on filename patterns"""
    filename_upper = filename.upper()
    
    # Only classify files that end with .gz, .GZ, .zip, or .ZIP
    if not (filename_upper.endswith('.GZ') or filename_upper.endswith('.gz') or 
            filename_upper.endswith('.ZIP') or filename_upper.endswith('.zip')):
        return 'OTHER'
    
    # For ZIP files, they contain multiple GR reports - classify as MULTI-GR
    if filename_upper.endswith('.ZIP') or filename_upper.endswith('.zip'):
        # Check if it's an NZX comprehensive report (contains multiple GR types)
        if 'COMPRSD' in filename_upper or any(pattern in filename_upper for pattern in 
                                            ['ACCYNHH', 'ACCYHHR', 'ESUPSUB', 'ICPCOMP', 'ICPCSUM', 'ICPMISS', 'ICPMSUM']):
            return 'MULTI-GR-REPORTS'
        else:
            return 'OTHER'
    
    # Individual GZ files - classify by specific type
    # GR-170: Purchaser's Submission Accuracy
    if 'ACCYNHH' in filename_upper or 'ACCYHHR' in filename_upper:
        return 'GR-170-SUBMISSION-ACCURACY'
    # GR-130: Electricity Supplied or Submitted Comparison
    elif 'ESUPSUB' in filename_upper:
        return 'GR-130-SUPPLY-SUBMISSION'
    # GR-100: ICP Days Comparison
    elif 'ICPCOMP' in filename_upper:
        return 'GR-100-ICP-DAYS'
    # GR-150: ICP Days Comparison Summary
    elif 'ICPCSUM' in filename_upper:
        return 'GR-150-ICP-DAYS-SUMMARY'
    # GR-090: Missing HHR ICPs
    elif 'ICPMISS' in filename_upper:
        return 'GR-090-MISSING-ICPS'
    # GR-140: Missing HHR ICPs Summary
    elif 'ICPMSUM' in filename_upper:
        return 'GR-140-MISSING-ICPS-SUMMARY'
    else:
        return 'OTHER'  # Not a recognized GR report

def download_gr_files(**context):
    """Step 3: Download ALL GR report files with duplicate checking"""
    logging.info("⬇️ Step 3: Downloading ALL GR Report Files")
    
    discovered_files = context['ti'].xcom_pull(key='discovered_files')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    if not discovered_files:
        logging.info("ℹ️ No GR report files discovered")
        return []
    
    if not conn_config:
        logging.info("ℹ️ No connection config, creating new one")
        conn_config = {
            'protocol': os.getenv('NZX_PROTOCOL', 'SFTP'),
            'host': os.getenv('NZX_HOST'),
            'port': int(os.getenv('NZX_PORT', 22)),
            'user': os.getenv('NZX_USER'),
            'password': os.getenv('NZX_PASS'),
            'key_path': os.getenv('NZX_PRIVATE_KEY_PATH'),
            'key_passphrase': os.getenv('NZX_PRIVATE_KEY_PASSPHRASE'),
            'remote_path': '/nzx/',
            'timeout': 30
        }
    
    try:
        from connection_manager import ConnectionManager
        
        # Ensure directories exist
        ensure_directories()
        
        # Create GR tables before checking import log
        conn = get_timescale_connection()
        cur = conn.cursor()
        create_gr_tables(cur)
        conn.commit()
        
        # Get already processed files from import_log
        cur.execute("""
            SELECT file_name, file_hash 
            FROM nzx_gr.import_log 
            WHERE status = 'completed'
        """)
        processed_files = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
        conn.close()
        
        downloaded_files = []
        skipped_files = []
        
        for file_info in discovered_files:
            filename = file_info['filename']
            file_type = file_info['file_type']
            
            # Extract GR type prefix for folder organization
            gr_type_prefix = get_gr_type_prefix(file_type)
            
            if not gr_type_prefix:
                logging.warning(f"⚠️ Unknown GR type for {filename}, skipping")
                continue
            
            # Create nested path based on GR type: {GR_TYPE}/{STATUS}
            local_file_path = DATA_DIR / gr_type_prefix / 'imported' / filename
            
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
                        # Move to archive: {GR_TYPE}/archive/
                        archive_path = DATA_DIR / gr_type_prefix / 'archive' / filename
                        archive_path.parent.mkdir(parents=True, exist_ok=True)
                        local_file_path.rename(archive_path)
                        continue
                    
                    downloaded_files.append({
                        'filename': filename,
                        'file_type': file_type,
                        'gr_type_prefix': gr_type_prefix,
                        'local_path': str(local_file_path),
                        'file_size': file_size,
                        'file_hash': file_hash
                    })
                    
                    logging.info(f"✅ Downloaded: {filename} -> {gr_type_prefix}/ ({file_size} bytes)")
                else:
                    logging.error(f"❌ Failed to download: {filename}")
                    
            except Exception as e:
                logging.error(f"❌ Error downloading {filename}: {e}")
                # Move to error folder if it exists: {GR_TYPE}/error/
                if local_file_path.exists():
                    error_path = DATA_DIR / gr_type_prefix / 'error' / filename
                    error_path.parent.mkdir(parents=True, exist_ok=True)
                    local_file_path.rename(error_path)
        
        logging.info(f"📊 Download Summary:")
        logging.info(f"  ✅ Downloaded: {len(downloaded_files)} files")
        logging.info(f"  ⏭️ Skipped: {len(skipped_files)} files")
        
        # Group by GR type for summary
        type_counts = {}
        for file_info in downloaded_files:
            gr_type_prefix = file_info['gr_type_prefix']
            if gr_type_prefix not in type_counts:
                type_counts[gr_type_prefix] = []
            type_counts[gr_type_prefix].append(file_info['filename'])
        
        for gr_type_prefix, files in type_counts.items():
            logging.info(f"  📁 {gr_type_prefix}/: {len(files)} files")
        
        context['ti'].xcom_push(key='downloaded_files', value=downloaded_files)
        context['ti'].xcom_push(key='skipped_files', value=skipped_files)
        context['ti'].xcom_push(key='total_downloaded', value=len(downloaded_files))
        
        return downloaded_files
        
    except Exception as e:
        logging.error(f"❌ Download error: {e}")
        raise

def get_gr_type_prefix(file_type: str) -> str:
    """Extract GR type prefix for folder organization"""
    if file_type == 'MULTI-GR-REPORTS':
        return 'MULTI-GR'
    elif file_type.startswith('GR-'):
        # Extract the GR type code (GR-170, GR-130, etc.)
        parts = file_type.split('-')
        if len(parts) >= 2:
            return f"GR-{parts[1]}"  # GR-170, GR-130, etc.
    return None 

def extract_and_import_gr_files(**context):
    """Step 4: Extract gz files and import ALL GR reports with comprehensive parsing"""
    logging.info("📦 Step 4: Extracting and Importing ALL GR Report Files")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No GR report files to extract and import")
        return {'imported_files': 0, 'total_records': 0}

    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Create the schema and all tables
                create_gr_tables(cur)
                
                imported_count = 0
                total_records = 0
                
                for i, file_info in enumerate(downloaded_files, 1):
                    filename = file_info['filename']
                    file_path = Path(file_info['local_path'])
                    file_size = file_info['file_size']
                    file_type = file_info['file_type']
                    gr_type_prefix = file_info['gr_type_prefix']
                    
                    logging.info(f"📦 Processing file {i}/{len(downloaded_files)}: {filename} ({file_type})")
                    
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
                            """SELECT COUNT(*) FROM nzx_gr.import_log 
                               WHERE file_name = %s AND file_hash = %s AND status = 'completed'""",
                            (filename, file_hash)
                        )
                        
                        if cur.fetchone()[0] > 0:
                            logging.info(f"🔄 Skipping {filename} - already imported")
                            continue
                        
                        # Extract zip/gz file and parse contents
                        logging.info(f"📦 Extracting file: {filename}")
                        extracted_files = extract_archive_file(file_path, gr_type_prefix)
                        logging.info(f"✅ Extracted {len(extracted_files)} files from {filename}")
                        
                        file_records = 0
                        for extracted_file in extracted_files:
                            # Parse extracted file based on GR type
                            logging.info(f"📖 Parsing extracted file: {extracted_file['filename']}")
                            parsed_records = parse_gr_file(extracted_file, file_type, filename)
                            logging.info(f"✅ Parsed {len(parsed_records)} records from {extracted_file['filename']}")
                            
                            if parsed_records:
                                # Import parsed records into specific tables
                                logging.info(f"💾 Importing {len(parsed_records)} records for {extracted_file['filename']}")
                                
                                # For MULTI-GR files, determine the specific type from extracted filename
                                if file_type == 'MULTI-GR-REPORTS':
                                    extracted_filename = extracted_file['filename'].upper()
                                    if 'ACCYNHH' in extracted_filename or 'ACCYHHR' in extracted_filename:
                                        specific_type = 'GR-170-SUBMISSION-ACCURACY'
                                    elif 'ESUPSUB' in extracted_filename:
                                        specific_type = 'GR-130-SUPPLY-SUBMISSION'
                                    elif 'ICPCOMP' in extracted_filename:
                                        specific_type = 'GR-100-ICP-DAYS'
                                    elif 'ICPCSUM' in extracted_filename:
                                        specific_type = 'GR-150-ICP-DAYS-SUMMARY'
                                    elif 'ICPMISS' in extracted_filename:
                                        specific_type = 'GR-090-MISSING-ICPS'
                                    elif 'ICPMSUM' in extracted_filename:
                                        specific_type = 'GR-140-MISSING-ICPS-SUMMARY'
                                    else:
                                        specific_type = file_type
                                else:
                                    specific_type = file_type
                                
                                loaded_records = import_parsed_gr_records(cur, specific_type, extracted_file['filename'], parsed_records, file_hash)
                                logging.info(f"✅ Imported {loaded_records} records")
                                
                                # Log successful import for each extracted file
                                try:
                                    log_import_with_cursor(
                                        cur, dag_id, task_id, run_id, 'NZX_GR',
                                        extracted_file['filename'], specific_type,
                                        extracted_file['size'], file_hash, 'completed',
                                        len(parsed_records), loaded_records
                                    )
                                    logging.info(f"📝 Logged successful import of {extracted_file['filename']}")
                                except Exception as log_error:
                                    logging.warning(f"⚠️ Failed to log import for {extracted_file['filename']}: {log_error}")
                                
                                logging.info(f"✅ Completed processing {extracted_file['filename']}: {loaded_records} records imported")
                                
                                file_records += len(parsed_records)
                            else:
                                # Log empty files too
                                specific_type = file_type
                                if file_type == 'MULTI-GR-REPORTS':
                                    extracted_filename = extracted_file['filename'].upper()
                                    if 'ACCYNHH' in extracted_filename or 'ACCYHHR' in extracted_filename:
                                        specific_type = 'GR-170-SUBMISSION-ACCURACY'
                                    elif 'ESUPSUB' in extracted_filename:
                                        specific_type = 'GR-130-SUPPLY-SUBMISSION'
                                    elif 'ICPCOMP' in extracted_filename:
                                        specific_type = 'GR-100-ICP-DAYS'
                                    elif 'ICPCSUM' in extracted_filename:
                                        specific_type = 'GR-150-ICP-DAYS-SUMMARY'
                                    elif 'ICPMISS' in extracted_filename:
                                        specific_type = 'GR-090-MISSING-ICPS'
                                    elif 'ICPMSUM' in extracted_filename:
                                        specific_type = 'GR-140-MISSING-ICPS-SUMMARY'
                                
                                # Log empty file import
                                try:
                                    log_import_with_cursor(
                                        cur, dag_id, task_id, run_id, 'NZX_GR',
                                        extracted_file['filename'], specific_type,
                                        extracted_file['size'], file_hash, 'completed',
                                        0, 0
                                    )
                                    logging.info(f"📝 Logged empty file import: {extracted_file['filename']}")
                                except Exception as log_error:
                                    logging.warning(f"⚠️ Failed to log empty file for {extracted_file['filename']}: {log_error}")
                                
                                logging.info(f"✅ Completed processing empty file: {extracted_file['filename']}")
                        
                        if file_records > 0:
                            imported_count += 1
                            total_records += file_records
                            
                            # Commit after each archive file to prevent long transactions
                            conn.commit()
                            logging.info(f"💾 Committed changes for {filename}")
                            
                            # Verify the commit worked by checking record count
                            cur.execute("SELECT COUNT(*) FROM nzx_gr.gr_170_hhr_submission_accuracy")
                            hhr_count = cur.fetchone()[0]
                            cur.execute("SELECT COUNT(*) FROM nzx_gr.gr_170_nhh_submission_accuracy")
                            nhh_count = cur.fetchone()[0]
                            logging.info(f"📊 Database verification: HHR={hhr_count}, NHH={nhh_count} records")
                            
                            logging.info(f"✅ Completed processing {filename}: {file_records} records from {len(extracted_files)} extracted files")
                        else:
                            logging.warning(f"⚠️ No records found in {filename}")
                        
                    except Exception as file_error:
                        logging.error(f"❌ Failed to process {filename}: {file_error}")
                        import traceback
                        logging.error(f"📋 Error details: {traceback.format_exc()}")
                        
                        # Log failed import and continue with next file
                        try:
                            log_import_with_cursor(
                                cur, dag_id, task_id, run_id, 'NZX_GR',
                                filename, file_type, file_size,
                                file_hash if 'file_hash' in locals() else '',
                                'failed', 0, 0, str(file_error)
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
                    source_group='NZX_GR',
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

def extract_archive_file(archive_file_path: Path, gr_type_prefix: str):
    """Extract ZIP or GZ file and return list of extracted files"""
    extracted_files = []
    extraction_dir = DATA_DIR / gr_type_prefix / 'extracted'
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if archive_file_path.suffix.lower() == '.zip':
            # Handle ZIP files
            import zipfile
            with zipfile.ZipFile(archive_file_path, 'r') as zip_ref:
                zip_contents = zip_ref.namelist()
                logging.info(f"📦 ZIP contains {len(zip_contents)} files")
                
                # Extract only GR report CSV files
                gr_patterns = ['ACCYNHH', 'ACCYHHR', 'ESUPSUB', 'ICPCOMP', 'ICPCSUM', 'ICPMISS', 'ICPMSUM']
                
                for file_in_zip in zip_contents:
                    file_upper = file_in_zip.upper()
                    
                    # Check if it's a GR report file
                    if any(pattern in file_upper for pattern in gr_patterns):
                        # Extract to extraction directory
                        extracted_path = extraction_dir / file_in_zip
                        with zip_ref.open(file_in_zip) as source, open(extracted_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        
                        extracted_files.append({
                            'filename': file_in_zip,
                            'local_path': str(extracted_path),
                            'size': extracted_path.stat().st_size
                        })
                        
                        logging.info(f"📦 Extracted GR file: {file_in_zip} ({extracted_path.stat().st_size:,} bytes)")
                
        elif archive_file_path.suffix.lower() == '.gz':
            # Handle GZ files (original logic)
            with gzip.open(archive_file_path, 'rb') as gz_file:
                temp_file = extraction_dir / f"{archive_file_path.stem}_extracted.txt"
                with open(temp_file, 'wb') as out_file:
                    shutil.copyfileobj(gz_file, out_file)
                
                extracted_files.append({
                    'filename': temp_file.name,
                    'local_path': str(temp_file),
                    'size': temp_file.stat().st_size
                })
                
                logging.info(f"📦 Extracted {archive_file_path.name} to {temp_file.name}")
        else:
            raise ValueError(f"Unsupported file type: {archive_file_path.suffix}")
            
    except Exception as e:
        logging.error(f"❌ Failed to extract {archive_file_path}: {e}")
        raise
    
    return extracted_files

def create_gr_tables(cur):
    """Create GR report tables based on specifications"""
    
    # Create schema
    cur.execute("CREATE SCHEMA IF NOT EXISTS nzx_gr;")
    
    # GR-170 HHR: Purchaser's Submission Accuracy (Half-Hourly Reading)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_170_hhr_submission_accuracy (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-170 HHR specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14
            balancing_area VARCHAR(12),
            poc VARCHAR(7),
            network_id VARCHAR(4),
            participant_code VARCHAR(4),
            metering_type VARCHAR(3) DEFAULT 'HHR',  -- Always HHR for this table
            total_monthly_submission_volume DECIMAL(14,2),
            total_monthly_historical_volume DECIMAL(14,2),
            pct_historical_estimate_in_revision DECIMAL(10,2),
            pct_variation_submission_vs_initial DECIMAL(10,2),
            pct_variation_historical_vs_initial DECIMAL(10,2),
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # GR-170 NHH: Purchaser's Submission Accuracy (Non-Half-Hourly)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_170_nhh_submission_accuracy (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-170 NHH specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14
            balancing_area VARCHAR(12),
            poc VARCHAR(7),
            network_id VARCHAR(4),
            participant_code VARCHAR(4),
            metering_type VARCHAR(3) DEFAULT 'NHH',  -- Always NHH for this table
            total_monthly_submission_volume DECIMAL(14,2),
            total_monthly_historical_volume DECIMAL(14,2),
            pct_historical_estimate_in_revision DECIMAL(10,2),
            pct_variation_submission_vs_initial DECIMAL(10,2),
            pct_variation_historical_vs_initial DECIMAL(10,2),
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # GR-130: Report Electricity Supplied or Submitted Comparison
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_130_supply_submission (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-130 specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14,18,24
            nsp VARCHAR(12),  -- POC Code (7) "-" Network Code (4)
            grid_nsp VARCHAR(12),  -- Grid Level Parent NSP
            balancing_area VARCHAR(12),
            participant_identifier VARCHAR(4),
            total_trader_consumption_submissions DECIMAL(14,2),
            total_trader_sales_electricity_supplied DECIMAL(14,2),
            difference_kwh DECIMAL(14,2),
            sales_submission_ratio DECIMAL(10,4),
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # GR-100: ICP Days Comparison
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_100_icp_days (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-100 specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14
            balancing_area VARCHAR(12),
            poc VARCHAR(7),
            network_id VARCHAR(4),
            participant_code VARCHAR(4),
            metering_type VARCHAR(3),  -- HHR or NHH
            registry_icp_days INTEGER,
            icp_days INTEGER,
            difference_registry_purchaser INTEGER,
            percentage_difference DECIMAL(10,2),
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # GR-150: ICP Days Comparison Summary
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_150_icp_days_summary (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-150 specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14
            participant_code VARCHAR(4),
            metering_type VARCHAR(3),  -- NHH or HHR
            difference_registry_purchaser INTEGER,
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # GR-090: Missing HHR ICPs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_090_missing_icps (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-090 specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14
            balancing_area VARCHAR(12),
            poc VARCHAR(7),
            network_id VARCHAR(4),
            participant_code VARCHAR(4),
            discrepancy_type VARCHAR(1),  -- R or A
            icp_number VARCHAR(15),
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # GR-140: Missing HHR ICPs Summary
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.gr_140_missing_icps_summary (
            id SERIAL PRIMARY KEY,
            -- File metadata
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            
            -- GR-140 specific fields
            consumption_period VARCHAR(7),  -- MM/YYYY
            revision_cycle INTEGER,  -- 0,1,3,7,14
            participant_code VARCHAR(4),
            number_of_discrepancies INTEGER,
            
            -- Metadata
            raw_line TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Import log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nzx_gr.import_log (
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
        # GR-170 HHR indexes
        "CREATE INDEX IF NOT EXISTS idx_gr_170_hhr_file_name ON nzx_gr.gr_170_hhr_submission_accuracy(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_170_hhr_file_hash ON nzx_gr.gr_170_hhr_submission_accuracy(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_170_hhr_consumption_period ON nzx_gr.gr_170_hhr_submission_accuracy(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_170_hhr_participant_code ON nzx_gr.gr_170_hhr_submission_accuracy(participant_code);",
        
        # GR-170 NHH indexes
        "CREATE INDEX IF NOT EXISTS idx_gr_170_nhh_file_name ON nzx_gr.gr_170_nhh_submission_accuracy(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_170_nhh_file_hash ON nzx_gr.gr_170_nhh_submission_accuracy(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_170_nhh_consumption_period ON nzx_gr.gr_170_nhh_submission_accuracy(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_170_nhh_participant_code ON nzx_gr.gr_170_nhh_submission_accuracy(participant_code);",
        
        "CREATE INDEX IF NOT EXISTS idx_gr_130_file_name ON nzx_gr.gr_130_supply_submission(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_130_file_hash ON nzx_gr.gr_130_supply_submission(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_130_consumption_period ON nzx_gr.gr_130_supply_submission(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_130_participant_identifier ON nzx_gr.gr_130_supply_submission(participant_identifier);",
        
        "CREATE INDEX IF NOT EXISTS idx_gr_100_file_name ON nzx_gr.gr_100_icp_days(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_100_file_hash ON nzx_gr.gr_100_icp_days(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_100_consumption_period ON nzx_gr.gr_100_icp_days(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_100_participant_code ON nzx_gr.gr_100_icp_days(participant_code);",
        
        "CREATE INDEX IF NOT EXISTS idx_gr_150_file_name ON nzx_gr.gr_150_icp_days_summary(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_150_file_hash ON nzx_gr.gr_150_icp_days_summary(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_150_consumption_period ON nzx_gr.gr_150_icp_days_summary(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_150_participant_code ON nzx_gr.gr_150_icp_days_summary(participant_code);",
        
        "CREATE INDEX IF NOT EXISTS idx_gr_090_file_name ON nzx_gr.gr_090_missing_icps(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_090_file_hash ON nzx_gr.gr_090_missing_icps(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_090_consumption_period ON nzx_gr.gr_090_missing_icps(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_090_participant_code ON nzx_gr.gr_090_missing_icps(participant_code);",
        "CREATE INDEX IF NOT EXISTS idx_gr_090_icp_number ON nzx_gr.gr_090_missing_icps(icp_number);",
        
        "CREATE INDEX IF NOT EXISTS idx_gr_140_file_name ON nzx_gr.gr_140_missing_icps_summary(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_gr_140_file_hash ON nzx_gr.gr_140_missing_icps_summary(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_gr_140_consumption_period ON nzx_gr.gr_140_missing_icps_summary(consumption_period);",
        "CREATE INDEX IF NOT EXISTS idx_gr_140_participant_code ON nzx_gr.gr_140_missing_icps_summary(participant_code);",
        
        "CREATE INDEX IF NOT EXISTS idx_import_log_file_name ON nzx_gr.import_log(file_name);",
        "CREATE INDEX IF NOT EXISTS idx_import_log_file_hash ON nzx_gr.import_log(file_hash);",
        "CREATE INDEX IF NOT EXISTS idx_import_log_status ON nzx_gr.import_log(status);"
    ]
    
    for cmd in index_commands:
        cur.execute(cmd)
    
    logging.info("✅ All GR report tables created successfully with proper schema") 

def parse_gr_file(extracted_file, file_type, original_filename):
    """Parse GR report file based on type and return structured records"""
    try:
        with open(extracted_file['local_path'], 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    
        # For MULTI-GR-REPORTS (ZIP files), determine type from extracted filename
        if file_type == 'MULTI-GR-REPORTS':
            extracted_filename = extracted_file['filename'].upper()
            if 'ACCYHHR' in extracted_filename:
                return parse_gr_170_hhr(lines, extracted_file['filename'])
            elif 'ACCYNHH' in extracted_filename:
                return parse_gr_170_nhh(lines, extracted_file['filename'])
            elif 'ESUPSUB' in extracted_filename:
                return parse_gr_130(lines, extracted_file['filename'])
            elif 'ICPCOMP' in extracted_filename:
                return parse_gr_100(lines, extracted_file['filename'])
            elif 'ICPCSUM' in extracted_filename:
                return parse_gr_150(lines, extracted_file['filename'])
            elif 'ICPMISS' in extracted_filename:
                return parse_gr_090(lines, extracted_file['filename'])
            elif 'ICPMSUM' in extracted_filename:
                return parse_gr_140(lines, extracted_file['filename'])
            else:
                logging.warning(f"Unknown GR file type in ZIP: {extracted_file['filename']}")
                return parse_generic_gr_file(lines, extracted_file['filename'])
        
        # Handle individual GZ files
        elif file_type == 'GR-170-SUBMISSION-ACCURACY':
            return parse_gr_170(lines, original_filename)
        elif file_type == 'GR-130-SUPPLY-SUBMISSION':
            return parse_gr_130(lines, original_filename)
        elif file_type == 'GR-100-ICP-DAYS':
            return parse_gr_100(lines, original_filename)
        elif file_type == 'GR-150-ICP-DAYS-SUMMARY':
            return parse_gr_150(lines, original_filename)
        elif file_type == 'GR-090-MISSING-ICPS':
            return parse_gr_090(lines, original_filename)
        elif file_type == 'GR-140-MISSING-ICPS-SUMMARY':
            return parse_gr_140(lines, original_filename)
        else:
            # Generic parsing for unknown GR report types
            return parse_generic_gr_file(lines, original_filename)
            
    except Exception as e:
        logging.error(f"Error parsing {original_filename}: {e}")
        return []

def parse_gr_170_hhr(lines, filename):
    """Parse GR-170 HHR (Half-Hourly Reading) Purchaser's Submission Accuracy files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 11:  # Minimum expected fields for GR-170
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'balancing_area': fields[2] if len(fields) > 2 else '',
                'poc': fields[3] if len(fields) > 3 else '',
                'network_id': fields[4] if len(fields) > 4 else '',
                'participant_code': fields[5] if len(fields) > 5 else '',
                'metering_type': 'HHR',  # Always HHR for this parser
                'total_monthly_submission_volume': parse_decimal(fields[7]) if len(fields) > 7 else None,
                'total_monthly_historical_volume': parse_decimal(fields[8]) if len(fields) > 8 else None,
                'pct_historical_estimate_in_revision': parse_decimal(fields[9]) if len(fields) > 9 else None,
                'pct_variation_submission_vs_initial': parse_decimal(fields[10]) if len(fields) > 10 else None,
                'pct_variation_historical_vs_initial': parse_decimal(fields[11]) if len(fields) > 11 else None,
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_gr_170_nhh(lines, filename):
    """Parse GR-170 NHH (Non-Half-Hourly) Purchaser's Submission Accuracy files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 11:  # Minimum expected fields for GR-170
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'balancing_area': fields[2] if len(fields) > 2 else '',
                'poc': fields[3] if len(fields) > 3 else '',
                'network_id': fields[4] if len(fields) > 4 else '',
                'participant_code': fields[5] if len(fields) > 5 else '',
                'metering_type': 'NHH',  # Always NHH for this parser
                'total_monthly_submission_volume': parse_decimal(fields[7]) if len(fields) > 7 else None,
                'total_monthly_historical_volume': parse_decimal(fields[8]) if len(fields) > 8 else None,
                'pct_historical_estimate_in_revision': parse_decimal(fields[9]) if len(fields) > 9 else None,
                'pct_variation_submission_vs_initial': parse_decimal(fields[10]) if len(fields) > 10 else None,
                'pct_variation_historical_vs_initial': parse_decimal(fields[11]) if len(fields) > 11 else None,
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_gr_130(lines, filename):
    """Parse GR-130 Electricity Supplied or Submitted Comparison files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 9:  # Minimum expected fields for GR-130
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'nsp': fields[2] if len(fields) > 2 else '',
                'grid_nsp': fields[3] if len(fields) > 3 else '',
                'balancing_area': fields[4] if len(fields) > 4 else '',
                'participant_identifier': fields[5] if len(fields) > 5 else '',
                'total_trader_consumption_submissions': parse_decimal(fields[6]) if len(fields) > 6 else None,
                'total_trader_sales_electricity_supplied': parse_decimal(fields[7]) if len(fields) > 7 else None,
                'difference_kwh': parse_decimal(fields[8]) if len(fields) > 8 else None,
                'sales_submission_ratio': parse_decimal(fields[9]) if len(fields) > 9 else None,
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_gr_100(lines, filename):
    """Parse GR-100 ICP Days Comparison files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 10:  # Minimum expected fields for GR-100
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'balancing_area': fields[2] if len(fields) > 2 else '',
                'poc': fields[3] if len(fields) > 3 else '',
                'network_id': fields[4] if len(fields) > 4 else '',
                'participant_code': fields[5] if len(fields) > 5 else '',
                'metering_type': fields[6] if len(fields) > 6 else '',
                'registry_icp_days': parse_int(fields[7]) if len(fields) > 7 else None,
                'icp_days': parse_int(fields[8]) if len(fields) > 8 else None,
                'difference_registry_purchaser': parse_int(fields[9]) if len(fields) > 9 else None,
                'percentage_difference': parse_decimal(fields[10]) if len(fields) > 10 else None,
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_gr_150(lines, filename):
    """Parse GR-150 ICP Days Comparison Summary files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 5:  # Minimum expected fields for GR-150
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'participant_code': fields[2] if len(fields) > 2 else '',
                'metering_type': fields[3] if len(fields) > 3 else '',
                'difference_registry_purchaser': parse_int(fields[4]) if len(fields) > 4 else None,
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_gr_090(lines, filename):
    """Parse GR-090 Missing HHR ICPs files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 8:  # Minimum expected fields for GR-090
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'balancing_area': fields[2] if len(fields) > 2 else '',
                'poc': fields[3] if len(fields) > 3 else '',
                'network_id': fields[4] if len(fields) > 4 else '',
                'participant_code': fields[5] if len(fields) > 5 else '',
                'discrepancy_type': fields[6] if len(fields) > 6 else '',
                'icp_number': fields[7] if len(fields) > 7 else '',
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_gr_140(lines, filename):
    """Parse GR-140 Missing HHR ICPs Summary files"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        # Skip header line if present
        if line_num == 1 and (line.startswith('HDR,') or 'consumption' in line.lower() or 'period' in line.lower()):
            continue
        
        if len(fields) >= 4:  # Minimum expected fields for GR-140
            record = {
                'line_number': line_num,
                'consumption_period': fields[0] if len(fields) > 0 else '',
                'revision_cycle': parse_int(fields[1]) if len(fields) > 1 else None,
                'participant_code': fields[2] if len(fields) > 2 else '',
                'number_of_discrepancies': parse_int(fields[3]) if len(fields) > 3 else None,
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_generic_gr_file(lines, filename):
    """Generic parser for unknown GR report types"""
    records = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        record = {
            'line_number': line_num,
            'data_fields': fields,
            'raw_line': line
        }
        records.append(record)
    
    return records

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

def execute_batched_insert(cur, insert_sql, values, batch_size=1000):
    """Execute insert with batching to reduce memory pressure"""
    total_inserted = 0
    
    for i in range(0, len(values), batch_size):
        batch = values[i:i + batch_size]
        execute_values(cur, insert_sql, batch)
        total_inserted += len(batch)
        
        # Log progress for large imports
        if len(values) > batch_size:
            logging.info(f"   📊 Imported batch {i//batch_size + 1}: {total_inserted}/{len(values)} records")
    
    return total_inserted

def import_parsed_gr_records(cur, file_type, filename, records, file_hash):
    """Import parsed records into appropriate GR tables"""
    # Determine specific file type from filename for MULTI-GR-REPORTS
    if file_type == 'MULTI-GR-REPORTS':
        filename_upper = filename.upper()
        if 'ACCYHHR' in filename_upper:
            return import_gr_170_hhr_records(cur, filename, records, file_hash)
        elif 'ACCYNHH' in filename_upper:
            return import_gr_170_nhh_records(cur, filename, records, file_hash)
        elif 'ESUPSUB' in filename_upper:
            return import_gr_130_records(cur, filename, records, file_hash)
        elif 'ICPCOMP' in filename_upper:
            return import_gr_100_records(cur, filename, records, file_hash)
        elif 'ICPCSUM' in filename_upper:
            return import_gr_150_records(cur, filename, records, file_hash)
        elif 'ICPMISS' in filename_upper:
            return import_gr_090_records(cur, filename, records, file_hash)
        elif 'ICPMSUM' in filename_upper:
            return import_gr_140_records(cur, filename, records, file_hash)
        else:
            logging.warning(f"Unknown GR file in ZIP: {filename}")
            return 0
    # Handle individual GZ files
    elif file_type == 'GR-170-SUBMISSION-ACCURACY':
        # For individual files, check filename to determine HHR vs NHH
        filename_upper = filename.upper()
        if 'HHR' in filename_upper:
            return import_gr_170_hhr_records(cur, filename, records, file_hash)
        elif 'NHH' in filename_upper:
            return import_gr_170_nhh_records(cur, filename, records, file_hash)
        else:
            # Default to HHR if unclear
            logging.warning(f"Unclear GR-170 type for {filename}, defaulting to HHR")
            return import_gr_170_hhr_records(cur, filename, records, file_hash)
    elif file_type == 'GR-130-SUPPLY-SUBMISSION':
        return import_gr_130_records(cur, filename, records, file_hash)
    elif file_type == 'GR-100-ICP-DAYS':
        return import_gr_100_records(cur, filename, records, file_hash)
    elif file_type == 'GR-150-ICP-DAYS-SUMMARY':
        return import_gr_150_records(cur, filename, records, file_hash)
    elif file_type == 'GR-090-MISSING-ICPS':
        return import_gr_090_records(cur, filename, records, file_hash)
    elif file_type == 'GR-140-MISSING-ICPS-SUMMARY':
        return import_gr_140_records(cur, filename, records, file_hash)
    else:
        logging.warning(f"Unknown GR report type: {file_type}")
        return 0

def import_gr_170_hhr_records(cur, filename, records, file_hash):
    """Import GR-170 HHR Submission Accuracy records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_170_hhr_submission_accuracy (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            balancing_area, poc, network_id, participant_code, metering_type,
            total_monthly_submission_volume, total_monthly_historical_volume,
            pct_historical_estimate_in_revision, pct_variation_submission_vs_initial,
            pct_variation_historical_vs_initial, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('balancing_area'), record.get('poc'), record.get('network_id'),
            record.get('participant_code'), record.get('metering_type'),
            record.get('total_monthly_submission_volume'), record.get('total_monthly_historical_volume'),
            record.get('pct_historical_estimate_in_revision'), record.get('pct_variation_submission_vs_initial'),
            record.get('pct_variation_historical_vs_initial'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_gr_170_nhh_records(cur, filename, records, file_hash):
    """Import GR-170 NHH Submission Accuracy records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_170_nhh_submission_accuracy (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            balancing_area, poc, network_id, participant_code, metering_type,
            total_monthly_submission_volume, total_monthly_historical_volume,
            pct_historical_estimate_in_revision, pct_variation_submission_vs_initial,
            pct_variation_historical_vs_initial, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('balancing_area'), record.get('poc'), record.get('network_id'),
            record.get('participant_code'), record.get('metering_type'),
            record.get('total_monthly_submission_volume'), record.get('total_monthly_historical_volume'),
            record.get('pct_historical_estimate_in_revision'), record.get('pct_variation_submission_vs_initial'),
            record.get('pct_variation_historical_vs_initial'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_gr_130_records(cur, filename, records, file_hash):
    """Import GR-130 Supply Submission records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_130_supply_submission (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            nsp, grid_nsp, balancing_area, participant_identifier,
            total_trader_consumption_submissions, total_trader_sales_electricity_supplied,
            difference_kwh, sales_submission_ratio, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('nsp'), record.get('grid_nsp'), record.get('balancing_area'),
            record.get('participant_identifier'), record.get('total_trader_consumption_submissions'),
            record.get('total_trader_sales_electricity_supplied'), record.get('difference_kwh'),
            record.get('sales_submission_ratio'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_gr_100_records(cur, filename, records, file_hash):
    """Import GR-100 ICP Days records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_100_icp_days (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            balancing_area, poc, network_id, participant_code, metering_type,
            registry_icp_days, icp_days, difference_registry_purchaser,
            percentage_difference, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('balancing_area'), record.get('poc'), record.get('network_id'),
            record.get('participant_code'), record.get('metering_type'),
            record.get('registry_icp_days'), record.get('icp_days'),
            record.get('difference_registry_purchaser'), record.get('percentage_difference'),
            record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_gr_150_records(cur, filename, records, file_hash):
    """Import GR-150 ICP Days Summary records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_150_icp_days_summary (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            participant_code, metering_type, difference_registry_purchaser, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('participant_code'), record.get('metering_type'),
            record.get('difference_registry_purchaser'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_gr_090_records(cur, filename, records, file_hash):
    """Import GR-090 Missing ICPs records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_090_missing_icps (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            balancing_area, poc, network_id, participant_code, discrepancy_type,
            icp_number, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('balancing_area'), record.get('poc'), record.get('network_id'),
            record.get('participant_code'), record.get('discrepancy_type'),
            record.get('icp_number'), record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def import_gr_140_records(cur, filename, records, file_hash):
    """Import GR-140 Missing ICPs Summary records"""
    if not records:
        return 0
    
    insert_sql = """
        INSERT INTO nzx_gr.gr_140_missing_icps_summary (
            file_name, file_hash, line_number, consumption_period, revision_cycle,
            participant_code, number_of_discrepancies, raw_line
        ) VALUES %s
    """
    
    values = []
    for record in records:
        values.append((
            filename, file_hash, record.get('line_number'),
            record.get('consumption_period'), record.get('revision_cycle'),
            record.get('participant_code'), record.get('number_of_discrepancies'),
            record.get('raw_line')
        ))
    
    execute_values(cur, insert_sql, values)
    return len(values)

def verify_gr_import(**context):
    """Step 5: Verify import with comprehensive audit"""
    logging.info("🔍 Step 5: Verifying GR Import")
    
    try:
        imported_files = context['ti'].xcom_pull(key='imported_files') or 0
        total_records = context['ti'].xcom_pull(key='total_records') or 0
        
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                # Count records across all GR tables
                table_counts = {}
                tables = ['gr_170_hhr_submission_accuracy', 'gr_170_nhh_submission_accuracy', 
                         'gr_130_supply_submission', 'gr_100_icp_days', 
                         'gr_150_icp_days_summary', 'gr_090_missing_icps', 'gr_140_missing_icps_summary']
                
                total_db_records = 0
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM nzx_gr.{table}")
                    count = cur.fetchone()[0]
                    table_counts[table] = count
                    total_db_records += count
                
                # Get file type breakdown from import_log
                cur.execute("""
                    SELECT file_type, COUNT(DISTINCT file_name) as file_count, 
                           SUM(records_loaded) as total_records
                    FROM nzx_gr.import_log 
                    WHERE status = 'completed'
                    GROUP BY file_type 
                    ORDER BY file_count DESC
                """)
                type_breakdown = cur.fetchall()
                
                # Get recent import activity
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM nzx_gr.import_log 
                    WHERE started_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY status
                """)
                recent_imports = cur.fetchall()
        
        logging.info("📊 GR Import Verification:")
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
            logging.info("ℹ️ No new GR report files imported (all were duplicates)")
        
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

def cleanup_gr_files(**context):
    """Step 6: Cleanup and archive processed files with compression"""
    logging.info("🧹 Step 6: Cleanup and Archive GR Report Files")
    
    try:
        downloaded_files = context['ti'].xcom_pull(key='downloaded_files') or []
        verification_success = context['ti'].xcom_pull(key='verification_success', default=False)
        
        if not downloaded_files:
            logging.info("ℹ️ No GR report files to cleanup")
            return {'files_processed': 0}
        
        archived_count = 0
        error_count = 0
        total_original_size = 0
        total_compressed_size = 0
        
        for file_info in downloaded_files:
            source_path = Path(file_info['local_path'])
            gr_type_prefix = file_info['gr_type_prefix']
            
            if not source_path.exists():
                logging.warning(f"⚠️ Source file not found: {source_path}")
                continue
            
            original_size = source_path.stat().st_size
            total_original_size += original_size
            
            # Determine target directory based on verification success
            if verification_success:
                target_dir = DATA_DIR / gr_type_prefix / 'archive'
                archived_count += 1
            else:
                target_dir = DATA_DIR / gr_type_prefix / 'error'
                error_count += 1
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Keep original gz file compressed, just move it
            target_path = target_dir / source_path.name
            
            try:
                # Move file to target location
                source_path.rename(target_path)
                
                compressed_size = target_path.stat().st_size
                total_compressed_size += compressed_size
                
                logging.info(f"📁 Moved {source_path.name} to {gr_type_prefix}/{target_dir.name}/")
                
                # Also cleanup extracted files
                extraction_dir = DATA_DIR / gr_type_prefix / 'extracted'
                if extraction_dir.exists():
                    for extracted_file in extraction_dir.glob('*'):
                        if extracted_file.is_file():
                            extracted_file.unlink()
                            logging.info(f"🗑️ Cleaned up extracted file: {extracted_file.name}")
                
            except Exception as e:
                logging.error(f"❌ Failed to move {source_path.name}: {e}")
        
        overall_compression = (1 - total_compressed_size / total_original_size) * 100 if total_original_size > 0 else 0
        
        logging.info(f"🧹 Cleanup Summary:")
        logging.info(f"  Files archived: {archived_count}")
        logging.info(f"  Files in error: {error_count}")
        logging.info(f"  Total size processed: {total_original_size:,} bytes")
        
        return {
            'files_processed': len(downloaded_files),
            'files_archived': archived_count,
            'files_error': error_count,
            'total_size': total_original_size
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

def log_import_with_cursor(cur, dag_id: str, task_id: str, run_id: str, source_group: str, 
                          file_name: str, file_type: str, file_size: int, file_hash: str, 
                          status: str, records_parsed: int = 0, records_loaded: int = 0, 
                          error_message: str = None):
    """Log import activity to nzx_gr.import_log table using existing cursor"""
    if status == 'completed':
        cur.execute("""
            INSERT INTO nzx_gr.import_log 
            (dag_id, task_id, run_id, source_group, file_name, file_type, 
             file_size, file_hash, status, records_parsed, records_loaded, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (dag_id, task_id, run_id, source_group, file_name, file_type,
              file_size, file_hash, status, records_parsed, records_loaded))
    else:
        cur.execute("""
            INSERT INTO nzx_gr.import_log 
            (dag_id, task_id, run_id, source_group, file_name, file_type, 
             file_size, file_hash, status, records_parsed, records_loaded, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (dag_id, task_id, run_id, source_group, file_name, file_type,
              file_size, file_hash, status, records_parsed, records_loaded, error_message))

def log_import(dag_id: str, task_id: str, run_id: str, source_group: str, 
               file_name: str, file_type: str, file_size: int, file_hash: str, 
               status: str, records_parsed: int = 0, records_loaded: int = 0, 
               error_message: str = None):
    """Log import activity to nzx_gr.import_log table"""
    try:
        with get_timescale_connection() as conn:
            with conn.cursor() as cur:
                log_import_with_cursor(cur, dag_id, task_id, run_id, source_group,
                                     file_name, file_type, file_size, file_hash,
                                     status, records_parsed, records_loaded, error_message)
                conn.commit()
    except Exception as e:
        logging.error(f"Failed to log import: {e}")

# Create DAG
dag = DAG(
    'gr_reports_nzx',
    default_args=default_args,
    description='NZX GR Reports Import DAG - Raw Import Philosophy',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    max_active_runs=1,  # Prevent multiple concurrent runs
    catchup=False,  # Explicitly disable catchup to prevent backfill
    tags=['nzx', 'gr_reports', 'import', 'electricity', 'raw']
)

# Define tasks (simplified workflow following switching philosophy)
test_connection_task = PythonOperator(
    task_id='1_test_nzx_connection',
    python_callable=test_nzx_connection,
    dag=dag
)

discover_files_task = PythonOperator(
    task_id='2_discover_gr_files',
    python_callable=discover_gr_files,
    dag=dag
)

download_files_task = PythonOperator(
    task_id='3_download_gr_files',
    python_callable=download_gr_files,
    dag=dag
)

extract_import_task = PythonOperator(
    task_id='4_extract_and_import_gr_files',
    python_callable=extract_and_import_gr_files,
    dag=dag
)

verify_import_task = PythonOperator(
    task_id='5_verify_gr_import',
    python_callable=verify_gr_import,
    dag=dag
)

cleanup_files_task = PythonOperator(
    task_id='6_cleanup_gr_files',
    python_callable=cleanup_gr_files,
    dag=dag
)

# Set task dependencies (linear workflow like switching)
test_connection_task >> discover_files_task >> download_files_task >> extract_import_task >> verify_import_task >> cleanup_files_task 