"""
Registry Information Files Import DAG

Downloads ALL files from SFTP /fromreg/ folder and imports them RAW into database tables.
Follows the same philosophy as metering_bcmm.py:
- Download all files (not selective)
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
import zipfile
import csv
import json
from typing import Dict, List, Any
import gzip

# Add utils to path
sys.path.append("/app/airflow/utils")
sys.path.append("/app/airflow/dags/registryinformation/utils")
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "utils"))

# Default arguments
default_args = {
    'owner': 'registry_import',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 25),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'catchup': False
}

# Data processing directories
DATA_DIR = Path('/data/imports/electricity/registryinformation')

def ensure_directories():
    """Ensure processing directories exist with proper nested structure by file type"""
    # Create nested directories by registry file type first, then by status
    registry_types = ['PR010', 'PR030', 'PR040', 'PR100', 'NP030_AU', 'NP030_ME', 'EDA', 'LIS', 'SCD', 'AUDIT']
    status_dirs = ['imported', 'archive', 'error']
    
    for registry_type in registry_types:
        for status_dir in status_dirs:
            (DATA_DIR / registry_type / status_dir).mkdir(parents=True, exist_ok=True)
    
    logging.info("✅ Created nested directory structure: {TYPE}/{STATUS} format")

def get_file_type_prefix(file_type: str) -> str:
    """Extract file type prefix for folder organization"""
    if file_type == 'PR-010-ICPLIST':
        return 'PR010'
    elif file_type == 'PR-030-EVENTDTL':
        return 'PR030'
    elif file_type == 'PR-040-SWBRCURD':
        return 'PR040'
    elif file_type == 'PR-100-LOSSFS':
        return 'PR100'
    elif file_type == 'NP-030-AUNOTIFY':
        return 'NP030_AU'
    elif file_type == 'NP-030-MENOTIFY':
        return 'NP030_ME'
    elif file_type == 'NMR-METERING-NOTIFY':
        return 'NMR'
    elif file_type in ['AUDIT-COMPLIANCE', 'AUDIT-COMPLIANCE-TXT', 'AUDIT-NOTIFICATION', 'AUDIT-WARNING']:
        return 'AUDIT'
    else:
        return 'AUDIT'  # Default fallback for unknown types
def classify_file_type(filename: str) -> str:
    """
    Classify registry file types based on filename patterns.
    Returns the file type category for registry information files.
    Now includes NMR, EDA, LIS, and SCD file types.
    """
    filename_lower = filename.lower()
    
    # Registry Information file types - Check specific patterns first
    if 'pr' in filename_lower and '010' in filename_lower:
        return 'PR-010-ICPLIST'
    elif 'pr' in filename_lower and '030' in filename_lower:
        return 'PR-030-EVENTDTL'
    elif 'pr' in filename_lower and '040' in filename_lower:
        return 'PR-040-SWBRCURD'
    elif 'pr' in filename_lower and '100' in filename_lower:
        return 'PR-100-LOSSFS'
    elif filename_lower.startswith('not') and filename_lower.endswith('.txt'):
        return 'NP-030-AUNOTIFY'
    elif filename_lower.startswith('nmr') and filename_lower.endswith('.txt'):
        return 'NMR-METERING-NOTIFY'  # Include NMR files as metering notifications
    elif filename_lower.startswith('eda') and filename_lower.endswith('.txt'):
        return 'PR-030-EVENTDTL'  # EDA files are Event Detail outputs from PR-030
    elif filename_lower.endswith('.eda'):  # Any .eda files are Event Detail files
        return 'PR-030-EVENTDTL'  # Include CS*.eda and other .eda files as Event Detail
    elif filename_lower.startswith('lis') and filename_lower.endswith('.txt'):
        return 'PR-010-ICPLIST'  # LIS files are ICP List outputs from PR-010
    elif filename_lower.startswith('scd') and filename_lower.endswith('.txt'):
        return 'PR-040-SWBRCURD'  # SCD files are Switch Compliance outputs from PR-040
    elif 'audit' in filename_lower and 'compliance' in filename_lower and filename_lower.endswith(('.xlsx', '.xls')):
        return 'AUDIT-COMPLIANCE'
    # EXCLUDE switching files - these should be handled by switching DAG
    elif filename_lower.startswith(('nt', 'cs', 'rr', 'nw', 'ac', 'an', 'aw')) and len(filename) >= 16 and filename_lower.endswith('.txt'):
        return 'SWITCHING-FILE-EXCLUDED'  # Mark as excluded - NT, CS, RR, NW, AC, AN, AW are switching files
    else:
        return 'UNKNOWN'

def test_registry_connection(**context):
    """Step 1: Test Registry SFTP connection"""
    logging.info("🔍 Step 1: Testing Registry SFTP Connection")
    
    try:
        from connection_manager import ConnectionManager
        
        # Use ConnectionManager for consistency with other DAGs
        conn_config = ConnectionManager.get_connection_config(
            protocol='SFTP',
            prefix='REGISTRY',
            default_host=None,
            default_port=22,
            default_user=None
        )
        # Override remote path for registry files
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

def discover_registry_files(**context):
    """Step 2: Discover registry information files ONLY (excluding switching files)"""
    logging.info("📁 Step 2: Discovering Registry Information Files ONLY")
    
    conn_config = context['ti'].xcom_pull(key='conn_config')
    if not conn_config:
        logging.info("ℹ️ No connection data from previous task, creating new connection config")
        # Use ConnectionManager for consistency with other DAGs
        conn_config = ConnectionManager.get_connection_config(
            protocol='SFTP',
            prefix='REGISTRY',
            default_host=None,
            default_port=22,
            default_user=None
        )
        # Override remote path for registry files
        conn_config['remote_path'] = '/fromreg/'
    
    try:
        from connection_manager import ConnectionManager
        
        # Get ALL files and filter for registry information files ONLY
        logging.info("🔍 Scanning for ALL files and filtering for registry information files...")
        all_files = ConnectionManager.list_remote_files(conn_config, r'^.*$')  # Get ALL files
        
        # Filter for registry information file types (exclude switching files only)
        registry_files = []
        switching_files_found = []
        unknown_files_found = []
        
        for filename in all_files:
            file_type = classify_file_type(filename)
            if file_type == 'SWITCHING-FILE-EXCLUDED':
                switching_files_found.append(filename)
                logging.info(f"🔄 Excluding switching file: {filename} (handled by switching DAG)")
            elif file_type == 'UNKNOWN':
                unknown_files_found.append(filename)
                logging.info(f"❓ Unknown file type: {filename} (will be skipped)")
            else:
                registry_files.append({
                    'filename': filename,
                    'file_type': file_type,
                    'size': 0  # Size will be determined during download
                })
        
        logging.info(f"📊 Found {len(registry_files)} registry files, {len(switching_files_found)} switching files (excluded), and {len(unknown_files_found)} unknown files (skipped):")
        
        # Group by file type for summary
        type_counts = {}
        for file_info in registry_files:
            file_type = file_info['file_type']
            if file_type not in type_counts:
                type_counts[file_type] = []
            type_counts[file_type].append(file_info['filename'])
        
        for file_type, files in type_counts.items():
            logging.info(f"  📄 {file_type}: {len(files)} files")
            for filename in files:
                logging.info(f"    - {filename}")
        
        if switching_files_found:
            logging.info(f"  🔄 Switching files excluded: {len(switching_files_found)} files")
            for filename in switching_files_found:
                logging.info(f"    - {filename} (will be processed by switching DAG)")
        
        if unknown_files_found:
            logging.info(f"  ❓ Unknown files skipped: {len(unknown_files_found)} files")
            for filename in unknown_files_found:
                logging.info(f"    - {filename} (file type not recognized)")
        
        context['ti'].xcom_push(key='discovered_files', value=registry_files)
        context['ti'].xcom_push(key='conn_config', value=conn_config)
        context['ti'].xcom_push(key='total_files', value=len(registry_files))
        context['ti'].xcom_push(key='excluded_switching_files', value=switching_files_found)
        context['ti'].xcom_push(key='unknown_files', value=unknown_files_found)
        
        return registry_files
        
    except Exception as e:
        logging.error(f"❌ File discovery error: {e}")
        raise

def download_registry_files(**context):
    """Step 3: Download ALL registry files with duplicate checking (following metering philosophy)"""
    logging.info("⬇️ Step 3: Downloading ALL Registry Files")
    
    discovered_files = context['ti'].xcom_pull(key='discovered_files')
    conn_config = context['ti'].xcom_pull(key='conn_config')
    
    if not discovered_files:
        logging.info("ℹ️ No files discovered")
        return []
    
    if not conn_config:
        logging.info("ℹ️ No connection config, creating new one")
        # Use ConnectionManager for consistency with other DAGs
        conn_config = ConnectionManager.get_connection_config(
            protocol='SFTP',
            prefix='REGISTRY',
            default_host=None,
            default_port=22,
            default_user=None
        )
        # Override remote path for registry files
        conn_config['remote_path'] = '/fromreg/'
    
    try:
        from connection_manager import ConnectionManager
        
        ensure_directories()
        
        # Pre-filter files to exclude already processed ones (following metering philosophy)
        logging.info(f"🔍 Checking {len(discovered_files)} discovered files for duplicates...")
        files_to_download = []
        skipped_files = []
        
        # Check database for already processed files (create tables if needed)
        try:
            from connection import get_connection
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Create tables first if they don't exist
                    create_registry_tables(cur)
                    conn.commit()
                    
                    # Fetch all completed files to check in memory
                    cur.execute(
                        """SELECT file_name FROM registry_information.import_log 
                           WHERE status = 'completed'"""
                    )
                    processed_files = {row[0] for row in cur.fetchall()}
                    logging.info(f"Found {len(processed_files)} already processed files.")

                    for file_info in discovered_files:
                        filename = file_info['filename']
                        
                        if filename in processed_files:
                            logging.info(f"🔄 Skipping {filename} - already processed")
                            skipped_files.append(filename)
                        else:
                            logging.info(f"✅ {filename} - new file, will download")
                            files_to_download.append(file_info)
        except Exception as db_error:
            logging.warning(f"⚠️ Could not check database for duplicates: {db_error}")
            logging.info("📥 Downloading all discovered files (no duplicate check)")
            files_to_download = discovered_files
        
        logging.info(f"📊 Download Summary: {len(files_to_download)} new files, {len(skipped_files)} already processed")
        
        if len(files_to_download) == 0:
            logging.info("ℹ️ No new files to download")
            context['ti'].xcom_push(key='downloaded_files', value=[])
            return []
        
        downloaded_files = []
        
        for file_info in files_to_download:
            filename = file_info['filename']
            file_type = file_info['file_type']
            logging.info(f"⬇️ Downloading {filename} ({file_type})")
            
            # Get file type prefix for nested directory structure
            type_prefix = get_file_type_prefix(file_type)
            if type_prefix:
                local_path = DATA_DIR / type_prefix / 'imported' / filename
            else:
                # Fallback to root imported directory if no type prefix
                local_path = DATA_DIR / 'imported' / filename
            
            if ConnectionManager.download_file(conn_config, filename, local_path):
                file_size = local_path.stat().st_size
                downloaded_files.append({
                    'filename': filename,
                    'local_path': str(local_path),
                    'size': file_size,
                    'file_type': file_info['file_type']
                })
                logging.info(f"✅ Downloaded {filename} ({file_size:,} bytes)")
            else:
                logging.error(f"❌ Failed to download {filename}")
        
        logging.info(f"📥 Downloaded {len(downloaded_files)}/{len(files_to_download)} files")
        
        context['ti'].xcom_push(key='downloaded_files', value=downloaded_files)
        context['ti'].xcom_push(key='skipped_files', value=skipped_files)
        
        return downloaded_files
        
    except Exception as e:
        logging.error(f"❌ Download error: {e}")
        raise

def import_registry_files_raw(**context):
    """Step 4: Import ALL registry files RAW into database with functional spec parsing"""
    logging.info("💾 Step 4: Importing ALL Registry Files with Functional Spec Parsing")
    
    downloaded_files = context['ti'].xcom_pull(key='downloaded_files')
    if not downloaded_files:
        logging.info("ℹ️ No registry files to import")
        return {'imported_files': 0, 'total_records': 0}

    # Get DAG context info for logging
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    try:
        from connection import get_connection
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Create the schema and all tables
                create_registry_tables(cur)
                
                imported_count = 0
                total_records = 0
                
                for file_info in downloaded_files:
                    filename = file_info['filename']
                    file_path = Path(file_info['local_path'])
                    file_size = file_info['size']
                    file_type = file_info['file_type']
                    
                    logging.info(f"📄 Processing {filename} ({file_type})")
                    
                    # Calculate file hash
                    file_hash = calculate_file_hash(file_path)
                    
                    # Check if already imported by looking in import_log (any status) and data tables
                    cur.execute(
                        """SELECT COUNT(*) FROM registry_information.import_log 
                           WHERE file_name = %s AND file_hash = %s AND status = 'completed'""",
                        (filename, file_hash)
                    )
                    
                    completed_count = cur.fetchone()[0]
                    
                    # Also check if data exists in the actual data tables (more reliable)
                    data_exists = False
                    if file_type == 'AUDIT-COMPLIANCE-TXT':
                        cur.execute(
                            """SELECT COUNT(*) FROM registry_information.audit_compliance 
                               WHERE file_name = %s AND file_hash = %s""",
                            (filename, file_hash)
                        )
                        data_exists = cur.fetchone()[0] > 0
                    elif file_type == 'NP-030-AUNOTIFY':
                        cur.execute(
                            """SELECT COUNT(*) FROM registry_information.np030_notifications 
                               WHERE file_name = %s AND file_hash = %s""",
                            (filename, file_hash)
                        )
                        data_exists = cur.fetchone()[0] > 0
                    # Add more file type checks as needed
                    
                    if completed_count > 0 or data_exists:
                        status_msg = "completed in log" if completed_count > 0 else "data exists in tables"
                        logging.info(f"🔄 Skipping {filename} - already imported ({status_msg})")
                        continue
                    
                    # Parse file based on type and import into specific tables
                    parsed_records = parse_registry_file(file_path, file_type, filename)
                    
                    # Import parsed records into specific tables
                    import_parsed_records(cur, file_type, filename, parsed_records, file_hash)
                    
                    imported_count += 1
                    total_records += len(parsed_records)
                    
                    # Log import using existing cursor
                    log_import_with_cursor(
                        cur=cur,
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        source_group='REGISTRY_INFORMATION',
                        file_name=filename,
                        file_type=file_type,
                        file_size=file_size,
                        file_hash=file_hash,
                        status='completed',
                        records_parsed=len(parsed_records),
                        records_loaded=len(parsed_records)
                    )
                    
                    logging.info(f"✅ Processed {filename}: {len(parsed_records)} records")
                
                conn.commit()
                
                logging.info(f"📊 Import Summary: {imported_count} files, {total_records} total records")
                
                context['ti'].xcom_push(key='imported_files', value=imported_count)
                context['ti'].xcom_push(key='total_records', value=total_records)
                
                return {'imported_files': imported_count, 'total_records': total_records}
        
    except Exception as e:
        logging.error(f"❌ Import error: {e}")
        
        # Log errors for each file (using separate connection since main connection failed)
        if downloaded_files:
            for file_info in downloaded_files:
                log_import(
                    dag_id=dag_id,
                    task_id=task_id,
                    run_id=run_id,
                    source_group='REGISTRY_INFORMATION',
                    file_name=file_info['filename'],
                    file_type=file_info['file_type'],
                    file_size=file_info['size'],
                    file_hash='',
                    status='failed',
                    records_parsed=0,
                    records_loaded=0,
                    error_message=str(e)
                )
        
        raise

def create_registry_tables(cur):
    """Create all registry information tables using production schema from create_registry_switching_tables_updated.sql
    This includes all tables with proper field mappings from functional specifications"""
    
    # Create schema
    cur.execute("CREATE SCHEMA IF NOT EXISTS registry_information;")
    
    # Import log table - updated schema from SQL file
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.import_log (
            id SERIAL PRIMARY KEY,
            dag_id VARCHAR(255) NOT NULL,
            task_id VARCHAR(255) NOT NULL,
            run_id VARCHAR(255) NOT NULL,
            source_group VARCHAR(50) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size BIGINT,
            file_hash VARCHAR(64) NOT NULL,
            status VARCHAR(20) NOT NULL,
            records_parsed INTEGER DEFAULT 0,
            records_loaded INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(file_name, file_hash)
        );
    """)
    
    # PR-010 ICP List data (Enhanced) - Full schema from SQL file
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.pr010_icp_list (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Header information
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_description VARCHAR(200),
            
            -- Detail record information - All 63 fields from FS1.txt
            record_type VARCHAR(10),
            icp_identifier VARCHAR(15) NOT NULL,
            icp_creation_date DATE,
            original_commissioning_event_date DATE,
            event_start_date DATE,
            event_end_date DATE,
            nsp_event_audit_number VARCHAR(15),
            network_distributor VARCHAR(4),
            poc VARCHAR(7),
            reconciliation_type VARCHAR(2),
            dedicated_nsp VARCHAR(1),
            installation_type VARCHAR(1),
            proposed_trader VARCHAR(4),
            unmetered_load_details_distributor VARCHAR(50),
            shared_icp_list TEXT,
            generation_capacity DECIMAL(8,2),
            fuel_type VARCHAR(15),
            initial_electrically_connected_date DATE,
            direct_billed_status VARCHAR(11),
            direct_billed_details VARCHAR(60),
            nsp_user_reference VARCHAR(32),
            pricing_audit_number VARCHAR(15),
            distributor_price_category_code VARCHAR(50),
            distributor_loss_category_code VARCHAR(7),
            chargeable_capacity DECIMAL(9,2),
            distributor_installation_details VARCHAR(30),
            pricing_user_reference VARCHAR(32),
            trader_audit_number VARCHAR(15),
            trader VARCHAR(4),
            profile VARCHAR(25),
            anzsic VARCHAR(7),
            proposed_mep VARCHAR(4),
            submission_type_hhr VARCHAR(1),
            submission_type_nhh VARCHAR(1),
            unm_flag VARCHAR(1),
            daily_unmetered_kwh VARCHAR(6),
            unmetered_load_details_trader VARCHAR(50),
            trader_user_reference VARCHAR(32),
            metering_audit_number VARCHAR(15),
            mep VARCHAR(4),
            highest_metering_category INTEGER,
            metering_type_hhr VARCHAR(1),
            meter_type_nhh VARCHAR(1),
            meter_type_pp VARCHAR(1),
            advanced_metering_infrastructure_flag VARCHAR(1),
            meter_channel_count INTEGER,
            meter_multiplier_flag VARCHAR(1),
            metering_user_reference VARCHAR(32),
            status_audit_number VARCHAR(15),
            icp_status VARCHAR(3),
            icp_status_reason_code INTEGER,
            status_user_reference VARCHAR(32),
            address_audit_number VARCHAR(15),
            physical_address_unit VARCHAR(20),
            physical_address_number VARCHAR(25),
            physical_address_region VARCHAR(20),
            physical_address_street VARCHAR(30),
            physical_address_suburb VARCHAR(30),
            physical_address_town VARCHAR(30),
            physical_address_post_code INTEGER,
            address_property_name VARCHAR(75),
            gps_easting DECIMAL(10,3),
            gps_northing DECIMAL(10,3),
            address_user_reference VARCHAR(32),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(file_name, file_hash, line_number)
        );
    """)
    
    # PR-030 Event Detail data (Enhanced) - Full schema from SQL file
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.pr030_event_detail (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Header information
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_description VARCHAR(200),
            
            -- Detail record information - Fixed fields from FS1.txt
            record_type VARCHAR(10),
            icp_identifier VARCHAR(15) NOT NULL,
            event_type VARCHAR(14),
            event_audit_number VARCHAR(15),
            event_date DATE,
            event_creation_datetime TIMESTAMP,
            created_by VARCHAR(15),
            file_name_ref VARCHAR(25),
            event_state VARCHAR(8),
            reversal_replaced_datetime TIMESTAMP,
            reversed_replaced_by VARCHAR(15),
            reversal_replacement_file_name VARCHAR(25),
            replacement_event_audit_number VARCHAR(15),
            
            -- Common event fields (parsed from variable fields)
            participant_identifier VARCHAR(4),
            old_value VARCHAR(100),
            new_value VARCHAR(100),
            effective_date DATE,
            
            -- Network event specific fields
            network_audit_number VARCHAR(15),
            poc VARCHAR(7),
            reconciliation_type VARCHAR(2),
            installation_type VARCHAR(1),
            
            -- Pricing event specific fields
            pricing_audit_number VARCHAR(15),
            price_category_code VARCHAR(50),
            loss_category_code VARCHAR(7),
            chargeable_capacity DECIMAL(9,2),
            
            -- Trader event specific fields
            trader_audit_number VARCHAR(15),
            trader VARCHAR(4),
            profile VARCHAR(25),
            anzsic VARCHAR(7),
            
            -- Metering event specific fields
            metering_audit_number VARCHAR(15),
            mep VARCHAR(4),
            metering_category INTEGER,
            
            -- Status event specific fields
            status_audit_number VARCHAR(15),
            icp_status VARCHAR(3),
            status_reason_code INTEGER,
            
            -- Variable fields as JSONB for any additional data
            additional_fields JSONB,
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(file_name, file_hash, line_number)
        );
    """)
    
    # NP-030 Audit Notifications (Enhanced) - From SQL file
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.np030_notifications (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Header information  
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_description VARCHAR(200),
            
            -- Detail record information - Essential fields only (removed irrelevant address fields)
            record_type VARCHAR(10),
            event_date DATE,
            icp_identifier VARCHAR(15) NOT NULL,
            notification_type VARCHAR(1),
            switch_status VARCHAR(1),
            network_audit_number VARCHAR(15),
            network_participant_identifier VARCHAR(4),
            poc VARCHAR(7),
            reconciliation_type VARCHAR(2),
            dedicated_nsp VARCHAR(1),
            installation_type VARCHAR(1),
            proposed_trader VARCHAR(4),
            unmetered_load_details_distributor VARCHAR(50),
            shared_icp_list VARCHAR(50),
            generation_capacity DECIMAL(9,2),
            fuel_type VARCHAR(50),
            initial_electrically_connected_date DATE,
            direct_billed_status VARCHAR(1),
            direct_billed_details VARCHAR(60),
            nsp_user_reference VARCHAR(32),
            pricing_audit_number VARCHAR(15),
            distributor_price_category_code VARCHAR(50),
            distributor_loss_category_code VARCHAR(7),
            chargeable_capacity DECIMAL(9,2),
            distributor_installation_details VARCHAR(30),
            pricing_user_reference VARCHAR(32),
            trader_audit_number VARCHAR(15),
            trader VARCHAR(4),
            profile VARCHAR(25),
            anzsic VARCHAR(7),
            proposed_mep VARCHAR(4),
            submission_type_hhr VARCHAR(1),
            submission_type_nhh VARCHAR(1),
            unm_flag VARCHAR(1),
            daily_unmetered_kwh VARCHAR(6),
            unmetered_load_details_trader VARCHAR(50),
            trader_user_reference VARCHAR(32),
            metering_audit_number VARCHAR(15),
            mep VARCHAR(4),
            highest_metering_category INTEGER,
            metering_type_hhr VARCHAR(1),
            meter_type_nhh VARCHAR(1),
            meter_type_pp VARCHAR(1),
            advanced_metering_infrastructure_flag VARCHAR(1),
            meter_channel_count INTEGER,
            meter_multiplier_flag VARCHAR(1),
            metering_user_reference VARCHAR(32),
            status_audit_number VARCHAR(15),
            icp_status VARCHAR(3),
            icp_status_reason_code INTEGER,
            status_user_reference VARCHAR(32),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(file_name, file_hash, line_number)
        );
    """)
    
    # PR-040 Switch Compliance table - From production schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.pr040_switch_compliance (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Header information
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_description VARCHAR(200),
            
            -- Detail record information - Switch compliance fields from FS1.txt
            record_type VARCHAR(10),
            switch_type VARCHAR(20),
            breach_type VARCHAR(50),
            defaulting_participant VARCHAR(10),
            other_participant VARCHAR(10),
            icp_identifier VARCHAR(15),
            sent_date DATE,
            due_date DATE,
            days_till_due INTEGER,
            days_overdue INTEGER,
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(file_name, file_hash, line_number)
        );
    """)
    
    # Audit Compliance table - Enhanced with better structure from SQL file
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.audit_compliance (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            sheet_name VARCHAR(255) NOT NULL,
            sheet_data JSONB,
            record_count INTEGER DEFAULT 0,
            headers JSONB,
            UNIQUE(file_name, file_hash, sheet_name)
        );
    """)
    
    # NMR Metering Notifications table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registry_information.nmr_metering_notifications (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            line_number INTEGER,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Header information
            hdr_record_type VARCHAR(10),
            hdr_process_identifier VARCHAR(20),
            hdr_sender VARCHAR(10),
            hdr_recipient VARCHAR(10),
            hdr_creation_date DATE,
            hdr_creation_time TIME,
            hdr_record_count INTEGER,
            hdr_description VARCHAR(200),
            
            -- Detail record information
            record_type VARCHAR(10),
            icp_identifier VARCHAR(15) NOT NULL,
            event_date DATE,
            notification_type VARCHAR(50),
            meter_serial_number VARCHAR(20),
            meter_reading_type VARCHAR(10),
            meter_reading_value DECIMAL(12,4),
            reading_date DATE,
            reading_time TIME,
            meter_register VARCHAR(10),
            multiplier DECIMAL(8,4),
            units VARCHAR(10),
            status_code VARCHAR(5),
            
            -- Metadata
            total_fields INTEGER,
            raw_line TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(file_name, file_hash, line_number)
        );
    """)
    

    # Create comprehensive indexes from SQL file
    indexes = [
        # PR-010 indexes
        "CREATE INDEX IF NOT EXISTS idx_pr010_file_name ON registry_information.pr010_icp_list(file_name)",
        "CREATE INDEX IF NOT EXISTS idx_pr010_file_hash ON registry_information.pr010_icp_list(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_pr010_icp ON registry_information.pr010_icp_list(icp_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_pr010_processed_at ON registry_information.pr010_icp_list(processed_at)",
        
        # PR-030 indexes
        "CREATE INDEX IF NOT EXISTS idx_pr030_file_name ON registry_information.pr030_event_detail(file_name)",
        "CREATE INDEX IF NOT EXISTS idx_pr030_file_hash ON registry_information.pr030_event_detail(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_pr030_icp ON registry_information.pr030_event_detail(icp_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_pr030_event_type ON registry_information.pr030_event_detail(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_pr030_processed_at ON registry_information.pr030_event_detail(processed_at)",
        
        # PR-040 indexes
        "CREATE INDEX IF NOT EXISTS idx_pr040_file_name ON registry_information.pr040_switch_compliance(file_name)",
        "CREATE INDEX IF NOT EXISTS idx_pr040_file_hash ON registry_information.pr040_switch_compliance(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_pr040_icp ON registry_information.pr040_switch_compliance(icp_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_pr040_switch_type ON registry_information.pr040_switch_compliance(switch_type)",
        "CREATE INDEX IF NOT EXISTS idx_pr040_processed_at ON registry_information.pr040_switch_compliance(processed_at)",
        
        # NP-030 Audit Notifications indexes
        "CREATE INDEX IF NOT EXISTS idx_np030_file_name ON registry_information.np030_notifications(file_name)",
        "CREATE INDEX IF NOT EXISTS idx_np030_file_hash ON registry_information.np030_notifications(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_np030_icp ON registry_information.np030_notifications(icp_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_np030_processed_at ON registry_information.np030_notifications(processed_at)",
        
        # NMR Metering Notifications indexes
        "CREATE INDEX IF NOT EXISTS idx_nmr_file_name ON registry_information.nmr_metering_notifications(file_name)",
        "CREATE INDEX IF NOT EXISTS idx_nmr_file_hash ON registry_information.nmr_metering_notifications(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_nmr_icp ON registry_information.nmr_metering_notifications(icp_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_nmr_processed_at ON registry_information.nmr_metering_notifications(processed_at)",
        
        # Audit Compliance indexes
        "CREATE INDEX IF NOT EXISTS idx_audit_file_name ON registry_information.audit_compliance(file_name)",
        "CREATE INDEX IF NOT EXISTS idx_audit_file_hash ON registry_information.audit_compliance(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_audit_processed_at ON registry_information.audit_compliance(processed_at)",
        
        # Import Log indexes
        "CREATE INDEX IF NOT EXISTS idx_import_log_dag_run ON registry_information.import_log(dag_id, run_id)",
        "CREATE INDEX IF NOT EXISTS idx_import_log_file_hash ON registry_information.import_log(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_import_log_status ON registry_information.import_log(status)",
        "CREATE INDEX IF NOT EXISTS idx_import_log_created_at ON registry_information.import_log(created_at)"
    ]
    
    for index_sql in indexes:
        cur.execute(index_sql)
    
    logging.info("✅ All registry information tables created successfully with proper file type mapping: LIS→PR-010, EDA→PR-030, SCD→PR-040, NMR→separate table")

def parse_registry_file(file_path: Path, file_type: str, filename: str):
    """Parse registry file based on functional specifications"""
    
    try:
        if file_type == 'AUDIT-COMPLIANCE':
            # Handle Excel files - create record for new schema structure
            return [{
                'sheet_name': 'Excel_File',
                'sheet_data': {
                    'file_type': 'EXCEL', 
                    'size': file_path.stat().st_size,
                    'filename': filename
                },
                'record_count': 1,
                'headers': ['file_info']
            }]
        
        # Read text file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        parsed_records = []
        
        if file_type.startswith('PR-010'):
            parsed_records = parse_pr010_icp_list(lines, filename)
        elif file_type.startswith('PR-030'):
            parsed_records = parse_pr030_event_detail(lines, filename)
        elif file_type.startswith('PR-040'):
            parsed_records = parse_pr040_switch_compliance(lines, filename)
        elif file_type.startswith('NP-030'):
            parsed_records = parse_np030_notifications(lines, filename, file_type)
        elif file_type == 'NMR-METERING-NOTIFY':
            parsed_records = parse_nmr_file(lines, filename)

        else:
            # Generic parsing for unknown types
            parsed_records = [{'line_number': i+1, 'content': line.strip()} 
                            for i, line in enumerate(lines) if line.strip()]
        
        return parsed_records
        
    except Exception as e:
        logging.error(f"❌ Error parsing {filename}: {e}")
        return [{'error': str(e), 'filename': filename}]

def parse_pr010_icp_list(lines, filename):
    """Parse PR-010 ICP List files according to FS1.txt functional specs - Column by Column"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            # Parse header record: HDR,RSICPLIST,RGST,YESP,date,time,count,description
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_description': fields[7] if len(fields) > 7 else ''
            }
            continue
            
        elif line.startswith('DET'):
            # Parse detail record according to PR-010 specification - All 63 fields from FS1.txt
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp_identifier': fields[1] if len(fields) > 1 else '',
                'icp_creation_date': parse_date(fields[2]) if len(fields) > 2 else None,
                'original_commissioning_event_date': parse_date(fields[3]) if len(fields) > 3 else None,
                'event_start_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'event_end_date': parse_date(fields[5]) if len(fields) > 5 else None,
                'nsp_event_audit_number': fields[6] if len(fields) > 6 else '',
                'network_distributor': fields[7] if len(fields) > 7 else '',
                'poc': fields[8] if len(fields) > 8 else '',
                'reconciliation_type': fields[9] if len(fields) > 9 else '',
                'dedicated_nsp': fields[10] if len(fields) > 10 else '',
                'installation_type': fields[11] if len(fields) > 11 else '',
                'proposed_trader': fields[12] if len(fields) > 12 else '',
                'unmetered_load_details_distributor': fields[13] if len(fields) > 13 else '',
                'shared_icp_list': fields[14] if len(fields) > 14 else '',
                'generation_capacity': parse_decimal(fields[15]) if len(fields) > 15 else None,
                'fuel_type': fields[16] if len(fields) > 16 else '',
                'initial_electrically_connected_date': parse_date(fields[17]) if len(fields) > 17 else None,
                'direct_billed_status': fields[18] if len(fields) > 18 else '',
                'direct_billed_details': fields[19] if len(fields) > 19 else '',
                'nsp_user_reference': fields[20] if len(fields) > 20 else '',
                'pricing_audit_number': fields[21] if len(fields) > 21 else '',
                'distributor_price_category_code': fields[22] if len(fields) > 22 else '',
                'distributor_loss_category_code': fields[23] if len(fields) > 23 else '',
                'chargeable_capacity': parse_decimal(fields[24]) if len(fields) > 24 else None,
                'distributor_installation_details': fields[25] if len(fields) > 25 else '',
                'pricing_user_reference': fields[26] if len(fields) > 26 else '',
                'trader_audit_number': fields[27] if len(fields) > 27 else '',
                'trader': fields[28] if len(fields) > 28 else '',
                'profile': fields[29] if len(fields) > 29 else '',
                'anzsic': fields[30] if len(fields) > 30 else '',
                'proposed_mep': fields[31] if len(fields) > 31 else '',
                'submission_type_hhr': fields[32] if len(fields) > 32 else '',
                'submission_type_nhh': fields[33] if len(fields) > 33 else '',
                'unm_flag': fields[34] if len(fields) > 34 else '',
                'daily_unmetered_kwh': fields[35] if len(fields) > 35 else '',
                'unmetered_load_details_trader': fields[36] if len(fields) > 36 else '',
                'trader_user_reference': fields[37] if len(fields) > 37 else '',
                'metering_audit_number': fields[38] if len(fields) > 38 else '',
                'mep': fields[39] if len(fields) > 39 else '',
                'highest_metering_category': parse_int(fields[40]) if len(fields) > 40 else None,
                'metering_type_hhr': fields[41] if len(fields) > 41 else '',
                'meter_type_nhh': fields[42] if len(fields) > 42 else '',
                'meter_type_pp': fields[43] if len(fields) > 43 else '',
                'advanced_metering_infrastructure_flag': fields[44] if len(fields) > 44 else '',
                'meter_channel_count': parse_int(fields[45]) if len(fields) > 45 else None,
                'meter_multiplier_flag': fields[46] if len(fields) > 46 else '',
                'metering_user_reference': fields[47] if len(fields) > 47 else '',
                'status_audit_number': fields[48] if len(fields) > 48 else '',
                'icp_status': fields[49] if len(fields) > 49 else '',
                'icp_status_reason_code': parse_int(fields[50]) if len(fields) > 50 else None,
                'status_user_reference': fields[51] if len(fields) > 51 else '',
                'address_audit_number': fields[52] if len(fields) > 52 else '',
                'physical_address_unit': fields[53] if len(fields) > 53 else '',
                'physical_address_number': fields[54] if len(fields) > 54 else '',
                'physical_address_region': fields[55] if len(fields) > 55 else '',
                'physical_address_street': fields[56] if len(fields) > 56 else '',
                'physical_address_suburb': fields[57] if len(fields) > 57 else '',
                'physical_address_town': fields[58] if len(fields) > 58 else '',
                'physical_address_post_code': parse_int(fields[59]) if len(fields) > 59 else None,
                'address_property_name': fields[60] if len(fields) > 60 else '',
                'gps_easting': parse_decimal(fields[61]) if len(fields) > 61 else None,
                'gps_northing': parse_decimal(fields[62]) if len(fields) > 62 else None,
                'address_user_reference': fields[63] if len(fields) > 63 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_pr030_event_detail(lines, filename):
    """Parse PR-030 Event Detail files according to FS1.txt functional specs - Column by Column"""
    import json
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            # Parse header record: HDR,RSEVENTDTL,RGST,YESP,date,time,count,description
            # Ensure we have enough fields and handle missing fields gracefully
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else 'HDR',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 and fields[4].strip() else None,
                'hdr_creation_time': fields[5] if len(fields) > 5 else '',
                'hdr_record_count': int(fields[6]) if len(fields) > 6 and fields[6].strip().isdigit() else 0,
                'hdr_description': fields[7] if len(fields) > 7 else ''
            }
            continue
            
        elif line.startswith('DET'):
            # Parse detail record according to PR-030 specification - All required fields for import
            # Convert additional_fields list to JSON and handle data type conversions properly
            additional_fields_list = fields[35:] if len(fields) > 35 else []
            
            # Helper function to safely truncate strings to max length
            def safe_truncate(value, max_length):
                if not value or value == '':
                    return ''
                return str(value)[:max_length]
            
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'icp_identifier': safe_truncate(fields[1] if len(fields) > 1 else '', 15),  # Truncate to 15 chars max
                'event_type': safe_truncate(fields[2] if len(fields) > 2 else '', 14),  # Truncate to 14 chars max
                'event_audit_number': safe_truncate(fields[3] if len(fields) > 3 else '', 15),  # Truncate to 15 chars max
                'event_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'event_creation_datetime': parse_datetime(fields[5]) if len(fields) > 5 else None,
                'created_by': safe_truncate(fields[6] if len(fields) > 6 else '', 15),  # Truncate to 15 chars max
                'file_name_ref': safe_truncate(fields[7] if len(fields) > 7 else '', 25),  # Truncate to 25 chars max
                'event_state': safe_truncate(fields[8] if len(fields) > 8 else '', 8),  # Truncate to 8 chars max
                'reversal_replaced_datetime': parse_datetime(fields[9]) if len(fields) > 9 else None,
                'reversed_replaced_by': safe_truncate(fields[10] if len(fields) > 10 else '', 15),  # Truncate to 15 chars max
                'reversal_replacement_file_name': safe_truncate(fields[11] if len(fields) > 11 else '', 25),  # Truncate to 25 chars max
                'replacement_event_audit_number': safe_truncate(fields[12] if len(fields) > 12 else '', 15),  # Truncate to 15 chars max
                'participant_identifier': safe_truncate(fields[13] if len(fields) > 13 else '', 4),  # Truncate to 4 chars max
                'old_value': safe_truncate(fields[14] if len(fields) > 14 else '', 100),  # Truncate to 100 chars max
                'new_value': safe_truncate(fields[15] if len(fields) > 15 else '', 100),  # Truncate to 100 chars max
                'effective_date': parse_date(fields[16]) if len(fields) > 16 else None,
                'network_audit_number': safe_truncate(fields[17] if len(fields) > 17 else '', 15),  # Truncate to 15 chars max
                'poc': safe_truncate(fields[18] if len(fields) > 18 else '', 7),  # Truncate to 7 chars max
                'reconciliation_type': safe_truncate(fields[19] if len(fields) > 19 else '', 2),  # Truncate to 2 chars max
                'installation_type': safe_truncate(fields[20] if len(fields) > 20 else '', 1),  # Truncate to 1 char max
                'pricing_audit_number': safe_truncate(fields[21] if len(fields) > 21 else '', 15),  # Truncate to 15 chars max
                'price_category_code': safe_truncate(fields[22] if len(fields) > 22 else '', 50),  # Truncate to 50 chars max
                'loss_category_code': safe_truncate(fields[23] if len(fields) > 23 else '', 7),  # Truncate to 7 chars max
                'chargeable_capacity': parse_decimal(fields[24]) if len(fields) > 24 else None,
                'trader_audit_number': safe_truncate(fields[25] if len(fields) > 25 else '', 15),  # Truncate to 15 chars max
                'trader': safe_truncate(fields[26] if len(fields) > 26 else '', 4),  # Truncate to 4 chars max
                'profile': safe_truncate(fields[27] if len(fields) > 27 else '', 25),  # Truncate to 25 chars max
                'anzsic': safe_truncate(fields[28] if len(fields) > 28 else '', 7),  # Truncate to 7 chars max
                'metering_audit_number': safe_truncate(fields[29] if len(fields) > 29 else '', 15),  # Truncate to 15 chars max
                'mep': safe_truncate(fields[30] if len(fields) > 30 else '', 4),  # Truncate to 4 chars max
                'metering_category': parse_int(fields[31]) if len(fields) > 31 else None,
                'status_audit_number': safe_truncate(fields[32] if len(fields) > 32 else '', 15),  # Truncate to 15 chars max
                'icp_status': safe_truncate(fields[33] if len(fields) > 33 else '', 3),  # Truncate to 3 chars max
                'status_reason_code': parse_int(fields[34]) if len(fields) > 34 else None,
                'additional_fields': json.dumps(additional_fields_list) if additional_fields_list else None,  # Convert to JSON
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_pr040_switch_compliance(lines, filename):
    """Parse PR-040 Switch Compliance files according to FS1.txt functional specs"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            # Parse header record: HDR,RSSWBRCURD,RGST,YESP,date,time,count,description
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_description': fields[7] if len(fields) > 7 else ''
            }
            continue
            
        elif line.startswith('DET'):
            # Parse detail record according to PR-040 specification - Switch compliance fields
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'switch_type': fields[1] if len(fields) > 1 else '',
                'breach_type': fields[2] if len(fields) > 2 else '',
                'defaulting_participant': fields[3] if len(fields) > 3 else '',
                'other_participant': fields[4] if len(fields) > 4 else '',
                'icp_identifier': fields[5] if len(fields) > 5 else '',
                'sent_date': parse_date(fields[6]) if len(fields) > 6 else None,
                'due_date': parse_date(fields[7]) if len(fields) > 7 else None,
                'days_till_due': parse_int(fields[8]) if len(fields) > 8 else None,
                'days_overdue': parse_int(fields[9]) if len(fields) > 9 else None,
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_np030_notifications(lines, filename, file_type):
    """Parse NP-030 Notification files (AUNOTIFY/MENOTIFY) according to FS1.txt - Column by Column"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            # Parse header record: HDR,RSAUNOTIFY/RSMENOTIFY,RGST,YESP,date,time,count,description
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_description': fields[7] if len(fields) > 7 else ''
            }
            continue
            
        elif line.startswith('DET'):
            # Parse detail record according to NP-030 specification - All 52 fields from FS1.txt
            record = {
                'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                'event_date': parse_date(fields[1]) if len(fields) > 1 else None,
                'icp_identifier': fields[2] if len(fields) > 2 else '',
                'notification_type': fields[3] if len(fields) > 3 else '',
                'switch_status': fields[4] if len(fields) > 4 else '',
                'network_audit_number': fields[5] if len(fields) > 5 else '',
                'network_participant_identifier': fields[6] if len(fields) > 6 else '',
                'poc': fields[7] if len(fields) > 7 else '',
                'reconciliation_type': fields[8] if len(fields) > 8 else '',
                'dedicated_nsp': fields[9] if len(fields) > 9 else '',
                'installation_type': fields[10] if len(fields) > 10 else '',
                'proposed_trader': fields[11] if len(fields) > 11 else '',
                'unmetered_load_details_distributor': fields[12] if len(fields) > 12 else '',
                'shared_icp_list': fields[13] if len(fields) > 13 else '',
                'generation_capacity': parse_decimal(fields[14]) if len(fields) > 14 else None,
                'fuel_type': fields[15] if len(fields) > 15 else '',
                'initial_electrically_connected_date': parse_date(fields[16]) if len(fields) > 16 else None,
                'direct_billed_status': fields[17] if len(fields) > 17 else '',
                'direct_billed_details': fields[18] if len(fields) > 18 else '',
                'nsp_user_reference': fields[19] if len(fields) > 19 else '',
                'pricing_audit_number': fields[20] if len(fields) > 20 else '',
                'distributor_price_category_code': fields[21] if len(fields) > 21 else '',
                'distributor_loss_category_code': fields[22] if len(fields) > 22 else '',
                'chargeable_capacity': parse_decimal(fields[23]) if len(fields) > 23 else None,
                'distributor_installation_details': fields[24] if len(fields) > 24 else '',
                'pricing_user_reference': fields[25] if len(fields) > 25 else '',
                'address_audit_number': fields[26] if len(fields) > 26 else '',
                'physical_address_unit': fields[27] if len(fields) > 27 else '',
                'physical_address_number': fields[28] if len(fields) > 28 else '',
                'physical_address_street': fields[29] if len(fields) > 29 else '',
                'physical_address_suburb': fields[30] if len(fields) > 30 else '',
                'physical_address_town': fields[31] if len(fields) > 31 else '',
                'physical_address_post_code': parse_int(fields[32]) if len(fields) > 32 else None,
                'physical_address_region': fields[33] if len(fields) > 33 else '',
                'address_property_name': fields[34] if len(fields) > 34 else '',
                'gps_easting': parse_decimal(fields[35]) if len(fields) > 35 else None,
                'gps_northing': parse_decimal(fields[36]) if len(fields) > 36 else None,
                'address_user_reference': fields[37] if len(fields) > 37 else '',
                'trader_audit_number': fields[38] if len(fields) > 38 else '',
                'trader': fields[39] if len(fields) > 39 else '',
                'profile': fields[40] if len(fields) > 40 else '',
                'anzsic': fields[41] if len(fields) > 41 else '',
                'proposed_mep': fields[42] if len(fields) > 42 else '',
                'submission_type_hhr': fields[43] if len(fields) > 43 else '',
                'submission_type_nhh': fields[44] if len(fields) > 44 else '',
                'unm_flag': fields[45] if len(fields) > 45 else '',
                'unmetered_load_details_trader': fields[46] if len(fields) > 46 else '',
                'daily_unmetered_kwh': fields[47] if len(fields) > 47 else '',
                'trader_user_reference': fields[48] if len(fields) > 48 else '',
                'metering_audit_number': fields[49] if len(fields) > 49 else '',
                'mep': fields[50] if len(fields) > 50 else '',
                'highest_metering_category': parse_int(fields[51]) if len(fields) > 51 else None,
                'metering_type_hhr': fields[52] if len(fields) > 52 else '',
                'meter_type_nhh': fields[53] if len(fields) > 53 else '',
                'meter_type_pp': fields[54] if len(fields) > 54 else '',
                'advanced_metering_infrastructure_flag': fields[55] if len(fields) > 55 else '',
                'meter_channel_count': parse_int(fields[56]) if len(fields) > 56 else None,
                'meter_multiplier_flag': fields[57] if len(fields) > 57 else '',
                'metering_user_reference': fields[58] if len(fields) > 58 else '',
                'status_audit_number': fields[59] if len(fields) > 59 else '',
                'icp_status': fields[60] if len(fields) > 60 else '',
                'icp_status_reason_code': parse_int(fields[61]) if len(fields) > 61 else None,
                'status_user_reference': fields[62] if len(fields) > 62 else '',
                'header_info': header_info,
                'total_fields': len(fields),
                'raw_line': line
            }
            records.append(record)
    
    return records

def parse_nmr_file(lines, filename):
    """Parse NMR (Metering Notification) files according to FS1.txt - Metering data in CSV format"""
    records = []
    header_info = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        fields = [field.strip() for field in line.split(',')]
        
        if line.startswith('HDR'):
            # Parse header record: HDR,RSMENOTIFY,RGST,YESP,date,time,count,description
            header_info = {
                'hdr_record_type': fields[0] if len(fields) > 0 else '',
                'hdr_process_identifier': fields[1] if len(fields) > 1 else '',
                'hdr_sender': fields[2] if len(fields) > 2 else '',
                'hdr_recipient': fields[3] if len(fields) > 3 else '',
                'hdr_creation_date': parse_date(fields[4]) if len(fields) > 4 else None,
                'hdr_creation_time': parse_time(fields[5]) if len(fields) > 5 else None,
                'hdr_record_count': parse_int(fields[6]) if len(fields) > 6 else 0,
                'hdr_description': fields[7] if len(fields) > 7 else ''
            }
            continue
            
        elif line.startswith('DET'):
            # Parse detail record according to NMR specification - Metering notification fields
                record = {
                    'line_number': line_num,
                'record_type': fields[0] if len(fields) > 0 else '',
                    'icp_identifier': fields[1] if len(fields) > 1 else '',
                'event_date': parse_date(fields[2]) if len(fields) > 2 else None,
                'notification_type': fields[3] if len(fields) > 3 else '',
                'meter_serial_number': fields[4] if len(fields) > 4 else '',
                'meter_reading_type': fields[5] if len(fields) > 5 else '',
                'meter_reading_value': parse_decimal(fields[6]) if len(fields) > 6 else None,
                'reading_date': parse_date(fields[7]) if len(fields) > 7 else None,
                'reading_time': parse_time(fields[8]) if len(fields) > 8 else None,
                'meter_register': fields[9] if len(fields) > 9 else '',
                'multiplier': parse_decimal(fields[10]) if len(fields) > 10 else None,
                'units': fields[11] if len(fields) > 11 else '',
                'status_code': fields[12] if len(fields) > 12 else '',
                    'header_info': header_info,
                    'total_fields': len(fields),
                'raw_line': line
                }
                records.append(record)
    
    return records



def parse_date(date_str):
    """Parse date string in DD/MM/YYYY format according to FS1.txt specs"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        from datetime import datetime
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except:
        return None

def parse_datetime(datetime_str):
    """Parse datetime string in DD/MM/YYYY HH:MM:SS format according to FS1.txt specs"""
    if not datetime_str or datetime_str.strip() == '':
        return None
    try:
        from datetime import datetime
        return datetime.strptime(datetime_str.strip(), '%d/%m/%Y %H:%M:%S')
    except:
        return None

def parse_int(int_str):
    """Parse integer according to FS1.txt INT format"""
    if not int_str or int_str.strip() == '':
        return None
    try:
        return int(int_str.strip())
    except:
        return None

def parse_decimal(decimal_str):
    """Parse decimal according to FS1.txt Num format with DECIMAL(9,2) validation"""
    if not decimal_str or decimal_str.strip() == '':
        return None
    try:
        value = float(decimal_str.strip())
        # Validate DECIMAL(9,2) constraint: max value is 9,999,999.99
        if abs(value) >= 10000000:  # 10^7
            return None  # Return None for values that would cause overflow
        return value
    except:
        return None

def parse_time(time_str):
    """Parse time string in HH:MM:SS format according to FS1.txt specs"""
    if not time_str or time_str.strip() == '':
        return None
    try:
        from datetime import datetime
        return datetime.strptime(time_str.strip(), '%H:%M:%S').time()
    except:
        return None

def import_parsed_records(cur, file_type, filename, records, file_hash):
    """Import parsed records into appropriate tables - supports all registry file types"""
    
    if not records:
        return
    
    if file_type.startswith('PR-010'):
        import_pr010_records(cur, filename, records, file_hash)
    elif file_type.startswith('PR-030'):
        import_pr030_records(cur, filename, records, file_hash)
    elif file_type.startswith('PR-040'):
        import_pr040_records(cur, filename, records, file_hash)
    elif file_type.startswith('NP-030'):
        import_np030_records(cur, filename, records, file_hash)
    elif file_type == 'NMR-METERING-NOTIFY':
        import_nmr_records(cur, filename, records, file_hash)
    elif file_type == 'AUDIT-COMPLIANCE':
        import_audit_compliance_records(cur, filename, records, file_hash)
    else:
        logging.warning(f"⚠️ No import handler for file type: {file_type}")
        # For unknown types, we could log them but not import to avoid errors

def import_np030_records(cur, filename, records, file_hash):
    """Import NP-030 Notification records using updated schema structure"""
    for record in records:
        header_info = record.get('header_info', {})
        cur.execute("""
            INSERT INTO registry_information.np030_notifications 
            (file_name, file_hash, line_number,
             hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
             hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_description,
             record_type, event_date, icp_identifier, notification_type, switch_status,
             network_audit_number, network_participant_identifier, poc, reconciliation_type,
             dedicated_nsp, installation_type, proposed_trader, unmetered_load_details_distributor,
             shared_icp_list, generation_capacity, fuel_type, initial_electrically_connected_date,
             direct_billed_status, direct_billed_details, nsp_user_reference,
             pricing_audit_number, distributor_price_category_code, distributor_loss_category_code,
             chargeable_capacity, distributor_installation_details, pricing_user_reference,
             trader_audit_number, trader, profile, anzsic, proposed_mep,
             submission_type_hhr, submission_type_nhh, unm_flag, daily_unmetered_kwh,
             unmetered_load_details_trader, trader_user_reference, metering_audit_number,
             mep, highest_metering_category, metering_type_hhr, meter_type_nhh, meter_type_pp,
             advanced_metering_infrastructure_flag, meter_channel_count, meter_multiplier_flag,
             metering_user_reference, status_audit_number, icp_status, icp_status_reason_code,
             status_user_reference, total_fields, raw_line)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s)
        """, (
            filename, file_hash, record.get('line_number'),
            header_info.get('hdr_record_type'), header_info.get('hdr_process_identifier'),
            header_info.get('hdr_sender'), header_info.get('hdr_recipient'),
            header_info.get('hdr_creation_date'), header_info.get('hdr_creation_time'),
            header_info.get('hdr_record_count'), header_info.get('hdr_description'),
            record.get('record_type'), record.get('event_date'), record.get('icp_identifier'),
            record.get('notification_type'), record.get('switch_status'),
            record.get('network_audit_number'), record.get('network_participant_identifier'),
            record.get('poc'), record.get('reconciliation_type'), record.get('dedicated_nsp'),
            record.get('installation_type'), record.get('proposed_trader'),
            record.get('unmetered_load_details_distributor'), record.get('shared_icp_list'),
            record.get('generation_capacity'), record.get('fuel_type'),
            record.get('initial_electrically_connected_date'), record.get('direct_billed_status'),
            record.get('direct_billed_details'), record.get('nsp_user_reference'),
            record.get('pricing_audit_number'), record.get('distributor_price_category_code'),
            record.get('distributor_loss_category_code'), record.get('chargeable_capacity'),
            record.get('distributor_installation_details'), record.get('pricing_user_reference'),
            record.get('trader_audit_number'), record.get('trader'), record.get('profile'),
            record.get('anzsic'), record.get('proposed_mep'),
            record.get('submission_type_hhr'), record.get('submission_type_nhh'),
            record.get('unm_flag'), record.get('daily_unmetered_kwh'),
            record.get('unmetered_load_details_trader'), record.get('trader_user_reference'),
            record.get('metering_audit_number'), record.get('mep'), record.get('highest_metering_category'),
            record.get('metering_type_hhr'), record.get('meter_type_nhh'), record.get('meter_type_pp'),
            record.get('advanced_metering_infrastructure_flag'), record.get('meter_channel_count'),
            record.get('meter_multiplier_flag'), record.get('metering_user_reference'),
            record.get('status_audit_number'), record.get('icp_status'), record.get('icp_status_reason_code'),
            record.get('status_user_reference'), record.get('total_fields'), record.get('raw_line')
        ))

def import_audit_compliance_records(cur, filename, records, file_hash):
    """Import audit compliance Excel file records using new schema structure"""
    import json
    for record in records:
        cur.execute("""
            INSERT INTO registry_information.audit_compliance 
            (file_name, file_hash, sheet_name, sheet_data, record_count, headers)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_name, file_hash, sheet_name) 
            DO UPDATE SET 
                sheet_data = EXCLUDED.sheet_data,
                record_count = EXCLUDED.record_count,
                headers = EXCLUDED.headers,
                processed_at = NOW()
        """, (
            filename, 
            file_hash, 
            record.get('sheet_name', 'Sheet1'), 
            json.dumps(record.get('sheet_data', {})),
            record.get('record_count', 0),
            json.dumps(record.get('headers', []))
        ))

def import_pr010_records(cur, filename, records, file_hash):
    """Import PR-010 ICP List records using production schema with all 63 fields"""
    for record in records:
        header_info = record.get('header_info', {})
        cur.execute("""
            INSERT INTO registry_information.pr010_icp_list 
            (file_name, file_hash, line_number, 
             hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient, 
             hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_description,
             record_type, icp_identifier, icp_creation_date, original_commissioning_event_date,
             event_start_date, event_end_date, nsp_event_audit_number, network_distributor,
             poc, reconciliation_type, dedicated_nsp, installation_type, proposed_trader,
             unmetered_load_details_distributor, shared_icp_list, generation_capacity, fuel_type,
             initial_electrically_connected_date, direct_billed_status, direct_billed_details,
             nsp_user_reference, pricing_audit_number, distributor_price_category_code,
             distributor_loss_category_code, chargeable_capacity, distributor_installation_details,
             pricing_user_reference, trader_audit_number, trader, profile, anzsic, proposed_mep,
             submission_type_hhr, submission_type_nhh, unm_flag, daily_unmetered_kwh,
             unmetered_load_details_trader, trader_user_reference, metering_audit_number,
             mep, highest_metering_category, metering_type_hhr, meter_type_nhh, meter_type_pp,
             advanced_metering_infrastructure_flag, meter_channel_count, meter_multiplier_flag,
             metering_user_reference, status_audit_number, icp_status, icp_status_reason_code,
             status_user_reference, address_audit_number, physical_address_unit,
             physical_address_number, physical_address_region, physical_address_street,
             physical_address_suburb, physical_address_town, physical_address_post_code,
             address_property_name, gps_easting, gps_northing, address_user_reference,
             total_fields, raw_line)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_name, file_hash, line_number) DO NOTHING
        """, (
            filename, file_hash, record.get('line_number'),
            header_info.get('hdr_record_type'), header_info.get('hdr_process_identifier'),
            header_info.get('hdr_sender'), header_info.get('hdr_recipient'),
            header_info.get('hdr_creation_date'), header_info.get('hdr_creation_time'),
            header_info.get('hdr_record_count'), header_info.get('hdr_description'),
            record.get('record_type'), record.get('icp_identifier'), record.get('icp_creation_date'),
            record.get('original_commissioning_event_date'), record.get('event_start_date'),
            record.get('event_end_date'), record.get('nsp_event_audit_number'),
            record.get('network_distributor'), record.get('poc'), record.get('reconciliation_type'),
            record.get('dedicated_nsp'), record.get('installation_type'), record.get('proposed_trader'),
            record.get('unmetered_load_details_distributor'), record.get('shared_icp_list'),
            record.get('generation_capacity'), record.get('fuel_type'),
            record.get('initial_electrically_connected_date'), record.get('direct_billed_status'),
            record.get('direct_billed_details'), record.get('nsp_user_reference'),
            record.get('pricing_audit_number'), record.get('distributor_price_category_code'),
            record.get('distributor_loss_category_code'), record.get('chargeable_capacity'),
            record.get('distributor_installation_details'), record.get('pricing_user_reference'),
            record.get('trader_audit_number'), record.get('trader'), record.get('profile'),
            record.get('anzsic'), record.get('proposed_mep'), record.get('submission_type_hhr'),
            record.get('submission_type_nhh'), record.get('unm_flag'), record.get('daily_unmetered_kwh'),
            record.get('unmetered_load_details_trader'), record.get('trader_user_reference'),
            record.get('metering_audit_number'), record.get('mep'), record.get('highest_metering_category'),
            record.get('metering_type_hhr'), record.get('meter_type_nhh'), record.get('meter_type_pp'),
            record.get('advanced_metering_infrastructure_flag'), record.get('meter_channel_count'),
            record.get('meter_multiplier_flag'), record.get('metering_user_reference'),
            record.get('status_audit_number'), record.get('icp_status'), record.get('icp_status_reason_code'),
            record.get('status_user_reference'), record.get('address_audit_number'),
            record.get('physical_address_unit'), record.get('physical_address_number'),
            record.get('physical_address_region'), record.get('physical_address_street'),
            record.get('physical_address_suburb'), record.get('physical_address_town'),
            record.get('physical_address_post_code'), record.get('address_property_name'),
            record.get('gps_easting'), record.get('gps_northing'), record.get('address_user_reference'),
            record.get('total_fields'), record.get('raw_line')
        ))

def import_pr030_records(cur, filename, records, file_hash):
    """Import PR-030 Event Detail records using production schema with event-specific fields"""
    for record in records:
        header_info = record.get('header_info', {})
        cur.execute("""
            INSERT INTO registry_information.pr030_event_detail 
            (file_name, file_hash, line_number,
             hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
             hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_description,
             record_type, icp_identifier, event_type, event_audit_number, event_date,
             event_creation_datetime, created_by, file_name_ref, event_state,
             reversal_replaced_datetime, reversed_replaced_by, reversal_replacement_file_name,
             replacement_event_audit_number, participant_identifier, old_value, new_value,
             effective_date, network_audit_number, poc, reconciliation_type, installation_type,
             pricing_audit_number, price_category_code, loss_category_code, chargeable_capacity,
             trader_audit_number, trader, profile, anzsic, metering_audit_number, mep,
             metering_category, status_audit_number, icp_status, status_reason_code,
             additional_fields, total_fields, raw_line)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_name, file_hash, line_number) DO NOTHING
        """, (
            filename, file_hash, record.get('line_number'),
            header_info.get('hdr_record_type'), header_info.get('hdr_process_identifier'),
            header_info.get('hdr_sender'), header_info.get('hdr_recipient'),
            header_info.get('hdr_creation_date'), header_info.get('hdr_creation_time'),
            header_info.get('hdr_record_count'), header_info.get('hdr_description'),
            record.get('record_type'), record.get('icp_identifier'), record.get('event_type'),
            record.get('event_audit_number'), record.get('event_date'),
            record.get('event_creation_datetime'), record.get('created_by'),
            record.get('file_name_ref'), record.get('event_state'),
            record.get('reversal_replaced_datetime'), record.get('reversed_replaced_by'),
            record.get('reversal_replacement_file_name'), record.get('replacement_event_audit_number'),
            record.get('participant_identifier'), record.get('old_value'), record.get('new_value'),
            record.get('effective_date'), record.get('network_audit_number'), record.get('poc'),
            record.get('reconciliation_type'), record.get('installation_type'),
            record.get('pricing_audit_number'), record.get('price_category_code'),
            record.get('loss_category_code'), record.get('chargeable_capacity'),
            record.get('trader_audit_number'), record.get('trader'), record.get('profile'),
            record.get('anzsic'), record.get('metering_audit_number'), record.get('mep'),
            record.get('metering_category'), record.get('status_audit_number'),
            record.get('icp_status'), record.get('status_reason_code'),
            record.get('additional_fields'), record.get('total_fields'), record.get('raw_line')
        ))

def import_pr040_records(cur, filename, records, file_hash):
    """Import PR-040 Switch Compliance records using production schema"""
    for record in records:
        header_info = record.get('header_info', {})
        cur.execute("""
            INSERT INTO registry_information.pr040_switch_compliance 
            (file_name, file_hash, line_number,
             hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
             hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_description,
             record_type, switch_type, breach_type, defaulting_participant,
             other_participant, icp_identifier, sent_date, due_date,
             days_till_due, days_overdue, total_fields, raw_line)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_name, file_hash, line_number) DO NOTHING
        """, (
            filename, file_hash, record.get('line_number'),
            header_info.get('hdr_record_type'), header_info.get('hdr_process_identifier'),
            header_info.get('hdr_sender'), header_info.get('hdr_recipient'),
            header_info.get('hdr_creation_date'), header_info.get('hdr_creation_time'),
            header_info.get('hdr_record_count'), header_info.get('hdr_description'),
            record.get('record_type'), record.get('switch_type'), record.get('breach_type'),
            record.get('defaulting_participant'), record.get('other_participant'),
            record.get('icp_identifier'), record.get('sent_date'), record.get('due_date'),
            record.get('days_till_due'), record.get('days_overdue'),
            record.get('total_fields'), record.get('raw_line')
        ))

def import_nmr_records(cur, filename, records, file_hash):
    """Import NMR Metering Notification records"""
    for record in records:
        header_info = record.get('header_info', {})
        cur.execute("""
            INSERT INTO registry_information.nmr_metering_notifications 
            (file_name, file_hash, line_number,
             hdr_record_type, hdr_process_identifier, hdr_sender, hdr_recipient,
             hdr_creation_date, hdr_creation_time, hdr_record_count, hdr_description,
             record_type, icp_identifier, event_date, notification_type,
             meter_serial_number, meter_reading_type, meter_reading_value,
             reading_date, reading_time, meter_register, multiplier, units, status_code,
             total_fields, raw_line)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_name, file_hash, line_number) DO NOTHING
        """, (
            filename, file_hash, record.get('line_number'),
            header_info.get('hdr_record_type'), header_info.get('hdr_process_identifier'),
            header_info.get('hdr_sender'), header_info.get('hdr_recipient'),
            header_info.get('hdr_creation_date'), header_info.get('hdr_creation_time'),
            header_info.get('hdr_record_count'), header_info.get('hdr_description'),
            record.get('record_type'), record.get('icp_identifier'), record.get('event_date'),
            record.get('notification_type'), record.get('meter_serial_number'),
            record.get('meter_reading_type'), record.get('meter_reading_value'),
            record.get('reading_date'), record.get('reading_time'), record.get('meter_register'),
            record.get('multiplier'), record.get('units'), record.get('status_code'),
            record.get('total_fields'), record.get('raw_line')
        ))


def verify_registry_import(**context):
    """Step 5: Verify import with comprehensive audit"""
    logging.info("🔍 Step 5: Verifying Registry Import")
    
    try:
        imported_files = context['ti'].xcom_pull(key='imported_files') or 0
        total_records = context['ti'].xcom_pull(key='total_records') or 0
        
        from connection import get_connection
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Count records in import_log table
                cur.execute("SELECT COUNT(*) FROM registry_information.import_log WHERE status = 'completed'")
                db_file_count = cur.fetchone()[0]
                
                cur.execute("SELECT SUM(records_loaded) FROM registry_information.import_log WHERE status = 'completed'")
                db_line_count = cur.fetchone()[0] or 0
                
                # Get file type breakdown
                cur.execute("""
                    SELECT file_type, COUNT(*) as file_count, SUM(records_loaded) as total_lines
                    FROM registry_information.import_log 
                    WHERE status = 'completed'
                    GROUP BY file_type 
                    ORDER BY file_count DESC
                """)
                type_breakdown = cur.fetchall()
                
                # Get recent import activity
                cur.execute("""
                    SELECT status, COUNT(*) as count
                    FROM registry_information.import_log 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY status
                """)
                recent_imports = cur.fetchall()
        
        logging.info("📊 Registry Import Verification:")
        logging.info(f"  📁 Files - This run: {imported_files}, Total in DB: {db_file_count}")
        logging.info(f"  📄 Lines - This run: {total_records}, Total in DB: {db_line_count}")
        
        if type_breakdown:
            logging.info("📋 File Type Breakdown:")
            for file_type, file_count, total_lines in type_breakdown:
                logging.info(f"  {file_type}: {file_count} files, {total_lines or 0} lines")
        
        if recent_imports:
            logging.info("📈 Recent Import Activity (24h):")
            for status, count in recent_imports:
                logging.info(f"  {status.upper()}: {count} files")
        
        # Verification logic
        success = True
        if imported_files > 0:
            if db_file_count >= imported_files:
                logging.info("✅ Import verification successful")
            else:
                logging.warning("⚠️ File count mismatch in database")
                success = False
        else:
            logging.info("ℹ️ No new files imported (all were duplicates)")
        
        context['ti'].xcom_push(key='verification_success', value=success)
        
        return {
            'verification_success': success,
            'imported_files': imported_files,
            'total_records': total_records,
            'db_file_count': db_file_count,
            'db_line_count': db_line_count
        }
        
    except Exception as e:
        logging.error(f"❌ Verification error: {e}")
        raise

def cleanup_registry_files(**context):
    """Step 6: Cleanup and archive processed files with compression"""
    logging.info("🧹 Step 6: Cleanup and Archive Registry Files")
    
    try:
        downloaded_files = context['ti'].xcom_pull(key='downloaded_files') or []
        verification_success = context['ti'].xcom_pull(key='verification_success', default=False)
        
        if not downloaded_files:
            logging.info("ℹ️ No files to cleanup")
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
    """Calculate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def log_import(dag_id: str, task_id: str, run_id: str, source_group: str, 
               file_name: str, file_type: str, file_size: int, file_hash: str, 
               status: str, records_parsed: int = 0, records_loaded: int = 0, 
               error_message: str = None):
    """Log import activity to registry_information.import_log table - following switching DAG pattern"""
    try:
        from connection import get_connection
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO registry_information.import_log 
                    (dag_id, task_id, run_id, source_group, file_name, file_type, 
                         file_size, file_hash, status, records_parsed, records_loaded, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_name, file_hash) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        records_parsed = EXCLUDED.records_parsed,
                        records_loaded = EXCLUDED.records_loaded,
                        error_message = EXCLUDED.error_message,
                        created_at = NOW()
                    """, (dag_id, task_id, run_id, source_group, file_name, file_type,
                          file_size, file_hash, status, records_parsed, records_loaded, error_message))
            conn.commit()
    except Exception as e:
        logging.error(f"Failed to log import: {e}")

def log_import_with_cursor(cur, dag_id: str, task_id: str, run_id: str, source_group: str, 
                          file_name: str, file_type: str, file_size: int, file_hash: str, 
                          status: str, records_parsed: int = 0, records_loaded: int = 0, 
                          error_message: str = None):
    """Log import activity using existing cursor - avoids creating new connections"""
    try:
            cur.execute("""
                INSERT INTO registry_information.import_log 
            (dag_id, task_id, run_id, source_group, file_name, file_type, 
                 file_size, file_hash, status, records_parsed, records_loaded, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_name, file_hash) 
            DO UPDATE SET 
                status = EXCLUDED.status,
                records_parsed = EXCLUDED.records_parsed,
                records_loaded = EXCLUDED.records_loaded,
                error_message = EXCLUDED.error_message,
                created_at = NOW()
            """, (dag_id, task_id, run_id, source_group, file_name, file_type,
                  file_size, file_hash, status, records_parsed, records_loaded, error_message))
    except Exception as e:
        logging.error(f"Failed to log import with cursor: {e}")

# Create DAG
dag = DAG(
    'registry_information_files',
    default_args=default_args,
    description='Registry Information Files Import DAG - Raw Import Philosophy',
    schedule_interval='0 */2 * * *',  # Every 2 hours
    max_active_runs=1,  # Prevent multiple concurrent runs
    catchup=False,  # Explicitly disable catchup to prevent backfill
    tags=['registry', 'import', 'electricity', 'raw']
)

# Define tasks (simplified workflow following metering philosophy)
test_connection_task = PythonOperator(
    task_id='1_test_registry_connection',
    python_callable=test_registry_connection,
    dag=dag
)

discover_files_task = PythonOperator(
    task_id='2_discover_registry_files',
    python_callable=discover_registry_files,
    dag=dag
)

download_files_task = PythonOperator(
    task_id='3_download_registry_files',
    python_callable=download_registry_files,
    dag=dag
)

import_files_task = PythonOperator(
    task_id='4_import_registry_files_raw',
    python_callable=import_registry_files_raw,
    dag=dag
)

verify_import_task = PythonOperator(
    task_id='5_verify_registry_import',
    python_callable=verify_registry_import,
    dag=dag
)

cleanup_files_task = PythonOperator(
    task_id='6_cleanup_registry_files',
    python_callable=cleanup_registry_files,
    dag=dag
)

# Set task dependencies (linear workflow like metering)
test_connection_task >> discover_files_task >> download_files_task >> import_files_task >> verify_import_task >> cleanup_files_task
