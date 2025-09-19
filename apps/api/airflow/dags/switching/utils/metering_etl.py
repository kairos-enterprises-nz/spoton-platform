"""
Unified Metering ETL Module

This module provides ETL classes for different metering data providers.
It works with the ConnectionManager to handle SFTP connections and file processing.

Author: SpotOn Data Team
"""

import logging
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

# Add utils directory to path for imports
sys.path.append('/app/airflow/utils')
from connection_manager import ConnectionManager, DataSourceConfig


class BaseMeteringETL:
    """Base class for metering ETL operations"""
    
    def __init__(self, provider_name: str, data_source_config: Dict):
        self.provider_name = provider_name
        self.config = data_source_config
        self.connection_config = None
        self.sftp_client = None
        self.ssh_client = None
        
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def get_connection_config(self):
        """Get connection configuration"""
        if not self.connection_config:
            # Get configuration from ConnectionManager
            self.connection_config = ConnectionManager.get_connection_config(
                protocol=self.config['protocol'],
                prefix=self.config['prefix'],
                default_host=self.config['default_host'],
                default_port=self.config['default_port'],
                default_user=self.config['default_user']
            )
            
            # For MTRX provider, ensure we're using the correct host, port, and password
            if self.provider_name == 'MTRX':
                # Try both naming conventions: MTRX_ and METRIX_
                mtrx_host = os.getenv('METRIX_HOST') or os.getenv('MTRX_HOST')
                mtrx_port = os.getenv('METRIX_PORT') or os.getenv('MTRX_PORT')
                mtrx_user = os.getenv('METRIX_USER') or os.getenv('MTRX_USER')
                mtrx_pass = os.getenv('METRIX_PASS') or os.getenv('MTRX_PASS')
                mtrx_remote_path = os.getenv('METRIX_REMOTE_PATH') or os.getenv('MTRX_REMOTE_PATH')
                
                if mtrx_host:
                    self.connection_config['host'] = mtrx_host
                    logging.info(f"🔄 Updated MTRX host to {mtrx_host}")
                
                if mtrx_port:
                    self.connection_config['port'] = int(mtrx_port)
                    logging.info(f"🔄 Updated MTRX port to {mtrx_port}")
                
                if mtrx_user:
                    self.connection_config['user'] = mtrx_user
                    logging.info(f"🔄 Updated MTRX user to {mtrx_user}")
                
                if mtrx_pass:
                    self.connection_config['password'] = mtrx_pass
                    logging.info("🔄 Updated MTRX password from environment")
                
                # Set remote path from environment if available
                if mtrx_remote_path:
                    self.connection_config['remote_path'] = mtrx_remote_path
                    logging.info(f"🔄 Updated MTRX remote path to {mtrx_remote_path}")
        
        return self.connection_config
    
    def discover_files(self) -> List[Dict]:
        """Discover files on remote server"""
        config = self.get_connection_config()
        
        try:
            # Get file pattern from config
            file_pattern = self.config.get('file_pattern', r'.*')
            
            # Get remote path from config, with fallback to default
            remote_path = config.get('remote_path', '/')
            
            logging.info(f"📁 Discovering files for {self.provider_name} at {config['host']}:{config['port']}{remote_path}")
            
            # List files on remote server
            try:
                files = ConnectionManager.list_remote_files(config, file_pattern)
            except ConnectionError as e:
                logging.error(f"❌ Connection error during file discovery: {e}")
                return []
            except Exception as e:
                logging.error(f"❌ Error during file discovery: {e}")
                return []
            
            # Format results
            results = []
            for filename in files:
                results.append({
                    'filename': filename,
                    'provider': self.provider_name,
                    'remote_path': remote_path
                })
            
            logging.info(f"📁 Discovered {len(results)} files for {self.provider_name}")
            return results
            
        except Exception as e:
            logging.error(f"❌ File discovery error: {e}")
            return []
    
    def download_file(self, file_info: Dict) -> Optional[Path]:
        """Download a file from remote server"""
        config = self.get_connection_config()
        filename = file_info['filename']
        
        # Create local directory
        local_dir = Path(f"/app/data/imports/electricity/metering/{self.provider_name.lower()}")
        local_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = local_dir / filename
        
        try:
            if ConnectionManager.download_file(config, filename, local_path):
                logging.info(f"✅ Downloaded {filename} to {local_path}")
                return local_path
            else:
                logging.error(f"❌ Failed to download {filename}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Download error for {filename}: {e}")
            return None
    
    def get_timescale_connection(self):
        """Get TimescaleDB connection"""
        # Import connection utility
        import sys
        sys.path.append('/app/airflow/utils')
        from connection import get_connection
        
        return get_connection()
    
    def close(self):
        """Close connections"""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def parse_drr_file(self, file_path: str) -> int:
        """Parse Daily Register Reads file - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement parse_drr_file")
    
    def parse_hhr_file(self, file_path: str) -> int:
        """Parse Half-Hourly Reads file - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement parse_hhr_file")
    
    def load_drr_to_database(self, file_path: str) -> int:
        """Load Daily Register Reads to database - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement load_drr_to_database")
    
    def load_hhr_to_database(self, file_path: str) -> int:
        """Load Half-Hourly Reads to database - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement load_hhr_to_database")
    
    def count_drr_records_in_db(self) -> int:
        """Count DRR records in database"""
        try:
            with self.get_timescale_connection() as conn:
                with conn.cursor() as cur:
                    table_name = f"metering.{self.provider_name.lower()}_drr"
                    cur.execute(f"""
                        SELECT COUNT(*) FROM {table_name}
                        WHERE imported_at >= CURRENT_DATE
                    """)
                    return cur.fetchone()[0]
        except Exception as e:
            logging.error(f"❌ Error counting DRR records: {e}")
            return 0
    
    def count_hhr_records_in_db(self) -> int:
        """Count HHR records in database"""
        try:
            with self.get_timescale_connection() as conn:
                with conn.cursor() as cur:
                    table_name = f"metering.{self.provider_name.lower()}_hhr"
                    cur.execute(f"""
                        SELECT COUNT(*) FROM {table_name}
                        WHERE imported_at >= CURRENT_DATE
                    """)
                    return cur.fetchone()[0]
        except Exception as e:
            logging.error(f"❌ Error counting HHR records: {e}")
            return 0
    
    def archive_file(self, file_path: str) -> bool:
        """Archive processed file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False
            
            # Create archive directory
            archive_dir = source_path.parent / 'archive'
            archive_dir.mkdir(exist_ok=True)
            
            # Move file to archive
            archive_path = archive_dir / source_path.name
            source_path.rename(archive_path)
            
            logging.info(f"📦 Archived {source_path.name}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Archive error: {e}")
            return False


class BCCIMetering(BaseMeteringETL):
    """BlueCurrent Commercial & Industrial Metering ETL"""
    
    def __init__(self):
        super().__init__('BCCI', DataSourceConfig.BLUECURRENT_COMMERCIAL)
    
    def parse_drr_file(self, file_path: str) -> int:
        """Parse BCCI Daily Register Reads CSV file"""
        records = 0
        try:
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('ICP') and row.get('ReadDate'):
                        records += 1
            logging.info(f"📊 Parsed {records} DRR records from {Path(file_path).name}")
            return records
        except Exception as e:
            logging.error(f"❌ Error parsing DRR file {file_path}: {e}")
            return 0
    
    def parse_hhr_file(self, file_path: str) -> int:
        """Parse BCCI Half-Hourly Reads CSV file"""
        records = 0
        try:
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('ICP') and row.get('ReadDateTime'):
                        records += 1
            logging.info(f"📈 Parsed {records} HHR records from {Path(file_path).name}")
            return records
        except Exception as e:
            logging.error(f"❌ Error parsing HHR file {file_path}: {e}")
            return 0
    
    def load_drr_to_database(self, file_path: str) -> int:
        """Load BCCI DRR data to TimescaleDB"""
        return 0  # Placeholder implementation
    
    def load_hhr_to_database(self, file_path: str) -> int:
        """Load BCCI HHR data to TimescaleDB"""
        return 0  # Placeholder implementation


class IHUBMetering(BaseMeteringETL):
    """IntelliHub Metering ETL"""
    
    def __init__(self):
        super().__init__('IHUB', DataSourceConfig.INTELLIHUB)
    
    def parse_drr_file(self, file_path: str) -> int:
        """Parse IHUB Daily Register Reads file"""
        return 0  # Placeholder
    
    def parse_hhr_file(self, file_path: str) -> int:
        """Parse IHUB Half-Hourly Reads file"""
        return 0  # Placeholder
    
    def load_drr_to_database(self, file_path: str) -> int:
        """Load IHUB DRR data to TimescaleDB"""
        return 0  # Placeholder
    
    def load_hhr_to_database(self, file_path: str) -> int:
        """Load IHUB HHR data to TimescaleDB"""
        return 0  # Placeholder


class MTRXMetering(BaseMeteringETL):
    """Metrix Metering ETL"""
    
    def __init__(self):
        super().__init__('MTRX', DataSourceConfig.METRIX)
    
    def download_file(self, file_info, local_path=None):
        """
        Download a file from MTRX SFTP server
        
        This method handles both calling formats:
        1. download_file(file_info_dict) - from BaseMeteringETL
        2. download_file(filename, local_path) - from metering_mtrx.py
        """
        config = self.get_connection_config()
        
        # Handle both calling formats
        if isinstance(file_info, dict):
            # Called as download_file(file_info_dict) from discover_files
            filename = file_info['filename']
            
            # Create local directory if not provided
            if local_path is None:
                local_dir = Path(f"/app/data/imports/electricity/metering/{self.provider_name.lower()}")
                local_dir.mkdir(parents=True, exist_ok=True)
                local_path = local_dir / filename
            else:
                local_path = Path(local_path) / filename
        else:
            # Called as download_file(filename, local_path) from metering_mtrx.py
            filename = file_info
            local_path = Path(local_path)
            
        try:
            result = ConnectionManager.download_file(config, filename, local_path)
            if result:
                logging.info(f"✅ Downloaded {filename} to {local_path}")
                return local_path
            else:
                logging.error(f"❌ Failed to download {filename}")
                return None
        except Exception as e:
            logging.error(f"❌ Download error for {filename}: {e}")
            return None
    
    def parse_drr(self, file_path: str) -> List[Dict]:
        """Parse MTRX Daily Register Reads file - called by metering_mtrx.py"""
        logging.info(f"📊 Parsing MTRX DRR file: {file_path}")
        records = []
        
        try:
            # Determine file format based on extension
            if file_path.lower().endswith('.xml'):
                # XML format
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Parse MTRX XML structure: RESPONSE > ACCOUNT > PREMISE > ICP > METER > READINGS > READING
                # Use nested loops to access the hierarchy properly
                for icp in root.findall('.//ICP'):
                    icp_id = icp.get('ID', '')
                    
                    for meter in icp.findall('.//METER'):
                        meter_serial = meter.get('SERIAL', '')
                        
                        for reading in meter.findall('.//READING'):
                            timestamp = reading.get('TIMESTAMP', '')  # 2024-02-29T23:59:59+13
                            value_element = reading.find('VALUE')
                            register_reading = value_element.text if value_element is not None else ''
                            
                            record = {
                                'icp_identifier': icp_id,
                                'meter_serial_number': meter_serial,
                                'reading_date': timestamp,
                                'reading_time': '',  # Time is included in timestamp
                                'register_reading': register_reading,
                                'daylight_savings': 'N',  # Default
                                'customer_location_id': '',  # Not in this XML format
                                'meter_id': meter_serial  # Use meter serial as meter ID
                            }
                            records.append(record)
                
            else:
                # CSV format
                with open(file_path, 'r') as csvfile:
                    # Try to detect if file has headers
                    sample = csvfile.read(4096)
                    csvfile.seek(0)
                    
                    has_header = csv.Sniffer().has_header(sample)
                    
                    if has_header:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            # Map CSV fields to our standard format
                            record = {
                                'icp_identifier': row.get('ICP', ''),
                                'meter_serial_number': row.get('MeterSerial', row.get('Meter', '')),
                                'reading_date': row.get('ReadDate', row.get('Date', '')),
                                'reading_time': row.get('ReadTime', row.get('Time', '')),
                                'register_reading': row.get('Reading', row.get('RegisterReading', '')),
                                'daylight_savings': row.get('DaylightSavings', 'N'),
                                'customer_location_id': row.get('CustomerLocationId', row.get('LocationId', '')),
                                'meter_id': row.get('MeterId', row.get('Meter', ''))
                            }
                            records.append(record)
                    else:
                        # No header, assume fixed format
                        reader = csv.reader(csvfile)
                        for row in reader:
                            if len(row) >= 5:  # Minimum fields needed
                                record = {
                                    'icp_identifier': row[0],
                                    'meter_serial_number': row[1],
                                    'reading_date': row[2],
                                    'reading_time': row[3] if len(row) > 3 else '',
                                    'register_reading': row[4] if len(row) > 4 else '',
                                    'daylight_savings': row[5] if len(row) > 5 else 'N',
                                    'customer_location_id': row[6] if len(row) > 6 else '',
                                    'meter_id': row[7] if len(row) > 7 else ''
                                }
                                records.append(record)
            
            logging.info(f"✅ Parsed {len(records)} DRR records from {Path(file_path).name}")
            return records
            
        except Exception as e:
            logging.error(f"❌ Error parsing DRR file {file_path}: {e}")
            return []
    
    def parse_hhr(self, file_path: str) -> List[Dict]:
        """Parse MTRX Half-Hourly Reads file - called by metering_mtrx.py"""
        logging.info(f"📈 Parsing MTRX HHR file: {file_path}")
        records = []
        
        try:
            # Determine file format based on extension
            if file_path.lower().endswith('.xml'):
                # XML format
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                for reading in root.findall('.//IntervalReading'):
                    record = {
                        'icp_identifier': reading.find('ICP').text if reading.find('ICP') is not None else '',
                        'meter_serial_number': reading.find('MeterSerial').text if reading.find('MeterSerial') is not None else '',
                        'reading_date': reading.find('ReadDate').text if reading.find('ReadDate') is not None else '',
                        'trading_period': reading.find('Period').text if reading.find('Period') is not None else '',
                        'kwh_reading': reading.find('Reading').text if reading.find('Reading') is not None else '',
                        'reading_status_flag': reading.find('Status').text if reading.find('Status') is not None else ''
                    }
                    records.append(record)
                
            else:
                # CSV format - MTRX specific format
                with open(file_path, 'r') as csvfile:
                    reader = csv.reader(csvfile)
                    
                    for line_num, row in enumerate(reader, 1):
                        # Skip the header line (first line with 7 fields like "INITIAL,1,MTRX,YESP,NZDT,1666,1 of 1")
                        if line_num == 1 and len(row) == 7:
                            continue
                            
                        # Process data lines (should have 13 fields)
                        if len(row) >= 13:
                            # MTRX CSV format: ICP,Meter,Stream,Channel,RCC,Flow,Register,StartTime,EndTime,Reading,Status,Unit,Flag
                            try:
                                # Extract start time for date calculation
                                start_time = row[7]  # 2024-02-29T00:00:00+13
                                
                                # Calculate trading period from start time
                                # Parse the time part to get trading period (1-48 for half-hourly)
                                if 'T' in start_time:
                                    time_part = start_time.split('T')[1].split('+')[0]  # Get HH:MM:SS part
                                    hour, minute = map(int, time_part.split(':')[:2])
                                    trading_period = (hour * 2) + (1 if minute == 0 else 2)
                                else:
                                    trading_period = 1
                                
                                record = {
                                    'icp_identifier': row[0],           # ICP
                                    'meter_serial_number': row[1],      # Meter Serial
                                    'reading_date': start_time,         # Use start time as reading date
                                    'trading_period': str(trading_period),
                                    'kwh_reading': row[9],              # Reading value
                                    'reading_status_flag': row[10]      # Status
                                }
                                records.append(record)
                            except (ValueError, IndexError) as e:
                                logging.warning(f"⚠️ Error parsing line {line_num}: {e}")
                                continue
                        elif len(row) > 0:  # Skip empty lines but log unexpected formats
                            logging.warning(f"⚠️ Unexpected row format at line {line_num}: {len(row)} fields, expected 13")
            
            logging.info(f"✅ Parsed {len(records)} HHR records from {Path(file_path).name}")
            return records
            
        except Exception as e:
            logging.error(f"❌ Error parsing HHR file {file_path}: {e}")
            return []
    
    def parse_drr_file(self, file_path: str) -> int:
        """Parse MTRX Daily Register Reads file - returns count for compatibility"""
        records = self.parse_drr(file_path)
        return len(records)
    
    def parse_hhr_file(self, file_path: str) -> int:
        """Parse MTRX Half-Hourly Reads file - returns count for compatibility"""
        records = self.parse_hhr(file_path)
        return len(records)
    
    def load_drr_to_database(self, file_path: str) -> int:
        """Load MTRX DRR data to TimescaleDB"""
        records = self.parse_drr(file_path)
        if not records:
            return 0
            
        loaded_count = 0
        try:
            with self.get_timescale_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare data for batch insert
                    data_to_insert = []
                    # Use a set to track unique records and avoid duplicates
                    seen_records = set()
                    
                    for record in records:
                        try:
                            # Parse date and time from MTRX XML format
                            read_date_str = record.get('reading_date', '')
                            
                            # Handle MTRX XML timestamp format: 2024-02-29T23:59:59+13
                            try:
                                if 'T' in read_date_str:
                                    # Handle timezone info: 2024-02-29T23:59:59+13
                                    if '+' in read_date_str:
                                        read_date_str = read_date_str.split('+')[0]
                                    elif '-' in read_date_str.split('T')[1]:  # Handle negative timezone
                                        read_date_str = read_date_str.rsplit('-', 1)[0]
                                    read_datetime = datetime.fromisoformat(read_date_str)
                                else:
                                    # Fallback parsing
                                    read_datetime = datetime.now()
                                    logging.warning(f"⚠️ Unexpected date format: {read_date_str}")
                            except ValueError as e:
                                logging.warning(f"⚠️ Error parsing datetime {read_date_str}: {e}")
                                read_datetime = datetime.now()
                            
                            # Create unique key to avoid duplicates
                            unique_key = (
                                record.get('icp_identifier', ''),
                                record.get('meter_serial_number', ''),
                                read_datetime
                            )
                            
                            # Skip if we've already processed this record
                            if unique_key in seen_records:
                                continue
                            seen_records.add(unique_key)
                            
                            # Prepare row for insertion
                            row = (
                                record.get('icp_identifier', ''),
                                record.get('meter_serial_number', ''),
                                read_datetime,
                                float(record.get('register_reading', 0)),
                                record.get('daylight_savings', 'N') in ('Y', 'y', '1', 'True', 'true'),
                                record.get('customer_location_id', ''),
                                record.get('meter_id', ''),
                                Path(file_path).name,
                                'MTRX'
                            )
                            data_to_insert.append(row)
                        except Exception as e:
                            logging.warning(f"⚠️ Error preparing DRR record: {e}")
                            continue
                    
                    # Batch insert using execute_values
                    if data_to_insert:
                        execute_values(
                            cur,
                            """
                            INSERT INTO metering.mtrx_drr
                            (icp_identifier, meter_serial_number, reading_datetime, register_reading,
                             daylight_savings, customer_location_id, meter_id, filename, provider)
                            VALUES %s
                            ON CONFLICT (icp_identifier, meter_serial_number, reading_datetime)
                            DO UPDATE SET
                                register_reading = EXCLUDED.register_reading,
                                imported_at = NOW()
                            """,
                            data_to_insert
                        )
                        loaded_count = len(data_to_insert)
                        conn.commit()
                        
            logging.info(f"💾 Loaded {loaded_count} DRR records to database from {Path(file_path).name}")
            return loaded_count
            
        except Exception as e:
            logging.error(f"❌ Database load error for DRR: {e}")
            return 0
    
    def load_hhr_to_database(self, file_path: str) -> int:
        """Load MTRX HHR data to TimescaleDB"""
        records = self.parse_hhr(file_path)
        if not records:
            return 0
            
        loaded_count = 0
        try:
            with self.get_timescale_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare data for batch insert
                    data_to_insert = []
                    # Use a set to track unique records and avoid duplicates
                    seen_records = set()
                    
                    for record in records:
                        try:
                            # Use the already-parsed datetime from parse_hhr
                            read_date_str = record.get('reading_date', '')
                            trading_period = record.get('trading_period', '1')
                            
                            # Parse the ISO datetime from the record
                            try:
                                if 'T' in read_date_str:
                                    # Handle timezone info: 2024-02-29T00:00:00+13
                                    if '+' in read_date_str:
                                        read_date_str = read_date_str.split('+')[0]
                                    elif '-' in read_date_str.split('T')[1]:  # Handle negative timezone
                                        read_date_str = read_date_str.rsplit('-', 1)[0]
                                    read_datetime = datetime.fromisoformat(read_date_str)
                                else:
                                    # Fallback parsing
                                    read_datetime = datetime.now()
                                    logging.warning(f"⚠️ Unexpected date format: {read_date_str}")
                            except ValueError as e:
                                logging.warning(f"⚠️ Error parsing datetime {read_date_str}: {e}")
                                read_datetime = datetime.now()
                            
                            # Create unique key to avoid duplicates
                            unique_key = (
                                record.get('icp_identifier', ''),
                                record.get('meter_serial_number', ''),
                                read_datetime
                            )
                            
                            # Skip if we've already processed this record
                            if unique_key in seen_records:
                                continue
                            seen_records.add(unique_key)
                            
                            # Prepare row for insertion
                            row = (
                                record.get('icp_identifier', ''),
                                record.get('meter_serial_number', ''),
                                read_datetime,
                                int(trading_period) if trading_period.isdigit() else 0,
                                float(record.get('kwh_reading', 0)),
                                record.get('reading_status_flag', ''),
                                Path(file_path).name,
                                'MTRX'
                            )
                            data_to_insert.append(row)
                        except Exception as e:
                            logging.warning(f"⚠️ Error preparing HHR record: {e}")
                            continue
                    
                    # Batch insert using execute_values
                    if data_to_insert:
                        execute_values(
                            cur,
                            """
                            INSERT INTO metering.mtrx_hhr
                            (icp_identifier, meter_serial_number, reading_datetime, trading_period,
                             kwh_reading, status_flag, filename, provider)
                            VALUES %s
                            ON CONFLICT (icp_identifier, meter_serial_number, reading_datetime)
                            DO UPDATE SET
                                kwh_reading = EXCLUDED.kwh_reading,
                                imported_at = NOW()
                            """,
                            data_to_insert
                        )
                        loaded_count = len(data_to_insert)
                        conn.commit()
                        
            logging.info(f"💾 Loaded {loaded_count} HHR records to database from {Path(file_path).name}")
            return loaded_count
            
        except Exception as e:
            logging.error(f"❌ Database load error for HHR: {e}")
            return 0


class SMCOMetering(BaseMeteringETL):
    """SmartCo Metering ETL"""
    
    def __init__(self):
        super().__init__('SMCO', DataSourceConfig.SMARTCO)
    
    def parse_drr_file(self, file_path: str) -> int:
        """Parse SMCO Daily Register Reads file"""
        return 0  # Placeholder
    
    def parse_hhr_file(self, file_path: str) -> int:
        """Parse SMCO Half-Hourly Reads file"""
        return 0  # Placeholder
    
    def load_drr_to_database(self, file_path: str) -> int:
        """Load SMCO DRR data to TimescaleDB"""
        return 0  # Placeholder
    
    def load_hhr_to_database(self, file_path: str) -> int:
        """Load SMCO HHR data to TimescaleDB"""
        return 0  # Placeholder


# Wrapper class for backward compatibility
class SFTPDiscovery:
    """Wrapper class for backward compatibility with existing BCMM DAG"""
    
    def __init__(self, connection_config):
        self.config = self._normalize_config(connection_config)
        self.sftp_client = None
        self.ssh_client = None
    
    def _normalize_config(self, config):
        """Normalize config format for ConnectionManager compatibility"""
        normalized = config.copy()
        
        # Map different field names to what ConnectionManager expects
        if 'username' in config and 'user' not in config:
            normalized['user'] = config['username']
        elif 'user' in config and 'username' not in config:
            normalized['username'] = config['user']
            
        return normalized
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def test_connection(self):
        """Test connection using the connection manager"""
        try:
            return ConnectionManager.test_connection(self.config)
        except Exception as e:
            logging.error(f"❌ Connection test error: {e}")
            return False
    
    def discover_files(self):
        """Discover files using the connection manager"""
        try:
            # Look for CSV, XML, and NEW files (HERM format)
            remote_files = ConnectionManager.list_remote_files(self.config, r'^.*\.(csv|xml|new)$')
            return [{'filename': f, 'size': 0} for f in remote_files]
        except Exception as e:
            logging.error(f"❌ File discovery error: {e}")
            return []
    
    def download_file(self, file_info, local_path):
        """Download a file"""
        try:
            return ConnectionManager.download_file(self.config, file_info['filename'], local_path)
        except Exception as e:
            logging.error(f"❌ Download error: {e}")
            return False
    
    def close(self):
        """Close connections"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
