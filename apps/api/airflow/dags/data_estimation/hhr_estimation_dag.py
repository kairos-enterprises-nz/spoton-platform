"""
Enhanced HHR Estimation DAG with Register-Based Estimation

This DAG implements a sophisticated estimation process that uses daily register reads
to calculate consumption and distribute it across missing or invalid intervals.

Key Features:
1. Register-based consumption distribution (primary method)
2. Comprehensive gap analysis and identification
3. Multiple fallback estimation methods
4. Validation against register consumption
5. Detailed audit trail and confidence scoring
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/app')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
import django
django.setup()

from django.db import connection, transaction
from energy.validation.estimation_engine import EstimationEngine
from energy.validation.register_based_estimation import RegisterBasedEstimationEngine

logger = logging.getLogger(__name__)


class RegisterBasedEstimationOrchestrator:
    """Orchestrates the register-based estimation process"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.RegisterBasedEstimationOrchestrator')
        self.estimation_engine = EstimationEngine()
        self.register_engine = RegisterBasedEstimationEngine()
    
    def analyze_gaps_comprehensive(self, **context) -> Dict:
        """Comprehensive gap analysis to identify all intervals needing estimation"""
        self.logger.info("Starting comprehensive gap analysis")
        
        # Identify all gaps in the data
        gap_analysis_query = """
        WITH missing_intervals AS (
            -- Find missing intervals by comparing expected vs actual
            SELECT 
                r.connection_id,
                r.register_code,
                generate_series(
                    DATE_TRUNC('day', MIN(r.timestamp)),
                    DATE_TRUNC('day', MAX(r.timestamp)) + INTERVAL '1 day' - INTERVAL '30 minutes',
                    INTERVAL '30 minutes'
                ) as expected_timestamp
            FROM metering_processed.interval_reads_raw r
            GROUP BY r.connection_id, r.register_code
        ),
        actual_intervals AS (
            SELECT DISTINCT connection_id, register_code, timestamp
            FROM metering_processed.interval_reads_final
        ),
        gaps AS (
            SELECT 
                m.connection_id,
                m.register_code,
                m.expected_timestamp as timestamp,
                'missing' as gap_type
            FROM missing_intervals m
            LEFT JOIN actual_intervals a 
                ON m.connection_id = a.connection_id 
                AND m.register_code = a.register_code
                AND m.expected_timestamp = a.timestamp
            WHERE a.timestamp IS NULL
        ),
        invalid_intervals AS (
            SELECT 
                r.connection_id,
                r.register_code,
                r.timestamp,
                CASE 
                    WHEN r.quality_flag = 'error' THEN 'error'
                    WHEN r.quality_flag = 'suspect' THEN 'suspect'
                    WHEN r.quality_flag = 'raw' THEN 'needs_validation'
                    ELSE 'invalid'
                END as gap_type
            FROM metering_processed.interval_reads_raw r
            WHERE r.quality_flag IN ('error', 'suspect', 'raw')
            AND NOT EXISTS (
                SELECT 1 FROM metering_processed.interval_reads_final f
                WHERE f.connection_id = r.connection_id
                AND f.register_code = r.register_code
                AND f.timestamp = r.timestamp
            )
        )
        SELECT 
            connection_id,
            register_code,
            timestamp,
            gap_type,
            COUNT(*) OVER (PARTITION BY connection_id, register_code, DATE(timestamp)) as gaps_in_day
        FROM (
            SELECT * FROM gaps
            UNION ALL
            SELECT * FROM invalid_intervals
        ) all_gaps
        ORDER BY connection_id, register_code, timestamp
        """
        
        with connection.cursor() as cursor:
            cursor.execute(gap_analysis_query)
            columns = [desc[0] for desc in cursor.description]
            raw_gaps = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Map database column names to expected keys for estimation engine
            gaps = []
            for gap in raw_gaps:
                mapped_gap = {
                    'icp_id': gap['connection_id'],
                    'meter_register_id': gap['register_code'],
                    'timestamp': gap['timestamp'],  # This should already be a datetime object from the database
                    'gap_type': gap['gap_type'],
                    'gaps_in_day': gap['gaps_in_day']
                }
                gaps.append(mapped_gap)
        
        # Analyze gaps by type and priority
        gap_summary = {
            'total_gaps': len(gaps),
            'by_type': {},
            'by_icp': {},
            'priority_levels': {
                'high': 0,    # Many gaps in a day
                'medium': 0,  # Some gaps in a day
                'low': 0      # Few gaps in a day
            }
        }
        
        for gap in gaps:
            gap_type = gap['gap_type']
            icp_id = gap['icp_id']
            gaps_in_day = gap['gaps_in_day']
            
            # Count by type
            if gap_type not in gap_summary['by_type']:
                gap_summary['by_type'][gap_type] = 0
            gap_summary['by_type'][gap_type] += 1
            
            # Count by ICP
            if icp_id not in gap_summary['by_icp']:
                gap_summary['by_icp'][icp_id] = 0
            gap_summary['by_icp'][icp_id] += 1
            
            # Priority classification
            if gaps_in_day > 20:
                gap_summary['priority_levels']['high'] += 1
            elif gaps_in_day > 5:
                gap_summary['priority_levels']['medium'] += 1
            else:
                gap_summary['priority_levels']['low'] += 1
        
        self.logger.info(f"Gap analysis complete: {gap_summary}")
        
        # Store gaps for next task
        context['task_instance'].xcom_push(key='gaps', value=gaps)
        context['task_instance'].xcom_push(key='gap_summary', value=gap_summary)
        
        return gap_summary
    
    def run_register_based_estimation(self, **context) -> Dict:
        """Run register-based estimation for all identified gaps"""
        self.logger.info("Starting register-based estimation process")
        
        # Get gaps from previous task
        gaps = context['task_instance'].xcom_pull(key='gaps', task_ids='analyze_gaps_comprehensive')
        if not gaps:
            self.logger.warning("No gaps found for estimation")
            return {'total_estimated': 0, 'by_method': {}}
        
        self.logger.info(f"Processing {len(gaps)} gaps for estimation")
        
        # Run estimation
        estimation_results = self.estimation_engine.estimate_missing_intervals(gaps)
        
        if not estimation_results:
            self.logger.warning("No estimation results generated")
            return {'total_estimated': 0, 'by_method': {}}
        
        # Get estimation summary
        estimation_summary = self.estimation_engine.get_estimation_summary(estimation_results)
        
        self.logger.info(f"Estimation complete: {estimation_summary}")
        
        # Store results for next task
        context['task_instance'].xcom_push(key='estimation_results', value=estimation_results)
        context['task_instance'].xcom_push(key='estimation_summary', value=estimation_summary)
        
        return estimation_summary
    
    def validate_estimations(self, **context) -> Dict:
        """Validate estimated values against register consumption"""
        self.logger.info("Starting estimation validation")
        
        # Get estimation results
        estimation_results = context['task_instance'].xcom_pull(
            key='estimation_results', task_ids='run_register_based_estimation'
        )
        
        if not estimation_results:
            self.logger.warning("No estimation results to validate")
            return {'validation_passed': True, 'issues': []}
        
        # Validate register-based estimations
        register_results = [r for r in estimation_results 
                          if r.method.value == 'register_distribution']
        
        if register_results:
            validation_result = self.register_engine.validate_estimation(register_results)
            self.logger.info(f"Register validation result: {validation_result}")
        else:
            validation_result = {'valid': True, 'message': 'No register-based results to validate'}
        
        # Additional validation checks
        validation_issues = []
        
        # Check for extreme values
        for result in estimation_results:
            if result.estimated_value > 1000:  # 1000 kWh per 30min interval is extreme
                validation_issues.append({
                    'type': 'extreme_value',
                    'connection_id': result.icp_id,
                    'register_code': result.meter_register_id,
                    'timestamp': result.timestamp.isoformat(),
                    'value': float(result.estimated_value)
                })
        
        # Check confidence levels
        low_confidence_count = sum(1 for r in estimation_results if r.confidence < 0.5)
        if low_confidence_count > len(estimation_results) * 0.3:  # More than 30% low confidence
            validation_issues.append({
                'type': 'low_confidence_rate',
                'count': low_confidence_count,
                'total': len(estimation_results),
                'percentage': (low_confidence_count / len(estimation_results)) * 100
            })
        
        validation_summary = {
            'validation_passed': validation_result['valid'] and len(validation_issues) == 0,
            'register_validation': validation_result,
            'issues': validation_issues,
            'total_results': len(estimation_results)
        }
        
        self.logger.info(f"Validation complete: {validation_summary}")
        
        context['task_instance'].xcom_push(key='validation_summary', value=validation_summary)
        return validation_summary
    
    def update_final_table(self, **context) -> Dict:
        """Update final table with estimated values"""
        self.logger.info("Starting final table update")
        
        # Get estimation results and validation
        estimation_results = context['task_instance'].xcom_pull(
            key='estimation_results', task_ids='run_register_based_estimation'
        )
        validation_summary = context['task_instance'].xcom_pull(
            key='validation_summary', task_ids='validate_estimations'
        )
        
        if not estimation_results:
            self.logger.warning("No estimation results to update")
            return {'updated_count': 0}
        
        if not validation_summary['validation_passed']:
            self.logger.error("Validation failed, skipping final table update")
            return {'updated_count': 0, 'error': 'Validation failed'}
        
        updated_count = 0
        
        with transaction.atomic():
            for result in estimation_results:
                # Check if record exists
                check_query = """
                SELECT id FROM metering_processed.interval_reads_final
                WHERE connection_id = %s AND register_code = %s AND timestamp = %s
                """
                
                with connection.cursor() as cursor:
                    cursor.execute(check_query, [
                        result.icp_id, result.meter_register_id, result.timestamp
                    ])
                    existing_record = cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    update_query = """
                    UPDATE metering_processed.interval_reads_final
                    SET 
                        value = %s,
                        metadata = metadata || %s::jsonb
                    WHERE id = %s
                    """
                    
                    processing_update = {
                        'estimation_method': result.method.value,
                        'estimation_confidence': result.confidence,
                        'estimation_timestamp': datetime.now().isoformat(),
                        'source_register_date': result.source_register_date.isoformat(),
                        'daily_consumption': float(result.daily_consumption),
                        'audit_trail': result.audit_trail
                    }
                    
                    with connection.cursor() as cursor:
                        cursor.execute(update_query, [
                            result.estimated_value,
                            processing_update,
                            existing_record[0]
                        ])
                    
                    updated_count += 1
                
                else:
                    # Insert new record
                    insert_query = """
                    INSERT INTO metering_processed.interval_reads_final (
                        tenant_id, connection_id, register_code, timestamp,
                        value, source_type, metadata, finalization_date
                    ) VALUES (
                        %s, %s, %s, %s, %s, 'estimated', %s, %s
                    )
                    """
                    
                    processing_summary = {
                        'estimation_method': result.method.value,
                        'estimation_confidence': result.confidence,
                        'estimation_timestamp': datetime.now().isoformat(),
                        'source_register_date': result.source_register_date.isoformat(),
                        'daily_consumption': float(result.daily_consumption),
                        'audit_trail': result.audit_trail
                    }
                    
                    with connection.cursor() as cursor:
                        cursor.execute(insert_query, [
                            '00000000-0000-0000-0000-000000000000',  # Default tenant
                            result.icp_id,
                            result.meter_register_id,
                            result.timestamp,
                            result.estimated_value,
                            processing_summary,
                            datetime.now()
                        ])
                    
                    updated_count += 1
        
        self.logger.info(f"Final table update complete: {updated_count} records updated")
        
        return {'updated_count': updated_count}
    
    def generate_estimation_report(self, **context) -> Dict:
        """Generate comprehensive estimation report"""
        self.logger.info("Generating estimation report")
        
        # Get all results from previous tasks
        gap_summary = context['task_instance'].xcom_pull(
            key='gap_summary', task_ids='analyze_gaps_comprehensive'
        )
        estimation_summary = context['task_instance'].xcom_pull(
            key='estimation_summary', task_ids='run_register_based_estimation'
        )
        validation_summary = context['task_instance'].xcom_pull(
            key='validation_summary', task_ids='validate_estimations'
        )
        update_result = context['task_instance'].xcom_pull(
            key='return_value', task_ids='update_final_table'
        )
        
        report = {
            'run_timestamp': datetime.now().isoformat(),
            'gap_analysis': gap_summary,
            'estimation_summary': estimation_summary,
            'validation_summary': validation_summary,
            'update_result': update_result,
            'overall_status': 'SUCCESS' if (
                validation_summary and validation_summary['validation_passed'] and
                update_result and update_result.get('updated_count', 0) > 0
            ) else 'FAILED'
        }
        
        self.logger.info(f"Estimation report generated: {report}")
        return report


# Initialize orchestrator
orchestrator = RegisterBasedEstimationOrchestrator()

# DAG definition
default_args = {
    'owner': 'data-estimation',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'hhr_estimation_workflow',
    default_args=default_args,
    description='HHR interval estimation with comprehensive validation',
    schedule_interval='30 */6 * * *',  # Every 6 hours, 30 minutes after validation
    catchup=False,
    max_active_runs=1,
    tags=['metering', 'estimation', 'hhr', 'validation']
)

# Task definitions
start_task = DummyOperator(
    task_id='start',
    dag=dag
)

analyze_gaps_task = PythonOperator(
    task_id='analyze_gaps_comprehensive',
    python_callable=orchestrator.analyze_gaps_comprehensive,
    dag=dag
)

estimation_task = PythonOperator(
    task_id='run_register_based_estimation',
    python_callable=orchestrator.run_register_based_estimation,
    dag=dag
)

validation_task = PythonOperator(
    task_id='validate_estimations',
    python_callable=orchestrator.validate_estimations,
    dag=dag
)

update_final_task = PythonOperator(
    task_id='update_final_table',
    python_callable=orchestrator.update_final_table,
    dag=dag
)

report_task = PythonOperator(
    task_id='generate_estimation_report',
    python_callable=orchestrator.generate_estimation_report,
    dag=dag
)

end_task = DummyOperator(
    task_id='end',
    dag=dag
)

# Task dependencies
start_task >> analyze_gaps_task >> estimation_task >> validation_task >> update_final_task >> report_task >> end_task 