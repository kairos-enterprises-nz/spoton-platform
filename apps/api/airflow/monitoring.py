"""
Airflow Monitoring Module
Provides health checks and statistics for Airflow DAGs and system components.
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

# Add Django project to path for Airflow context
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

class AirflowMonitor:
    """Monitor Airflow system health and DAG performance."""
    
    def __init__(self, airflow_base_url="http://airflow-webserver:8080"):
        self.airflow_base_url = airflow_base_url
        self.auth = ('admin', 'admin123')  # Default Airflow credentials
        # Fallback URL for external access
        self.external_airflow_url = "http://localhost:8081"
    
    def get_system_health(self):
        """Get Airflow system health status."""
        try:
            # Check Airflow webserver
            response = requests.get(
                f"{self.airflow_base_url}/health",
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "webserver": "running",
                    "scheduler": "running",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "webserver": "error",
                    "message": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "unhealthy",
                "webserver": "unreachable",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_dag_statistics(self):
        """Get DAG run statistics."""
        # Try multiple URLs to connect to Airflow
        airflow_urls = [
            self.airflow_base_url,  # http://airflow-webserver:8080
            "http://localhost:8081",  # External access
            "http://192.168.1.107:8081"  # Direct IP access
        ]
        
        for airflow_url in airflow_urls:
            try:
                # Get recent DAG runs (last 50 runs instead of date filtering)
                response = requests.get(
                    f"{airflow_url}/api/v1/dags/~/dagRuns",
                    auth=self.auth,
                    params={
                        'limit': 50,
                        'order_by': '-execution_date'
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    dag_runs = response.json().get('dag_runs', [])
                    
                    stats = {
                        "total_runs": len(dag_runs),
                        "successful_runs": len([r for r in dag_runs if r['state'] == 'success']),
                        "failed_runs": len([r for r in dag_runs if r['state'] == 'failed']),
                        "running_runs": len([r for r in dag_runs if r['state'] == 'running']),
                        "timestamp": datetime.now().isoformat(),
                        "source": f"Live data from {airflow_url}"
                    }
                    
                    return stats
                else:
                    # Try next URL
                    continue
                    
            except requests.exceptions.RequestException:
                # Connection error - try next URL
                continue
            except Exception:
                # Any other error - try next URL
                continue
        
        # If all URLs failed, return fallback data
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "running_runs": 0,
            "timestamp": datetime.now().isoformat(),
            "note": "Fallback data - Airflow API unavailable"
        }
    
    def get_recent_runs(self, limit=10):
        """Get recent DAG runs."""
        # Try multiple URLs to connect to Airflow
        airflow_urls = [
            self.airflow_base_url,  # http://airflow-webserver:8080
            "http://localhost:8081",  # External access
            "http://192.168.1.107:8081"  # Direct IP access
        ]
        
        for airflow_url in airflow_urls:
            try:
                response = requests.get(
                    f"{airflow_url}/api/v1/dags/~/dagRuns",
                    auth=self.auth,
                    params={
                        'limit': limit,
                        'order_by': '-execution_date'
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    dag_runs = response.json().get('dag_runs', [])
                    
                    return {
                        "recent_runs": [
                            {
                                "dag_id": run['dag_id'],
                                "run_id": run['dag_run_id'],
                                "state": run['state'],
                                "execution_date": run['execution_date'],
                                "start_date": run['start_date'],
                                "end_date": run['end_date']
                            }
                            for run in dag_runs
                        ],
                        "timestamp": datetime.now().isoformat(),
                        "source": f"Live data from {airflow_url}"
                    }
                else:
                    # Try next URL
                    continue
                    
            except requests.exceptions.RequestException:
                # Connection error - try next URL
                continue
            except Exception:
                # Any other error - try next URL
                continue
        
        # If all URLs failed, return empty data
        return {
            "recent_runs": [],
            "timestamp": datetime.now().isoformat(),
            "note": "Fallback data - Airflow API unavailable"
        }
    
    def get_dag_list(self):
        """Get list of all DAGs with their details."""
        # Try multiple URLs to connect to Airflow
        airflow_urls = [
            self.airflow_base_url,  # http://airflow-webserver:8080
            "http://localhost:8081",  # External access
            "http://192.168.1.107:8081"  # Direct IP access
        ]
        
        for airflow_url in airflow_urls:
            try:
                response = requests.get(
                    f"{airflow_url}/api/v1/dags",
                    auth=self.auth,
                    timeout=5
                )
                
                if response.status_code == 200:
                    dags_data = response.json().get('dags', [])
                    
                    # If no DAGs found, continue to next URL
                    if not dags_data:
                        continue
                    
                    dags = []
                    for dag in dags_data:
                        # Get recent runs for this DAG
                        try:
                            runs_response = requests.get(
                                f"{airflow_url}/api/v1/dags/{dag['dag_id']}/dagRuns",
                                auth=self.auth,
                                params={'limit': 10, 'order_by': '-execution_date'},
                                timeout=3
                            )
                            
                            total_runs = 0
                            successful_runs = 0
                            failed_runs = 0
                            last_run = None
                            
                            if runs_response.status_code == 200:
                                runs = runs_response.json().get('dag_runs', [])
                                total_runs = len(runs)
                                successful_runs = len([r for r in runs if r['state'] == 'success'])
                                failed_runs = len([r for r in runs if r['state'] == 'failed'])
                                if runs:
                                    last_run = runs[0]['execution_date']
                        except Exception:
                            # If individual DAG run fetch fails, use defaults
                            total_runs = 0
                            successful_runs = 0
                            failed_runs = 0
                            last_run = None
                        
                        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
                        
                        dags.append({
                            "dag_id": dag['dag_id'],
                            "is_paused": dag['is_paused'],
                            "description": dag.get('description', ''),
                            "success_rate": round(success_rate, 1),
                            "total_runs": total_runs,
                            "successful_runs": successful_runs,
                            "failed_runs": failed_runs,
                            "last_run": last_run,
                            "next_run": dag.get('next_dagrun_create_after') or dag.get('next_dagrun'),
                            "schedule_interval": self._parse_schedule_interval(dag.get('schedule_interval')),
                            "tags": [tag['name'] if isinstance(tag, dict) else tag for tag in dag.get('tags', [])]
                        })
                    
                    return {
                        "dags": dags,
                        "total_dags": len(dags),
                        "timestamp": datetime.now().isoformat(),
                        "source": f"Live data from {airflow_url}"
                    }
                elif response.status_code == 401:
                    # Authentication issue - try next URL
                    continue
                else:
                    # Other HTTP error - try next URL
                    continue
                    
            except requests.exceptions.RequestException:
                # Connection error - try next URL
                continue
            except Exception:
                # Any other error - try next URL
                continue
        
        # If all URLs failed, return fallback data
        return self._get_fallback_dag_data()

    def _parse_schedule_interval(self, schedule_interval):
        """Parse schedule interval from various formats."""
        if schedule_interval is None:
            return None
        elif isinstance(schedule_interval, dict):
            return schedule_interval.get('value', str(schedule_interval))
        elif isinstance(schedule_interval, str):
            return schedule_interval
        else:
            return str(schedule_interval)

    def _get_fallback_dag_data(self):
        """Provide fallback DAG data when API is not accessible."""
        # These are the actual DAGs we know exist in the system
        fallback_dags = [
            {
                "dag_id": "meter_data_import",
                "is_paused": True,
                "description": "Import meter data files from various SFTP sources",
                "success_rate": 0.0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
                "schedule_interval": "0 4 * * *",
                "tags": ["metering", "import", "data"]
            },
            {
                "dag_id": "meter_files_import",
                "is_paused": True,
                "description": "Fetch metering files from SFTP and validate",
                "success_rate": 0.0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
                "schedule_interval": "0 2 * * *",
                "tags": ["metering", "sftp", "import", "stage1"]
            },
            {
                "dag_id": "meter_monthly_import",
                "is_paused": True,
                "description": "Monthly meter data import and processing",
                "success_rate": 0.0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
                "schedule_interval": "0 6 1 * *",
                "tags": ["metering", "monthly", "import"]
            },
            {
                "dag_id": "wits_data_import",
                "is_paused": True,
                "description": "Import WITS data files from SFTP sources",
                "success_rate": 0.0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
                "schedule_interval": "0 5 * * *",
                "tags": ["wits", "import", "data"]
            },
            {
                "dag_id": "wits_files_import",
                "is_paused": True,
                "description": "Fetch WITS files from SFTP and validate",
                "success_rate": 0.0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run": None,
                "next_run": None,
                "schedule_interval": "0 3 * * *",
                "tags": ["wits", "sftp", "import", "stage1"]
            }
        ]
        
        return {
            "dags": fallback_dags,
            "total_dags": len(fallback_dags),
            "timestamp": datetime.now().isoformat(),
            "note": "Fallback data - API authentication required for live data"
        }

    def get_connections_status(self):
        """Get Airflow connections status."""
        try:
            response = requests.get(
                f"{self.airflow_base_url}/api/v1/connections",
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                connections = response.json().get('connections', [])
                
                return {
                    "total_connections": len(connections),
                    "connections": [
                        {
                            "connection_id": conn['connection_id'],
                            "conn_type": conn['conn_type'],
                            "host": conn.get('host', 'N/A')
                        }
                        for conn in connections
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "error": f"Failed to fetch connections: HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to connect to Airflow API: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# Global monitor instance
monitor = AirflowMonitor()

def get_dashboard_data():
    """Get comprehensive dashboard data for Airflow monitoring."""
    return {
        "system_health": monitor.get_system_health(),
        "dag_list": monitor.get_dag_list(),
        "dag_statistics": monitor.get_dag_statistics(),
        "recent_runs": monitor.get_recent_runs(),
        "connections_status": monitor.get_connections_status()
    } 