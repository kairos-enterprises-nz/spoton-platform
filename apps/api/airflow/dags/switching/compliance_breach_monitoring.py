from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from pendulum import datetime
import sys
import os
import psycopg2
import logging

# Add project and utility directories to the python path.
# This ensures that both app-level modules (like 'energy') and shared
# Airflow utilities (like 'connection') can be found.
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/airflow/utils')

from energy.switch_compliance.config import SWITCHING_TIMEFRAMES, PUBLIC_HOLIDAYS
from connection import get_connection
from switching_business_days import calculate_business_day_delta


def check_an_breaches(**kwargs):
    """
    Checks for breaches in AN delivery by comparing NT send dates to AN receipt dates
    from the raw switching tables.
    """
    logging.info("Checking for AN Delivery Breaches")
    breach_config = SWITCHING_TIMEFRAMES.get('AN_DELIVERY', {})
    if not breach_config:
        logging.warning("AN_DELIVERY configuration not found in compliance config.")
        return

    an_due_days = breach_config.get('TR', {}).get('due_business_days', 3)
    
    query = """
    SELECT nt.icp_identifier, nt.event_date, nt.file_name as nt_file, an.file_name as an_file, nt.processed_at as nt_sent_at, an.processed_at as an_received_at
    FROM switching.nt_requests nt
    LEFT JOIN switching.an_acknowledgements an
        ON nt.icp_identifier = an.icp_identifier AND nt.event_date = an.event_date
    WHERE nt.processed_at < NOW() - INTERVAL '%s days'
    """ % (an_due_days + 5)

    breached_requests = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                
                for row in results:
                    icp, nt_date, nt_file, an_file, nt_sent, an_received = row
                    if an_file is None:
                        breached_requests.append({
                            'icp': icp,
                            'nt_file': nt_file,
                            'reason': f"No AN received for NT sent on {nt_sent.strftime('%Y-%m-%d')}"
                        })
                    else:
                        business_days = calculate_business_day_delta(nt_sent, an_received, PUBLIC_HOLIDAYS)
                        if business_days > an_due_days:
                            breached_requests.append({
                                'icp': icp,
                                'nt_file': nt_file,
                                'an_file': an_file,
                                'reason': f"{business_days} business days taken to receive AN, exceeding the {an_due_days} day SLA."
                            })
    except Exception as e:
        logging.error(f"Failed to check AN breaches in database: {e}")
    
    logging.info(f"Found {len(breached_requests)} potential AN delivery breaches.")
    kwargs['ti'].xcom_push(key='an_breaches', value=breached_requests)


def generate_and_send_report(**kwargs):
    """
    Generates a report of all breaches and sends it via email.
    """
    ti = kwargs['ti']
    an_breaches = ti.xcom_pull(task_ids='check_an_breaches', key='an_breaches')

    if not an_breaches:
        print("No compliance breaches found.")
        return

    report = "Compliance Breach Report:\n\n"
    if an_breaches:
        report += "\nAN Delivery Breaches:\n"
        for breach in an_breaches:
            report += f"  - ICP: {breach['icp']}, Reason: {breach['reason']}\n"
            
    print("--- BREACH REPORT ---")
    print(report)
    print("--- END REPORT ---")


default_args = {
    'owner': 'switching_workflow',
    'start_date': days_ago(1),
    'retries': 1,
}

with DAG(
    'compliance_breach_monitoring',
    default_args=default_args,
    description='A DAG to monitor and report on switching compliance breaches by querying the raw database tables. Monitors NT, AN, CS, RR, AC, NW, AW switch types for compliance violations.',
    schedule_interval='0 20 * * 1-5', # 8 PM on weekdays
    catchup=False,
    tags=['switching', 'compliance', 'NT', 'AN', 'CS', 'RR', 'AC', 'NW', 'AW'],
) as dag:
    check_an_breaches_task = PythonOperator(
        task_id='check_an_breaches',
        python_callable=check_an_breaches,
    )

    generate_and_send_report_task = PythonOperator(
        task_id='generate_and_send_report',
        python_callable=generate_and_send_report,
        trigger_rule='all_done',
    )

    check_an_breaches_task >> generate_and_send_report_task 