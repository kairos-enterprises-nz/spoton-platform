"""
Final Data Processing DAG for Validation System
Combined workflow: marks best readings and populates final table
Pipeline: interval_reads_calculated → interval_reads_final (complete processing)
"""
from datetime import datetime, timedelta
import logging
import os
import sys
from typing import List, Dict, Any
import json

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalDataProcessingOrchestrator:
    """
    Final data processing orchestrator for validation system
    Handles both reading analysis and final table population
    """
    
    def __init__(self):
        self.pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    def create_processing_session(self) -> str:
        """Create a new final processing session"""
        session_id = f"final_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🚀 Created final processing session: {session_id}")
        return session_id
    
    def analyze_calculated_readings(self, session_id: str) -> Dict[str, Any]:
        """Analyze readings in the calculated table"""
        
        # Query to analyze calculated readings with version information
        analysis_query = """
        WITH reading_analysis AS (
            SELECT 
                icp_id,
                meter_register_id,
                timestamp,
                value_calculated,
                original_quality_flag,
                validation_flag,
                plausibility_score,
                is_estimated,
                estimation_confidence,
                calculated_at,
                source,
                source_file_name,
                ROW_NUMBER() OVER (
                    PARTITION BY icp_id, meter_register_id, timestamp 
                    ORDER BY calculated_at DESC, id DESC
                ) as version_rank,
                COUNT(*) OVER (
                    PARTITION BY icp_id, meter_register_id, timestamp
                ) as total_versions
            FROM interval_reads_calculated
            WHERE calculated_at >= %s
            AND calculated_at <= %s
        )
        SELECT 
            COUNT(*) as total_calculated_readings,
            COUNT(DISTINCT CONCAT(icp_id, '|', meter_register_id, '|', timestamp)) as unique_intervals,
            SUM(CASE WHEN total_versions > 1 THEN 1 ELSE 0 END) as readings_with_multiple_versions,
            SUM(CASE WHEN is_estimated = true THEN 1 ELSE 0 END) as estimated_readings,
            SUM(CASE WHEN is_estimated = false THEN 1 ELSE 0 END) as actual_readings,
            SUM(CASE WHEN validation_flag = 'P' THEN 1 ELSE 0 END) as provider_validated,
            SUM(CASE WHEN validation_flag = 'F' THEN 1 ELSE 0 END) as provider_failed,
            SUM(CASE WHEN validation_flag = 'N' THEN 1 ELSE 0 END) as no_validation,
            SUM(CASE WHEN original_quality_flag = 'A' THEN 1 ELSE 0 END) as actual_quality,
            SUM(CASE WHEN original_quality_flag = 'E' THEN 1 ELSE 0 END) as estimated_quality,
            SUM(CASE WHEN original_quality_flag = 'M' THEN 1 ELSE 0 END) as missing_quality,
            COUNT(DISTINCT icp_id) as unique_icps
        FROM reading_analysis
        """
        
        # Use a wide date range to catch all readings
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        records = self.pg_hook.get_records(analysis_query, parameters=[start_date, end_date])
        
        if not records or not records[0]:
            return {}
        
        # Convert to analysis dictionary
        analysis = {
            'total_calculated_readings': records[0][0],
            'unique_intervals': records[0][1],
            'readings_with_multiple_versions': records[0][2],
            'estimated_readings': records[0][3],
            'actual_readings': records[0][4],
            'provider_validated': records[0][5],
            'provider_failed': records[0][6],
            'no_validation': records[0][7],
            'actual_quality': records[0][8],
            'estimated_quality': records[0][9],
            'missing_quality': records[0][10],
            'unique_icps': records[0][11]
        }
        
        logger.info(f"📊 Calculated readings analysis:")
        logger.info(f"   - Total calculated readings: {analysis['total_calculated_readings']}")
        logger.info(f"   - Unique intervals: {analysis['unique_intervals']}")
        logger.info(f"   - Readings with multiple versions: {analysis['readings_with_multiple_versions']}")
        logger.info(f"   - Estimated readings: {analysis['estimated_readings']}")
        logger.info(f"   - Actual readings: {analysis['actual_readings']}")
        logger.info(f"   - Provider validated: {analysis['provider_validated']}")
        logger.info(f"   - Unique ICPs: {analysis['unique_icps']}")
        
        return analysis
    
    def determine_best_readings(self, session_id: str) -> List[Dict]:
        """Determine the best reading for each interval"""
        
        # Query to find the best reading for each interval
        best_readings_query = """
        WITH ranked_readings AS (
            SELECT 
                id,
                tenant_id,
                icp_id,
                meter_serial_number,
                meter_register_id,
                timestamp,
                value_calculated,
                original_quality_flag,
                validation_flag,
                plausibility_score,
                is_estimated,
                estimation_method,
                estimation_confidence,
                source,
                source_file_name,
                validation_results,
                estimation_inputs,
                estimation_flags,
                processing_notes,
                metadata,
                calculated_at,
                -- Rank by priority: validation status, then estimation, then calculation time
                ROW_NUMBER() OVER (
                    PARTITION BY icp_id, meter_register_id, timestamp 
                    ORDER BY 
                        CASE 
                            WHEN validation_flag = 'P' THEN 1  -- Provider validated first
                            WHEN validation_flag = 'F' THEN 3  -- Failed validation last
                            ELSE 2  -- No validation in middle
                        END,
                        CASE 
                            WHEN is_estimated = true THEN 1  -- Estimated readings after validation
                            ELSE 2
                        END,
                        calculated_at DESC,  -- Most recent calculation time
                        id DESC  -- Highest ID as tiebreaker
                ) as reading_rank
            FROM interval_reads_calculated
            WHERE calculated_at >= %s
            AND calculated_at <= %s
        )
        SELECT 
            id, tenant_id, icp_id, meter_serial_number, meter_register_id,
            timestamp, value_calculated, original_quality_flag, validation_flag, plausibility_score,
            is_estimated, estimation_method, estimation_confidence,
            source, source_file_name, validation_results, estimation_inputs, estimation_flags,
            processing_notes, metadata, calculated_at, reading_rank
        FROM ranked_readings
        WHERE reading_rank = 1  -- Only the best reading for each interval
        ORDER BY icp_id, meter_register_id, timestamp
        """
        
        # Use a wide date range to catch all readings
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        records = self.pg_hook.get_records(best_readings_query, parameters=[start_date, end_date])
        
        # Convert to dictionaries
        columns = [
            'id', 'tenant_id', 'icp_id', 'meter_serial_number', 'meter_register_id',
            'timestamp', 'value_calculated', 'original_quality_flag', 'validation_flag', 'plausibility_score',
            'is_estimated', 'estimation_method', 'estimation_confidence',
            'source', 'source_file_name', 'validation_results', 'estimation_inputs', 'estimation_flags',
            'processing_notes', 'metadata', 'calculated_at', 'reading_rank'
        ]
        
        best_readings = []
        for record in records:
            reading_dict = dict(zip(columns, record))
            best_readings.append(reading_dict)
        
        logger.info(f"🎯 Determined {len(best_readings)} best readings")
        
        # Analyze reading types
        reading_types = {
            'estimated': len([r for r in best_readings if r['is_estimated']]),
            'actual': len([r for r in best_readings if not r['is_estimated']]),
            'provider_validated': len([r for r in best_readings if r['validation_flag'] == 'P']),
            'provider_failed': len([r for r in best_readings if r['validation_flag'] == 'F']),
            'no_validation': len([r for r in best_readings if r['validation_flag'] == 'N'])
        }
        
        logger.info(f"📊 Best reading types:")
        for reading_type, count in reading_types.items():
            logger.info(f"   - {reading_type}: {count}")
        
        return best_readings
    
    def prepare_final_readings(self, session_id: str, best_readings: List[Dict]) -> List[Dict]:
        """Prepare final readings for insertion into final table"""
        
        if not best_readings:
            logger.warning("No best readings to prepare")
            return []
        
        # Check which readings are not already in final table
        existing_check_query = """
        SELECT DISTINCT 
            CONCAT(connection_id, '|', register_code, '|', timestamp) as reading_key
        FROM interval_reads_final
        WHERE finalization_date >= %s
        """
        
        existing_records = self.pg_hook.get_records(
            existing_check_query, 
            parameters=[datetime.now() - timedelta(days=7)]
        )
        
        existing_keys = {record[0] for record in existing_records}
        
        final_readings = []
        for reading in best_readings:
            reading_key = f"{reading['icp_id']}|{reading['meter_register_id']}|{reading['timestamp']}"
            
            if reading_key not in existing_keys:
                final_reading = self._prepare_final_reading_data(reading, session_id)
                final_readings.append(final_reading)
        
        logger.info(f"📋 Prepared {len(final_readings)} new final readings for insertion")
        logger.info(f"   - Skipped {len(best_readings) - len(final_readings)} existing readings")
        
        return final_readings
    
    def _prepare_final_reading_data(self, reading: Dict, session_id: str) -> Dict:
        """Prepare individual final reading data"""
        
        # Determine final quality flag
        final_quality_flag = self._determine_final_quality_flag(reading)
        
        # Create processing summary
        processing_summary = {
            'session_id': session_id,
            'original_quality_flag': reading['original_quality_flag'],
            'meter_provider_validation': reading['validation_flag'],
            'plausibility_score': float(reading['plausibility_score']) if reading['plausibility_score'] else None,
            'estimation_applied': reading['is_estimated'],
            'estimation_method': reading['estimation_method'],
            'estimation_confidence': float(reading['estimation_confidence']) if reading['estimation_confidence'] else None,
            'validation_results': reading['validation_results'],
            'estimation_inputs': reading['estimation_inputs'],
            'estimation_flags': reading['estimation_flags'],
            'processing_notes': reading['processing_notes']
        }
        
        return {
            'tenant_id': reading['tenant_id'],
            'connection_id': reading['icp_id'],
            'register_code': reading['meter_register_id'],
            'timestamp': reading['timestamp'],
            'value': reading['value_calculated'],
            'source_type': 'calculated',
            'source_id': None,  # Set to None since we don't have a UUID for calculated readings
            'finalization_date': datetime.now(),
            'finalized_by': 'system_automated',
            'metadata': {
                'session_id': session_id,
                'calculated_reading_id': reading['id'],  # Store the integer ID in metadata
                'final_quality_flag': final_quality_flag,
                'processing_summary': processing_summary,
                'validation_passed': reading['validation_flag'] == 'P',
                'estimation_applied': reading['is_estimated'],
                'source': reading['source'],
                'approval_notes': f'Automatically processed by final data processing DAG ({session_id})'
            }
        }
    
    def _determine_final_quality_flag(self, reading: Dict) -> str:
        """Determine final quality flag based on validation system"""
        
        if reading['is_estimated']:
            return 'ESTIMATED'
        elif reading['original_quality_flag'] == 'A' and reading['validation_flag'] == 'P':
            return 'ACTUAL_VALIDATED'
        elif reading['original_quality_flag'] == 'A':
            return 'ACTUAL'
        elif reading['original_quality_flag'] == 'M':
            return 'MISSING'
        elif reading['validation_flag'] == 'P':
            return 'PROVIDER_VALIDATED'
        elif reading['validation_flag'] == 'F':
            return 'PROVIDER_FAILED'
        elif reading['validation_flag'] == 'N':
            return 'NOT_VALIDATED'
        else:
            return 'UNKNOWN'
    
    def populate_final_table(self, session_id: str, final_readings: List[Dict]) -> int:
        """Populate the interval_reads_final table with final readings"""
        
        if not final_readings:
            logger.warning("No final readings to populate")
            return 0
        
        # Prepare bulk insert query (no ON CONFLICT since we check for duplicates beforehand)
        insert_query = """
        INSERT INTO interval_reads_final (
            tenant_id,
            connection_id,
            register_code,
            timestamp,
            value,
            source_type,
            source_id,
            finalization_date,
            finalized_by,
            metadata
        ) VALUES %s
        """
        
        conn = self.pg_hook.get_conn()
        cursor = conn.cursor()
        
        try:
            # Prepare values for bulk insert
            values = []
            for reading in final_readings:
                values.append((
                    reading['tenant_id'],
                    reading['connection_id'],
                    reading['register_code'],
                    reading['timestamp'],
                    reading['value'],
                    reading['source_type'],
                    reading['source_id'],
                    reading['finalization_date'],
                    reading['finalized_by'],
                    json.dumps(reading['metadata'])
                ))
            
            # Execute bulk insert
            from psycopg2.extras import execute_values
            execute_values(cursor, insert_query, values)
            
            inserted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"✅ Successfully populated {inserted_count} final readings")
            
            # Verify the insertion
            verify_query = """
            SELECT 
                COUNT(*) as total_final_readings,
                COUNT(DISTINCT connection_id) as unique_connections
            FROM interval_reads_final
            WHERE finalization_date >= %s
            """
            
            cursor.execute(verify_query, [datetime.now() - timedelta(hours=1)])
            verification = cursor.fetchone()
            
            logger.info(f"📊 Final table verification:")
            logger.info(f"   - Total final readings: {verification[0]}")
            logger.info(f"   - Unique connections: {verification[1]}")
            
            return inserted_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to populate final table: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


# DAG Definition
default_args = {
    'owner': 'data-finalization',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'final_data_processing_workflow',
    default_args=default_args,
    description='Complete Final Data Processing for Validation System',
    schedule_interval='0 0 * * *',  # Daily at midnight
    catchup=False,
    max_active_runs=1,
    tags=['final_processing', 'validation', 'metering', 'combined']
)


def create_processing_session_task(**context):
    """Create processing session"""
    orchestrator = FinalDataProcessingOrchestrator()
    session_id = orchestrator.create_processing_session()
    context['ti'].xcom_push(key='session_id', value=session_id)
    return session_id


def analyze_calculated_readings_task(**context):
    """Analyze calculated readings"""
    session_id = context['ti'].xcom_pull(key='session_id')
    orchestrator = FinalDataProcessingOrchestrator()
    analysis = orchestrator.analyze_calculated_readings(session_id)
    context['ti'].xcom_push(key='analysis', value=analysis)
    return analysis


def determine_best_readings_task(**context):
    """Determine best readings"""
    session_id = context['ti'].xcom_pull(key='session_id')
    orchestrator = FinalDataProcessingOrchestrator()
    best_readings = orchestrator.determine_best_readings(session_id)
    context['ti'].xcom_push(key='best_readings', value=best_readings)
    return len(best_readings)


def prepare_final_readings_task(**context):
    """Prepare final readings"""
    session_id = context['ti'].xcom_pull(key='session_id')
    best_readings = context['ti'].xcom_pull(key='best_readings')
    
    if not best_readings:
        logger.info("No best readings to prepare")
        return 0
    
    orchestrator = FinalDataProcessingOrchestrator()
    final_readings = orchestrator.prepare_final_readings(session_id, best_readings)
    context['ti'].xcom_push(key='final_readings', value=final_readings)
    return len(final_readings)


def populate_final_table_task(**context):
    """Populate final table"""
    session_id = context['ti'].xcom_pull(key='session_id')
    final_readings = context['ti'].xcom_pull(key='final_readings')
    
    if not final_readings:
        logger.info("No final readings to populate")
        return 0
    
    orchestrator = FinalDataProcessingOrchestrator()
    return orchestrator.populate_final_table(session_id, final_readings)


# Task Definitions
create_session = PythonOperator(
    task_id='create_processing_session',
    python_callable=create_processing_session_task,
    dag=dag
)

analyze_readings = PythonOperator(
    task_id='analyze_calculated_readings',
    python_callable=analyze_calculated_readings_task,
    dag=dag
)

determine_best = PythonOperator(
    task_id='determine_best_readings',
    python_callable=determine_best_readings_task,
    dag=dag
)

prepare_final = PythonOperator(
    task_id='prepare_final_readings',
    python_callable=prepare_final_readings_task,
    dag=dag
)

populate_table = PythonOperator(
    task_id='populate_final_table',
    python_callable=populate_final_table_task,
    dag=dag
)

# Task Dependencies
create_session >> analyze_readings >> determine_best >> prepare_final >> populate_table 