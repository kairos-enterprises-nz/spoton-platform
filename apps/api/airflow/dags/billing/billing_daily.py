from __future__ import annotations

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except Exception:  # Airflow not available in all environments (e.g., CI lint)
    DAG = object  # type: ignore
    PythonOperator = object  # type: ignore


default_args = {
    'owner': 'spoton',
}


def noop():
    return True


with DAG(
    dag_id='billing_daily',
    start_date=datetime(2025, 8, 1),
    schedule_interval='@daily',
    catchup=False,
    default_args=default_args,
) as dag:
    calculate_bills = PythonOperator(task_id='calculate_bills', python_callable=noop)
    generate_draft_invoices = PythonOperator(task_id='generate_draft_invoices', python_callable=noop)
    wait_for_review = PythonOperator(task_id='wait_for_review', python_callable=noop)
    book_invoices = PythonOperator(task_id='book_invoices', python_callable=noop)
    generate_pdfs = PythonOperator(task_id='generate_pdfs', python_callable=noop)
    send_emails = PythonOperator(task_id='send_emails', python_callable=noop)
    check_reversals = PythonOperator(task_id='check_for_reversals_or_adjustments', python_callable=noop)

    calculate_bills >> generate_draft_invoices >> wait_for_review >> book_invoices >> generate_pdfs >> send_emails >> check_reversals

