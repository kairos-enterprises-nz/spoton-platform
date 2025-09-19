"""
Universal DRR Normalization DAG - Normalize ALL MEP DRR data into daily_register_reads

This DAG processes Daily Register Reading (DRR) data from all MEP providers and normalizes it into the
metering_processed.daily_register_reads table with proper ICP → Meter → Register hierarchy.

Supports:
- BCMM DRR (cumulative readings)
- FCLM DRR (cumulative readings) 
- SmartCo DRR (cumulative readings)
- IntelliHub DRR (cumulative readings)
- MTRX DRR (cumulative readings)

Author: AI Assistant
Date: 2025-07-04
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging
import uuid
import json
from typing import List, Dict, Tuple

# DAG Configuration
default_args = {
    'owner': 'data-transform',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'drr_data_normalization',
    default_args=default_args,
    description='Normalize ALL MEP DRR data into daily_register_reads',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    max_active_runs=1,
    tags=['metering', 'drr', 'normalization'],
)

class UniversalDRRNormalizer:
    """Universal DRR data normalizer for all MEP providers"""
    
    def __init__(self):
        self.pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    def get_unprocessed_drr_data(self, mep_provider: str, table_name: str) -> List:
        """Get unprocessed DRR data for a specific MEP provider"""
        
        # Define MEP-specific column mappings
        column_mappings = {
            'BCMM': {
                'columns': ['id', 'icp', 'read_date', 'meter_number', 'register_channel', 
                           'reading', 'read_type', 'read_time', 'register_id', 'units', 'file_name'],
                'date_field': 'read_date',
                'meter_field': 'meter_number',
                'register_field': 'register_channel',
                'reading_field': 'reading',
                'type_field': 'read_type',
                'time_field': 'read_time',
                'file_field': 'file_name'
            },
            'FCLM': {
                'columns': ['id', 'icp', 'read_date', 'register_id', 'reading', 
                           'read_type', 'read_time', 'meter_serial', 'filename'],
                'date_field': 'read_date',
                'meter_field': 'meter_serial',
                'register_field': 'register_id',
                'reading_field': 'reading',
                'type_field': 'read_type',
                'time_field': 'read_time',
                'file_field': 'filename'
            },
            'SmartCo': {
                'columns': ['id', 'icp', 'read_date', 'meter_number', 'register_channel', 
                           'midnight_read', 'read_type', 'read_time', 'file_name'],
                'date_field': 'read_date',
                'meter_field': 'meter_number',
                'register_field': 'register_channel',
                'reading_field': 'midnight_read',
                'type_field': 'read_type',
                'time_field': 'read_time',
                'file_field': 'file_name'
            },
            'IntelliHub': {
                'columns': ['id', 'icp', 'meter_serial', 'read_date', 'register_channel', 
                           'read_type', 'register_number', 'energy_flow', 'rcc', 'units', 
                           'stop_time', 'reading', 'filename'],
                'date_field': 'read_date',
                'meter_field': 'meter_serial',
                'register_field': 'register_channel',
                'reading_field': 'reading',
                'type_field': 'read_type',
                'time_field': 'stop_time',
                'file_field': 'filename'
            },
            'MTRX': {
                'columns': ['id', 'icp', 'meter_serial', 'read_date', 'register_channel', 
                           'read_type', 'register_number', 'energy_flow', 'rcc', 'units', 
                           'stop_time', 'reading', 'filename'],
                'date_field': 'read_date',
                'meter_field': 'meter_serial',
                'register_field': 'register_channel',
                'reading_field': 'reading',
                'type_field': 'read_type',
                'time_field': 'stop_time',
                'file_field': 'filename'
            }
        }
        
        mapping = column_mappings.get(mep_provider, column_mappings['BCMM'])
        
        query = f"""
        SELECT {', '.join(mapping['columns'])}
        FROM metering_raw.{table_name} d
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.daily_register_reads p
            WHERE p.icp_id = d.icp 
            AND p.reading_date = CASE 
                WHEN d.{mapping['date_field']}::text ~ '^[0-9]{{8}}$' 
                THEN TO_DATE(d.{mapping['date_field']}::text, 'YYYYMMDD')
                ELSE d.{mapping['date_field']}::date
            END
            AND p.source = '{mep_provider}'
            AND p.register_code = d.{mapping['register_field']}::text
        )
        AND d.imported_at >= NOW() - INTERVAL '30 days'
        ORDER BY d.{mapping['date_field']}, d.id
        LIMIT 1000
        """
        
        records = self.pg_hook.get_records(query)
        logging.info(f"Found {len(records)} unprocessed {mep_provider} DRR records")
        
        return records, mapping
    
    def normalize_drr_record(self, record: Tuple, mapping: Dict, mep_provider: str) -> Dict:
        """Normalize a single DRR record into daily_register_reads format"""
        
        # Extract fields based on MEP provider mapping
        record_dict = dict(zip(mapping['columns'], record))
        
        # Parse date
        read_date_str = str(record_dict[mapping['date_field']])
        try:
            if read_date_str.isdigit() and len(read_date_str) == 8:
                # YYYYMMDD format
                read_date = datetime.strptime(read_date_str, '%Y%m%d').date()
            else:
                # ISO format or other
                read_date = datetime.fromisoformat(read_date_str.replace('Z', '+00:00')).date()
        except:
            logging.warning(f"Invalid date format: {read_date_str}")
            return None
        
        # Parse reading value
        reading_value = record_dict.get(mapping['reading_field'])
        if reading_value is None or str(reading_value).strip() == '':
            logging.warning(f"No reading value for record: {record_dict}")
            return None
        
        try:
            reading_float = float(reading_value)
        except (ValueError, TypeError):
            logging.warning(f"Invalid reading value: {reading_value}")
            return None
        
        # Extract other fields
        icp = record_dict['icp']
        meter_serial = record_dict.get(mapping['meter_field'], '')
        register_code = str(record_dict.get(mapping['register_field'], ''))
        read_type = record_dict.get(mapping['type_field'], 'A')
        file_name = record_dict.get(mapping['file_field'], '')
        
        # Parse read timestamp if available
        read_timestamp = None
        time_field = record_dict.get(mapping.get('time_field'))
        if time_field and str(time_field).strip():
            try:
                if time_field.isdigit() and len(str(time_field)) == 6:
                    # HHMMSS format
                    time_str = str(time_field).zfill(6)
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                    read_timestamp = datetime.combine(read_date, datetime.min.time().replace(
                        hour=hour, minute=minute, second=second))
                else:
                    # ISO format
                    read_timestamp = datetime.fromisoformat(str(time_field).replace('Z', '+00:00'))
            except:
                pass
        
        # Create metadata
        metadata = {
            'source_system': mep_provider,
            'source_record_id': record_dict.get('id'),
            'original_read_type': read_type,
            'original_register_field': record_dict.get(mapping['register_field'])
        }
        
        # Add MEP-specific metadata
        if mep_provider == 'IntelliHub' or mep_provider == 'MTRX':
            metadata.update({
                'energy_flow': record_dict.get('energy_flow'),
                'rcc': record_dict.get('rcc'),
                'register_number': record_dict.get('register_number')
            })
        elif mep_provider == 'BCMM':
            metadata.update({
                'register_id': record_dict.get('register_id'),
                'units': record_dict.get('units')
            })
        
        return {
            'tenant_id': str(uuid.uuid4()),
            'icp_id': icp,
            'register_code': register_code,
            'reading_date': read_date,
            'start_reading': 0.0,  # DRR typically has cumulative readings, not start/end
            'end_reading': reading_float,
            'consumption': reading_float,  # For cumulative readings, consumption = end_reading
            'unit': 'kWh',
            'read_type': 'actual' if read_type in ['A', 'R'] else 'estimated',
            'quality_flag': 'valid' if read_type in ['A', 'R'] else 'estimated',
            'source': mep_provider,
            'metadata': json.dumps(metadata),
            'created_at': datetime.now(),
            # Enhanced hierarchy columns
            'meter_serial_number': meter_serial,
            'meter_register_id': register_code,
            'read_timestamp': read_timestamp,
            'validation_flag': read_type,
            'source_file_name': file_name
        }
    
    def bulk_insert_daily_readings(self, daily_records: List[Dict]) -> int:
        """Bulk insert daily register readings with deduplication"""
        
        if not daily_records:
            return 0
        
        # Deduplicate records by unique key (icp_id, register_code, reading_date, source)
        # Keep the last record for each unique combination
        unique_records = {}
        for record in daily_records:
            key = (record['icp_id'], record['register_code'], record['reading_date'], record['source'])
            unique_records[key] = record
        
        deduplicated_records = list(unique_records.values())
        
        if len(deduplicated_records) != len(daily_records):
            logging.info(f"Deduplicated {len(daily_records)} records to {len(deduplicated_records)} unique records")
            
        insert_query = """
        INSERT INTO metering_processed.daily_register_reads (
            tenant_id, icp_id, register_code, reading_date, start_reading, end_reading, consumption,
            unit, read_type, quality_flag, source, metadata, created_at,
            meter_serial_number, meter_register_id, read_timestamp, validation_flag, source_file_name
        ) VALUES %s
        ON CONFLICT (icp_id, register_code, reading_date, source) 
        DO UPDATE SET
            start_reading = EXCLUDED.start_reading,
            end_reading = EXCLUDED.end_reading,
            consumption = EXCLUDED.consumption,
            quality_flag = EXCLUDED.quality_flag,
            metadata = EXCLUDED.metadata,
            created_at = EXCLUDED.created_at,
            meter_serial_number = EXCLUDED.meter_serial_number,
            meter_register_id = EXCLUDED.meter_register_id,
            read_timestamp = EXCLUDED.read_timestamp,
            validation_flag = EXCLUDED.validation_flag,
            source_file_name = EXCLUDED.source_file_name
        """
        
        # Prepare data tuples
        data_tuples = [
            (
                record['tenant_id'], record['icp_id'], record['register_code'],
                record['reading_date'], record['start_reading'], record['end_reading'], record['consumption'],
                record['unit'], record['read_type'], record['quality_flag'], record['source'],
                record['metadata'], record['created_at'],
                record['meter_serial_number'], record['meter_register_id'],
                record['read_timestamp'], record['validation_flag'], record['source_file_name']
            )
            for record in deduplicated_records
        ]
        
        # Use execute_values for bulk insert
        from psycopg2.extras import execute_values
        
        with self.pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, insert_query, data_tuples)
                conn.commit()
        
        return len(deduplicated_records)

# Task functions for each MEP provider
def normalize_bcmm_drr_data(**context):
    """Normalize BCMM DRR data"""
    normalizer = UniversalDRRNormalizer()
    
    records, mapping = normalizer.get_unprocessed_drr_data('BCMM', 'bcmm_drr')
    if not records:
        logging.info("No unprocessed BCMM DRR records found")
        return 0
    
    daily_readings = []
    for record in records:
        normalized = normalizer.normalize_drr_record(record, mapping, 'BCMM')
        if normalized:
            daily_readings.append(normalized)
    
    inserted = normalizer.bulk_insert_daily_readings(daily_readings)
    logging.info(f"Normalized {len(records)} BCMM DRR records into {inserted} daily readings")
    return inserted

def normalize_fclm_drr_data(**context):
    """Normalize FCLM DRR data"""
    normalizer = UniversalDRRNormalizer()
    
    records, mapping = normalizer.get_unprocessed_drr_data('FCLM', 'fclm_drr')
    if not records:
        logging.info("No unprocessed FCLM DRR records found")
        return 0
    
    daily_readings = []
    for record in records:
        normalized = normalizer.normalize_drr_record(record, mapping, 'FCLM')
        if normalized:
            daily_readings.append(normalized)
    
    inserted = normalizer.bulk_insert_daily_readings(daily_readings)
    logging.info(f"Normalized {len(records)} FCLM DRR records into {inserted} daily readings")
    return inserted

def normalize_smartco_drr_data(**context):
    """Normalize SmartCo DRR data"""
    normalizer = UniversalDRRNormalizer()
    
    records, mapping = normalizer.get_unprocessed_drr_data('SmartCo', 'smartco_drr')
    if not records:
        logging.info("No unprocessed SmartCo DRR records found")
        return 0
    
    daily_readings = []
    for record in records:
        normalized = normalizer.normalize_drr_record(record, mapping, 'SmartCo')
        if normalized:
            daily_readings.append(normalized)
    
    inserted = normalizer.bulk_insert_daily_readings(daily_readings)
    logging.info(f"Normalized {len(records)} SmartCo DRR records into {inserted} daily readings")
    return inserted

def normalize_intellihub_drr_data(**context):
    """Normalize IntelliHub DRR data"""
    normalizer = UniversalDRRNormalizer()
    
    records, mapping = normalizer.get_unprocessed_drr_data('IntelliHub', 'intellihub_drr')
    if not records:
        logging.info("No unprocessed IntelliHub DRR records found")
        return 0
    
    daily_readings = []
    for record in records:
        normalized = normalizer.normalize_drr_record(record, mapping, 'IntelliHub')
        if normalized:
            daily_readings.append(normalized)
    
    inserted = normalizer.bulk_insert_daily_readings(daily_readings)
    logging.info(f"Normalized {len(records)} IntelliHub DRR records into {inserted} daily readings")
    return inserted

def normalize_mtrx_drr_data(**context):
    """Normalize MTRX DRR data"""
    normalizer = UniversalDRRNormalizer()
    
    records, mapping = normalizer.get_unprocessed_drr_data('MTRX', 'mtrx_drr')
    if not records:
        logging.info("No unprocessed MTRX DRR records found")
        return 0
    
    daily_readings = []
    for record in records:
        normalized = normalizer.normalize_drr_record(record, mapping, 'MTRX')
        if normalized:
            daily_readings.append(normalized)
    
    inserted = normalizer.bulk_insert_daily_readings(daily_readings)
    logging.info(f"Normalized {len(records)} MTRX DRR records into {inserted} daily readings")
    return inserted

def summarize_drr_normalization(**context):
    """Summarize the DRR normalization results"""
    
    # Get results from all tasks
    bcmm_count = context['ti'].xcom_pull(task_ids='normalize_bcmm_drr') or 0
    fclm_count = context['ti'].xcom_pull(task_ids='normalize_fclm_drr') or 0
    smartco_count = context['ti'].xcom_pull(task_ids='normalize_smartco_drr') or 0
    intellihub_count = context['ti'].xcom_pull(task_ids='normalize_intellihub_drr') or 0
    mtrx_count = context['ti'].xcom_pull(task_ids='normalize_mtrx_drr') or 0
    
    total_normalized = bcmm_count + fclm_count + smartco_count + intellihub_count + mtrx_count
    
    logging.info("=== Universal DRR Normalization Summary ===")
    logging.info(f"BCMM daily readings normalized: {bcmm_count:,}")
    logging.info(f"FCLM daily readings normalized: {fclm_count:,}")
    logging.info(f"SmartCo daily readings normalized: {smartco_count:,}")
    logging.info(f"IntelliHub daily readings normalized: {intellihub_count:,}")
    logging.info(f"MTRX daily readings normalized: {mtrx_count:,}")
    logging.info(f"Total daily readings normalized: {total_normalized:,}")
    
    return {
        'bcmm': bcmm_count,
        'fclm': fclm_count,
        'smartco': smartco_count,
        'intellihub': intellihub_count,
        'mtrx': mtrx_count,
        'total': total_normalized
    }

# Create tasks
normalize_bcmm_drr_task = PythonOperator(
    task_id='normalize_bcmm_drr',
    python_callable=normalize_bcmm_drr_data,
    dag=dag,
)

normalize_fclm_drr_task = PythonOperator(
    task_id='normalize_fclm_drr',
    python_callable=normalize_fclm_drr_data,
    dag=dag,
)

normalize_smartco_drr_task = PythonOperator(
    task_id='normalize_smartco_drr',
    python_callable=normalize_smartco_drr_data,
    dag=dag,
)

normalize_intellihub_drr_task = PythonOperator(
    task_id='normalize_intellihub_drr',
    python_callable=normalize_intellihub_drr_data,
    dag=dag,
)

normalize_mtrx_drr_task = PythonOperator(
    task_id='normalize_mtrx_drr',
    python_callable=normalize_mtrx_drr_data,
    dag=dag,
)

summarize_task = PythonOperator(
    task_id='summarize_drr_normalization',
    python_callable=summarize_drr_normalization,
    dag=dag,
)

# Set task dependencies (parallel processing)
[normalize_bcmm_drr_task, normalize_fclm_drr_task, normalize_smartco_drr_task, 
 normalize_intellihub_drr_task, normalize_mtrx_drr_task] >> summarize_task