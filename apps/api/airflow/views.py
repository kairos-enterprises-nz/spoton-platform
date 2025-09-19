from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import requests
from datetime import datetime
from .monitoring import monitor, get_dashboard_data

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_system_health(request):
    """Get Airflow system health status."""
    try:
        health_data = monitor.get_system_health()
        return Response(health_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_dag_statistics(request):
    """Get DAG performance statistics."""
    try:
        days = int(request.GET.get('days', 7))
        stats_data = monitor.get_dag_statistics()
        return Response(stats_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_dag_list(request):
    """Get list of all DAGs with their details."""
    try:
        dag_data = monitor.get_dag_list()
        return Response(dag_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_recent_runs(request):
    """Get recent DAG runs."""
    try:
        limit = int(request.GET.get('limit', 20))
        runs_data = monitor.get_recent_runs(limit=limit)
        return Response(runs_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_connections_status(request):
    """Get connections status."""
    try:
        connections_data = monitor.get_connections_status()
        return Response(connections_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_dashboard_data(request):
    """Get all dashboard data in one call."""
    try:
        dashboard_data = get_dashboard_data()
        return Response(dashboard_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def airflow_trigger_dag(request, dag_id):
    """Trigger a DAG run."""
    try:
        # Trigger DAG via Airflow API
        response = requests.post(
            f"http://airflow-webserver:8080/api/v1/dags/{dag_id}/dagRuns",
            auth=('admin', 'admin123'),
            json={
                'dag_run_id': f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'execution_date': datetime.now().isoformat(),
                'conf': request.data.get('conf', {})
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return Response(
                {'message': f'DAG {dag_id} triggered successfully', 'data': response.json()},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': f'Failed to trigger DAG: {response.text}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def airflow_pause_dag(request, dag_id):
    """Pause/unpause a DAG."""
    try:
        is_paused = request.data.get('is_paused', True)
        
        response = requests.patch(
            f"http://airflow-webserver:8080/api/v1/dags/{dag_id}",
            auth=('admin', 'admin123'),
            json={'is_paused': is_paused},
            timeout=10
        )
        
        if response.status_code == 200:
            action = 'paused' if is_paused else 'unpaused'
            return Response(
                {'message': f'DAG {dag_id} {action} successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': f'Failed to update DAG: {response.text}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def airflow_dag_logs(request, dag_id, run_id, task_id):
    """Get task logs for a specific DAG run."""
    try:
        response = requests.get(
            f"http://airflow-webserver:8080/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/1",
            auth=('admin', 'admin123'),
            timeout=10
        )
        
        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': f'Failed to get logs: {response.text}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Internal API endpoints (no authentication required for Staff Portal)
@csrf_exempt
@require_http_methods(["GET"])
def internal_airflow_health(request):
    """Internal endpoint for Airflow system health status."""
    try:
        health_data = monitor.get_system_health()
        return JsonResponse(health_data)
    except Exception as e:
        return JsonResponse(
            {'error': str(e)}, 
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
def internal_airflow_dags(request):
    """Internal endpoint for DAG list."""
    try:
        dag_data = monitor.get_dag_list()
        return JsonResponse(dag_data)
    except Exception as e:
        return JsonResponse(
            {'error': str(e)}, 
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
def internal_airflow_dashboard(request):
    """Internal endpoint for dashboard data."""
    try:
        dashboard_data = get_dashboard_data()
        return JsonResponse(dashboard_data)
    except Exception as e:
        return JsonResponse(
            {'error': str(e)}, 
            status=500
        ) 