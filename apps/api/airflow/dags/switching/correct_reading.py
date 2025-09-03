from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
import sys
import logging

# Add the project root to the path
sys.path.insert(0, '/app')

# from airflow.providers.http.sensors.http import HttpSensor

# Note: The responsibility of this DAG is to orchestrate a reading correction
# by calling the application layer. File generation and transmission are handled by
# a separate service based on state changes made here.

default_args = {
    'owner': 'switching_workflow',
    'start_date': days_ago(1),
    'retries': 1,
}

def queue_rr_correction(**kwargs):
    """
    Calls the Django application to create and queue an 'RR' reading correction message
    and update the switch status to 'RR_SENT'.
    """
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    logging.info(f"Triggering RR correction for switch: {switch_request_id}")
    # In a real implementation, this would be a single API call that handles
    # the business logic of initiating a reading correction.
    print(f"API CALL: POST /api/internal/switching/reading-correction/{switch_request_id}/initiate")
    pass

with DAG(
    'correct_reading',
    default_args=default_args,
    description='Initiates a reading correction via an application-layer call. Handles RR (Reading Request) and related correction switch types.',
    schedule_interval=None,
    catchup=False,
    tags=['switching', 'reading-correction', 'RR'],
) as dag:
    queue_rr_task = PythonOperator(
        task_id='queue_rr_correction',
        python_callable=queue_rr_correction,
    )

    # Sensor to wait for the correction acknowledgement (AC) message.
    # This would poll an API endpoint on the SwitchRequest model.
    # wait_for_ac_acknowledgement = HttpSensor(
    #     task_id='wait_for_ac_acknowledgement',
    #     http_conn_id='django_internal_api',
    #     endpoint=f"api/internal/switching/reading-correction/{{ dag_run.conf.switch_request_id }}/status",
    #     response_check=lambda response: response.json().get('status') in ['CORRECTION_ACCEPTED', 'CORRECTION_REJECTED'],
    #     poke_interval=60 * 5, # 5 minutes
    #     timeout=60 * 60 * 24 * 2, # 2 days
    # )

    queue_rr_task # >> wait_for_ac_acknowledgement 