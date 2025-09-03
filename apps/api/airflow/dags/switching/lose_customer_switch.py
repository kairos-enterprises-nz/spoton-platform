from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from pendulum import datetime
import sys
import logging

# Add the project root to the path for utility and config imports
sys.path.insert(0, '/app')

# from airflow.providers.http.operators.http import SimpleHttpOperator
# from airflow.providers.http.sensors.http import HttpSensor

# Note: The responsibility of this DAG is to orchestrate the switch-loss process
# by calling the application layer (e.g., Django API or management commands).
# It should not be responsible for generating file content or performing SFTP uploads directly.
# A separate, dedicated service should handle file generation and transmission based on
# state changes made by this DAG.

default_args = {
    'owner': 'switching_workflow',
    'start_date': days_ago(1),
    'retries': 1,
}

def queue_an_acknowledgement(**kwargs):
    """
    Calls the Django application to create and queue an 'AN' (RS-020) message.
    The application will mark the switch as 'accepted' and generate the outbound file.
    """
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    logging.info(f"Triggering AN generation for switch loss: {switch_request_id}")
    # In a real implementation, this would be an API call or a Django management command.
    # e.g., using SimpleHttpOperator or BashOperator to call manage.py
    # For now, this is a placeholder.
    print(f"API CALL: POST /api/internal/switching/loss/{switch_request_id}/acknowledge")
    # The application layer is now responsible for content and file transmission.
    pass

def trigger_final_reading_process(**kwargs):
    """
    Initiates the final reading process within the Django application.
    """
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    logging.info(f"Triggering final reading process for switch loss: {switch_request_id}")
    # This would call an API endpoint that handles the complex logic
    # of gathering a final read, which might be asynchronous.
    print(f"API CALL: POST /api/internal/switching/loss/{switch_request_id}/gather-reading")
    pass

def queue_cs_final_statement(**kwargs):
    """
    Calls the Django application to generate the final 'CS' (RS-050) statement.
    """
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    logging.info(f"Triggering CS final statement generation for switch loss: {switch_request_id}")
    # This would call an API endpoint that uses the final reading data to create the CS file.
    print(f"API CALL: POST /api/internal/switching/loss/{switch_request_id}/final-statement")
    pass

with DAG(
    'lose_customer_switch',
    default_args=default_args,
    description='Orchestrates a switch-out by calling application-layer services. Handles AN (Acknowledgement) and related switch types for customer loss.',
    schedule_interval=None,
    catchup=False,
    tags=['switching', 'switch-loss', 'AN'],
) as dag:
    queue_an_task = PythonOperator(
        task_id='queue_an_acknowledgement',
        python_callable=queue_an_acknowledgement,
    )

    # Sensor to wait for the final reading to be available in the application.
    # This would poll an API endpoint on the SwitchRequest model.
    # wait_for_final_reading = HttpSensor(
    #     task_id='wait_for_final_reading',
    #     http_conn_id='django_internal_api',
    #     endpoint=f"api/internal/switching/loss/{{ dag_run.conf.switch_request_id }}/status",
    #     response_check=lambda response: response.json().get('final_reading_status') == 'COMPLETE',
    #     poke_interval=60 * 5, # 5 minutes
    #     timeout=60 * 60 * 24 * 2, # 2 days
    # )

    trigger_reading_task = PythonOperator(
        task_id='trigger_final_reading_process',
        python_callable=trigger_final_reading_process,
    )

    queue_cs_task = PythonOperator(
        task_id='queue_cs_final_statement',
        python_callable=queue_cs_final_statement,
    )

    queue_an_task >> trigger_reading_task >> queue_cs_task 