from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.sftp.operators.sftp import SFTPOperator
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.dates import days_ago
from pendulum import datetime
import json
from airflow.exceptions import AirflowSkipException
import requests
from airflow.utils.decorators import apply_defaults

class RegistryMessageSensor(BaseSensorOperator):
    @apply_defaults
    def __init__(self, switch_request_id, expected_message_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switch_request_id = switch_request_id
        self.expected_message_type = expected_message_type

    def poke(self, context):
        self.log.info(
            f"Poking for message type {self.expected_message_type} "
            f"for switch request {self.switch_request_id}"
        )

        # This should be an internal API call to your Django app to check for the message.
        # from airflow.providers.http.hooks.http import HttpHook
        # http_hook = HttpHook(method='GET', http_conn_id='django_internal_api')
        # response = http_hook.run(
        #     f'api/staff/v1/switching/internal/switches/{self.switch_request_id}/messages/',
        #     data={'message_type': self.expected_message_type}
        # )
        # return response.json().get('message_exists', False)
        
        # Placeholder logic
        return False # This will cause the sensor to wait until the timeout

def check_for_override(**kwargs):
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    if not switch_request_id:
        raise ValueError("switch_request_id not found in DAG run configuration")

    # This should be an internal API call to your Django app.
    # You would use the HttpHook to make the request.
    # from airflow.providers.http.hooks.http import HttpHook
    # http_hook = HttpHook(method='GET', http_conn_id='django_internal_api')
    # response = http_hook.run(f'api/staff/v1/switching/internal/switches/{switch_request_id}/')
    # if response.json().get('override_active'):
    #     raise AirflowSkipException("Manual override is active for this switch request.")
    
    # Placeholder logic
    print(f"Checking for override for switch request {switch_request_id}")

def generate_nt_content(**kwargs):
    switch_request_id = kwargs['dag_run'].conf.get('switch_request_id')
    if not switch_request_id:
        raise ValueError("switch_request_id not found in DAG run configuration")

    # This should be an internal API call to your Django app to get the contract details.
    # from airflow.providers.http.hooks.http import HttpHook
    # http_hook = HttpHook(method='GET', http_conn_id='django_internal_api')
    # response = http_hook.run(f'api/staff/v1/switching/internal/switches/{switch_request_id}/details/')
    # contract_details = response.json()

    # Placeholder logic
    print(f"Generating NT content for switch request {switch_request_id}")
    nt_content = f"NT file for {switch_request_id}"
    filename = f"NT_{switch_request_id}.txt"
    
    kwargs['ti'].xcom_push(key='filename', value=filename)
    kwargs['ti'].xcom_push(key='nt_content', value=nt_content)

default_args = {
    'owner': 'switching_workflow',
    'start_date': days_ago(1),
    'retries': 3,
}

with DAG(
    'gain_customer_switch',
    default_args=default_args,
    description='A DAG to handle the customer switching process. Primarily handles CS (Customer Switch) and related NT (New Connection) switch types.',
    schedule_interval=None,
    catchup=False,
    tags=['switching', 'CS', 'NT'],
) as dag:
    check_for_override_task = PythonOperator(
        task_id='check_for_override',
        python_callable=check_for_override,
        provide_context=True,
    )

    generate_nt_content_task = PythonOperator(
        task_id='generate_nt_content',
        python_callable=generate_nt_content,
        provide_context=True,
    )

    upload_nt_file_task = SFTPOperator(
        task_id='upload_nt_file',
        ssh_conn_id='registry_sftp',
        local_filepath="/tmp/{{ ti.xcom_pull(task_ids='generate_nt_content', key='filename') }}",
        remote_filepath="/toreg/{{ ti.xcom_pull(task_ids='generate_nt_content', key='filename') }}",
    )

    update_status_nt_sent_task = SimpleHttpOperator(
        task_id='update_status_nt_sent',
        http_conn_id='django_internal_api',
        endpoint='/api/staff/v1/switching/internal/switches/{{ dag_run.conf["switch_request_id"] }}/update/',
        method='PATCH',
        data=json.dumps({'status': 'NT_SENT', 'nt_sent_at': '{{ ts }}'}),
        headers={"Content-Type": "application/json", "Authorization": "Token {{ var.value.django_api_token }}"},
    )

    wait_for_an_message_task = RegistryMessageSensor(
        task_id='wait_for_an_message',
        switch_request_id='{{ dag_run.conf["switch_request_id"] }}',
        expected_message_type='RS-020',
        timeout=60 * 60 * 24 * 5,  # 5 days
    )

    check_for_override_task >> generate_nt_content_task >> upload_nt_file_task >> update_status_nt_sent_task >> wait_for_an_message_task 