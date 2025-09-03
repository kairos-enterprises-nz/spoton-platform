"""
Audit logging utilities for Airflow DAGs

Provides functions to log DAG execution details to the audit app for compliance and monitoring.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

# Django setup for Airflow context
import sys
import django
from django.conf import settings

# Add the Django project path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')

try:
    django.setup()
    from energy.audit.models import AuditLog, FileMovementLog, SystemEvent, DataIntegrityCheck
    DJANGO_AVAILABLE = True
except Exception as e:
    print(f"Django not available in Airflow context: {e}")
    DJANGO_AVAILABLE = False


class DAGAuditLogger:
    """Audit logger for Airflow DAG operations."""
    
    def __init__(self, dag_id: str, run_id: str = None):
        self.dag_id = dag_id
        self.run_id = run_id or str(uuid.uuid4())
        self.batch_id = str(uuid.uuid4())
        self.server_name = os.getenv('HOSTNAME', 'airflow-worker')
        
    def log_dag_start(self, task_count: int = 0, context: Dict = None):
        """Log DAG execution start."""
        if not DJANGO_AVAILABLE:
            return
            
        try:
            SystemEvent.objects.create(
                event_type='dag_started',
                severity='info',
                title=f'DAG {self.dag_id} Started',
                description=f'Started DAG execution with {task_count} tasks',
                event_data={
                    'dag_id': self.dag_id,
                    'run_id': self.run_id,
                    'batch_id': self.batch_id,
                    'task_count': task_count,
                    'context': context or {}
                },
                service_name='airflow',
                server_name=self.server_name
            )
        except Exception as e:
            print(f"Failed to log DAG start: {e}")
    
    def log_dag_completion(self, success: bool, summary: Dict = None, error_msg: str = None):
        """Log DAG execution completion."""
        if not DJANGO_AVAILABLE:
            return
            
        try:
            severity = 'info' if success else 'error'
            status = 'completed' if success else 'failed'
            
            SystemEvent.objects.create(
                event_type='dag_completed' if success else 'dag_failed',
                severity=severity,
                title=f'DAG {self.dag_id} {status.title()}',
                description=f'DAG execution {status}' + (f': {error_msg}' if error_msg else ''),
                event_data={
                    'dag_id': self.dag_id,
                    'run_id': self.run_id,
                    'batch_id': self.batch_id,
                    'success': success,
                    'summary': summary or {},
                    'error_message': error_msg
                },
                service_name='airflow',
                server_name=self.server_name,
                is_resolved=success
            )
            
            # Also log to AuditLog for comprehensive tracking
            AuditLog.objects.create(
                action='import',
                description=f'DAG {self.dag_id} execution {status}',
                result='success' if success else 'failure',
                user_email='system@spoton.nz',
                error_message=error_msg or '',
                request_data={'dag_id': self.dag_id, 'run_id': self.run_id},
                response_data=summary or {}
            )
        except Exception as e:
            print(f"Failed to log DAG completion: {e}")
    
    def log_file_operation(self, 
                          filename: str,
                          operation: str,
                          status: str,
                          file_path: str = None,
                          source_path: str = None,
                          destination_path: str = None,
                          file_size: int = None,
                          records_processed: int = 0,
                          records_successful: int = 0,
                          records_failed: int = 0,
                          error_message: str = None,
                          started_at: datetime = None,
                          completed_at: datetime = None):
        """Log file operations (download, process, archive, etc.)."""
        if not DJANGO_AVAILABLE:
            return
            
        try:
            FileMovementLog.objects.create(
                file_name=filename,
                file_path=file_path or '',
                file_size=file_size,
                operation=operation,
                source_path=source_path or '',
                destination_path=destination_path or '',
                status=status,
                started_at=started_at or datetime.now(),
                completed_at=completed_at,
                system_process=self.dag_id,
                batch_id=self.batch_id,
                records_processed=records_processed,
                records_successful=records_successful,
                records_failed=records_failed,
                error_message=error_message or '',
                file_metadata={
                    'dag_id': self.dag_id,
                    'run_id': self.run_id
                }
            )
        except Exception as e:
            print(f"Failed to log file operation: {e}")
    
    def log_data_validation(self,
                           check_name: str,
                           check_type: str,
                           result: str,
                           records_checked: int = 0,
                           issues_found: int = 0,
                           error_message: str = None,
                           check_parameters: Dict = None,
                           check_results: Dict = None):
        """Log data validation and integrity checks."""
        if not DJANGO_AVAILABLE:
            return
            
        try:
            DataIntegrityCheck.objects.create(
                check_type=check_type,
                check_name=check_name,
                description=f'Data validation for {self.dag_id}',
                status='completed',
                started_at=datetime.now(),
                completed_at=datetime.now(),
                result=result,
                records_checked=records_checked,
                issues_found=issues_found,
                check_parameters=check_parameters or {},
                check_results=check_results or {},
                error_message=error_message or '',
                automated=True
            )
        except Exception as e:
            print(f"Failed to log data validation: {e}")


def get_dag_audit_logger(dag_id: str, context: Dict = None) -> DAGAuditLogger:
    """Get a configured audit logger for a DAG."""
    run_id = None
    if context:
        run_id = context.get('run_id') or context.get('dag_run', {}).get('run_id')
    
    return DAGAuditLogger(dag_id=dag_id, run_id=run_id) 