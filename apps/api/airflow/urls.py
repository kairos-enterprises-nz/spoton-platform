from django.urls import path
from . import views

app_name = 'airflow'

urlpatterns = [
    # Airflow monitoring endpoints (authenticated)
    path('health/', views.airflow_system_health, name='airflow_health'),
    path('dags/', views.airflow_dag_list, name='airflow_dag_list'),
    path('dags/statistics/', views.airflow_dag_statistics, name='airflow_dag_statistics'),
    path('runs/recent/', views.airflow_recent_runs, name='airflow_recent_runs'),
    path('connections/', views.airflow_connections_status, name='airflow_connections'),
    path('dashboard/', views.airflow_dashboard_data, name='airflow_dashboard'),
    
    # Internal endpoints (no authentication required)
    path('internal/health/', views.internal_airflow_health, name='internal_airflow_health'),
    path('internal/dags/', views.internal_airflow_dags, name='internal_airflow_dags'),
    path('internal/dashboard/', views.internal_airflow_dashboard, name='internal_airflow_dashboard'),
    
    # DAG management endpoints (authenticated)
    path('dags/<str:dag_id>/trigger/', views.airflow_trigger_dag, name='airflow_trigger_dag'),
    path('dags/<str:dag_id>/pause/', views.airflow_pause_dag, name='airflow_pause_dag'),
    path('dags/<str:dag_id>/runs/<str:run_id>/tasks/<str:task_id>/logs/', 
         views.airflow_dag_logs, name='airflow_dag_logs'),
] 