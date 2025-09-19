"""
Universal HHR Normalization DAG - Normalize ALL MEP HHR data into interval_reads_raw

This DAG processes HHR data from all MEP providers and normalizes it into the 
metering_processed.interval_reads_raw table with proper ICP → Meter → Register hierarchy.

MEP Providers Supported:
- BCMM: Wide format (48 intervals per row)
- SmartCo: Wide format (48 intervals per row)  
- FCLM: Wide format (48 intervals per row)
- IntelliHub: Long format (1 interval per row)
- MTRX: Long format (1 interval per row)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging
import json
import uuid
from typing import Dict, List, Tuple, Optional

# Default arguments for the DAG
default_args = {
    'owner': 'data-transform',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# Create the DAG
dag = DAG(
    'hhr_data_normalization',
    default_args=default_args,
    description='Normalize ALL MEP HHR data into interval_reads_raw',
    schedule_interval='0 */6 * * *',  # Every 6 hours (0, 6, 12, 18)
    max_active_runs=1,
    catchup=False,  # Prevent backfill runs like other metering DAGs
    tags=['metering', 'normalization', 'hhr'],
)

class UniversalHHRNormalizer:
    """Universal normalizer for all MEP HHR data formats"""
    
    def __init__(self):
        self.pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        
    def get_unprocessed_wide_format_data(self, mep_provider: str, table_name: str) -> Tuple[List, Dict]:
        """Get unprocessed wide format data (BCMM, SmartCo, FCLM)"""
        
        # Map MEP-specific column names
        column_mappings = {
            'BCMM': {
                'meter_field': 'bcmm_number',
                'serial_field': 'bcmm_serial_number',
                'element_field': 'element',
                'register_field': 'register_number',
                'register_map_field': 'register_map',
                'date_field': 'reading_date',
                'validation_field': 'validation_flag',
                'dst_field': 'daylight_savings_adjusted',
                'midnight_field': 'midnight_read_value',
                'file_field': 'file_name',
                'flow_direction_field': None,  # Flow direction no longer stored in extra fields
                'register_content_field': 'register_number',  # Register content code
                'channel_field': 'register_map'  # Channel number
            },
            'SmartCo': {
                'meter_field': 'smco_number',
                'serial_field': 'smco_serial_number',
                'element_field': 'element',
                'register_field': 'register_number',
                'register_map_field': 'register_map',
                'date_field': 'reading_date',
                'validation_field': 'validation_flag',
                'dst_field': 'daylight_savings_adjusted',
                'midnight_field': 'midnight_read_value',
                'file_field': 'file_name',
                'flow_direction_field': None,  # Flow direction no longer stored in extra fields
                'register_content_field': 'register_number',  # Register content code
                'channel_field': 'register_map'  # Channel number
            },
            'FCLM': {
                'meter_field': 'meter_serial',
                'serial_field': 'meter_serial',
                'element_field': 'reading_type',
                'register_field': 'register_code',
                'register_map_field': 'channel',
                'date_field': 'read_date',
                'validation_field': 'read_type',
                'dst_field': None,  # FCLM doesn't have DST field
                'midnight_field': 'midnight_read',
                'file_field': 'filename',  # FCLM uses 'filename' not 'file_name'
                'flow_direction_field': None,  # Flow direction no longer stored in extra fields
                'register_content_field': 'register_code',  # Register content code
                'channel_field': 'channel'  # Channel number
            }
        }
        
        mapping = column_mappings.get(mep_provider, column_mappings['BCMM'])
        
        # Build column list
        columns = [
            'id', 'icp', 
            mapping['meter_field'], 
            mapping['serial_field'], 
            mapping['element_field'], 
            mapping['register_field'],
            mapping['register_map_field'], 
            mapping['date_field'], 
            mapping['validation_field'],
            mapping['midnight_field'],
            mapping['file_field']
        ]
        
        # Add DST field if available
        if mapping['dst_field']:
            columns.append(mapping['dst_field'])
            
        # Add flow direction field (extra_field_1 or extra_field_2)
        if mapping.get('flow_direction_field'):
            columns.append(mapping['flow_direction_field'])
            
        # Add interval columns (1-50 for standardized schema)
        interval_columns = [f'interval_{i:02d}' for i in range(1, 51)]
        columns.extend(interval_columns)
        
        query = f"""
        SELECT {', '.join(columns)}
        FROM metering_raw.{table_name} h
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.interval_reads_raw p
            WHERE p.connection_id = h.icp 
            AND DATE(p.timestamp) = h.{mapping['date_field']}::date
            AND p.source = '{mep_provider}'
            AND p.register_code = h.{mapping['register_field']}
        )
        AND h.imported_at >= NOW() - INTERVAL '30 days'
        ORDER BY h.{mapping['date_field']} DESC, h.id
        LIMIT 1000
        """
        
        records = self.pg_hook.get_records(query)
        logging.info(f"Found {len(records)} unprocessed {mep_provider} records")
        
        return records, mapping
    
    def get_unprocessed_long_format_data(self, mep_provider: str, table_name: str) -> List:
        """Get unprocessed long format data (IntelliHub, MTRX)"""
        
        query = f"""
        SELECT id, icp, meter_serial, register, stream, register_type, status,
               interval_number, start_datetime, end_datetime, reading, quality, 
               unit, flag, filename, imported_at
        FROM metering_raw.{table_name} h
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.interval_reads_raw p
            WHERE p.connection_id = h.icp 
            AND p.timestamp = h.start_datetime
            AND p.source = '{mep_provider}'
            AND p.register_code = h.register
        )
        AND h.imported_at >= NOW() - INTERVAL '30 days'
        ORDER BY h.start_datetime DESC, h.id
        LIMIT 10000
        """
        
        records = self.pg_hook.get_records(query)
        logging.info(f"Found {len(records)} unprocessed {mep_provider} records")
        
        return records
    
    def get_unprocessed_eiep3_data(self) -> List:
        """Get unprocessed EIEP3 data from bluecurrent_eiep3 table"""
        
        query = """
        SELECT id, icp_identifier, data_stream_identifier, reading_type, 
               date_field, trading_period, active_energy, energy_flow_direction,
               data_stream_type, file_name, imported_at
        FROM metering_raw.bluecurrent_eiep3 h
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.interval_reads_raw p
            WHERE p.connection_id = h.icp_identifier 
            AND p.day = TO_DATE(h.date_field, 'DD/MM/YYYY')
            AND p.trading_period = h.trading_period
            AND p.source = 'EIEP3'
            AND p.register_code = h.reading_type
            AND p.flow_direction = h.energy_flow_direction
        )
        AND h.imported_at >= NOW() - INTERVAL '30 days'
        ORDER BY h.date_field DESC, h.trading_period, h.id
        LIMIT 10000
        """
        
        records = self.pg_hook.get_records(query)
        logging.info(f"Found {len(records)} unprocessed EIEP3 records")
        
        return records
    
    def normalize_wide_format_record(self, record: Tuple, mapping: Dict, mep_provider: str, run_id: str) -> List[Dict]:
        """Normalize a single wide format record into interval readings"""
        
        # Extract basic fields
        id_val = record[0]
        icp = record[1]
        meter_number = record[2]
        meter_serial = record[3]
        element_type = record[4]
        register_code = record[5]
        register_map = record[6]
        reading_date = record[7]
        validation_flag = record[8]
        midnight_read = record[9]
        file_name = record[10]
        
        # Handle DST field if present
        dst_adjusted = False
        current_idx = 11
        if mapping['dst_field']:
            dst_adjusted = record[current_idx] == 'Y' if record[current_idx] else False
            current_idx += 1
        
        # Initialize flow_direction (will be set based on MEP provider logic below)
        flow_direction = None
            
        # For register_content_code and meter_channel_number, we extract from existing fields
        # For BCMM/SmartCo: register_map contains the actual register content code (e.g., EG24)
        # For FCLM: register_code contains the register content code (e.g., EG24)
        if mep_provider in ['BCMM', 'SmartCo']:
            register_content_code = register_map  # register_map contains the actual register content (EG24, UN24, etc.)
            meter_channel_number = register_code  # register_code is the channel number (001, 002, 003)
        else:  # FCLM and others
            register_content_code = register_code  # register_code contains the register content
            meter_channel_number = register_map    # register_map is the channel number
        
        # Fix flow direction logic for HERM files (BCMM, SmartCo, FCLM)
        # Flow direction is not in the MEP files, so we determine it from the register code
        if mep_provider in ['BCMM', 'SmartCo', 'FCLM']:
            # For HERM files: EG register = "I" (Import), otherwise = "X" (Export)
            # For BCMM/SmartCo: Check register_map field for EG
            # For FCLM: Check register_code field for EG
            if mep_provider in ['BCMM', 'SmartCo']:
                # Check register_map field for EG
                if register_map and 'EG' in register_map.upper():
                    flow_direction = 'I'  # Import
                else:
                    flow_direction = 'X'  # Export
                logging.info(f"[RUN_ID:{run_id}] {mep_provider} flow direction determined: register_map={register_map} → flow_direction={flow_direction}")
            else:  # FCLM
                # Check register_code field for EG
                if register_code and 'EG' in register_code.upper():
                    flow_direction = 'I'  # Import
                else:
                    flow_direction = 'X'  # Export
                logging.info(f"[RUN_ID:{run_id}] FCLM flow direction determined: register_code={register_code} → flow_direction={flow_direction}")
        else:
            # For other MEPs, try to extract from extra_field columns
            if mapping.get('flow_direction_field'):
                flow_direction = record[current_idx] if current_idx < len(record) else None
                current_idx += 1
            else:
                flow_direction = None
        
        # Validate and clean flow_direction
        if flow_direction:
            flow_direction = flow_direction.strip().upper()
            if flow_direction not in ['X', 'I']:
                logging.warning(f"[RUN_ID:{run_id}] Invalid flow_direction '{flow_direction}' for {mep_provider} ICP {icp}, setting to None")
                flow_direction = None
        
        # Validate register_content_code format (should be alphanumeric)
        if register_content_code:
            register_content_code = register_content_code.strip()
            if not register_content_code.replace('+', '').replace('-', '').isalnum():
                logging.warning(f"[RUN_ID:{run_id}] Unusual register_content_code format '{register_content_code}' for {mep_provider} ICP {icp}")
        
        # Validate meter_channel_number format (should be numeric or alphanumeric)
        if meter_channel_number:
            meter_channel_number = meter_channel_number.strip()
            if not meter_channel_number.replace('.', '').isalnum():
                logging.warning(f"[RUN_ID:{run_id}] Unusual meter_channel_number format '{meter_channel_number}' for {mep_provider} ICP {icp}")
        
        # Parse reading date with multiple format support BEFORE DST checks
        read_date = None  # Initialize to avoid UnboundLocalError
        try:
            if isinstance(reading_date, str):
                # Try YYYY-MM-DD format first
                try:
                    read_date = datetime.strptime(reading_date, '%Y-%m-%d').date()
                except ValueError:
                    # Try YYYYMMDD format (FCLM uses this)
                    read_date = datetime.strptime(reading_date, '%Y%m%d').date()
            else:
                read_date = reading_date
        except Exception as e:
            error_msg = f"[RUN_ID:{run_id}] CRITICAL: Invalid date format for {mep_provider} record {id_val}, ICP {icp}: {reading_date} - {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Extract interval values (48 intervals) - start after all metadata fields
        interval_start_idx = current_idx
        
        # Determine the number of intervals to process based on DST
        # NOTE: Function names are backwards - _is_dst_spring_day checks September, _is_dst_autumn_day checks April
        is_dst_spring = self._is_dst_autumn_day(read_date) if read_date else False  # April = Spring DST (clocks forward)
        is_dst_autumn = self._is_dst_spring_day(read_date) if read_date else False  # September = Autumn DST (clocks back)
        
        if is_dst_spring and dst_adjusted:
            # Spring DST: only 46 intervals (skip 2:00-2:59 AM), intervals 49-50 are NULL
            expected_intervals = 46
            logging.info(f"[RUN_ID:{run_id}] DST Spring day detected for {mep_provider} ICP {icp}, processing {expected_intervals} intervals")
        elif is_dst_autumn and dst_adjusted:
            # Autumn DST: 50 intervals (repeat 2:00-2:59 AM), use intervals 49-50
            expected_intervals = 50
            logging.info(f"[RUN_ID:{run_id}] DST Autumn day detected for {mep_provider} ICP {icp}, processing {expected_intervals} intervals")
        else:
            # Standard day: 48 intervals, intervals 49-50 are NULL
            expected_intervals = 48
        
        # Extract interval values with proper DST handling
        # Always extract up to 50 intervals from the record (intervals 1-50)
        available_intervals = record[interval_start_idx:interval_start_idx + 50]
        
        # Map intervals correctly based on DST status
        interval_values = [None] * 50  # Initialize all 50 intervals as NULL
        
        if is_dst_spring and dst_adjusted:
            # Spring DST: Skip 2:00-3:00 AM (intervals 47-48), map 1-46 normally, 49-50 stay NULL
            for i in range(46):  # intervals 1-46
                if i < len(available_intervals):
                    interval_values[i] = available_intervals[i]
            # Intervals 47-48 (2:00-3:00 AM) are skipped due to DST spring forward
            # Intervals 49-50 remain NULL for spring DST
            logging.info(f"[RUN_ID:{run_id}] Spring DST: Using intervals 1-46, skipping 47-48 (2:00-3:00 AM), 49-50 are NULL")
            
        elif is_dst_autumn and dst_adjusted:
            # Autumn DST: Use intervals 1-48 normally, map repeated 2:00-3:00 AM to intervals 49-50
            for i in range(48):  # intervals 1-48
                if i < len(available_intervals):
                    interval_values[i] = available_intervals[i]
            # Map the repeated 2:00-3:00 AM readings (originally intervals 47-48) to intervals 49-50
            if len(available_intervals) >= 50:
                interval_values[48] = available_intervals[48]  # interval_49 = repeated 2:00-2:30 AM
                interval_values[49] = available_intervals[49]  # interval_50 = repeated 2:30-3:00 AM
            logging.info(f"[RUN_ID:{run_id}] Autumn DST: Using intervals 1-48, repeated 2:00-3:00 AM in intervals 49-50")
            
        else:
            # Standard day: Use intervals 1-48, intervals 49-50 remain NULL
            for i in range(48):  # intervals 1-48
                if i < len(available_intervals):
                    interval_values[i] = available_intervals[i]
            # Intervals 49-50 remain NULL for standard days
            logging.info(f"[RUN_ID:{run_id}] Standard day: Using intervals 1-48, 49-50 are NULL")
        
        # Log midnight read value for audit purposes but don't process it
        if midnight_read is not None and str(midnight_read).strip():
            logging.info(f"[RUN_ID:{run_id}] Midnight read value {midnight_read} found for {mep_provider} ICP {icp} but excluded from interval processing")
        
        interval_inserts = []
        
        # Track quality flag mapping statistics
        quality_flag_mapping = {
            'P': 0, 'A': 0, 'M': 0, 'E': 0, 'S': 0,
            'empty_values': 0, 'missing_flags': 0
        }
        
        # Log processing summary for this record
        non_null_count = sum(1 for v in interval_values if v is not None and str(v).strip() != '')
        logging.info(f"[RUN_ID:{run_id}] Processing {mep_provider} ICP {icp} with {non_null_count} non-null intervals out of 50 total")
        logging.info(f"[RUN_ID:{run_id}] Flow direction: {flow_direction}, Register: {register_content_code}, Channel: {meter_channel_number}")
        
        for interval_num, interval_value in enumerate(interval_values, 1):
            # Process all 50 intervals, including NULL values for proper database structure
            # Skip only if interval_num > 50 (shouldn't happen with our fixed array)
            if interval_num > 50:
                logging.warning(f"[RUN_ID:{run_id}] Unexpected interval {interval_num} for {mep_provider} ICP {icp}, skipping")
                break
            
            # Calculate trading period based on interval position with corrected DST mapping
            if is_dst_spring and dst_adjusted:
                # Spring DST: intervals 1-46 map to TP 1-46, skip TP 47-48, intervals 49-50 are NULL
                if interval_num <= 46:
                    trading_period = interval_num
                elif interval_num in [47, 48]:
                    # These intervals are skipped - should not be processed
                    trading_period = None
                else:  # intervals 49-50
                    # These are NULL for spring DST
                    trading_period = None
            elif is_dst_autumn and dst_adjusted:
                # Autumn DST: intervals 1-48 map to TP 1-48, intervals 49-50 map to repeated TP 47-48
                if interval_num <= 48:
                    trading_period = interval_num
                elif interval_num == 49:
                    trading_period = 47  # Repeated 2:00-2:30 AM
                elif interval_num == 50:
                    trading_period = 48  # Repeated 2:30-3:00 AM
                else:
                    trading_period = interval_num  # Fallback
            else:
                # Standard day: intervals 1-48 map to TP 1-48, intervals 49-50 are NULL
                if interval_num <= 48:
                    trading_period = interval_num
                else:
                    # Intervals 49-50 are NULL for standard days
                    trading_period = None
                
            # Skip NULL intervals (intervals 49-50 for standard days, specific DST intervals)
            if trading_period is None:
                logging.debug(f"[RUN_ID:{run_id}] Skipping NULL interval {interval_num} for {mep_provider} ICP {icp}")
                continue
                
            # Handle empty/null values - insert 0.0 instead of skipping
            # Track if the original value was NULL for proper statistics
            was_originally_null = interval_value is None or str(interval_value).strip() == ''
            
            if was_originally_null:
                logging.debug(f"[RUN_ID:{run_id}] Empty interval value for {mep_provider} ICP {icp}, interval {interval_num}, using 0.0")
                consumption_kwh = 0.0
            else:
                try:
                    consumption_kwh = float(interval_value)
                except (ValueError, TypeError) as e:
                    error_msg = f"[RUN_ID:{run_id}] CRITICAL: Invalid interval value for {mep_provider} ICP {icp}, interval {interval_num}: '{interval_value}' - {str(e)}"
                    logging.error(error_msg)
                    raise ValueError(error_msg)
            
            # Calculate interval timestamp with DST support
            interval_time = self._calculate_interval_timestamp(read_date, interval_num, dst_adjusted, is_dst_spring, is_dst_autumn)
            
            # CORRECTED FLAG MAPPING LOGIC
            # Three distinct flag types from meter provider:
            # 1. validation_status: P (Pass), F (Fail), N (No validation)
            # 2. reading_status: F (Final), E (Estimate) 
            # 3. data_status: A (Actual), E (Estimated), M (Missing)
            
            # Determine data status and quality flag
            if interval_value is None or str(interval_value).strip() == '':
                quality_flag_mapping['empty_values'] += 1
                # Empty/missing values
                data_status = 'M'  # Missing data
                quality_flag = 'M'  # Missing data
                validation_status = 'N'  # Cannot validate missing data
                reading_status = 'E'  # Estimate needed
                quality_flag_mapping['missing_flags'] += 1
                logging.info(f"[RUN_ID:{run_id}] Empty value for {mep_provider} ICP {icp}, interval {interval_num}: validation_flag={validation_flag} → data_status=M, quality=M")
            else:
                # Map validation_flag to appropriate data_status and quality_flag
                # Note: validation_flag from raw files can contain mixed meanings
                # We need to interpret based on context and meter provider standards
                
                if validation_flag in ['P']:
                    # P = Successfully validated by meter provider
                    data_status = 'A'  # Actual reading (validated)
                    quality_flag = 'A'  # Actual reading
                    validation_status = 'P'  # Pass validation
                    reading_status = 'F'  # Final reading
                elif validation_flag in ['A']:
                    # A = Actual reading
                    data_status = 'A'  # Actual reading
                    quality_flag = 'A'  # Actual reading
                    validation_status = 'P'  # Assume passed if actual
                    reading_status = 'F'  # Final reading
                elif validation_flag in ['F']:
                    # F = Failed validation OR Final reading (context dependent)
                    # For now, treat as failed validation
                    data_status = 'A'  # Still actual data but failed validation
                    quality_flag = 'S'  # Suspect due to failed validation
                    validation_status = 'F'  # Failed validation
                    reading_status = 'E'  # Estimate needed
                elif validation_flag in ['E']:
                    # E = Estimated reading
                    data_status = 'E'  # Estimated data
                    quality_flag = 'E'  # Estimated reading
                    validation_status = 'N'  # Could not validate (estimated)
                    reading_status = 'E'  # Estimate
                elif validation_flag in ['M']:
                    # M = Missing reading (but has value - suspicious)
                    data_status = 'M'  # Missing data flag
                    quality_flag = 'M'  # Missing reading
                    validation_status = 'N'  # Could not validate
                    reading_status = 'E'  # Estimate needed
                    logging.warning(f"[RUN_ID:{run_id}] SUSPICIOUS: Missing flag but value present for {mep_provider} ICP {icp}, interval {interval_num}: value={interval_value}, flag={validation_flag}")
                elif validation_flag in ['N']:
                    # N = No validation possible
                    data_status = 'M'  # No reads
                    quality_flag = 'M'  # Missing reading
                    validation_status = 'N'  # No validation possible
                    reading_status = 'E'  # Estimate needed
                    logging.warning(f"[RUN_ID:{run_id}] SUSPICIOUS: No validation flag but value present for {mep_provider} ICP {icp}, interval {interval_num}: value={interval_value}, flag={validation_flag}")
                elif validation_flag in ['R']:
                    # R = Revised reading
                    data_status = 'E'  # Revised/Estimated
                    quality_flag = 'E'  # Estimated reading
                    validation_status = 'P'  # Assume revised means validated
                    reading_status = 'F'  # Final revised reading
                else:
                    # Unknown validation flag
                    data_status = 'S'  # Suspect
                    quality_flag = 'S'  # Suspect - unknown validation flag
                    validation_status = 'N'  # Cannot validate unknown flag
                    reading_status = 'E'  # Estimate needed
                    logging.warning(f"[RUN_ID:{run_id}] UNKNOWN FLAG: {mep_provider} ICP {icp}, interval {interval_num}: value={interval_value}, flag={validation_flag} → data_status=S, quality=S")
            
            # Track quality flag statistics
            quality_flag_mapping[quality_flag] = quality_flag_mapping.get(quality_flag, 0) + 1
            
            # Create comprehensive metadata for additional fields
            metadata = {
                # Core processing information
                'source_system': mep_provider,
                'source_record_id': id_val,
                'run_id': run_id,
                'interval_number': interval_num,
                'was_empty': was_originally_null,
                'original_interval_value': str(interval_value) if interval_value is not None else 'NULL',
                
                # Data quality and validation
                'data_status': data_status,
                'validation_status': validation_status if 'validation_status' in locals() else 'N',
                'reading_status': reading_status if 'reading_status' in locals() else 'E',
                'original_validation_flag': validation_flag,
                
                # Raw source fields from MEP provider
                'meter_number': meter_number,
                'meter_serial_number': meter_serial,
                'element_type': element_type,
                'register_number': register_code,
                'register_map': register_map,
                'midnight_read_value': float(midnight_read) if midnight_read and str(midnight_read).strip() else None,
                'daylight_savings_adjusted': dst_adjusted,
                'source_file_name': file_name,
                
                # Key metering fields (also stored in dedicated columns)
                'flow_direction': flow_direction,
                'register_content_code': register_content_code,
                'meter_channel_number': meter_channel_number,
                
                # Additional raw fields for audit trail
                'reading_date': str(read_date),
                'original_flow_direction': flow_direction,
                'original_register_content_code': register_content_code,
                'original_meter_channel_number': meter_channel_number,
                
                # Processing metadata
                'normalized_at': datetime.now().isoformat(),
                'interval_timestamp': interval_time.isoformat() if interval_time else None,
                'trading_period': trading_period
            }
            
            interval_inserts.append({
                'connection_id': icp,
                'register_code': register_code,
                'timestamp': interval_time,
                'day': read_date,
                'trading_period': trading_period,
                'value': consumption_kwh,
                'unit': 'kWh',
                'quality_flag': quality_flag,
                'flow_direction': flow_direction,
                'register_content_code': register_content_code,
                'meter_channel_number': meter_channel_number,
                'source': mep_provider,
                'import_id': str(uuid.uuid4()),  # Generate proper UUID
                'metadata': json.dumps(metadata),
                'was_originally_null': was_originally_null  # Add flag for counting
            })
        
        # Log quality flag mapping summary
        total_intervals = len(interval_inserts)
        logging.info(f"[RUN_ID:{run_id}] QUALITY FLAG MAPPING SUMMARY for {mep_provider} ICP {icp}:")
        logging.info(f"[RUN_ID:{run_id}] - Total intervals: {total_intervals}")
        logging.info(f"[RUN_ID:{run_id}] - Permanent (P): {quality_flag_mapping.get('P', 0)} ({quality_flag_mapping.get('P', 0)/total_intervals*100:.1f}%)")
        logging.info(f"[RUN_ID:{run_id}] - Actual (A): {quality_flag_mapping.get('A', 0)} ({quality_flag_mapping.get('A', 0)/total_intervals*100:.1f}%)")
        logging.info(f"[RUN_ID:{run_id}] - Missing (M): {quality_flag_mapping.get('M', 0)} ({quality_flag_mapping.get('M', 0)/total_intervals*100:.1f}%)")
        logging.info(f"[RUN_ID:{run_id}] - Estimated (E): {quality_flag_mapping.get('E', 0)} ({quality_flag_mapping.get('E', 0)/total_intervals*100:.1f}%)")
        logging.info(f"[RUN_ID:{run_id}] - Suspect (S): {quality_flag_mapping.get('S', 0)} ({quality_flag_mapping.get('S', 0)/total_intervals*100:.1f}%)")
        logging.info(f"[RUN_ID:{run_id}] - Empty values: {quality_flag_mapping.get('empty_values', 0)}")
        logging.info(f"[RUN_ID:{run_id}] - Missing flags: {quality_flag_mapping.get('missing_flags', 0)}")
        
        return interval_inserts
    
    def normalize_long_format_record(self, record: Tuple, mep_provider: str, run_id: str) -> Dict:
        """Normalize a single long format record"""
        
        # Extract fields
        id_val, icp, meter_serial, register, stream, register_type, status, \
        interval_number, start_datetime, end_datetime, reading, quality, \
        unit, flag, filename, imported_at = record
        
        # Initialize variables to avoid UnboundLocalError
        flow_direction = None
        register_content_code = None
        meter_channel_number = None
        
        # CORRECTED FLAG MAPPING LOGIC for long format
        # Three distinct flag types from meter provider:
        # 1. validation_status: P (Pass), F (Fail), N (No validation)
        # 2. reading_status: F (Final), E (Estimate) 
        # 3. data_status: A (Actual), E (Estimated), M (Missing)
        
        # Track if the original value was NULL for proper statistics
        was_originally_null = reading is None or str(reading).strip() == ''
        
        if was_originally_null:
            logging.info(f"[RUN_ID:{run_id}] Empty reading value for {mep_provider} ICP {icp}, interval {interval_number}, using 0.0")
            consumption_kwh = 0.0
            # Empty/missing values
            data_status = 'M'  # Missing data
            quality_flag = 'M'  # Missing data
            validation_status = 'N'  # Cannot validate missing data
            reading_status = 'E'  # Estimate needed
        else:
            try:
                consumption_kwh = float(reading)
                # Map quality flag to appropriate data_status and quality_flag
                if quality in ['P']:
                    # P = Successfully validated by meter provider
                    data_status = 'A'  # Actual reading (validated)
                    quality_flag = 'A'  # Actual reading
                    validation_status = 'P'  # Pass validation
                    reading_status = 'F'  # Final reading
                elif quality in ['A']:
                    # A = Actual reading
                    data_status = 'A'  # Actual reading
                    quality_flag = 'A'  # Actual reading
                    validation_status = 'P'  # Assume passed if actual
                    reading_status = 'F'  # Final reading
                elif quality in ['F']:
                    # F = Failed validation OR Final reading (context dependent)
                    # For now, treat as failed validation
                    data_status = 'A'  # Still actual data but failed validation
                    quality_flag = 'S'  # Suspect due to failed validation
                    validation_status = 'F'  # Failed validation
                    reading_status = 'E'  # Estimate needed
                elif quality in ['E']:
                    # E = Estimated reading
                    data_status = 'E'  # Estimated data
                    quality_flag = 'E'  # Estimated reading
                    validation_status = 'N'  # Could not validate (estimated)
                    reading_status = 'E'  # Estimate
                elif quality in ['M']:
                    # M = Missing reading (but has value - suspicious)
                    data_status = 'M'  # Missing data flag
                    quality_flag = 'M'  # Missing reading
                    validation_status = 'N'  # Could not validate
                    reading_status = 'E'  # Estimate needed
                elif quality in ['N']:
                    # N = No validation possible
                    data_status = 'M'  # No reads
                    quality_flag = 'M'  # Missing reading
                    validation_status = 'N'  # No validation possible
                    reading_status = 'E'  # Estimate needed
                elif quality in ['R']:
                    # R = Revised reading
                    data_status = 'E'  # Revised/Estimated
                    quality_flag = 'E'  # Estimated reading
                    validation_status = 'P'  # Assume revised means validated
                    reading_status = 'F'  # Final revised reading
                else:
                    # Unknown or null quality flag
                    data_status = 'S'  # Suspect
                    quality_flag = 'S'  # Suspect - unknown validation flag
                    validation_status = 'N'  # Cannot validate unknown flag
                    reading_status = 'E'  # Estimate needed
            except (ValueError, TypeError) as e:
                error_msg = f"[RUN_ID:{run_id}] CRITICAL: Invalid reading value for {mep_provider} ICP {icp}, interval {interval_number}: '{reading}' - {str(e)}"
                logging.error(error_msg)
                raise ValueError(error_msg)
        
        # Extract key fields for long format (IntelliHub/MTRX)
        # Based on the example data:
        # - status="X" maps to flow_direction 
        # - register_type="UN24" maps to register_content_code
        # - stream="051" maps to meter_channel_number
        # - register="KWH-IMP-PRI-TOT" is the register code
        
        # Extract flow direction from status field (X=Export, I=Import)
        if status and status.strip().upper() in ['X', 'I']:
            flow_direction = status.strip().upper()
        elif register and ('IMP' in register.upper() or 'EXP' in register.upper()):
            # Fallback: try to extract from register name
            if 'IMP' in register.upper():
                flow_direction = 'I'
            elif 'EXP' in register.upper():
                flow_direction = 'X'
        
        # Extract register content code from register_type field
        if register_type:
            register_content_code = register_type.strip()
        
        # Extract meter channel number from stream field
        if stream:
            meter_channel_number = stream.strip()
        
        # Validate flow_direction for long format
        if flow_direction:
            flow_direction = flow_direction.strip().upper()
            if flow_direction not in ['X', 'I']:
                logging.warning(f"[RUN_ID:{run_id}] Invalid flow_direction '{flow_direction}' for {mep_provider} ICP {icp}, setting to None")
                flow_direction = None
        
        # Validate register_content_code format
        if register_content_code:
            if not register_content_code.replace('+', '').replace('-', '').isalnum():
                logging.warning(f"[RUN_ID:{run_id}] Unusual register_content_code format '{register_content_code}' for {mep_provider} ICP {icp}")
        
        # Validate meter_channel_number format
        if meter_channel_number:
            if not meter_channel_number.replace('.', '').isalnum():
                logging.warning(f"[RUN_ID:{run_id}] Unusual meter_channel_number format '{meter_channel_number}' for {mep_provider} ICP {icp}")
        
        # Calculate trading period based on interval_number from the record
        # For long format, interval_number directly corresponds to trading period
        trading_period = interval_number
        
        # Create comprehensive metadata for long format
        metadata = {
            # Core processing information
            'source_system': mep_provider,
            'source_record_id': id_val,
            'run_id': run_id,
            'was_empty': was_originally_null,
            'original_reading_value': str(reading) if reading is not None else 'NULL',
            
            # Data quality and validation
            'data_status': data_status,
            'validation_status': validation_status,
            'reading_status': reading_status,
            'original_quality_flag': quality,
            
            # Raw source fields from MEP provider (IntelliHub/MTRX)
            'meter_serial_number': meter_serial,
            'register': register,
            'stream': stream,
            'register_type': register_type,
            'status': status,
            'flag': flag,
            'interval_number': interval_number,
            'start_datetime': start_datetime.isoformat() if start_datetime else None,
            'end_datetime': end_datetime.isoformat() if end_datetime else None,
            'unit': unit,
            'source_file_name': filename,
            
            # Key metering fields (also stored in dedicated columns)
            'flow_direction': flow_direction,
            'register_content_code': register_content_code,
            'meter_channel_number': meter_channel_number,
            
            # Additional fields for audit trail
            'original_flow_direction': flow_direction,
            'original_register_content_code': register_content_code,
            'original_meter_channel_number': meter_channel_number,
            
            # Processing metadata
            'normalized_at': datetime.now().isoformat(),
            'interval_timestamp': start_datetime.isoformat() if start_datetime else None,
            'trading_period': trading_period
        }
        
        return {
            'connection_id': icp,
            'register_code': register,
            'timestamp': start_datetime,
            'day': start_datetime.date() if start_datetime else None,
            'trading_period': trading_period,
            'value': consumption_kwh,
            'unit': unit or 'kWh',
            'quality_flag': quality_flag,
            'flow_direction': flow_direction,
            'register_content_code': register_content_code,
            'meter_channel_number': meter_channel_number,
            'source': mep_provider,
            'import_id': str(uuid.uuid4()),  # Generate proper UUID
            'metadata': json.dumps(metadata),
            'was_originally_null': was_originally_null  # Add flag for counting
        }
    
    def normalize_eiep3_record(self, record: Tuple, run_id: str) -> Dict:
        """Normalize a single EIEP3 record into interval reading"""
        
        # Extract EIEP3 fields
        id_val = record[0]
        icp_identifier = record[1]
        data_stream_identifier = record[2]  # meter serial
        reading_type = record[3]  # register code
        date_field = record[4]  # DD/MM/YYYY format
        trading_period = record[5]
        active_energy = record[6]
        energy_flow_direction = record[7]
        data_stream_type = record[8]
        file_name = record[9]
        imported_at = record[10]
        
        # Convert date from DD/MM/YYYY to datetime
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_field, '%d/%m/%Y').date()
        except ValueError:
            logging.error(f"[RUN_ID:{run_id}] Invalid date format: {date_field}")
            return None
        
        # Calculate timestamp from trading period
        # Trading period 1 = 00:30, 2 = 01:00, 3 = 01:30, 4 = 02:00, etc.
        # For NZ, trading day starts at 00:00 but first period is 00:30
        total_minutes = trading_period * 30
        hour = (total_minutes // 60) % 24
        minute = total_minutes % 60
        
        # Create timestamp in UTC (NZ time is UTC+12/13)
        # For now, store as local time and let the system handle timezone
        timestamp = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute))
        
        # Convert energy value
        # Track if the original value was NULL for proper statistics
        was_originally_null = active_energy is None or str(active_energy).strip() == ''
        
        try:
            consumption_kwh = float(active_energy) if active_energy is not None else 0.0
        except (ValueError, TypeError):
            logging.warning(f"[RUN_ID:{run_id}] Invalid energy value: {active_energy}")
            consumption_kwh = 0.0
            was_originally_null = True  # Invalid values are treated as null
        
        # Map flow direction
        flow_direction = energy_flow_direction if energy_flow_direction in ['I', 'X'] else 'I'
        
        # Create metadata
        metadata = {
            'source_id': id_val,
            'data_stream_identifier': data_stream_identifier,
            'data_stream_type': data_stream_type,
            'file_name': file_name,
            'imported_at': imported_at.isoformat() if imported_at else None,
            'original_date_field': date_field,
            'run_id': run_id
        }
        
        logging.info(f"[RUN_ID:{run_id}] EIEP3 normalized: {icp_identifier} | {reading_type} | {date_obj} | TP{trading_period} | {consumption_kwh}kWh | {flow_direction}")
        
        return {
            'connection_id': icp_identifier,
            'register_code': reading_type,
            'timestamp': timestamp,
            'day': date_obj,
            'trading_period': trading_period,
            'value': consumption_kwh,
            'unit': 'kWh',
            'quality_flag': 'A',  # Assume good quality for EIEP3
            'flow_direction': flow_direction,
            'register_content_code': reading_type,
            'meter_channel_number': data_stream_identifier,
            'source': 'EIEP3',
            'import_id': str(uuid.uuid4()),
            'metadata': json.dumps(metadata),
            'was_originally_null': was_originally_null  # Add flag for counting
        }
    
    def bulk_insert_intervals(self, interval_records: List[Dict]):
        """Bulk insert interval records with enhanced columns"""
        
        if not interval_records:
            return 0
            
        insert_query = """
        INSERT INTO metering_processed.interval_reads_raw (
            connection_id, register_code, timestamp, day, trading_period, value, unit,
            quality_flag, flow_direction, register_content_code, meter_channel_number,
            source, import_id, metadata
        ) VALUES %s
        ON CONFLICT DO NOTHING
        """
        
        # Prepare data tuples
        data_tuples = [
            (
                record['connection_id'], record['register_code'], record['timestamp'],
                record['day'], record.get('trading_period'), record['value'], record['unit'],
                record['quality_flag'], record.get('flow_direction'), 
                record.get('register_content_code'), record.get('meter_channel_number'),
                record['source'], record['import_id'], record['metadata']
            )
            for record in interval_records
        ]
        
        # Use execute_values for bulk insert
        from psycopg2.extras import execute_values
        
        with self.pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                # Get count before insert
                cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_raw")
                count_before = cursor.fetchone()[0]
                
                # Execute the insert
                execute_values(cursor, insert_query, data_tuples)
                
                # Get count after insert to determine actual inserted records
                cursor.execute("SELECT COUNT(*) FROM metering_processed.interval_reads_raw")
                count_after = cursor.fetchone()[0]
                
                conn.commit()
                
                actual_inserted = count_after - count_before
                logging.info(f"Bulk insert: attempted {len(interval_records)}, actually inserted {actual_inserted}")
        
        return actual_inserted
    
    def _calculate_interval_timestamp(self, read_date, interval_num: int, dst_adjusted: bool = False, 
                                    is_dst_spring: bool = False, is_dst_autumn: bool = False) -> datetime:
        """
        Calculate interval timestamp with corrected DST support for New Zealand
        
        Args:
            read_date: The reading date
            interval_num: Interval number (1-50, with DST-specific mapping)
            dst_adjusted: Whether this is a DST-adjusted reading
            is_dst_spring: Whether this is a spring DST day
            is_dst_autumn: Whether this is an autumn DST day
            
        Returns:
            datetime: The timestamp for this interval
        """
        import pytz
        
        # New Zealand timezone
        nz_tz = pytz.timezone('Pacific/Auckland')
        
        if is_dst_spring and dst_adjusted:
            # Spring DST: Skip 2:00-3:00 AM (intervals 47-48), intervals 49-50 are NULL
            if interval_num <= 46:
                # Normal calculation for intervals 1-46 (00:30-23:00, skipping 02:00-03:00)
                if interval_num <= 4:  # 00:30-02:00
                    interval_minutes = interval_num * 30
                else:  # Skip 02:00-03:00, continue from 03:00
                    interval_minutes = (interval_num + 4) * 30
            elif interval_num in [47, 48]:
                # These intervals are skipped in spring DST - should not be processed
                logging.warning(f"Interval {interval_num} should be skipped for spring DST")
                interval_minutes = interval_num * 30  # Fallback
            else:  # intervals 49-50
                # These should be NULL for spring DST
                logging.warning(f"Interval {interval_num} should be NULL for spring DST")
                interval_minutes = interval_num * 30  # Fallback
                
        elif is_dst_autumn and dst_adjusted:
            # Autumn DST: Use intervals 1-48 normally, intervals 49-50 for repeated 2:00-3:00 AM
            if interval_num <= 48:
                # Normal calculation for intervals 1-48
                interval_minutes = interval_num * 30
            elif interval_num == 49:
                # Repeated 2:00-2:30 AM (second occurrence)
                interval_minutes = 4 * 30  # 2:00 AM
            elif interval_num == 50:
                # Repeated 2:30-3:00 AM (second occurrence)  
                interval_minutes = 4.5 * 30  # 2:30 AM
            else:
                interval_minutes = interval_num * 30  # Fallback
                
        else:
            # Standard day: intervals 1-48, intervals 49-50 should be NULL
            if interval_num <= 48:
                interval_minutes = interval_num * 30
            else:
                # Intervals 49-50 should be NULL for standard days
                logging.warning(f"Interval {interval_num} should be NULL for standard day")
                interval_minutes = interval_num * 30  # Fallback
        
        # Create naive datetime
        base_time = datetime.combine(read_date, datetime.min.time())
        interval_time = base_time + timedelta(minutes=interval_minutes)
        
        # Localize to New Zealand timezone
        try:
            localized_time = nz_tz.localize(interval_time)
        except pytz.AmbiguousTimeError:
            # Handle ambiguous time during autumn DST transition
            # Use is_dst=False for the second occurrence
            localized_time = nz_tz.localize(interval_time, is_dst=False)
        except pytz.NonExistentTimeError:
            # Handle non-existent time during spring DST transition
            # This shouldn't happen with our logic above, but handle it
            localized_time = nz_tz.localize(interval_time, is_dst=True)
        
        # Convert to UTC for storage
        return localized_time.astimezone(pytz.UTC).replace(tzinfo=None)
    
    # Trading period calculation is now simplified - based on interval position
    # Wide format: interval_num (1-48, 46/50 for DST) directly maps to trading period
    # Long format: interval_number from database directly maps to trading period
    
    def _is_dst_spring_day(self, date) -> bool:
        """Check if date is DST spring transition day (last Sunday in September)"""
        import calendar
        
        if date.month != 9:  # September
            return False
            
        # Find last Sunday in September
        last_day = calendar.monthrange(date.year, 9)[1]
        
        for day in range(last_day, 0, -1):
            test_date = date.replace(day=day)
            if test_date.weekday() == 6:  # Sunday
                return date == test_date
                
        return False

    def _is_dst_autumn_day(self, date) -> bool:
        """Check if date is DST autumn transition day (first Sunday in April)"""
        if date.month != 4:  # April
            return False
            
        # Find first Sunday in April
        for day in range(1, 8):
            test_date = date.replace(day=day)
            if test_date.weekday() == 6:  # Sunday
                return date == test_date
                
        return False

def log_processing(dag_id: str, task_id: str, run_id: str, mep_provider: str,
                  processing_type: str, status: str, source_records: int = 0,
                  source_intervals: int = 0, intervals_processed: int = 0, 
                  intervals_non_zero: int = 0, intervals_zero: int = 0, 
                  intervals_null: int = 0, intervals_estimated: int = 0,
                  intervals_total: int = 0, quality_flag_a: int = 0,
                  quality_flag_e: int = 0, quality_flag_f: int = 0,
                  quality_flag_n: int = 0, quality_flag_s: int = 0,
                  quality_flag_other: int = 0, error_message: str = None):
    """Log processing activity to metering_processed.processing_log table"""
    # Import connection utility
    import sys
    sys.path.append('/app/airflow/utils')
    from connection import get_connection
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Create schema and table if not exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS metering_processed")
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metering_processed.processing_log (
                        id SERIAL PRIMARY KEY,
                        dag_id VARCHAR(100) NOT NULL,
                        task_id VARCHAR(100) NOT NULL,
                        run_id VARCHAR(255) NOT NULL,
                        mep_provider VARCHAR(50) NOT NULL,
                        processing_type VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        source_records INTEGER DEFAULT 0,
                        source_intervals INTEGER DEFAULT 0,
                        intervals_processed INTEGER DEFAULT 0,
                        intervals_non_zero INTEGER DEFAULT 0,
                        intervals_zero INTEGER DEFAULT 0,
                        intervals_null INTEGER DEFAULT 0,
                        intervals_estimated INTEGER DEFAULT 0,
                        intervals_total INTEGER DEFAULT 0,
                        quality_flag_a INTEGER DEFAULT 0,
                        quality_flag_e INTEGER DEFAULT 0,
                        quality_flag_f INTEGER DEFAULT 0,
                        quality_flag_n INTEGER DEFAULT 0,
                        quality_flag_s INTEGER DEFAULT 0,
                        quality_flag_other INTEGER DEFAULT 0,
                        error_message TEXT,
                        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        completed_at TIMESTAMP WITH TIME ZONE,
                        UNIQUE(dag_id, task_id, run_id, mep_provider, processing_type)
                    )
                """)
                
                # Insert or update processing log record
                if status == 'completed':
                    cur.execute(
                        """INSERT INTO metering_processed.processing_log 
                           (dag_id, task_id, run_id, mep_provider, processing_type, status, 
                            source_records, source_intervals, intervals_processed, intervals_non_zero, 
                            intervals_zero, intervals_null, intervals_estimated, intervals_total,
                            quality_flag_a, quality_flag_e, quality_flag_f, quality_flag_n,
                            quality_flag_s, quality_flag_other, error_message, completed_at) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) 
                           ON CONFLICT (dag_id, task_id, run_id, mep_provider, processing_type) DO UPDATE SET
                               status = EXCLUDED.status,
                               source_records = EXCLUDED.source_records,
                               source_intervals = EXCLUDED.source_intervals,
                               intervals_processed = EXCLUDED.intervals_processed,
                               intervals_non_zero = EXCLUDED.intervals_non_zero,
                               intervals_zero = EXCLUDED.intervals_zero,
                               intervals_null = EXCLUDED.intervals_null,
                               intervals_estimated = EXCLUDED.intervals_estimated,
                               intervals_total = EXCLUDED.intervals_total,
                               quality_flag_a = EXCLUDED.quality_flag_a,
                               quality_flag_e = EXCLUDED.quality_flag_e,
                               quality_flag_f = EXCLUDED.quality_flag_f,
                               quality_flag_n = EXCLUDED.quality_flag_n,
                               quality_flag_s = EXCLUDED.quality_flag_s,
                               quality_flag_other = EXCLUDED.quality_flag_other,
                               error_message = EXCLUDED.error_message,
                               completed_at = EXCLUDED.completed_at""",
                        [dag_id, task_id, run_id, mep_provider, processing_type, status,
                         source_records, source_intervals, intervals_processed, intervals_non_zero,
                         intervals_zero, intervals_null, intervals_estimated, intervals_total,
                         quality_flag_a, quality_flag_e, quality_flag_f, quality_flag_n,
                         quality_flag_s, quality_flag_other, error_message]
                    )
                else:
                    cur.execute(
                        """INSERT INTO metering_processed.processing_log 
                           (dag_id, task_id, run_id, mep_provider, processing_type, status, error_message) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s) 
                           ON CONFLICT (dag_id, task_id, run_id, mep_provider, processing_type) DO UPDATE SET
                               status = EXCLUDED.status,
                               error_message = EXCLUDED.error_message""",
                        [dag_id, task_id, run_id, mep_provider, processing_type, status, error_message]
                    )
                
                conn.commit()
                logging.info(f"✅ Logged processing: {mep_provider} {processing_type} - {status}")
                
    except Exception as e:
        logging.error(f"❌ Failed to log processing: {e}")

# Task functions
def normalize_bcmm_hhr_data(**context):
    """Normalize BCMM HHR data"""
    normalizer = UniversalHHRNormalizer()
    
    # Generate run ID for this execution
    run_id = f"bcmm_hhr_{context['ds']}_{context['ts_nodash']}"
    
    records, mapping = normalizer.get_unprocessed_wide_format_data('BCMM', 'bcmm_hhr')
    if not records:
        logging.info(f"[RUN_ID:{run_id}] No unprocessed BCMM records found")
        # Log zero processing activity
        log_processing(
            dag_id=context.get('dag').dag_id,
            task_id=context.get('task').task_id,
            run_id=run_id,
            mep_provider='BCMM',
            processing_type='HHR_NORMALIZATION',
            status='completed',
            source_records=0,
            source_intervals=0,
            intervals_processed=0,
            intervals_non_zero=0,
            intervals_zero=0,
            intervals_null=0,
            intervals_estimated=0,
            intervals_total=0,
            quality_flag_a=0,
            quality_flag_e=0,
            quality_flag_f=0,
            quality_flag_n=0,
            quality_flag_s=0,
            quality_flag_other=0
        )
        return 0
    
    logging.info(f"[RUN_ID:{run_id}] Processing {len(records)} BCMM records")
    
    all_intervals = []
    processed_records = 0
    error_count = 0
    
    # Track detailed interval statistics
    intervals_non_zero = 0
    intervals_zero = 0  
    intervals_null = 0
    intervals_estimated = 0
    intervals_total = 0
    expected_intervals_total = 0  # Track actual expected intervals accounting for DST
    quality_flag_counts = {'A': 0, 'E': 0, 'F': 0, 'N': 0, 'S': 0, 'OTHER': 0}
    
    for record in records:
        try:
            intervals = normalizer.normalize_wide_format_record(record, mapping, 'BCMM', run_id)
            all_intervals.extend(intervals)
            processed_records += 1
            
            # Calculate expected intervals for this record based on DST
            reading_date = record[7]  # Date field position in BCMM record
            try:
                if isinstance(reading_date, str):
                    read_date = datetime.strptime(reading_date, '%Y-%m-%d').date()
                else:
                    read_date = reading_date
                    
                # Check DST status for this record
                is_dst_spring = normalizer._is_dst_autumn_day(read_date)  # April = Spring DST (clocks forward)
                is_dst_autumn = normalizer._is_dst_spring_day(read_date)  # September = Autumn DST (clocks back)
                dst_adjusted = record[12] == 'Y' if len(record) > 12 and record[12] else False  # DST adjusted field
                
                if is_dst_spring and dst_adjusted:
                    expected_intervals_this_record = 46  # Spring DST: 46 intervals
                elif is_dst_autumn and dst_adjusted:
                    expected_intervals_this_record = 50  # Autumn DST: 50 intervals
                else:
                    expected_intervals_this_record = 48  # Standard day: 48 intervals
                    
                expected_intervals_total += expected_intervals_this_record
                
            except Exception as e:
                # Fallback to 48 if date parsing fails
                expected_intervals_total += 48
                logging.warning(f"[RUN_ID:{run_id}] Could not determine DST status for BCMM record {record[0]}, using 48 intervals: {e}")
            
            # Count interval types and quality flags for this record
            for interval_data in intervals:
                intervals_total += 1
                value = interval_data.get('value', 0)
                quality_flag = interval_data.get('quality_flag', 'N')
                was_originally_null = interval_data.get('was_originally_null', False)
                
                # Count by value type - check original null status first
                if was_originally_null:
                    intervals_null += 1
                elif value == 0:
                    intervals_zero += 1
                else:
                    intervals_non_zero += 1
                    
                # Count estimated intervals (E flag)
                if quality_flag == 'E':
                    intervals_estimated += 1
                    
                # Count quality flags
                if quality_flag in quality_flag_counts:
                    quality_flag_counts[quality_flag] += 1
                else:
                    quality_flag_counts['OTHER'] += 1
                    
        except Exception as e:
            error_count += 1
            logging.error(f"[RUN_ID:{run_id}] Failed to process BCMM record {record[0]}: {str(e)}")
            # Re-raise to stop processing on critical errors
            raise
    
    inserted = normalizer.bulk_insert_intervals(all_intervals)
    
    # Log detailed processing statistics
    log_processing(
        dag_id=context.get('dag').dag_id,
        task_id=context.get('task').task_id,
        run_id=run_id,
        mep_provider='BCMM',
        processing_type='HHR_NORMALIZATION',
        status='completed',
        source_records=len(records),
        source_intervals=expected_intervals_total,  # Expected intervals accounting for DST
        intervals_processed=inserted,
        intervals_non_zero=intervals_non_zero,
        intervals_zero=intervals_zero,
        intervals_null=intervals_null,
        intervals_estimated=intervals_estimated,
        intervals_total=intervals_total,
        quality_flag_a=quality_flag_counts['A'],
        quality_flag_e=quality_flag_counts['E'],
        quality_flag_f=quality_flag_counts['F'],
        quality_flag_n=quality_flag_counts['N'],
        quality_flag_s=quality_flag_counts['S'],
        quality_flag_other=quality_flag_counts['OTHER']
    )
    
    logging.info(f"[RUN_ID:{run_id}] BCMM Normalization Complete:")
    logging.info(f"[RUN_ID:{run_id}] - Records processed: {processed_records}")
    logging.info(f"[RUN_ID:{run_id}] - Intervals created: {inserted}")
    logging.info(f"[RUN_ID:{run_id}] - Expected intervals: {expected_intervals_total} (accounting for DST)")
    logging.info(f"[RUN_ID:{run_id}] - Non-zero intervals: {intervals_non_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Zero intervals: {intervals_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Null intervals: {intervals_null}")
    logging.info(f"[RUN_ID:{run_id}] - Errors: {error_count}")
    
    return inserted

def normalize_smartco_hhr_data(**context):
    """Normalize SmartCo HHR data"""
    normalizer = UniversalHHRNormalizer()
    
    # Generate run ID for this execution
    run_id = f"smartco_hhr_{context['ds']}_{context['ts_nodash']}"
    
    records, mapping = normalizer.get_unprocessed_wide_format_data('SmartCo', 'smartco_hhr')
    if not records:
        logging.info(f"[RUN_ID:{run_id}] No unprocessed SmartCo records found")
        # Log zero processing activity
        log_processing(
            dag_id=context.get('dag').dag_id,
            task_id=context.get('task').task_id,
            run_id=run_id,
            mep_provider='SmartCo',
            processing_type='HHR_NORMALIZATION',
            status='completed',
            source_records=0,
            source_intervals=0,
            intervals_processed=0,
            intervals_non_zero=0,
            intervals_zero=0,
            intervals_null=0,
            intervals_estimated=0,
            intervals_total=0,
            quality_flag_a=0,
            quality_flag_e=0,
            quality_flag_f=0,
            quality_flag_n=0,
            quality_flag_s=0,
            quality_flag_other=0
        )
        return 0
    
    logging.info(f"[RUN_ID:{run_id}] Processing {len(records)} SmartCo records")
    
    all_intervals = []
    processed_records = 0
    error_count = 0
    
    # Track detailed interval statistics
    intervals_non_zero = 0
    intervals_zero = 0  
    intervals_null = 0
    intervals_estimated = 0
    intervals_total = 0
    expected_intervals_total = 0  # Track actual expected intervals accounting for DST
    quality_flag_counts = {'A': 0, 'E': 0, 'F': 0, 'N': 0, 'S': 0, 'OTHER': 0}
    
    for record in records:
        try:
            intervals = normalizer.normalize_wide_format_record(record, mapping, 'SmartCo', run_id)
            all_intervals.extend(intervals)
            processed_records += 1
            
            # Calculate expected intervals for this record based on DST
            reading_date = record[7]  # Date field position in SmartCo record
            try:
                if isinstance(reading_date, str):
                    read_date = datetime.strptime(reading_date, '%Y-%m-%d').date()
                else:
                    read_date = reading_date
                    
                # Check DST status for this record
                is_dst_spring = normalizer._is_dst_autumn_day(read_date)  # April = Spring DST (clocks forward)
                is_dst_autumn = normalizer._is_dst_spring_day(read_date)  # September = Autumn DST (clocks back)
                dst_adjusted = record[12] == 'Y' if len(record) > 12 and record[12] else False  # DST adjusted field
                
                if is_dst_spring and dst_adjusted:
                    expected_intervals_this_record = 46  # Spring DST: 46 intervals
                elif is_dst_autumn and dst_adjusted:
                    expected_intervals_this_record = 50  # Autumn DST: 50 intervals
                else:
                    expected_intervals_this_record = 48  # Standard day: 48 intervals
                    
                expected_intervals_total += expected_intervals_this_record
                
            except Exception as e:
                # Fallback to 48 if date parsing fails
                expected_intervals_total += 48
                logging.warning(f"[RUN_ID:{run_id}] Could not determine DST status for SmartCo record {record[0]}, using 48 intervals: {e}")
            
            # Count interval types and quality flags for this record
            for interval_data in intervals:
                intervals_total += 1
                value = interval_data.get('value', 0)
                quality_flag = interval_data.get('quality_flag', 'N')
                was_originally_null = interval_data.get('was_originally_null', False)
                
                # Count by value type - check original null status first
                if was_originally_null:
                    intervals_null += 1
                elif value == 0:
                    intervals_zero += 1
                else:
                    intervals_non_zero += 1
                    
                # Count estimated intervals (E flag)
                if quality_flag == 'E':
                    intervals_estimated += 1
                    
                # Count quality flags
                if quality_flag in quality_flag_counts:
                    quality_flag_counts[quality_flag] += 1
                else:
                    quality_flag_counts['OTHER'] += 1
                    
        except Exception as e:
            error_count += 1
            logging.error(f"[RUN_ID:{run_id}] Failed to process SmartCo record {record[0]}: {str(e)}")
            raise
    
    inserted = normalizer.bulk_insert_intervals(all_intervals)
    
    # Log detailed processing statistics
    log_processing(
        dag_id=context.get('dag').dag_id,
        task_id=context.get('task').task_id,
        run_id=run_id,
        mep_provider='SmartCo',
        processing_type='HHR_NORMALIZATION',
        status='completed',
        source_records=len(records),
        source_intervals=expected_intervals_total,  # Expected intervals accounting for DST
        intervals_processed=inserted,
        intervals_non_zero=intervals_non_zero,
        intervals_zero=intervals_zero,
        intervals_null=intervals_null,
        intervals_estimated=intervals_estimated,
        intervals_total=intervals_total,
        quality_flag_a=quality_flag_counts['A'],
        quality_flag_e=quality_flag_counts['E'],
        quality_flag_f=quality_flag_counts['F'],
        quality_flag_n=quality_flag_counts['N'],
        quality_flag_s=quality_flag_counts['S'],
        quality_flag_other=quality_flag_counts['OTHER']
    )
    
    logging.info(f"[RUN_ID:{run_id}] SmartCo Normalization Complete:")
    logging.info(f"[RUN_ID:{run_id}] - Records processed: {processed_records}")
    logging.info(f"[RUN_ID:{run_id}] - Intervals created: {inserted}")
    logging.info(f"[RUN_ID:{run_id}] - Expected intervals: {expected_intervals_total} (accounting for DST)")
    logging.info(f"[RUN_ID:{run_id}] - Non-zero intervals: {intervals_non_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Zero intervals: {intervals_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Null intervals: {intervals_null}")
    logging.info(f"[RUN_ID:{run_id}] - Estimated intervals: {intervals_estimated}")
    logging.info(f"[RUN_ID:{run_id}] - Quality flags: A={quality_flag_counts['A']}, E={quality_flag_counts['E']}, F={quality_flag_counts['F']}, N={quality_flag_counts['N']}, S={quality_flag_counts['S']}")
    logging.info(f"[RUN_ID:{run_id}] - Errors: {error_count}")
    
    return inserted

def normalize_fclm_hhr_data(**context):
    """Normalize FCLM HHR data"""
    normalizer = UniversalHHRNormalizer()
    
    # Generate run ID for this execution
    run_id = f"fclm_hhr_{context['ds']}_{context['ts_nodash']}"
    
    records, mapping = normalizer.get_unprocessed_wide_format_data('FCLM', 'fclm_hhr')
    if not records:
        logging.info(f"[RUN_ID:{run_id}] No unprocessed FCLM records found")
        # Log zero processing activity
        log_processing(
            dag_id=context.get('dag').dag_id,
            task_id=context.get('task').task_id,
            run_id=run_id,
            mep_provider='FCLM',
            processing_type='HHR_NORMALIZATION',
            status='completed',
            source_records=0,
            source_intervals=0,
            intervals_processed=0,
            intervals_non_zero=0,
            intervals_zero=0,
            intervals_null=0,
            intervals_estimated=0,
            intervals_total=0,
            quality_flag_a=0,
            quality_flag_e=0,
            quality_flag_f=0,
            quality_flag_n=0,
            quality_flag_s=0,
            quality_flag_other=0
        )
        return 0
    
    logging.info(f"[RUN_ID:{run_id}] Processing {len(records)} FCLM records")
    
    all_intervals = []
    processed_records = 0
    error_count = 0
    
    # Track detailed interval statistics
    intervals_non_zero = 0
    intervals_zero = 0  
    intervals_null = 0
    intervals_estimated = 0
    intervals_total = 0
    expected_intervals_total = 0  # Track actual expected intervals accounting for DST
    quality_flag_counts = {'A': 0, 'E': 0, 'F': 0, 'N': 0, 'S': 0, 'OTHER': 0}
    
    for record in records:
        try:
            intervals = normalizer.normalize_wide_format_record(record, mapping, 'FCLM', run_id)
            all_intervals.extend(intervals)
            processed_records += 1
            
            # Calculate expected intervals for this record based on DST
            reading_date = record[7]  # Date field position in FCLM record
            try:
                if isinstance(reading_date, str):
                    # FCLM uses YYYYMMDD format
                    read_date = datetime.strptime(reading_date, '%Y%m%d').date()
                else:
                    read_date = reading_date
                    
                # Check DST status for this record
                is_dst_spring = normalizer._is_dst_autumn_day(read_date)  # April = Spring DST (clocks forward)
                is_dst_autumn = normalizer._is_dst_spring_day(read_date)  # September = Autumn DST (clocks back)
                # FCLM doesn't have DST field, so we assume dst_adjusted = True for DST days
                dst_adjusted = is_dst_spring or is_dst_autumn
                
                if is_dst_spring and dst_adjusted:
                    expected_intervals_this_record = 46  # Spring DST: 46 intervals
                elif is_dst_autumn and dst_adjusted:
                    expected_intervals_this_record = 50  # Autumn DST: 50 intervals
                else:
                    expected_intervals_this_record = 48  # Standard day: 48 intervals
                    
                expected_intervals_total += expected_intervals_this_record
                
            except Exception as e:
                # Fallback to 48 if date parsing fails
                expected_intervals_total += 48
                logging.warning(f"[RUN_ID:{run_id}] Could not determine DST status for FCLM record {record[0]}, using 48 intervals: {e}")
            
            # Count interval types and quality flags for this record
            for interval_data in intervals:
                intervals_total += 1
                value = interval_data.get('value', 0)
                quality_flag = interval_data.get('quality_flag', 'N')
                was_originally_null = interval_data.get('was_originally_null', False)
                
                # Count by value type - check original null status first
                if was_originally_null:
                    intervals_null += 1
                elif value == 0:
                    intervals_zero += 1
                else:
                    intervals_non_zero += 1
                    
                # Count estimated intervals (E flag)
                if quality_flag == 'E':
                    intervals_estimated += 1
                    
                # Count quality flags
                if quality_flag in quality_flag_counts:
                    quality_flag_counts[quality_flag] += 1
                else:
                    quality_flag_counts['OTHER'] += 1
                    
        except Exception as e:
            error_count += 1
            logging.error(f"[RUN_ID:{run_id}] Failed to process FCLM record {record[0]}: {str(e)}")
            raise
    
    inserted = normalizer.bulk_insert_intervals(all_intervals)
    
    # Log detailed processing statistics
    log_processing(
        dag_id=context.get('dag').dag_id,
        task_id=context.get('task').task_id,
        run_id=run_id,
        mep_provider='FCLM',
        processing_type='HHR_NORMALIZATION',
        status='completed',
        source_records=len(records),
        source_intervals=expected_intervals_total,  # Expected intervals accounting for DST
        intervals_processed=inserted,
        intervals_non_zero=intervals_non_zero,
        intervals_zero=intervals_zero,
        intervals_null=intervals_null,
        intervals_estimated=intervals_estimated,
        intervals_total=intervals_total,
        quality_flag_a=quality_flag_counts['A'],
        quality_flag_e=quality_flag_counts['E'],
        quality_flag_f=quality_flag_counts['F'],
        quality_flag_n=quality_flag_counts['N'],
        quality_flag_s=quality_flag_counts['S'],
        quality_flag_other=quality_flag_counts['OTHER']
    )
    
    logging.info(f"[RUN_ID:{run_id}] FCLM Normalization Complete:")
    logging.info(f"[RUN_ID:{run_id}] - Records processed: {processed_records}")
    logging.info(f"[RUN_ID:{run_id}] - Intervals created: {inserted}")
    logging.info(f"[RUN_ID:{run_id}] - Expected intervals: {expected_intervals_total} (accounting for DST)")
    logging.info(f"[RUN_ID:{run_id}] - Non-zero intervals: {intervals_non_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Zero intervals: {intervals_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Null intervals: {intervals_null}")
    logging.info(f"[RUN_ID:{run_id}] - Estimated intervals: {intervals_estimated}")
    logging.info(f"[RUN_ID:{run_id}] - Quality flags: A={quality_flag_counts['A']}, E={quality_flag_counts['E']}, F={quality_flag_counts['F']}, N={quality_flag_counts['N']}, S={quality_flag_counts['S']}")
    logging.info(f"[RUN_ID:{run_id}] - Errors: {error_count}")
    
    return inserted

def normalize_intellihub_hhr_data(**context):
    """Normalize IntelliHub HHR data"""
    normalizer = UniversalHHRNormalizer()
    
    # Generate run ID for this execution
    run_id = f"intellihub_hhr_{context['ds']}_{context['ts_nodash']}"
    
    records = normalizer.get_unprocessed_long_format_data('IntelliHub', 'intellihub_hhr')
    if not records:
        logging.info(f"[RUN_ID:{run_id}] No unprocessed IntelliHub records found")
        # Log zero processing activity
        log_processing(
            dag_id=context.get('dag').dag_id,
            task_id=context.get('task').task_id,
            run_id=run_id,
            mep_provider='IntelliHub',
            processing_type='HHR_NORMALIZATION',
            status='completed',
            source_records=0,
            source_intervals=0,
            intervals_processed=0,
            intervals_non_zero=0,
            intervals_zero=0,
            intervals_null=0,
            intervals_estimated=0,
            intervals_total=0,
            quality_flag_a=0,
            quality_flag_e=0,
            quality_flag_f=0,
            quality_flag_n=0,
            quality_flag_s=0,
            quality_flag_other=0
        )
        return 0
    
    logging.info(f"[RUN_ID:{run_id}] Processing {len(records)} IntelliHub records")
    
    all_intervals = []
    processed_records = 0
    error_count = 0
    
    # Track detailed interval statistics
    intervals_non_zero = 0
    intervals_zero = 0  
    intervals_null = 0
    intervals_estimated = 0
    intervals_total = 0
    quality_flag_counts = {'A': 0, 'E': 0, 'F': 0, 'N': 0, 'S': 0, 'OTHER': 0}
    
    for record in records:
        try:
            interval = normalizer.normalize_long_format_record(record, 'IntelliHub', run_id)
            all_intervals.append(interval)
            processed_records += 1
            
            # Count interval types and quality flags
            intervals_total += 1
            value = interval.get('value', 0)
            quality_flag = interval.get('quality_flag', 'N')
            was_originally_null = interval.get('was_originally_null', False)
            
            # Count by value type - check original null status first
            if was_originally_null:
                intervals_null += 1
            elif value == 0:
                intervals_zero += 1
            else:
                intervals_non_zero += 1
                
            # Count estimated intervals (E flag)
            if quality_flag == 'E':
                intervals_estimated += 1
                
            # Count quality flags
            if quality_flag in quality_flag_counts:
                quality_flag_counts[quality_flag] += 1
            else:
                quality_flag_counts['OTHER'] += 1
                
        except Exception as e:
            error_count += 1
            logging.error(f"[RUN_ID:{run_id}] Failed to process IntelliHub record {record[0]}: {str(e)}")
            raise
    
    inserted = normalizer.bulk_insert_intervals(all_intervals)
    
    # Log detailed processing statistics
    log_processing(
        dag_id=context.get('dag').dag_id,
        task_id=context.get('task').task_id,
        run_id=run_id,
        mep_provider='IntelliHub',
        processing_type='HHR_NORMALIZATION',
        status='completed',
        source_records=len(records),
        source_intervals=len(records),  # Long format: 1 interval per record
        intervals_processed=inserted,
        intervals_non_zero=intervals_non_zero,
        intervals_zero=intervals_zero,
        intervals_null=intervals_null,
        intervals_estimated=intervals_estimated,
        intervals_total=intervals_total,
        quality_flag_a=quality_flag_counts['A'],
        quality_flag_e=quality_flag_counts['E'],
        quality_flag_f=quality_flag_counts['F'],
        quality_flag_n=quality_flag_counts['N'],
        quality_flag_s=quality_flag_counts['S'],
        quality_flag_other=quality_flag_counts['OTHER']
    )
    
    logging.info(f"[RUN_ID:{run_id}] IntelliHub Normalization Complete:")
    logging.info(f"[RUN_ID:{run_id}] - Records processed: {processed_records}")
    logging.info(f"[RUN_ID:{run_id}] - Intervals created: {inserted}")
    logging.info(f"[RUN_ID:{run_id}] - Expected intervals: {len(records)} (long format)")
    logging.info(f"[RUN_ID:{run_id}] - Non-zero intervals: {intervals_non_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Zero intervals: {intervals_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Null intervals: {intervals_null}")
    logging.info(f"[RUN_ID:{run_id}] - Estimated intervals: {intervals_estimated}")
    logging.info(f"[RUN_ID:{run_id}] - Quality flags: A={quality_flag_counts['A']}, E={quality_flag_counts['E']}, F={quality_flag_counts['F']}, N={quality_flag_counts['N']}, S={quality_flag_counts['S']}")
    logging.info(f"[RUN_ID:{run_id}] - Errors: {error_count}")
    
    return inserted

def normalize_mtrx_hhr_data(**context):
    """Normalize MTRX HHR data"""
    normalizer = UniversalHHRNormalizer()
    
    # Generate run ID for this execution
    run_id = f"mtrx_hhr_{context['ds']}_{context['ts_nodash']}"
    
    records = normalizer.get_unprocessed_long_format_data('MTRX', 'mtrx_hhr')
    if not records:
        logging.info(f"[RUN_ID:{run_id}] No unprocessed MTRX records found")
        # Log zero processing activity
        log_processing(
            dag_id=context.get('dag').dag_id,
            task_id=context.get('task').task_id,
            run_id=run_id,
            mep_provider='MTRX',
            processing_type='HHR_NORMALIZATION',
            status='completed',
            source_records=0,
            source_intervals=0,
            intervals_processed=0,
            intervals_non_zero=0,
            intervals_zero=0,
            intervals_null=0,
            intervals_estimated=0,
            intervals_total=0,
            quality_flag_a=0,
            quality_flag_e=0,
            quality_flag_f=0,
            quality_flag_n=0,
            quality_flag_s=0,
            quality_flag_other=0
        )
        return 0
    
    logging.info(f"[RUN_ID:{run_id}] Processing {len(records)} MTRX records")
    
    all_intervals = []
    processed_records = 0
    error_count = 0
    
    # Track detailed interval statistics
    intervals_non_zero = 0
    intervals_zero = 0  
    intervals_null = 0
    intervals_estimated = 0
    intervals_total = 0
    quality_flag_counts = {'A': 0, 'E': 0, 'F': 0, 'N': 0, 'S': 0, 'OTHER': 0}
    
    for record in records:
        try:
            interval = normalizer.normalize_long_format_record(record, 'MTRX', run_id)
            all_intervals.append(interval)
            processed_records += 1
            
            # Count interval types and quality flags
            intervals_total += 1
            value = interval.get('value', 0)
            quality_flag = interval.get('quality_flag', 'N')
            was_originally_null = interval.get('was_originally_null', False)
            
            # Count by value type - check original null status first
            if was_originally_null:
                intervals_null += 1
            elif value == 0:
                intervals_zero += 1
            else:
                intervals_non_zero += 1
                
            # Count estimated intervals (E flag)
            if quality_flag == 'E':
                intervals_estimated += 1
                
            # Count quality flags
            if quality_flag in quality_flag_counts:
                quality_flag_counts[quality_flag] += 1
            else:
                quality_flag_counts['OTHER'] += 1
                
        except Exception as e:
            error_count += 1
            logging.error(f"[RUN_ID:{run_id}] Failed to process MTRX record {record[0]}: {str(e)}")
            raise
    
    inserted = normalizer.bulk_insert_intervals(all_intervals)
    
    # Log detailed processing statistics
    log_processing(
        dag_id=context.get('dag').dag_id,
        task_id=context.get('task').task_id,
        run_id=run_id,
        mep_provider='MTRX',
        processing_type='HHR_NORMALIZATION',
        status='completed',
        source_records=len(records),
        source_intervals=len(records),  # Long format: 1 interval per record
        intervals_processed=inserted,
        intervals_non_zero=intervals_non_zero,
        intervals_zero=intervals_zero,
        intervals_null=intervals_null,
        intervals_estimated=intervals_estimated,
        intervals_total=intervals_total,
        quality_flag_a=quality_flag_counts['A'],
        quality_flag_e=quality_flag_counts['E'],
        quality_flag_f=quality_flag_counts['F'],
        quality_flag_n=quality_flag_counts['N'],
        quality_flag_s=quality_flag_counts['S'],
        quality_flag_other=quality_flag_counts['OTHER']
    )
    
    logging.info(f"[RUN_ID:{run_id}] MTRX Normalization Complete:")
    logging.info(f"[RUN_ID:{run_id}] - Records processed: {processed_records}")
    logging.info(f"[RUN_ID:{run_id}] - Intervals created: {inserted}")
    logging.info(f"[RUN_ID:{run_id}] - Expected intervals: {len(records)} (long format)")
    logging.info(f"[RUN_ID:{run_id}] - Non-zero intervals: {intervals_non_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Zero intervals: {intervals_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Null intervals: {intervals_null}")
    logging.info(f"[RUN_ID:{run_id}] - Estimated intervals: {intervals_estimated}")
    logging.info(f"[RUN_ID:{run_id}] - Quality flags: A={quality_flag_counts['A']}, E={quality_flag_counts['E']}, F={quality_flag_counts['F']}, N={quality_flag_counts['N']}, S={quality_flag_counts['S']}")
    logging.info(f"[RUN_ID:{run_id}] - Errors: {error_count}")
    
    return inserted

def normalize_eiep3_data(**context):
    """Normalize EIEP3 data from bluecurrent_eiep3 table"""
    normalizer = UniversalHHRNormalizer()
    
    # Generate run ID for this execution
    run_id = f"eiep3_{context['ds']}_{context['ts_nodash']}"
    
    logging.info(f"[RUN_ID:{run_id}] Starting EIEP3 data normalization")
    
    records = normalizer.get_unprocessed_eiep3_data()
    if not records:
        logging.info(f"[RUN_ID:{run_id}] No unprocessed EIEP3 records found")
        # Log zero processing activity
        log_processing(
            dag_id=context.get('dag').dag_id,
            task_id=context.get('task').task_id,
            run_id=run_id,
            mep_provider='EIEP3',
            processing_type='HHR_NORMALIZATION',
            status='completed',
            source_records=0,
            source_intervals=0,
            intervals_processed=0,
            intervals_non_zero=0,
            intervals_zero=0,
            intervals_null=0,
            intervals_estimated=0,
            intervals_total=0,
            quality_flag_a=0,
            quality_flag_e=0,
            quality_flag_f=0,
            quality_flag_n=0,
            quality_flag_s=0,
            quality_flag_other=0
        )
        return 0
    
    logging.info(f"[RUN_ID:{run_id}] Processing {len(records)} EIEP3 records")
    
    all_intervals = []
    processed_records = 0
    error_count = 0
    
    # Track detailed interval statistics
    intervals_non_zero = 0
    intervals_zero = 0  
    intervals_null = 0
    intervals_estimated = 0
    intervals_total = 0
    quality_flag_counts = {'A': 0, 'E': 0, 'F': 0, 'N': 0, 'S': 0, 'OTHER': 0}
    
    for record in records:
        try:
            interval = normalizer.normalize_eiep3_record(record, run_id)
            if interval:
                all_intervals.append(interval)
                processed_records += 1
                
                # Count interval types and quality flags
                intervals_total += 1
                value = interval.get('value', 0)
                quality_flag = interval.get('quality_flag', 'N')
                was_originally_null = interval.get('was_originally_null', False)
                
                # Count by value type - check original null status first
                if was_originally_null:
                    intervals_null += 1
                elif value == 0:
                    intervals_zero += 1
                else:
                    intervals_non_zero += 1
                    
                # Count estimated intervals (E flag)
                if quality_flag == 'E':
                    intervals_estimated += 1
                    
                # Count quality flags
                if quality_flag in quality_flag_counts:
                    quality_flag_counts[quality_flag] += 1
                else:
                    quality_flag_counts['OTHER'] += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            logging.error(f"[RUN_ID:{run_id}] Failed to process EIEP3 record {record[0]}: {str(e)}")
            raise
    
    inserted = normalizer.bulk_insert_intervals(all_intervals)
    
    # Log detailed processing statistics
    log_processing(
        dag_id=context.get('dag').dag_id,
        task_id=context.get('task').task_id,
        run_id=run_id,
        mep_provider='EIEP3',
        processing_type='HHR_NORMALIZATION',
        status='completed',
        source_records=len(records),
        source_intervals=len(records),  # EIEP3 format: 1 interval per record
        intervals_processed=inserted,
        intervals_non_zero=intervals_non_zero,
        intervals_zero=intervals_zero,
        intervals_null=intervals_null,
        intervals_estimated=intervals_estimated,
        intervals_total=intervals_total,
        quality_flag_a=quality_flag_counts['A'],
        quality_flag_e=quality_flag_counts['E'],
        quality_flag_f=quality_flag_counts['F'],
        quality_flag_n=quality_flag_counts['N'],
        quality_flag_s=quality_flag_counts['S'],
        quality_flag_other=quality_flag_counts['OTHER']
    )
    
    logging.info(f"[RUN_ID:{run_id}] EIEP3 Normalization Complete:")
    logging.info(f"[RUN_ID:{run_id}] - Records processed: {processed_records}")
    logging.info(f"[RUN_ID:{run_id}] - Intervals created: {inserted}")
    logging.info(f"[RUN_ID:{run_id}] - Expected intervals: {len(records)} (EIEP3 format)")
    logging.info(f"[RUN_ID:{run_id}] - Non-zero intervals: {intervals_non_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Zero intervals: {intervals_zero}")
    logging.info(f"[RUN_ID:{run_id}] - Null intervals: {intervals_null}")
    logging.info(f"[RUN_ID:{run_id}] - Estimated intervals: {intervals_estimated}")
    logging.info(f"[RUN_ID:{run_id}] - Quality flags: A={quality_flag_counts['A']}, E={quality_flag_counts['E']}, F={quality_flag_counts['F']}, N={quality_flag_counts['N']}, S={quality_flag_counts['S']}")
    logging.info(f"[RUN_ID:{run_id}] - Errors: {error_count}")
    
    return inserted

def summarize_normalization(**context):
    """Summarize the normalization results"""
    
    # Get results from all tasks
    bcmm_count = context['ti'].xcom_pull(task_ids='normalize_bcmm_hhr') or 0
    smartco_count = context['ti'].xcom_pull(task_ids='normalize_smartco_hhr') or 0
    fclm_count = context['ti'].xcom_pull(task_ids='normalize_fclm_hhr') or 0
    intellihub_count = context['ti'].xcom_pull(task_ids='normalize_intellihub_hhr') or 0
    mtrx_count = context['ti'].xcom_pull(task_ids='normalize_mtrx_hhr') or 0
    eiep3_count = context['ti'].xcom_pull(task_ids='normalize_eiep3') or 0
    
    total_normalized = bcmm_count + smartco_count + fclm_count + intellihub_count + mtrx_count + eiep3_count
    
    logging.info("=== Universal HHR Normalization Summary ===")
    logging.info(f"BCMM intervals normalized: {bcmm_count:,}")
    logging.info(f"SmartCo intervals normalized: {smartco_count:,}")
    logging.info(f"FCLM intervals normalized: {fclm_count:,}")
    logging.info(f"IntelliHub intervals normalized: {intellihub_count:,}")
    logging.info(f"MTRX intervals normalized: {mtrx_count:,}")
    logging.info(f"EIEP3 intervals normalized: {eiep3_count:,}")
    logging.info(f"Total intervals normalized: {total_normalized:,}")
    
    return {
        'bcmm': bcmm_count,
        'smartco': smartco_count,
        'fclm': fclm_count,
        'intellihub': intellihub_count,
        'mtrx': mtrx_count,
        'eiep3': eiep3_count,
        'total': total_normalized
    }

# Create tasks
normalize_bcmm_task = PythonOperator(
    task_id='normalize_bcmm_hhr',
    python_callable=normalize_bcmm_hhr_data,
    dag=dag,
)

normalize_smartco_task = PythonOperator(
    task_id='normalize_smartco_hhr',
    python_callable=normalize_smartco_hhr_data,
    dag=dag,
)

normalize_fclm_task = PythonOperator(
    task_id='normalize_fclm_hhr',
    python_callable=normalize_fclm_hhr_data,
    dag=dag,
)

normalize_intellihub_task = PythonOperator(
    task_id='normalize_intellihub_hhr',
    python_callable=normalize_intellihub_hhr_data,
    dag=dag,
)

normalize_mtrx_task = PythonOperator(
    task_id='normalize_mtrx_hhr',
    python_callable=normalize_mtrx_hhr_data,
    dag=dag,
)

normalize_eiep3_task = PythonOperator(
    task_id='normalize_eiep3',
    python_callable=normalize_eiep3_data,
    dag=dag,
)

summarize_task = PythonOperator(
    task_id='summarize_normalization',
    python_callable=summarize_normalization,
    dag=dag,
)

# Set task dependencies - run all normalizations in parallel, then summarize
[normalize_bcmm_task, normalize_smartco_task, normalize_fclm_task, 
 normalize_intellihub_task, normalize_mtrx_task, normalize_eiep3_task] >> summarize_task 