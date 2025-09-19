from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
import sys
import logging

# Add the project root to the path
sys.path.insert(0, '/app')

# from airflow.providers.http.sensors.http import HttpSensor

# Note: The responsibility of this DAG is to orchestrate the switch withdrawal
# by calling the application layer. File generation and transmission are handled by
# a separate service based on state changes made here.

default_args = {
    'owner': 'switching_workflow',
    'start_date': days_ago(1),
    'retries': 1,
}

def queue_nw_withdrawal(**kwargs):
    """
    Calls the Django application to create and queue an 'NW' withdrawal message
    and update the switch status to 'WITHDRAWAL_SENT'.
    """
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    logging.info(f"Triggering NW withdrawal for switch: {switch_request_id}")
    # In a real implementation, this would be a single API call that handles
    # the business logic of initiating a withdrawal.
    print(f"API CALL: POST /api/internal/switching/withdrawal/{switch_request_id}/initiate")
    pass

with DAG(
    'withdraw_switch',
    default_args=default_args,
    description='Initiates a switch withdrawal via an application-layer call. Handles NW (New Withdrawal) and AW (Acknowledgement Withdrawal) switch types.',
    schedule_interval=None,
    catchup=False,
    tags=['switching', 'withdrawal', 'NW', 'AW'],
) as dag:
    queue_nw_task = PythonOperator(
        task_id='queue_nw_withdrawal',
        python_callable=queue_nw_withdrawal,
    )

    # Sensor to wait for the withdrawal acknowledgement (AW) message.
    # This would poll an API endpoint on the SwitchRequest model.
    # wait_for_aw_acknowledgement = HttpSensor(
    #     task_id='wait_for_aw_acknowledgement',
    #     http_conn_id='django_internal_api',
    #     endpoint=f"api/internal/switching/withdrawal/{{ dag_run.conf.switch_request_id }}/status",
    #     response_check=lambda response: response.json().get('status') in ['WITHDRAWAL_ACCEPTED', 'WITHDRAWAL_REJECTED'],
    #     poke_interval=60 * 5, # 5 minutes
    #     timeout=60 * 60 * 24 * 2, # 2 days
    # )

    queue_nw_task # >> wait_for_aw_acknowledgement 