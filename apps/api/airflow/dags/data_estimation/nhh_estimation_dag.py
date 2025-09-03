"""
NHH Estimation DAG for Daily Register Reads

This DAG implements estimation for Non-Half-Hourly (daily register reads) data
that uses historical patterns and interpolation methods to estimate missing
or invalid daily consumption values.

Key Features:
1. Historical average-based estimation (primary method)
2. Linear interpolation for short gaps
3. Seasonal adjustment for consumption patterns
4. Validation against typical consumption ranges
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
from energy.validation.models import ValidationSession, EstimationSession

logger = logging.getLogger(__name__)


class NHHEstimationOrchestrator:
    """Orchestrates the NHH estimation process for daily register reads"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.NHHEstimationOrchestrator')
        self.estimation_engine = EstimationEngine()
    
    def analyze_gaps_comprehensive(self, **context) -> Dict:
        """Comprehensive gap analysis to identify all daily readings needing estimation"""
        self.logger.info("Starting comprehensive NHH gap analysis")
        
        # Identify all gaps in daily register reads
        gap_analysis_query = """
        WITH missing_days AS (
            -- Find missing days by comparing expected vs actual
            SELECT 
                r.connection_id as icp_id,
                r.register_code as meter_register_id,
                generate_series(
                    DATE_TRUNC('day', MIN(r.reading_date)),
                    DATE_TRUNC('day', MAX(r.reading_date)),
                    INTERVAL '1 day'
                )::date as expected_date
            FROM metering_processed.daily_register_reads r
            GROUP BY r.connection_id, r.register_code
        ),
        actual_days AS (
            SELECT DISTINCT connection_id as icp_id, register_code as meter_register_id, reading_date
            FROM metering_processed.daily_register_reads
        ),
        gaps AS (
            SELECT 
                m.icp_id,
                m.meter_register_id,
                m.expected_date as reading_date,
                'missing' as gap_type
            FROM missing_days m
            LEFT JOIN actual_days a 
                ON m.icp_id = a.icp_id 
                AND m.meter_register_id = a.meter_register_id
                AND m.expected_date = a.reading_date
            WHERE a.reading_date IS NULL
        ),
        invalid_readings AS (
            SELECT 
                icp_id,
                meter_register_id,
                reading_date,
                CASE 
                    WHEN spoton_validation_flag = 'S' THEN 'suspect'
                    WHEN spoton_validation_flag = 'F' THEN 'failed'
                    WHEN consumption_calculated IS NULL THEN 'missing_consumption'
                    WHEN consumption_calculated < 0 THEN 'negative_consumption'
                    ELSE 'invalid'
                END as gap_type
            FROM metering_processed.daily_register_reads_calculated
            WHERE spoton_validation_flag IN ('S', 'F') 
            OR consumption_calculated IS NULL
            OR consumption_calculated < 0
        )
        SELECT 
            icp_id,
            meter_register_id,
            reading_date,
            gap_type,
            COUNT(*) OVER (PARTITION BY icp_id, meter_register_id, DATE_TRUNC('month', reading_date)) as gaps_in_month
        FROM (
            SELECT * FROM gaps
            UNION ALL
            SELECT * FROM invalid_readings
        ) all_gaps
        ORDER BY icp_id, meter_register_id, reading_date
        """
        
        with connection.cursor() as cursor:
            cursor.execute(gap_analysis_query)
            columns = [desc[0] for desc in cursor.description]
            gaps = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Analyze gaps by type and priority
        gap_summary = {
            'total_gaps': len(gaps),
            'by_type': {},
            'by_icp': {},
            'priority_levels': {
                'high': 0,    # Many gaps in a month
                'medium': 0,  # Some gaps in a month
                'low': 0      # Few gaps in a month
            }
        }
        
        for gap in gaps:
            gap_type = gap['gap_type']
            icp_id = gap['icp_id']
            gaps_in_month = gap['gaps_in_month']
            
            # Count by type
            if gap_type not in gap_summary['by_type']:
                gap_summary['by_type'][gap_type] = 0
            gap_summary['by_type'][gap_type] += 1
            
            # Count by ICP
            if icp_id not in gap_summary['by_icp']:
                gap_summary['by_icp'][icp_id] = 0
            gap_summary['by_icp'][icp_id] += 1
            
            # Priority classification
            if gaps_in_month > 10:  # More than 10 days missing per month
                gap_summary['priority_levels']['high'] += 1
            elif gaps_in_month > 3:  # 3-10 days missing per month
                gap_summary['priority_levels']['medium'] += 1
            else:
                gap_summary['priority_levels']['low'] += 1
        
        self.logger.info(f"NHH Gap analysis complete: {gap_summary}")
        
        # Store gaps for next task
        context['task_instance'].xcom_push(key='gaps', value=gaps)
        context['task_instance'].xcom_push(key='gap_summary', value=gap_summary)
        
        return gap_summary
    
    def run_nhh_estimation(self, **context) -> Dict:
        """Run NHH estimation for all identified gaps"""
        self.logger.info("Starting NHH estimation process")
        
        # Get gaps from previous task
        gaps = context['task_instance'].xcom_pull(key='gaps', task_ids='analyze_gaps_comprehensive')
        if not gaps:
            self.logger.warning("No gaps found for NHH estimation")
            return {'total_estimated': 0, 'by_method': {}}
        
        self.logger.info(f"Processing {len(gaps)} gaps for NHH estimation")
        
        # Run estimation using different methods
        estimation_results = []
        
        # Group gaps by meter for better estimation
        meter_gaps = {}
        for gap in gaps:
            key = (gap['icp_id'], gap['meter_register_id'])
            if key not in meter_gaps:
                meter_gaps[key] = []
            meter_gaps[key].append(gap)
        
        for (icp_id, meter_register_id), meter_gap_list in meter_gaps.items():
            # Sort gaps by date
            meter_gap_list.sort(key=lambda x: x['reading_date'])
            
            # Estimate each gap
            for gap in meter_gap_list:
                estimation_result = self._estimate_daily_consumption(
                    icp_id, 
                    meter_register_id, 
                    gap['reading_date'], 
                    gap['gap_type']
                )
                if estimation_result:
                    estimation_results.append(estimation_result)
        
        # Get estimation summary
        estimation_summary = self._get_estimation_summary(estimation_results)
        
        self.logger.info(f"NHH Estimation complete: {estimation_summary}")
        
        # Store results for next task
        context['task_instance'].xcom_push(key='estimation_results', value=estimation_results)
        context['task_instance'].xcom_push(key='estimation_summary', value=estimation_summary)
        
        return estimation_summary
    
    def _estimate_daily_consumption(self, icp_id: str, meter_register_id: str, 
                                   reading_date: datetime, gap_type: str) -> Optional[Dict]:
        """Estimate daily consumption for a specific gap"""
        
        # Get historical data for this meter
        historical_query = """
        SELECT 
            reading_date,
            consumption_calculated,
            register_reading,
            quality_flag
        FROM metering_processed.daily_register_reads_calculated
        WHERE icp_id = %s 
        AND meter_register_id = %s
        AND reading_date >= %s
        AND reading_date <= %s
        AND consumption_calculated IS NOT NULL
        AND consumption_calculated >= 0
        ORDER BY reading_date
        """
        
        # Look at 90 days before and after for context
        start_date = reading_date - timedelta(days=90)
        end_date = reading_date + timedelta(days=90)
        
        with connection.cursor() as cursor:
            cursor.execute(historical_query, [icp_id, meter_register_id, start_date, end_date])
            historical_data = cursor.fetchall()
        
        if not historical_data:
            self.logger.warning(f"No historical data found for {icp_id}/{meter_register_id}")
            return None
        
        # Convert to list of dicts
        historical_readings = []
        for row in historical_data:
            historical_readings.append({
                'reading_date': row[0],
                'consumption_calculated': float(row[1]),
                'register_reading': float(row[2]) if row[2] else None,
                'quality_flag': row[3]
            })
        
        # Choose estimation method based on gap type and available data
        if gap_type == 'missing':
            estimated_value, method, confidence = self._estimate_missing_day(
                reading_date, historical_readings
            )
        elif gap_type in ['suspect', 'failed']:
            estimated_value, method, confidence = self._estimate_suspect_day(
                reading_date, historical_readings
            )
        else:
            estimated_value, method, confidence = self._estimate_default_day(
                reading_date, historical_readings
            )
        
        if estimated_value is None:
            return None
        
        return {
            'icp_id': icp_id,
            'meter_register_id': meter_register_id,
            'reading_date': reading_date,
            'estimated_consumption': estimated_value,
            'estimation_method': method,
            'confidence': confidence,
            'gap_type': gap_type,
            'historical_data_points': len(historical_readings),
            'audit_trail': {
                'estimation_timestamp': datetime.now().isoformat(),
                'historical_range': f"{start_date} to {end_date}",
                'data_points_used': len(historical_readings)
            }
        }
    
    def _estimate_missing_day(self, reading_date: datetime, historical_readings: List[Dict]) -> tuple:
        """Estimate missing day using historical average with seasonal adjustment"""
        
        if not historical_readings:
            return None, 'no_data', 0.0
        
        # Get same day of week from previous weeks
        same_weekday = [r for r in historical_readings 
                       if r['reading_date'].weekday() == reading_date.weekday()]
        
        if same_weekday:
            # Use same weekday average
            avg_consumption = sum(r['consumption_calculated'] for r in same_weekday) / len(same_weekday)
            method = 'weekday_historical_average'
            confidence = min(0.8, len(same_weekday) / 12)  # Higher confidence with more data points
        else:
            # Fallback to overall average
            avg_consumption = sum(r['consumption_calculated'] for r in historical_readings) / len(historical_readings)
            method = 'overall_historical_average'
            confidence = min(0.6, len(historical_readings) / 30)
        
        # Apply seasonal adjustment
        month = reading_date.month
        seasonal_factor = self._get_seasonal_factor(month)
        estimated_value = avg_consumption * seasonal_factor
        
        return estimated_value, method, confidence
    
    def _estimate_suspect_day(self, reading_date: datetime, historical_readings: List[Dict]) -> tuple:
        """Estimate suspect day using interpolation if possible, otherwise historical average"""
        
        if len(historical_readings) < 2:
            return None, 'insufficient_data', 0.0
        
        # Try linear interpolation first
        before_readings = [r for r in historical_readings if r['reading_date'] < reading_date]
        after_readings = [r for r in historical_readings if r['reading_date'] > reading_date]
        
        if before_readings and after_readings:
            # Linear interpolation
            before_reading = max(before_readings, key=lambda x: x['reading_date'])
            after_reading = min(after_readings, key=lambda x: x['reading_date'])
            
            days_diff = (after_reading['reading_date'] - before_reading['reading_date']).days
            if days_diff <= 7:  # Only interpolate for gaps up to 7 days
                consumption_diff = after_reading['consumption_calculated'] - before_reading['consumption_calculated']
                daily_change = consumption_diff / days_diff
                days_from_before = (reading_date - before_reading['reading_date']).days
                
                estimated_value = before_reading['consumption_calculated'] + (daily_change * days_from_before)
                return estimated_value, 'linear_interpolation', 0.7
        
        # Fallback to historical average
        return self._estimate_missing_day(reading_date, historical_readings)
    
    def _estimate_default_day(self, reading_date: datetime, historical_readings: List[Dict]) -> tuple:
        """Default estimation method"""
        return self._estimate_missing_day(reading_date, historical_readings)
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Get seasonal adjustment factor for the given month"""
        # New Zealand seasonal factors (Southern Hemisphere)
        seasonal_factors = {
            1: 1.2,   # January - Summer, higher usage (cooling)
            2: 1.1,   # February - Summer
            3: 1.0,   # March - Autumn
            4: 0.9,   # April - Autumn
            5: 0.8,   # May - Autumn
            6: 1.3,   # June - Winter, highest usage (heating)
            7: 1.4,   # July - Winter, highest usage
            8: 1.3,   # August - Winter
            9: 1.0,   # September - Spring
            10: 0.9,  # October - Spring
            11: 0.8,  # November - Spring
            12: 1.1   # December - Summer
        }
        return seasonal_factors.get(month, 1.0)
    
    def _get_estimation_summary(self, estimation_results: List[Dict]) -> Dict:
        """Generate estimation summary"""
        if not estimation_results:
            return {'total_estimated': 0, 'by_method': {}, 'average_confidence': 0.0}
        
        by_method = {}
        total_confidence = 0.0
        
        for result in estimation_results:
            method = result['estimation_method']
            if method not in by_method:
                by_method[method] = 0
            by_method[method] += 1
            total_confidence += result['confidence']
        
        return {
            'total_estimated': len(estimation_results),
            'by_method': by_method,
            'average_confidence': total_confidence / len(estimation_results),
            'confidence_distribution': {
                'high': len([r for r in estimation_results if r['confidence'] > 0.7]),
                'medium': len([r for r in estimation_results if 0.4 <= r['confidence'] <= 0.7]),
                'low': len([r for r in estimation_results if r['confidence'] < 0.4])
            }
        }
    
    def validate_estimations(self, **context) -> Dict:
        """Validate estimated values against reasonable consumption ranges"""
        self.logger.info("Starting NHH estimation validation")
        
        # Get estimation results
        estimation_results = context['task_instance'].xcom_pull(
            key='estimation_results', task_ids='run_nhh_estimation'
        )
        
        if not estimation_results:
            self.logger.warning("No estimation results to validate")
            return {'validation_passed': True, 'issues': []}
        
        validation_issues = []
        
        for result in estimation_results:
            estimated_value = result['estimated_consumption']
            
            # Check for extreme values (daily consumption > 500 kWh is very high for residential)
            if estimated_value > 500:
                validation_issues.append({
                    'type': 'extreme_high_value',
                    'icp_id': result['icp_id'],
                    'meter_register_id': result['meter_register_id'],
                    'reading_date': result['reading_date'].isoformat(),
                    'value': float(estimated_value),
                    'threshold': 500
                })
            
            # Check for negative values
            if estimated_value < 0:
                validation_issues.append({
                    'type': 'negative_value',
                    'icp_id': result['icp_id'],
                    'meter_register_id': result['meter_register_id'],
                    'reading_date': result['reading_date'].isoformat(),
                    'value': float(estimated_value)
                })
        
        # Check overall confidence levels
        low_confidence_count = sum(1 for r in estimation_results if r['confidence'] < 0.4)
        if low_confidence_count > len(estimation_results) * 0.5:  # More than 50% low confidence
            validation_issues.append({
                'type': 'low_confidence_rate',
                'count': low_confidence_count,
                'total': len(estimation_results),
                'percentage': (low_confidence_count / len(estimation_results)) * 100
            })
        
        validation_summary = {
            'validation_passed': len(validation_issues) == 0,
            'issues': validation_issues,
            'total_results': len(estimation_results),
            'extreme_values': len([i for i in validation_issues if i['type'] == 'extreme_high_value']),
            'negative_values': len([i for i in validation_issues if i['type'] == 'negative_value'])
        }
        
        self.logger.info(f"NHH Validation complete: {validation_summary}")
        
        context['task_instance'].xcom_push(key='validation_summary', value=validation_summary)
        return validation_summary
    
    def update_calculated_table(self, **context) -> Dict:
        """Update calculated table with estimated values"""
        self.logger.info("Starting NHH calculated table update")
        
        # Get estimation results and validation
        estimation_results = context['task_instance'].xcom_pull(
            key='estimation_results', task_ids='run_nhh_estimation'
        )
        validation_summary = context['task_instance'].xcom_pull(
            key='validation_summary', task_ids='validate_estimations'
        )
        
        if not estimation_results:
            self.logger.warning("No estimation results to update")
            return {'updated_count': 0}
        
        if not validation_summary['validation_passed']:
            self.logger.error("Validation failed, skipping calculated table update")
            return {'updated_count': 0, 'error': 'Validation failed'}
        
        updated_count = 0
        
        with transaction.atomic():
            for result in estimation_results:
                # Check if record exists
                check_query = """
                SELECT id FROM metering_processed.daily_register_reads_calculated
                WHERE icp_id = %s AND meter_register_id = %s AND reading_date = %s
                """
                
                with connection.cursor() as cursor:
                    cursor.execute(check_query, [
                        result['icp_id'], result['meter_register_id'], result['reading_date']
                    ])
                    existing_record = cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    update_query = """
                    UPDATE metering_processed.daily_register_reads_calculated
                    SET 
                        consumption_calculated = %s,
                        quality_flag = 'E',
                        spoton_validation_flag = 'E',
                        is_estimated = true,
                        estimation_method = %s,
                        estimation_confidence = %s,
                        processing_notes = COALESCE(processing_notes, '') || %s,
                        calculated_at = %s
                    WHERE id = %s
                    """
                    
                    processing_note = f" | NHH Estimated: {result['estimation_method']} (conf: {result['confidence']:.2f})"
                    
                    with connection.cursor() as cursor:
                        cursor.execute(update_query, [
                            result['estimated_consumption'],
                            result['estimation_method'],
                            result['confidence'],
                            processing_note,
                            datetime.now(),
                            existing_record[0]
                        ])
                    
                    updated_count += 1
                
                else:
                    # Insert new record
                    insert_query = """
                    INSERT INTO metering_processed.daily_register_reads_calculated (
                        tenant_id, icp_id, meter_register_id, reading_date,
                        consumption_calculated, quality_flag, spoton_validation_flag,
                        is_estimated, estimation_method, estimation_confidence,
                        processing_notes, calculated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, 'E', 'E', true, %s, %s, %s, %s
                    )
                    """
                    
                    processing_note = f"NHH Estimated: {result['estimation_method']} (conf: {result['confidence']:.2f})"
                    
                    with connection.cursor() as cursor:
                        cursor.execute(insert_query, [
                            '00000000-0000-0000-0000-000000000000',  # Default tenant
                            result['icp_id'],
                            result['meter_register_id'],
                            result['reading_date'],
                            result['estimated_consumption'],
                            result['estimation_method'],
                            result['confidence'],
                            processing_note,
                            datetime.now()
                        ])
                    
                    updated_count += 1
        
        self.logger.info(f"NHH calculated table update complete: {updated_count} records updated")
        
        return {'updated_count': updated_count}
    
    def generate_estimation_report(self, **context) -> Dict:
        """Generate comprehensive NHH estimation report"""
        self.logger.info("Generating NHH estimation report")
        
        # Get all results from previous tasks
        gap_summary = context['task_instance'].xcom_pull(
            key='gap_summary', task_ids='analyze_gaps_comprehensive'
        )
        estimation_summary = context['task_instance'].xcom_pull(
            key='estimation_summary', task_ids='run_nhh_estimation'
        )
        validation_summary = context['task_instance'].xcom_pull(
            key='validation_summary', task_ids='validate_estimations'
        )
        update_result = context['task_instance'].xcom_pull(
            key='return_value', task_ids='update_calculated_table'
        )
        
        report = {
            'run_timestamp': datetime.now().isoformat(),
            'data_type': 'NHH_daily_register_reads',
            'gap_analysis': gap_summary,
            'estimation_summary': estimation_summary,
            'validation_summary': validation_summary,
            'update_result': update_result,
            'overall_status': 'SUCCESS' if (
                validation_summary and validation_summary['validation_passed'] and
                update_result and update_result.get('updated_count', 0) > 0
            ) else 'FAILED'
        }
        
        self.logger.info(f"NHH estimation report generated: {report}")
        return report


# Initialize orchestrator
orchestrator = NHHEstimationOrchestrator()

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
    'nhh_estimation_workflow',
    default_args=default_args,
    description='NHH daily register reads estimation with validation',
    schedule_interval='30 */12 * * *',  # Every 12 hours, 30 minutes after validation
    catchup=False,
    max_active_runs=1,
    tags=['metering', 'estimation', 'nhh', 'daily_reads', 'validation']
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
    task_id='run_nhh_estimation',
    python_callable=orchestrator.run_nhh_estimation,
    dag=dag
)

validation_task = PythonOperator(
    task_id='validate_estimations',
    python_callable=orchestrator.validate_estimations,
    dag=dag
)

update_calculated_task = PythonOperator(
    task_id='update_calculated_table',
    python_callable=orchestrator.update_calculated_table,
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
start_task >> analyze_gaps_task >> estimation_task >> validation_task >> update_calculated_task >> report_task >> end_task 