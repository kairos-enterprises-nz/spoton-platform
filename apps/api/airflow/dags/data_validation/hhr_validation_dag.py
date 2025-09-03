"""
HHR Data Validation DAG with Simplified 3-Table Architecture
Validates normalized interval readings using energy.validation app workflows
Pipeline: interval_reads_raw → interval_reads_calculated → interval_reads_final
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

class HHRValidationOrchestrator:
    """
    Enhanced HHR validation orchestrator using validation app workflows
    Manages the complete validation pipeline with proper audit trail
    """
    
    def __init__(self):
        self.pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        self.validation_engine = ValidationEngine()
        
    def create_validation_session(self, workflow_code: str = 'HHR_STANDARD') -> str:
        """Create a new validation session"""
        
        # Get default tenant first
        tenant = Tenant.objects.first()
        if not tenant:
            raise Exception("No tenant found. Please create a tenant first.")
        
        try:
            # Get or create workflow
            workflow = ValidationWorkflow.objects.get(workflow_code=workflow_code)
        except ValidationWorkflow.DoesNotExist:
            # Create default HHR workflow
            workflow = ValidationWorkflow.objects.create(
                tenant=tenant,
                workflow_code=workflow_code,
                name='Standard HHR Validation',
                description='Standard half-hourly reading validation workflow',
                meter_type='hhr',
                validation_rules=[
                    'MISSING_VALUE_CHECK',
                    'NEGATIVE_VALUE_CHECK', 
                    'HIGH_VALUE_CHECK',
                    'PLAUSIBILITY_CHECK',
                    'CONTINUITY_CHECK'
                ],
                estimation_config={
                    'methods': ['interpolation', 'historical_average'],
                    'confidence_threshold': 70.0,
                    'max_gap_hours': 4
                },
                processing_config={
                    'batch_size': 10000,
                    'parallel_processing': True,
                    'timeout_minutes': 30
                }
            )
        
        # Create validation session with dynamic date range
        session_id = f"hhr_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get actual data range from interval_reads_raw
        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        date_range_query = """
        SELECT 
            MIN(DATE(timestamp)) as min_date,
            MAX(DATE(timestamp)) as max_date,
            COUNT(*) as total_raw_readings
        FROM metering_processed.interval_reads_raw
        """
        date_range_result = pg_hook.get_first(date_range_query)
        
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
        
        logger.info(f"🚀 Created validation session: {session_id}")
        return session_id
    
    def _sanitize_for_json(self, obj):
        """Convert UUID objects to strings for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'UUID':
            return str(obj)
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        else:
            return obj
    
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

    def get_unprocessed_readings(self, session_id: str, limit: int = 50000) -> List[Dict]:
        """Get unprocessed interval readings for validation - Smart processing of new data only"""
        
        session = ValidationSession.objects.get(session_id=session_id)
        
        # Smart date range detection - only process new data
        smart_date_query = """
        WITH recent_processed AS (
            SELECT MAX(DATE(timestamp)) as last_processed_date
            FROM metering_processed.interval_reads_calculated
        ),
        recent_raw AS (
            SELECT 
                MIN(DATE(timestamp)) as earliest_raw,
                MAX(DATE(timestamp)) as latest_raw,
                COUNT(*) as total_raw
            FROM metering_processed.interval_reads_raw
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
        FROM metering_processed.interval_reads_raw r
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.interval_reads_calculated c
            WHERE c.icp_id = r.connection_id 
            AND c.meter_register_id = r.register_code
            AND c.timestamp = r.timestamp
            AND c.source = r.source
        )
        AND r.timestamp >= %s
        AND r.timestamp <= %s
        """
        
        unprocessed_count = self.pg_hook.get_first(count_query, parameters=[
            smart_start_date,
            smart_end_date + timedelta(days=1)
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
            r.timestamp,
            r.value,
            r.quality_flag,
            '' as validation_flag,
            r.source,
            '' as source_file_name,
            r.metadata
        FROM metering_processed.interval_reads_raw r
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.interval_reads_calculated c
            WHERE c.icp_id = r.connection_id 
            AND c.meter_register_id = r.register_code
            AND c.timestamp = r.timestamp
            AND c.source = r.source
        )
        AND r.timestamp >= %s
        AND r.timestamp <= %s
        ORDER BY r.timestamp DESC, r.connection_id, r.register_code
        LIMIT %s
        """
        
        records = self.pg_hook.get_records(query, parameters=[
            smart_start_date, 
            smart_end_date + timedelta(days=1),
            actual_limit
        ])
        
        # Convert to dictionaries
        columns = ['id', 'tenant_id', 'icp_id', 'meter_serial_number', 'meter_register_id', 
                  'timestamp', 'value', 'quality_flag', 'validation_flag', 'source', 'source_file_name', 'metadata']
        
        readings = []
        for record in records:
            reading_dict = dict(zip(columns, record))
            # Keep timestamp as datetime object for validation logic
            # Only convert UUID objects to strings for JSON serialization
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
    
    def execute_validation_workflow(self, session_id: str, readings: List[Dict]) -> List[Dict]:
        """Execute validation workflow according to session configuration"""
        
        session = ValidationSession.objects.get(session_id=session_id)
        workflow = session.workflow
        
        logger.info(f"📊 PIPELINE TRACKING - Starting validation workflow for {len(readings)} readings")
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
            
            # Apply estimation if configured
            if workflow.estimation_config.get('methods'):
                batch_before = len(batch)
                batch = self._apply_estimation(session, batch)
                batch_after = len(batch)
                
                if batch_before != batch_after:
                    logger.warning(f"⚠️ PIPELINE TRACKING - Estimation changed batch size from {batch_before} to {batch_after}")
                
                estimated_count = len([r for r in batch if r.get('is_estimated', False)])
                logger.info(f"📊 PIPELINE TRACKING - Batch {batch_num}: Estimation applied to {estimated_count} readings")
            
            # Calculate plausibility flags for all readings in the batch
            for reading in batch:
                reading['plausibility_flag'] = self._calculate_plausibility_flag(reading)
            
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
        
        logger.info(f"📊 PIPELINE TRACKING - Validation complete: {validation_stats}")
        
        # Update session progress
        session.processed_readings = len(validated_readings)
        session.valid_readings = validation_stats['valid']
        session.estimated_readings = validation_stats['is_estimated']
        session.save()
        
        return validated_readings
    
    def _execute_validation_rule(self, session: ValidationSession, rule_code: str, readings: List[Dict]) -> List[Dict]:
        """Execute a specific validation rule"""
        
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
            elif rule.rule_type == 'spike_detection':
                readings = self._apply_spike_detection(rule, readings)
            elif rule.rule_type == 'continuity_check':
                readings = self._apply_continuity_check(rule, readings)
            elif rule.rule_type == 'missing_data':
                readings = self._apply_missing_data_check(rule, readings)
            elif rule.rule_type == 'plausibility_check':
                readings = self._apply_plausibility_check(rule, readings)
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
                
                # Add trading period information
                if 'trading_period' not in reading:
                    reading['trading_period'] = self._calculate_trading_period(reading['timestamp'])
                
                # Add interval information (30-minute intervals)
                if 'interval_number' not in reading:
                    reading['interval_number'] = self._calculate_interval_number(reading['timestamp'])

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
        """Apply range check validation rule with detailed failure logging"""
        
        params = rule.parameters
        min_value = params.get('min_value', 0)
        max_value = params.get('max_value', 1000)
        
        initial_count = len(readings)
        processed_count = 0
        failed_count = 0
        null_count = 0
        estimated_zero_count = 0
        
        for reading in readings:
            start_time = timezone.now()
            processed_count += 1
            
            if reading['value'] is None:
                null_count += 1
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = 'Missing value'
                
                # Log detailed failure
                validation_failure_logger.log_validation_failure(
                    session_id=reading.get('session_id', 'unknown'),
                    rule_code=rule.rule_code,
                    reading_data=reading,
                    failure_reason='Missing value - null or empty reading',
                    validation_context={
                        'expected_value': f'Value between {min_value} and {max_value}',
                        'rule_parameters': params,
                        'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                    },
                    severity=FailureSeverity.HIGH
                )
                
            elif reading['value'] < min_value or reading['value'] > max_value:
                failed_count += 1
                reading['validation_flag'] = 'S'
                reading['validation_notes'] = f'Value {reading["value"]} outside range [{min_value}, {max_value}]'
                
                # Determine severity based on how far outside the range
                value_deviation = max(
                    abs(reading['value'] - min_value) if reading['value'] < min_value else 0,
                    abs(reading['value'] - max_value) if reading['value'] > max_value else 0
                )
                severity = FailureSeverity.CRITICAL if value_deviation > max_value else FailureSeverity.HIGH
                
                # Log detailed failure
                validation_failure_logger.log_validation_failure(
                    session_id=reading.get('session_id', 'unknown'),
                    rule_code=rule.rule_code,
                    reading_data=reading,
                    failure_reason=f'Value {reading["value"]} outside acceptable range [{min_value}, {max_value}]',
                    validation_context={
                        'expected_range': f'{min_value} to {max_value}',
                        'deviation': value_deviation,
                        'rule_parameters': params,
                        'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                    },
                    severity=severity
                )
            
            # CRITICAL FIX: Check for quality flag based issues
            elif reading.get('quality_flag') == 'E' and reading['value'] == 0.0:
                estimated_zero_count += 1
                failed_count += 1
                reading['spoton_validation_result'] = 'S'  # Our validation result
                reading['validation_notes'] = 'Estimated reading with zero value - implausible consumption pattern'
                
                # Log detailed failure for estimated zero readings
                validation_failure_logger.log_validation_failure(
                    session_id=reading.get('session_id', 'unknown'),
                    rule_code=rule.rule_code,
                    reading_data=reading,
                    failure_reason='Estimated reading with zero value - implausible for normal consumption patterns',
                    validation_context={
                        'quality_flag': reading.get('quality_flag'),
                        'value': reading['value'],
                        'issue_type': 'estimated_zero_consumption',
                        'rule_parameters': params,
                        'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                    },
                    severity=FailureSeverity.HIGH
                )
            
            # Check for missing data flag with values (data integrity issue)
            elif reading.get('quality_flag') == 'M' and reading['value'] != 0.0:
                failed_count += 1
                reading['spoton_validation_result'] = 'S'  # Our validation result
                reading['validation_notes'] = 'Missing data flag but value present - data integrity issue'
                
                # Log detailed failure
                validation_failure_logger.log_validation_failure(
                    session_id=reading.get('session_id', 'unknown'),
                    rule_code=rule.rule_code,
                    reading_data=reading,
                    failure_reason='Reading flagged as missing but contains value - data integrity issue',
                    validation_context={
                        'quality_flag': reading.get('quality_flag'),
                        'value': reading['value'],
                        'issue_type': 'missing_flag_with_value',
                        'rule_parameters': params,
                        'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                    },
                    severity=FailureSeverity.HIGH
                )
            
            # Check for pre-flagged suspect quality
            elif reading.get('quality_flag') == 'S':
                failed_count += 1
                reading['spoton_validation_result'] = 'S'  # Our validation result
                reading['validation_notes'] = 'Pre-flagged as suspect quality - requires manual review'
                
                # Log detailed failure
                validation_failure_logger.log_validation_failure(
                    session_id=reading.get('session_id', 'unknown'),
                    rule_code=rule.rule_code,
                    reading_data=reading,
                    failure_reason='Reading pre-flagged as suspect quality in source data',
                    validation_context={
                        'quality_flag': reading.get('quality_flag'),
                        'value': reading['value'],
                        'issue_type': 'pre_flagged_suspect',
                        'rule_parameters': params,
                        'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                    },
                    severity=FailureSeverity.MEDIUM
                )
                
            else:
                reading['spoton_validation_result'] = reading.get('spoton_validation_result', 'V')  # Our validation result
        
        final_count = len(readings)
        logger.info(f"📊 RANGE CHECK - Processed {processed_count}/{initial_count} readings: {null_count} null values, {failed_count} out of range ({estimated_zero_count} estimated zeros), {final_count} remaining")
        
        return readings
    
    def _apply_spike_detection(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply spike detection validation rule"""
        
        # Group by meter for spike detection
        meter_groups = {}
        for reading in readings:
            key = (reading['icp_id'], reading['meter_register_id'])
            if key not in meter_groups:
                meter_groups[key] = []
            meter_groups[key].append(reading)
        
        # Check for spikes within each meter group
        for meter_readings in meter_groups.values():
            meter_readings.sort(key=lambda x: x['timestamp'])
            
            for i, reading in enumerate(meter_readings):
                if i == 0 or reading['value'] is None:
                    continue
                
                prev_value = meter_readings[i-1]['value']
                if prev_value is None:
                    continue
                
                # Simple spike detection: >500% change
                if prev_value > 0 and abs(reading['value'] - prev_value) / prev_value > 5.0:
                    reading['spoton_validation_result'] = 'S'  # Our validation result
                    reading['validation_notes'] = f'Spike detected: {prev_value} → {reading["value"]}'
        
        return readings
    
    def _apply_continuity_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply continuity check validation rule"""
        
        # Helper function to convert timestamp to datetime for comparison
        def to_datetime(timestamp):
            if isinstance(timestamp, str):
                if 'T' in timestamp:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(timestamp)
            return timestamp
        
        # Group by meter and check for gaps
        meter_groups = {}
        for reading in readings:
            key = (reading['icp_id'], reading['meter_register_id'])
            if key not in meter_groups:
                meter_groups[key] = []
            meter_groups[key].append(reading)
        
        for meter_readings in meter_groups.values():
            meter_readings.sort(key=lambda x: to_datetime(x['timestamp']))
            
            for i in range(1, len(meter_readings)):
                current = meter_readings[i]
                previous = meter_readings[i-1]
                
                current_time = to_datetime(current['timestamp'])
                previous_time = to_datetime(previous['timestamp'])
                
                time_diff = current_time - previous_time
                expected_diff = timedelta(minutes=30)
                
                if time_diff > expected_diff * 2:  # Allow some tolerance
                    current['spoton_validation_result'] = 'S'  # Our validation result
                    current['validation_notes'] = f'Gap detected: {time_diff} since last reading'
        
        return readings
    
    def _apply_missing_data_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply missing data check validation rule"""
        
        for reading in readings:
            if reading['value'] is None:
                reading['spoton_validation_result'] = 'S'  # Our validation result
                reading['validation_notes'] = 'Missing data value'
                reading['requires_estimation'] = True
        
        return readings
    
    def _apply_plausibility_check(self, rule: ValidationRule, readings: List[Dict]) -> List[Dict]:
        """Apply comprehensive plausibility check validation rule"""
        
        initial_count = len(readings)
        failed_count = 0
        estimated_zero_count = 0
        implausible_pattern_count = 0
        
        # Helper function to convert timestamp to datetime for comparison
        def to_datetime(timestamp):
            if isinstance(timestamp, str):
                if 'T' in timestamp:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(timestamp)
            return timestamp
        
        # Group readings by meter for pattern analysis
        meter_groups = {}
        for reading in readings:
            key = (reading['icp_id'], reading['meter_register_id'])
            if key not in meter_groups:
                meter_groups[key] = []
            meter_groups[key].append(reading)
        
        for meter_readings in meter_groups.values():
            meter_readings.sort(key=lambda x: to_datetime(x['timestamp']))
            
            # Check for implausible patterns
            zero_count = 0
            estimated_count = 0
            
            for i, reading in enumerate(meter_readings):
                start_time = timezone.now()
                
                # Check 1: Quality flag based plausibility checks
                quality_flag = reading.get('quality_flag')
                value = reading['value']
                
                # Check 1a: Estimated readings with zero values
                if quality_flag == 'E' and value == 0.0:
                    estimated_zero_count += 1
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = 'Estimated zero consumption - implausible pattern'
                    
                    # Log detailed failure
                    validation_failure_logger.log_validation_failure(
                        session_id=reading.get('session_id', 'unknown'),
                        rule_code=rule.rule_code,
                        reading_data=reading,
                        failure_reason='Estimated reading with zero value - implausible consumption pattern',
                        validation_context={
                            'quality_flag': quality_flag,
                            'value': value,
                            'check_type': 'estimated_zero_consumption',
                            'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                        },
                        severity=FailureSeverity.HIGH
                    )
                    continue
                
                # Check 1b: Missing data flags with values (suspicious)
                elif quality_flag == 'M' and value != 0.0:
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = 'Missing data flag but value present - data integrity issue'
                    
                    # Log detailed failure
                    validation_failure_logger.log_validation_failure(
                        session_id=reading.get('session_id', 'unknown'),
                        rule_code=rule.rule_code,
                        reading_data=reading,
                        failure_reason='Reading flagged as missing but contains value - data integrity issue',
                        validation_context={
                            'quality_flag': quality_flag,
                            'value': value,
                            'check_type': 'missing_flag_with_value',
                            'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                        },
                        severity=FailureSeverity.HIGH
                    )
                    continue
                
                # Check 1c: Suspect quality flags
                elif quality_flag == 'S':
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = 'Pre-flagged as suspect quality - requires manual review'
                    
                    # Log detailed failure
                    validation_failure_logger.log_validation_failure(
                        session_id=reading.get('session_id', 'unknown'),
                        rule_code=rule.rule_code,
                        reading_data=reading,
                        failure_reason='Reading pre-flagged as suspect quality in source data',
                        validation_context={
                            'quality_flag': quality_flag,
                            'value': value,
                            'check_type': 'pre_flagged_suspect',
                            'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                        },
                        severity=FailureSeverity.MEDIUM
                    )
                    continue
                
                # Check 1b: Non-finalized readings with suspicious patterns
                if (reading.get('quality_flag') in ['S', 'E', 'U'] and 
                    reading.get('is_final_reading', True) == False):
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = f'Non-finalized reading with quality flag {reading.get("quality_flag")} - requires review'
                    
                    # Log detailed failure
                    validation_failure_logger.log_validation_failure(
                        session_id=reading.get('session_id', 'unknown'),
                        rule_code=rule.rule_code,
                        reading_data=reading,
                        failure_reason=f'Non-finalized reading with quality flag {reading.get("quality_flag")} - requires manual review',
                        validation_context={
                            'quality_flag': reading.get('quality_flag'),
                            'is_final_reading': reading.get('is_final_reading', True),
                            'check_type': 'non_finalized_reading',
                            'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                        },
                        severity=FailureSeverity.MEDIUM
                    )
                    continue
                
                # Check 2: Extended periods of zero consumption (>12 hours)
                if reading['value'] == 0.0:
                    zero_count += 1
                else:
                    zero_count = 0
                
                if zero_count > 24:  # 24 consecutive 30-minute intervals = 12 hours
                    implausible_pattern_count += 1
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = f'Extended zero consumption pattern ({zero_count * 0.5} hours)'
                    
                    # Log detailed failure
                    validation_failure_logger.log_validation_failure(
                        session_id=reading.get('session_id', 'unknown'),
                        rule_code=rule.rule_code,
                        reading_data=reading,
                        failure_reason=f'Extended zero consumption pattern detected ({zero_count * 0.5} hours)',
                        validation_context={
                            'consecutive_zeros': zero_count,
                            'duration_hours': zero_count * 0.5,
                            'check_type': 'extended_zero_pattern',
                            'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                        },
                        severity=FailureSeverity.MEDIUM
                    )
                    continue
                
                # Check 3: High percentage of estimated readings in sequence
                if reading.get('quality_flag') == 'E':
                    estimated_count += 1
                else:
                    estimated_count = 0
                
                if estimated_count > 12:  # 12 consecutive estimated readings = 6 hours
                    implausible_pattern_count += 1
                    failed_count += 1
                    reading['validation_flag'] = 'S'
                    reading['validation_notes'] = f'Extended estimated reading pattern ({estimated_count * 0.5} hours)'
                    
                    # Log detailed failure
                    validation_failure_logger.log_validation_failure(
                        session_id=reading.get('session_id', 'unknown'),
                        rule_code=rule.rule_code,
                        reading_data=reading,
                        failure_reason=f'Extended estimated reading pattern detected ({estimated_count * 0.5} hours)',
                        validation_context={
                            'consecutive_estimated': estimated_count,
                            'duration_hours': estimated_count * 0.5,
                            'check_type': 'extended_estimated_pattern',
                            'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                        },
                        severity=FailureSeverity.MEDIUM
                    )
                    continue
                
                # Check 4: Implausible quality flag transitions
                if i > 0:
                    prev_reading = meter_readings[i-1]
                    if (prev_reading.get('quality_flag') == 'A' and 
                        reading.get('quality_flag') == 'E' and 
                        reading['value'] == 0.0):
                        
                        implausible_pattern_count += 1
                        failed_count += 1
                        reading['validation_flag'] = 'S'
                        reading['validation_notes'] = 'Implausible quality transition: A→E with zero value'
                        
                        # Log detailed failure
                        validation_failure_logger.log_validation_failure(
                            session_id=reading.get('session_id', 'unknown'),
                            rule_code=rule.rule_code,
                            reading_data=reading,
                            failure_reason='Implausible quality flag transition from actual to estimated with zero value',
                            validation_context={
                                'previous_quality': prev_reading.get('quality_flag'),
                                'current_quality': reading.get('quality_flag'),
                                'value': reading['value'],
                                'check_type': 'implausible_quality_transition',
                                'processing_time_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                            },
                            severity=FailureSeverity.HIGH
                        )
                        continue
        
        final_count = len(readings)
        # Log quality flag distribution for analysis
        quality_distribution = {}
        for reading in readings:
            quality_flag = reading.get('quality_flag', 'unknown')
            quality_distribution[quality_flag] = quality_distribution.get(quality_flag, 0) + 1
        
        logger.info(f"📊 PLAUSIBILITY CHECK - Processed {initial_count} readings: {estimated_zero_count} estimated zeros, {implausible_pattern_count} implausible patterns, {failed_count} total failures")
        logger.info(f"📊 QUALITY FLAG DISTRIBUTION - P:{quality_distribution.get('P', 0)}, A:{quality_distribution.get('A', 0)}, M:{quality_distribution.get('M', 0)}, E:{quality_distribution.get('E', 0)}, S:{quality_distribution.get('S', 0)}")
        
        return readings
    
    def _calculate_plausibility_flag(self, reading: Dict) -> str:
        """Calculate plausibility flag based on validation results and quality flags"""
        validation_results = reading.get('validation_results', {})
        quality_flag = reading.get('quality_flag')
        value = reading.get('value')
        validation_flag = reading.get('validation_flag', 'V')
        
        # Industry standard plausibility flags:
        # 'CHECKED_POSITIVE' - Green: Checked positive for plausibility
        # 'NOT_CHECKED' - Pink/Magenta: Not checked for plausibility  
        # 'CHECKED_NEGATIVE' - Red: Checked negative for plausibility
        # 'SUSPECT' - Yellow: Suspect quality requiring review
        
        # Critical quality flag issues - automatically negative plausibility
        if quality_flag == 'E' and value == 0.0:
            return 'CHECKED_NEGATIVE'  # Estimated zero consumption - implausible
        
        # Check for zero values in permanent/actual readings (high priority)
        if quality_flag in ['P', 'A'] and value == 0.0:
            return 'CHECKED_NEGATIVE'  # Zero values are negative for P/A readings
        
        if quality_flag == 'M':
            return 'CHECKED_NEGATIVE'  # Missing data flag is always negative
        
        if quality_flag == 'S':
            return 'CHECKED_NEGATIVE'  # Pre-flagged suspect quality
        
        # Validation flag based assessment
        if validation_flag == 'S':
            return 'SUSPECT'  # Flagged as suspect during validation
        
        # Check validation results if available
        if validation_results:
            total_checks = len(validation_results)
            passed_checks = sum(1 for result in validation_results.values() if result.get('passed', False))
            
            if total_checks > 0:
                pass_rate = passed_checks / total_checks
                
                # Low pass rate - suspect
                if pass_rate < 0.6:
                    return 'SUSPECT'
                else:
                    # For estimated readings, even with good validation, mark as suspect
                    if quality_flag == 'E':
                        return 'SUSPECT'
                    return 'CHECKED_POSITIVE'
        
        # Default assessment based on quality flags when no validation results
        if quality_flag in ['P', 'A']:  # Permanent/Actual readings
            return 'CHECKED_POSITIVE'
        elif quality_flag == 'E':  # Estimated readings
            return 'SUSPECT'  # Estimated readings are suspect by default
        elif quality_flag in ['N'] and value is None:
            return 'CHECKED_POSITIVE'  # No reads with no value is normal
        else:
            return 'NOT_CHECKED'  # Unknown quality flag
    
    def _apply_estimation(self, session: ValidationSession, readings: List[Dict]) -> List[Dict]:
        """Mark readings that require estimation - actual estimation handled by separate DAG"""
        
        for reading in readings:
            # Only set value_calculated to original value - estimation DAG will handle actual estimation
            reading['value_calculated'] = reading['value']
            
            # Mark readings that require estimation but don't populate estimation fields
            if reading.get('requires_estimation') or reading.get('validation_flag') == 'S':
                # Add a flag to indicate this reading needs estimation
                reading['requires_estimation'] = True
            else:
                reading['requires_estimation'] = False
        
        return readings
    
    def store_calculated_readings(self, session_id: str, validated_readings: List[Dict]) -> int:
        """Store validated readings in interval_reads_calculated table"""
        
        if not validated_readings:
            logger.warning("⚠️ No validated readings to store")
            return 0

        logger.info(f"📊 PIPELINE TRACKING - Starting storage of {len(validated_readings)} validated readings")

        # Get current raw reading count for comparison
        raw_count_query = "SELECT COUNT(*) FROM metering_processed.interval_reads_raw"
        raw_count = self.pg_hook.get_first(raw_count_query)[0]
        logger.info(f"📊 PIPELINE TRACKING - Total raw readings in database: {raw_count}")
        
        # Get unprocessed raw reading count
        unprocessed_query = """
        SELECT COUNT(*) FROM metering_processed.interval_reads_raw r
        WHERE NOT EXISTS (
            SELECT 1 FROM metering_processed.interval_reads_calculated c
            WHERE c.icp_id = r.connection_id 
            AND c.meter_register_id = r.register_code
            AND c.timestamp = r.timestamp
            AND c.source = r.source
        )
        """
        unprocessed_count = self.pg_hook.get_first(unprocessed_query)[0]
        logger.info(f"📊 PIPELINE TRACKING - Unprocessed raw readings: {unprocessed_count}")
        
        # Expected vs actual analysis
        expected_total = raw_count
        actual_processing = len(validated_readings)
        missing_in_pipeline = expected_total - actual_processing
        
        if missing_in_pipeline > 0:
            logger.warning(f"⚠️ PIPELINE TRACKING - {missing_in_pipeline} readings missing from pipeline (Expected: {expected_total}, Processing: {actual_processing})")
            
            # Find missing readings by source
            missing_by_source_query = """
            SELECT r.source, COUNT(*) as missing_count
            FROM metering_processed.interval_reads_raw r
            WHERE NOT EXISTS (
                SELECT 1 FROM metering_processed.interval_reads_calculated c
                WHERE c.icp_id = r.connection_id 
                AND c.meter_register_id = r.register_code
                AND c.timestamp = r.timestamp
                AND c.source = r.source
            )
            GROUP BY r.source
            ORDER BY missing_count DESC
            """
            missing_by_source = self.pg_hook.get_records(missing_by_source_query)
            logger.warning(f"⚠️ PIPELINE TRACKING - Missing readings by source: {missing_by_source}")
            
            # Find specific missing readings (sample)
            missing_sample_query = """
            SELECT r.connection_id as icp_id, r.register_code as meter_register_id, r.timestamp, r.source, r.value, r.quality_flag
            FROM metering_processed.interval_reads_raw r
            WHERE NOT EXISTS (
                SELECT 1 FROM metering_processed.interval_reads_calculated c
                WHERE c.icp_id = r.connection_id 
                AND c.meter_register_id = r.register_code
                AND c.timestamp = r.timestamp
                AND c.source = r.source
            )
            ORDER BY r.timestamp DESC
            LIMIT 10
            """
            missing_sample = self.pg_hook.get_records(missing_sample_query)
            logger.warning(f"⚠️ PIPELINE TRACKING - Sample of missing readings: {missing_sample}")
        else:
            logger.info(f"✅ PIPELINE TRACKING - All {expected_total} raw readings are being processed")

        # Deduplicate readings based on unique constraint (icp_id, meter_register_id, timestamp, source)
        unique_readings = {}
        duplicates_found = 0
        duplicate_details = []
        
        for reading in validated_readings:
            # Convert timestamp to string for consistent comparison
            timestamp_str = str(reading['timestamp'])
            key = (reading['icp_id'], reading['meter_register_id'], timestamp_str, reading['source'])
            
            if key not in unique_readings:
                unique_readings[key] = reading
            else:
                duplicates_found += 1
                
                # Capture detailed comparison for logging
                existing = unique_readings[key]
                duplicate_info = {
                    'key': f"ICP:{reading['icp_id']}, Register:{reading['meter_register_id']}, Time:{timestamp_str}, Source:{reading['source']}",
                    'first_occurrence': {
                        'value': existing.get('value'),
                        'quality_flag': existing.get('quality_flag'),
                        'validation_flag': existing.get('validation_flag', 'V'),
                        'source_file': existing.get('source_file_name', 'unknown')
                    },
                    'duplicate_occurrence': {
                        'value': reading.get('value'),
                        'quality_flag': reading.get('quality_flag'),
                        'validation_flag': reading.get('validation_flag', 'V'),
                        'source_file': reading.get('source_file_name', 'unknown')
                    }
                }
                duplicate_details.append(duplicate_info)
                
                logger.warning(f"🔍 DUPLICATE FOUND - {duplicate_info['key']}")
                logger.warning(f"   📊 FIRST:     Value={duplicate_info['first_occurrence']['value']}, Quality={duplicate_info['first_occurrence']['quality_flag']}, Validation={duplicate_info['first_occurrence']['validation_flag']}, File={duplicate_info['first_occurrence']['source_file']}")
                logger.warning(f"   📊 DUPLICATE: Value={duplicate_info['duplicate_occurrence']['value']}, Quality={duplicate_info['duplicate_occurrence']['quality_flag']}, Validation={duplicate_info['duplicate_occurrence']['validation_flag']}, File={duplicate_info['duplicate_occurrence']['source_file']}")
                
                # Check if values are different (potential data correction)
                if duplicate_info['first_occurrence']['value'] != duplicate_info['duplicate_occurrence']['value']:
                    logger.error(f"   ⚠️ VALUE MISMATCH: {duplicate_info['first_occurrence']['value']} vs {duplicate_info['duplicate_occurrence']['value']} - Potential data correction!")
        
        deduplicated_readings = list(unique_readings.values())
        logger.info(f"📊 PIPELINE TRACKING - Deduplicated {len(validated_readings)} readings to {len(deduplicated_readings)} unique readings ({duplicates_found} duplicates removed)")
        
        # Summary of duplicates by source and pattern
        if duplicate_details:
            duplicate_summary = {}
            for dup in duplicate_details:
                source = dup['key'].split('Source:')[1] if 'Source:' in dup['key'] else 'unknown'
                icp = dup['key'].split('ICP:')[1].split(',')[0] if 'ICP:' in dup['key'] else 'unknown'
                key = f"{source}_{icp}"
                duplicate_summary[key] = duplicate_summary.get(key, 0) + 1
            
            logger.warning(f"📊 DUPLICATE SUMMARY by Source_ICP: {duplicate_summary}")
            
            # Show pattern analysis
            if duplicates_found >= 24:  # Likely full day duplicates
                logger.warning(f"🔍 PATTERN ANALYSIS: {duplicates_found} duplicates detected - likely represents {duplicates_found//48} full day(s) + {duplicates_found%48} partial intervals")
        else:
            logger.info("✅ No duplicates found - all readings are unique")

        # Mark final readings for each meter/register/trading period combination
        self._mark_final_readings(deduplicated_readings)
        
        # Additional debugging: check for any remaining duplicates in the final list
        final_keys = set()
        for reading in deduplicated_readings:
            timestamp_str = str(reading['timestamp'])
            key = (reading['icp_id'], reading['meter_register_id'], timestamp_str, reading['source'])
            if key in final_keys:
                logger.error(f"❌ CRITICAL: Duplicate key still exists after deduplication: {key}")
            final_keys.add(key)
        
        logger.info(f"✅ PIPELINE TRACKING - Final verification: {len(final_keys)} unique keys for {len(deduplicated_readings)} readings")

        # Count by source for detailed tracking
        source_counts = {}
        for reading in deduplicated_readings:
            source = reading['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        logger.info(f"📊 PIPELINE TRACKING - Readings by source: {source_counts}")

        # Prepare bulk insert with new flag structure
        insert_query = """
        INSERT INTO metering_processed.interval_reads_calculated (
            raw_reading_id, tenant_id, icp_id, meter_serial_number, meter_register_id, timestamp,
            value_raw, value_calculated, original_quality_flag, validation_flag,
            validation_rules_applied, validation_results, plausibility_score,
            is_estimated, estimation_method, estimation_confidence, estimation_inputs, estimation_flags,
            source, source_file_name, processing_notes, metadata
        ) VALUES %s
        ON CONFLICT (icp_id, meter_register_id, timestamp, source) 
        DO NOTHING
        """
        
        # Prepare values
        values = []
        for reading in deduplicated_readings:
            # Debug: Check for problematic data
            validation_rules = reading.get('validation_rules_applied', [])
            if isinstance(validation_rules, list):
                validation_rules_str = '{' + ','.join(f'"{rule}"' for rule in validation_rules) + '}'
            else:
                validation_rules_str = '{}'
            
            plausibility_flag = reading.get('plausibility_flag', 'NOT_CHECKED')
            
            # Validate plausibility flag
            valid_flags = ['CHECKED_POSITIVE', 'CHECKED_NEGATIVE', 'SUSPECT', 'NOT_CHECKED']
            if plausibility_flag not in valid_flags:
                logger.warning(f"Invalid plausibility_flag '{plausibility_flag}', defaulting to 'NOT_CHECKED'")
                plausibility_flag = 'NOT_CHECKED'
            
            # Map quality flags properly for the new structure
            original_quality_flag = reading.get('quality_flag')  # Original from raw data
            raw_validation_flag = reading.get('validation_flag')  # Meter provider validation flag from raw data
            
            # Use the actual meter provider validation_flag from raw data (P/F/N)
            # This represents the true meter provider validation status
            meter_provider_validation_flag = raw_validation_flag if raw_validation_flag in ['P', 'F', 'N'] else 'V'
            
            values.append((
                reading.get('id'),
                reading.get('tenant_id'),
                reading['icp_id'],
                reading.get('meter_serial_number'),
                reading['meter_register_id'],
                reading['timestamp'],
                reading['value'],
                reading.get('value_calculated', reading['value']),
                original_quality_flag,  # original_quality_flag - preserve original
                meter_provider_validation_flag,        # validation_flag - meter provider validation (P/F/N)
                validation_rules_str,  # validation_rules_applied as PostgreSQL array
                json.dumps(reading.get('validation_results', {})),  # validation_results as JSON
                100.0,  # plausibility_score - default to 100.0
                False,  # is_estimated - will be set by estimation DAG
                None,   # estimation_method - will be set by estimation DAG
                None,   # estimation_confidence - will be set by estimation DAG
                '{}',   # estimation_inputs - will be set by estimation DAG
                '{}',   # estimation_flags - will be set by estimation DAG
                reading['source'],
                reading.get('source_file_name'),
                reading.get('validation_notes'),
                json.dumps(reading.get('metadata', {}))
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
            
            # Check if there's a mismatch
            if inserted_count < len(values):
                conflicts = len(values) - inserted_count
                logger.warning(f"⚠️ PIPELINE TRACKING - {conflicts} readings were skipped due to conflicts (already exist)")
            
            # Get total count in calculated table
            count_query = "SELECT COUNT(*) FROM metering_processed.interval_reads_calculated"
            total_calculated = cursor.fetchone()[0] if cursor.execute(count_query) else 0
            logger.info(f"📊 PIPELINE TRACKING - Total calculated readings in database: {total_calculated}")
            
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

    def _calculate_trading_period(self, timestamp) -> int:
        """
        Calculate trading period (1-48 for normal days, 1-46 for DST spring, 1-50 for DST autumn)
        
        DST Rules for New Zealand:
        - Spring DST: Last Sunday in September (clock forward 2:00 AM → 3:00 AM) = 46 trading periods
        - Autumn DST: First Sunday in April (clock backward 3:00 AM → 2:00 AM) = 50 trading periods
        """
        # Handle string timestamps
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Convert to New Zealand timezone for DST calculation
        import pytz
        nz_tz = pytz.timezone('Pacific/Auckland')
        nz_timestamp = timestamp.astimezone(nz_tz)
        
        # Get date for DST checking
        date = nz_timestamp.date()
        
        # Check if this is a DST transition day
        is_dst_spring = self._is_dst_spring_day(date)  # 46 trading periods
        is_dst_autumn = self._is_dst_autumn_day(date)  # 50 trading periods
        
        hour = nz_timestamp.hour
        minute = nz_timestamp.minute
        
        if is_dst_spring:
            # Spring DST: 2:00 AM → 3:00 AM (skip 2:00-2:59)
            # Trading periods: 1-4 (00:00-01:59), then 7-48 (03:00-23:59)
            if hour < 2:
                # Normal calculation for hours 0-1
                interval_of_day = (hour * 2) + (1 if minute >= 30 else 0)
                return interval_of_day + 1
            elif hour == 2:
                # 2:00 AM doesn't exist on spring DST day - this shouldn't happen
                # But if it does, treat as 3:00 AM
                return 7  # First trading period after DST gap
            else:
                # Hours 3-23: subtract 2 hours worth of trading periods (4 periods)
                interval_of_day = (hour * 2) + (1 if minute >= 30 else 0) - 4
                return interval_of_day + 1
                
        elif is_dst_autumn:
            # Autumn DST: 3:00 AM → 2:00 AM (repeat 2:00-2:59)
            # Trading periods: 1-6 (00:00-02:59), then 7-10 (02:00-02:59 again), then 11-50 (03:00-23:59)
            if hour < 2:
                # Normal calculation for hours 0-1
                interval_of_day = (hour * 2) + (1 if minute >= 30 else 0)
                return interval_of_day + 1
            elif hour == 2:
                # For 2:00 AM hour, we need to determine if it's first or second occurrence
                # This is complex - for now, assign to first occurrence (TPs 5-6)
                return 5 + (1 if minute >= 30 else 0)
            else:
                # Hours 3-23: add 2 hours worth of trading periods (4 periods)
                interval_of_day = (hour * 2) + (1 if minute >= 30 else 0) + 4
                return interval_of_day + 1
        else:
            # Normal day: 48 trading periods
            interval_of_day = (hour * 2) + (1 if minute >= 30 else 0)
            return interval_of_day + 1

    def _is_dst_spring_day(self, date) -> bool:
        """Check if date is DST spring transition day (last Sunday in September)"""
        import calendar
        
        if date.month != 9:  # September
            return False
            
        # Find last Sunday in September
        last_day = calendar.monthrange(date.year, 9)[1]
        last_sunday = None
        
        for day in range(last_day, 0, -1):
            test_date = date.replace(day=day)
            if test_date.weekday() == 6:  # Sunday
                last_sunday = test_date
                break
                
        return date == last_sunday

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

    def _calculate_interval_number(self, timestamp) -> int:
        """Calculate interval number within the day (1-48 for 30-minute intervals)"""
        return self._calculate_trading_period(timestamp)

    def _mark_final_readings(self, readings: List[Dict]):
        """Mark final readings for each meter/register/trading period combination"""
        final_readings = {}
        for reading in readings:
            # Ensure trading_period is calculated if not already present
            if 'trading_period' not in reading:
                reading['trading_period'] = self._calculate_trading_period(reading['timestamp'])
            if 'interval_number' not in reading:
                reading['interval_number'] = self._calculate_interval_number(reading['timestamp'])
                
            key = (reading['icp_id'], reading['meter_register_id'], reading['trading_period'])
            if key not in final_readings:
                final_readings[key] = reading
        
        for reading in final_readings.values():
            reading['is_final_reading'] = True


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
    'hhr_validation_workflow',
    default_args=default_args,
    description='HHR Data Validation using Validation App Workflows',
    schedule_interval='0 */6 * * *',  # Every 6 hours, after HHR normalization
    catchup=False,
    max_active_runs=1,
    tags=['validation', 'hhr', 'metering']
)


def create_validation_session_task(**context):
    """Create validation session"""
    orchestrator = HHRValidationOrchestrator()
    session_id = orchestrator.create_validation_session()
    context['ti'].xcom_push(key='session_id', value=session_id)
    return session_id


def get_unprocessed_readings_task(**context):
    """Get unprocessed readings for validation"""
    session_id = context['ti'].xcom_pull(key='session_id')
    orchestrator = HHRValidationOrchestrator()
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
    
    orchestrator = HHRValidationOrchestrator()
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
    
    orchestrator = HHRValidationOrchestrator()
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

# Diagnostic function to analyze missing readings
def analyze_missing_readings():
    """Diagnostic function to analyze the 48 missing readings"""
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Get total counts
    raw_count = pg_hook.get_first("SELECT COUNT(*) FROM metering_processed.interval_reads_raw")[0]
    calculated_count = pg_hook.get_first("SELECT COUNT(*) FROM metering_processed.interval_reads_calculated")[0]
    
    print(f"📊 DIAGNOSTIC - Raw readings: {raw_count}")
    print(f"📊 DIAGNOSTIC - Calculated readings: {calculated_count}")
    print(f"📊 DIAGNOSTIC - Missing: {raw_count - calculated_count}")
    
    # Check for unprocessed readings
    unprocessed_query = """
    SELECT r.source, COUNT(*) as count
    FROM metering_processed.interval_reads_raw r
    WHERE NOT EXISTS (
        SELECT 1 FROM metering_processed.interval_reads_calculated c
        WHERE c.icp_id = r.connection_id 
        AND c.meter_register_id = r.register_code
        AND c.timestamp = r.timestamp
        AND c.source = r.source
    )
    GROUP BY r.source
    ORDER BY count DESC
    """
    unprocessed = pg_hook.get_records(unprocessed_query)
    print(f"📊 DIAGNOSTIC - Unprocessed by source: {unprocessed}")
    
    # Check for data quality issues
    quality_query = """
    SELECT 
        CASE 
            WHEN value IS NULL THEN 'NULL_VALUE'
            WHEN value < 0 THEN 'NEGATIVE_VALUE'
            WHEN value > 1000 THEN 'HIGH_VALUE'
            ELSE 'NORMAL'
        END as quality_issue,
        COUNT(*) as count
    FROM metering_processed.interval_reads_raw
    GROUP BY 1
    ORDER BY count DESC
    """
    quality_issues = pg_hook.get_records(quality_query)
    print(f"📊 DIAGNOSTIC - Quality issues: {quality_issues}")
    
    # Sample of unprocessed readings
    sample_query = """
    SELECT r.connection_id as icp_id, r.register_code as meter_register_id, r.timestamp, r.source, r.value, r.quality_flag
    FROM metering_processed.interval_reads_raw r
    WHERE NOT EXISTS (
        SELECT 1 FROM metering_processed.interval_reads_calculated c
        WHERE c.icp_id = r.connection_id 
        AND c.meter_register_id = r.register_code
        AND c.timestamp = r.timestamp
        AND c.source = r.source
    )
    LIMIT 10
    """
    sample = pg_hook.get_records(sample_query)
    print(f"📊 DIAGNOSTIC - Sample unprocessed readings:")
    for reading in sample:
        print(f"  - ICP: {reading[0]}, Register: {reading[1]}, Time: {reading[2]}, Source: {reading[3]}, Value: {reading[4]}, Quality: {reading[5]}")

# To run the diagnostic: python -c "from hhr_validation_dag import analyze_missing_readings; analyze_missing_readings()" 