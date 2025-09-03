"""
NHH Data Validation DAG
Validates Non-Half-Hourly (daily register reads) data using energy.validation app workflows
Pipeline: daily_register_reads_raw → daily_register_reads_calculated → daily_register_reads_final
"""
from datetime import datetime, timedelta, date
import logging
import os
import sys
from typing import List, Dict, Any
import uuid
import json
from django.utils import timezone
from django.utils.timezone import now as timezone_now

# Add project root to path
sys.path.insert(0, '/app')

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from airflow.models import Variable

# Add utils to path
sys.path.append("/app/airflow/utils")

from connection_manager import ConnectionManager
from energy.validation.validation_engine import ValidationEngine
from energy.validation.models import (
    ValidationWorkflow, ValidationSession, ValidationRuleExecution,
    ValidationBatch, ValidationRule, ValidationAuditLog
)
from energy.validation.failure_logger import validation_failure_logger, FailureSeverity
from users.models import Tenant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NHHValidationOrchestrator:
    """
    NHH validation orchestrator using validation app workflows
    Manages the complete validation pipeline for daily register reads
    """
    
    def __init__(self):
        self.pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        self.validation_engine = ValidationEngine()
        
    def create_validation_session(self, workflow_code: str = 'NHH_STANDARD') -> str:
        """Create a new NHH validation session"""
        
        try:
            # Get or create workflow
            workflow = ValidationWorkflow.objects.get(workflow_code=workflow_code)
        except ValidationWorkflow.DoesNotExist:
            # Create default NHH workflow
            workflow = ValidationWorkflow.objects.create(
                workflow_code=workflow_code,
                name='Standard NHH Validation',
                description='Standard non-half-hourly (daily register reads) validation workflow',
                meter_type='nhh',
                validation_rules=[
                    'MISSING_VALUE_CHECK',
                    'NEGATIVE_VALUE_CHECK', 
                    'HIGH_VALUE_CHECK',
                    'REGISTER_CONSISTENCY_CHECK',
                    'CUMULATIVE_CHECK'
                ],
                estimation_config={
                    'methods': ['linear_interpolation', 'historical_average'],
                    'confidence_threshold': 80.0,
                    'max_gap_days': 7
                },
                processing_config={
                    'batch_size': 5000,
                    'parallel_processing': True,
                    'timeout_minutes': 60
                }
            )
        
        # Get default tenant
        tenant = Tenant.objects.first()
        
        # Create validation session with dynamic date range
        session_id = f"nhh_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get actual data range from daily_register_reads table
        date_range_query = """
        SELECT 
            MIN(reading_date) as min_date,
            MAX(reading_date) as max_date,
            COUNT(*) as total_raw_readings
        FROM metering_processed.daily_register_reads
        """
        date_range_result = self.pg_hook.get_first(date_range_query)
        
        if date_range_result and date_range_result[0] and date_range_result[1]:
            start_date = date_range_result[0]
            end_date = date_range_result[1]
            total_raw_readings = date_range_result[2]
            logger.info(f"📅 Dynamic date range: {start_date} to {end_date} ({total_raw_readings:,} raw readings)")
        else:
            # Fallback to recent data if no data found
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            total_raw_readings = 0
            logger.warning(f"⚠️ No data found, using fallback range: {start_date} to {end_date}")
        
        session = ValidationSession.objects.create(
            tenant=tenant,
            session_id=session_id,
            workflow=workflow,
            start_date=start_date,
            end_date=end_date,
            status='pending'
        )
        
        logger.info(f"🚀 Created NHH validation session: {session_id}")
        return session_id
    
    def get_unprocessed_readings(self, session_id: str, limit: int = 25000) -> List[Dict]:
        """Get unprocessed daily register readings for validation"""
        
        session = ValidationSession.objects.get(session_id=session_id)
        
        # Smart date range detection - only process new data
        smart_date_query = """
        WITH recent_processed AS (
            SELECT MAX(reading_date) as last_processed_date
            FROM metering_processed.daily_register_reads_calculated
        ),
        recent_raw AS (
            SELECT 
                MIN(reading_date) as earliest_raw,
                MAX(reading_date) as latest_raw,
                COUNT(*) as total_raw
            FROM metering_processed.daily_register_reads
        ),
        unprocessed_range AS (
            SELECT 
                CASE 
                    WHEN rp.last_processed_date IS NULL THEN rr.earliest_raw
                    ELSE GREATEST(rp.last_processed_date, rr.earliest_raw)
                END as start_date,
                rr.latest_raw as end_date,
                rr.total_raw
            FROM recent_processed rp
            CROSS JOIN recent_raw rr
        )
        SELECT start_date, end_date, total_raw FROM unprocessed_range
        """
        
        date_range_result = self.pg_hook.get_first(smart_date_query)
        
        if date_range_result:
            smart_start_date = date_range_result[0]
            smart_end_date = date_range_result[1]
            total_raw_readings = date_range_result[2]
            
            logger.info(f"🧠 SMART PROCESSING - Auto-detected optimal range: {smart_start_date} to {smart_end_date}")
            logger.info(f"🧠 SMART PROCESSING - Total raw readings in system: {total_raw_readings:,}")
            
            # Update session with smart date range
            session.start_date = smart_start_date
            session.end_date = smart_end_date
            session.save()
        else:
            # Fallback to session dates
            smart_start_date = session.start_date
            smart_end_date = session.end_date
            logger.warning("⚠️ Could not determine smart date range, using session defaults")
        
        # Count unprocessed readings first
        count_query = """
        SELECT COUNT(*) 
        FROM metering_processed.daily_register_reads r
        WHERE r.reading_date >= %s
        AND r.reading_date <= %s
        """
        
        unprocessed_count = self.pg_hook.get_first(count_query, parameters=[
            smart_start_date,
            smart_end_date
        ])[0]
        
        logger.info(f"🧠 SMART PROCESSING - Found {unprocessed_count:,} unprocessed readings in optimal range")
        
        if unprocessed_count == 0:
            logger.info("✅ SMART PROCESSING - All data is already processed, nothing to do!")
            return []
        
        # Adjust limit if needed
        actual_limit = min(limit, unprocessed_count + 1000)  # Small buffer for safety
        
        if unprocessed_count > limit:
            logger.warning(f"⚠️ SMART PROCESSING - {unprocessed_count:,} readings exceed limit of {limit:,}, will process in batches")
        
        query = """
        SELECT 
            r.id,
            r.tenant_id,
            r.connection_id as icp_id,
            '' as meter_serial_number,
            r.register_code as meter_register_id,
            r.reading_date,
            r.end_reading as register_reading,
            r.start_reading as previous_reading,
            r.consumption as consumption_kwh,
            r.quality_flag,
            '' as validation_flag,
            r.source,
            '' as source_file_name,
            r.metadata
        FROM metering_processed.daily_register_reads r
        WHERE r.reading_date >= %s
        AND r.reading_date <= %s
        ORDER BY r.reading_date DESC, r.connection_id, r.register_code
        LIMIT %s
        """
        
        records = self.pg_hook.get_records(query, parameters=[
            smart_start_date, 
            smart_end_date,
            actual_limit
        ])
        
        # Convert to dictionaries
        columns = ['id', 'tenant_id', 'icp_id', 'meter_serial_number', 'meter_register_id', 
                  'reading_date', 'register_reading', 'previous_reading', 'consumption_kwh', 
                  'quality_flag', 'validation_flag', 'source', 'source_file_name', 'metadata']
        
        readings = []
        for record in records:
            reading_dict = dict(zip(columns, record))
            # Convert UUID objects to strings for JSON serialization
            reading_dict = self._sanitize_for_json_selective(reading_dict)
            readings.append(reading_dict)
        
        # Update session statistics
        session.total_readings = len(readings)
        session.status = 'processing'
        session.started_at = datetime.now()
        session.save()
        
        # Smart processing summary
        processing_efficiency = (len(readings) / unprocessed_count * 100) if unprocessed_count > 0 else 100
        
        logger.info(f"📊 SMART PROCESSING SUMMARY:")
        logger.info(f"   🎯 Target unprocessed: {unprocessed_count:,}")
        logger.info(f"   📦 Retrieved for processing: {len(readings):,}")
        logger.info(f"   ⚡ Processing efficiency: {processing_efficiency:.1f}%")
        logger.info(f"   📅 Date range: {smart_start_date} to {smart_end_date}")
        
        if len(readings) < unprocessed_count:
            remaining = unprocessed_count - len(readings)
            logger.info(f"   ⏭️  Remaining for next run: {remaining:,}")
        
        return readings
    
    def _sanitize_for_json_selective(self, obj):
        """Convert UUID objects to strings but preserve datetime objects for validation logic"""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json_selective(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json_selective(item) for item in obj]
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'UUID':
            return str(obj)
        # Keep datetime objects as-is for validation logic
        else:
            return obj
    
    def execute_validation_workflow(self, session_id: str, readings: List[Dict]) -> List[Dict]:
        """Execute NHH validation workflow according to session configuration"""
        
        session = ValidationSession.objects.get(session_id=session_id)
        workflow = session.workflow
        
        logger.info(f"📊 PIPELINE TRACKING - Starting NHH validation workflow for {len(readings)} readings")
        logger.info(f"📊 PIPELINE TRACKING - Validation rules: {workflow.validation_rules}")
        
        validated_readings = []
        
        # Process readings in batches
        batch_size = workflow.processing_config.get('batch_size', 1000)
        total_batches = (len(readings) - 1) // batch_size + 1
        
        logger.info(f"📊 PIPELINE TRACKING - Processing {len(readings)} readings in {total_batches} batches of {batch_size}")
        
        for i in range(0, len(readings), batch_size):
            batch = readings[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"🔍 PIPELINE TRACKING - Processing batch {batch_num}/{total_batches} ({len(batch)} readings)")
            
            # Execute validation rules in order
            for rule_idx, rule_code in enumerate(workflow.validation_rules):
                batch_before = len(batch)
                batch = self._execute_validation_rule(session, rule_code, batch)
                batch_after = len(batch)
                
                if batch_before != batch_after:
                    logger.warning(f"⚠️ PIPELINE TRACKING - Rule {rule_code} changed batch size from {batch_before} to {batch_after}")
                
                logger.info(f"📊 PIPELINE TRACKING - Batch {batch_num}: Rule {rule_idx+1}/{len(workflow.validation_rules)} ({rule_code}) processed {len(batch)} readings")
            
            validated_readings.extend(batch)
            logger.info(f"📊 PIPELINE TRACKING - Batch {batch_num} complete: {len(batch)} readings added to validated set")
        
        # Count validation results
        validation_stats = {
            'total': len(validated_readings),
            'valid': len([r for r in validated_readings if r.get('validation_flag') == 'V']),
            'suspect': len([r for r in validated_readings if r.get('validation_flag') == 'S']),
            'estimated': len([r for r in validated_readings if r.get('validation_flag') == 'E']),
            'is_estimated': len([r for r in validated_readings if r.get('is_estimated', False)])
        }
        
        logger.info(f"📊 PIPELINE TRACKING - NHH Validation complete: {validation_stats}")
        
        # Update session progress
        session.processed_readings = len(validated_readings)
        session.valid_readings = validation_stats['valid']
        session.estimated_readings = validation_stats['is_estimated']
        session.save()
        
        return validated_readings
    
    def _execute_validation_rule(self, session: ValidationSession, rule_code: str, readings: List[Dict]) -> List[Dict]:
        """Execute a specific validation rule for NHH data"""
        
        try:
            rule = ValidationRule.objects.get(rule_code=rule_code)
        except ValidationRule.DoesNotExist:
            logger.warning(f"⚠️ Validation rule {rule_code} not found, skipping")
            return readings

        # Create rule execution record
        execution = ValidationRuleExecution.objects.create(
            session=session,
            rule=rule,
            execution_order=1,  # Simplified for now
            status='running'
        )

        start_time = timezone.now()

        try:
            # Apply rule logic based on rule type
            if rule.rule_type == 'range_check':
                readings = self._apply_range_check(rule, readings)
            elif rule.rule_type == 'register_consistency':
                readings = self._apply_register_consistency_check(rule, readings)
            elif rule.rule_type == 'cumulative_check':
                readings = self._apply_cumulative_check(rule, readings)
            elif rule.rule_type == 'missing_data':
                readings = self._apply_missing_data_check(rule, readings)
            else:
                logger.warning(f"⚠️ Unknown rule type: {rule.rule_type}")

            # Track validation results for each reading
            for reading in readings:
                # Initialize validation tracking if not exists
                if 'validation_rules_applied' not in reading:
                    reading['validation_rules_applied'] = []
                if 'validation_results' not in reading:
                    reading['validation_results'] = {}
                
                # Add this rule to the applied rules
                reading['validation_rules_applied'].append(rule_code)
                
                # Record the result
                reading['validation_results'][rule_code] = {
                    'passed': reading.get('validation_flag', 'V') == 'V',
                    'rule_type': rule.rule_type,
                    'execution_time': start_time.isoformat(),
                    'notes': reading.get('validation_notes', '')
                }

            # Update execution record
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.processing_time_ms = int((execution.completed_at - start_time).total_seconds() * 1000)
            execution.readings_processed = len(readings)
            execution.readings_passed = len([r for r in readings if r.get('validation_flag') == 'V'])
            execution.readings_failed = len([r for r in readings if r.get('validation_flag') in ['S', 'E']])
            execution.save()

            logger.info(f"✅ Completed rule {rule_code}: {execution.readings_passed}/{execution.readings_processed} passed")

        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.save()
            logger.error(f"❌ Rule {rule_code} failed: {e}")

        return readings
    
    def _apply_range_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply range check validation rule for NHH data"""
        
        params = rule.parameters
        min_consumption = params.get('min_consumption', 0)
        max_consumption = params.get('max_consumption', 10000)  # 10,000 kWh per day is high but possible
        
        for reading in readings:
            consumption = reading.get('consumption_kwh', 0)
            
            if consumption is None:
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = 'Missing consumption value'
            elif consumption < min_consumption or consumption > max_consumption:
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = f'Consumption {consumption} outside range [{min_consumption}, {max_consumption}]'
            else:
                reading['validation_flag'] = reading.get('validation_flag', 'V')
        
        return readings
    
    def _apply_register_consistency_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply register consistency check for NHH data"""
        
        for reading in readings:
            current_reading = reading.get('register_reading')
            previous_reading = reading.get('previous_reading')
            consumption = reading.get('consumption_kwh')
            
            if current_reading is not None and previous_reading is not None:
                calculated_consumption = current_reading - previous_reading
                
                # Allow for small rounding differences
                if abs(calculated_consumption - consumption) > 0.1:
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = f'Consumption mismatch: calculated {calculated_consumption}, recorded {consumption}'
            
        return readings
    
    def _apply_cumulative_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply cumulative check for register readings"""
        
        # Group by meter for cumulative checks
        meter_groups = {}
        for reading in readings:
            key = (reading['icp_id'], reading['meter_register_id'])
            if key not in meter_groups:
                meter_groups[key] = []
            meter_groups[key].append(reading)
        
        # Check for cumulative consistency within each meter group
        for meter_readings in meter_groups.values():
            meter_readings.sort(key=lambda x: x['reading_date'])
            
            for i in range(1, len(meter_readings)):
                current = meter_readings[i]
                previous = meter_readings[i-1]
                
                current_register = current.get('register_reading')
                previous_register = previous.get('register_reading')
                
                if current_register is not None and previous_register is not None:
                    # Check for rollover (meter reset)
                    if current_register < previous_register:
                        # Potential rollover - mark as suspect for manual review
                        current['validation_flag'] = 'S'
                        current['validation_notes'] = f'Potential meter rollover: {previous_register} → {current_register}'
        
        return readings
    
    def _apply_missing_data_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply missing data check validation rule"""
        
        for reading in readings:
            if reading.get('register_reading') is None:
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = 'Missing register reading'
                reading['requires_estimation'] = True
        
        return readings
    
    def store_calculated_readings(self, session_id: str, validated_readings: List[Dict]) -> int:
        """Store validated NHH readings in daily_register_reads_calculated table"""
        
        if not validated_readings:
            logger.warning("⚠️ No validated readings to store")
            return 0

        logger.info(f"📊 PIPELINE TRACKING - Starting storage of {len(validated_readings)} validated NHH readings")
        
        # Prepare bulk insert
        insert_query = """
        INSERT INTO metering_processed.daily_register_reads_calculated (
            raw_reading_id, tenant_id, icp_id, meter_serial_number, meter_register_id, reading_date,
            register_reading, previous_reading, consumption_calculated, original_quality_flag, quality_flag, 
            validation_flag, spoton_validation_flag, validation_rules_applied, validation_results,
            source, source_file_name, processing_notes, metadata, calculated_at
        ) VALUES %s
        ON CONFLICT (icp_id, meter_register_id, reading_date, source) 
        DO NOTHING
        """
        
        # Prepare values
        values = []
        for reading in validated_readings:
            # Debug: Check for problematic data
            validation_rules = reading.get('validation_rules_applied', [])
            if isinstance(validation_rules, list):
                validation_rules_str = '{' + ','.join(f'"{rule}"' for rule in validation_rules) + '}'
            else:
                validation_rules_str = '{}'
            
            values.append((
                reading.get('id'),
                reading.get('tenant_id'),
                reading['icp_id'],
                reading.get('meter_serial_number'),
                reading['meter_register_id'],
                reading['reading_date'],
                reading.get('register_reading'),
                reading.get('previous_reading'),
                reading.get('consumption_kwh'),
                reading.get('quality_flag'),  # original_quality_flag
                reading.get('quality_flag'),  # quality_flag
                reading.get('validation_flag', 'V'),  # validation_flag
                reading.get('spoton_validation_result', 'V'),  # spoton_validation_flag
                validation_rules_str,  # validation_rules_applied as PostgreSQL array
                json.dumps(reading.get('validation_results', {})),  # validation_results as JSON
                reading['source'],
                reading.get('source_file_name'),
                reading.get('validation_notes'),
                json.dumps(reading.get('metadata', {})),
                datetime.now()
            ))
        
        logger.info(f"📊 PIPELINE TRACKING - Prepared {len(values)} values for database insertion")
        
        # Execute bulk insert
        from psycopg2.extras import execute_values
        
        conn = self.pg_hook.get_conn()
        cursor = conn.cursor()
        
        try:
            execute_values(cursor, insert_query, values, template=None, page_size=1000)
            conn.commit()
            
            # Get the actual number of inserted rows
            inserted_count = cursor.rowcount
            logger.info(f"💾 PIPELINE TRACKING - Attempted to store {len(values)} readings, actually inserted {inserted_count} new readings")
            
            # Update session
            session = ValidationSession.objects.get(session_id=session_id)
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.processing_duration = session.completed_at - session.started_at
            session.save()
            
            return inserted_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to store calculated readings: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


# DAG Definition
default_args = {
    'owner': 'data-validation',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'nhh_validation_workflow',
    default_args=default_args,
    description='NHH Data Validation using Validation App Workflows',
    schedule_interval='0 */12 * * *',  # Every 12 hours, after DRR normalization
    catchup=False,
    max_active_runs=1,
    tags=['validation', 'nhh', 'metering', 'daily_reads']
)


def create_validation_session_task(**context):
    """Create validation session"""
    orchestrator = NHHValidationOrchestrator()
    session_id = orchestrator.create_validation_session()
    context['ti'].xcom_push(key='session_id', value=session_id)
    return session_id


def get_unprocessed_readings_task(**context):
    """Get unprocessed readings for validation"""
    session_id = context['ti'].xcom_pull(key='session_id')
    orchestrator = NHHValidationOrchestrator()
    readings = orchestrator.get_unprocessed_readings(session_id)
    context['ti'].xcom_push(key='readings', value=readings)
    return len(readings)


def execute_validation_workflow_task(**context):
    """Execute validation workflow"""
    session_id = context['ti'].xcom_pull(key='session_id')
    readings = context['ti'].xcom_pull(key='readings')
    
    if not readings:
        logger.info("No readings to validate")
        return 0
    
    orchestrator = NHHValidationOrchestrator()
    validated_readings = orchestrator.execute_validation_workflow(session_id, readings)
    context['ti'].xcom_push(key='validated_readings', value=validated_readings)
    return len(validated_readings)


def store_calculated_readings_task(**context):
    """Store calculated readings"""
    session_id = context['ti'].xcom_pull(key='session_id')
    validated_readings = context['ti'].xcom_pull(key='validated_readings')
    
    if not validated_readings:
        logger.info("No validated readings to store")
        return 0
    
    orchestrator = NHHValidationOrchestrator()
    return orchestrator.store_calculated_readings(session_id, validated_readings)


# Task Definitions
create_session = PythonOperator(
    task_id='create_validation_session',
    python_callable=create_validation_session_task,
    dag=dag
)

get_readings = PythonOperator(
    task_id='get_unprocessed_readings',
    python_callable=get_unprocessed_readings_task,
    dag=dag
)

execute_validation = PythonOperator(
    task_id='execute_validation_workflow',
    python_callable=execute_validation_workflow_task,
    dag=dag
)

store_results = PythonOperator(
    task_id='store_calculated_readings',
    python_callable=store_calculated_readings_task,
    dag=dag
)

# Task Dependencies
create_session >> get_readings >> execute_validation >> store_results 