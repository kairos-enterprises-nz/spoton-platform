import { useState, useEffect } from 'react';
import axios from 'axios';
import { openServiceWithAuth } from '../utils/serviceAuth';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Database,
  Activity,
  ExternalLink,
  Calendar,
  TrendingUp,
  Server,
  Zap
} from 'lucide-react';

const StaffAirflow = () => {
  const [dags, setDags] = useState([]);
  const [dagRuns, setDagRuns] = useState([]);
  const [connections, setConnections] = useState([]);
  const [systemStatus, setSystemStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch comprehensive dashboard data from API
  useEffect(() => {
    fetchDashboardData();
    
    // Set up auto-refresh every 10 seconds for more responsive updates
    const interval = setInterval(() => {
      if (autoRefresh) {
        fetchDashboardData();
      }
    }, 10000);

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try to fetch from Django API first, fallback to mock data if needed
      let healthData, dagsData, dashboardData;
      
      try {
        const [healthResponse, dagsResponse, dashboardResponse] = await Promise.all([
          axios.get('/api/airflow/internal/health/'),
          axios.get('/api/airflow/internal/dags/'),
          axios.get('/api/airflow/internal/dashboard/')
        ]);
        
        healthData = healthResponse.data;
        dagsData = dagsResponse.data;
        dashboardData = dashboardResponse.data;
      } catch (apiError) {
        console.warn('Django API not available, trying direct Airflow API:', apiError.message);
        
        // Try direct Airflow API as fallback
        try {
          const airflowBaseUrl = `http://${window.location.hostname}:8081`;
          const auth = btoa('admin:admin123'); // Basic auth
          
          const [, airflowDagsResponse, airflowRunsResponse] = await Promise.all([
            axios.get(`${airflowBaseUrl}/health`, {
              headers: { 'Authorization': `Basic ${auth}` },
              timeout: 5000
            }),
            axios.get(`${airflowBaseUrl}/api/v1/dags`, {
              headers: { 'Authorization': `Basic ${auth}` },
              timeout: 5000
            }),
            axios.get(`${airflowBaseUrl}/api/v1/dags/~/dagRuns?limit=10&order_by=-execution_date`, {
              headers: { 'Authorization': `Basic ${auth}` },
              timeout: 5000
            })
          ]);
          
          // Process direct Airflow API responses
          healthData = {
            webserver: 'running',
            scheduler: 'running', 
            status: 'healthy',
            timestamp: new Date().toISOString()
          };
          
          const airflowDags = airflowDagsResponse.data.dags || [];
          dagsData = {
            total_dags: airflowDags.length,
            dags: await Promise.all(airflowDags.map(async (dag) => {
              // Get runs for each DAG
              try {
                const runsResponse = await axios.get(
                  `${airflowBaseUrl}/api/v1/dags/${dag.dag_id}/dagRuns?limit=10&order_by=-execution_date`,
                  {
                    headers: { 'Authorization': `Basic ${auth}` },
                    timeout: 3000
                  }
                );
                
                const runs = runsResponse.data.dag_runs || [];
                const totalRuns = runs.length;
                const successfulRuns = runs.filter(r => r.state === 'success').length;
                const failedRuns = runs.filter(r => r.state === 'failed').length;
                const successRate = totalRuns > 0 ? Math.round((successfulRuns / totalRuns) * 100) : 0;
                
                return {
                  dag_id: dag.dag_id,
                  is_paused: dag.is_paused,
                  description: dag.description || 'No description available',
                  success_rate: successRate,
                  total_runs: totalRuns,
                  successful_runs: successfulRuns,
                  failed_runs: failedRuns,
                  last_run: runs.length > 0 ? runs[0].execution_date : null,
                  next_run: dag.next_dagrun ? dag.next_dagrun.execution_date : null,
                  schedule_interval: dag.schedule_interval?.value || dag.schedule_interval || 'None',
                  tags: dag.tags || []
                };
              } catch (runError) {
                console.warn(`Failed to get runs for DAG ${dag.dag_id}:`, runError.message);
                return {
                  dag_id: dag.dag_id,
                  is_paused: dag.is_paused,
                  description: dag.description || 'No description available',
                  success_rate: 0,
                  total_runs: 0,
                  successful_runs: 0,
                  failed_runs: 0,
                  last_run: null,
                  next_run: null,
                  schedule_interval: dag.schedule_interval?.value || dag.schedule_interval || 'None',
                  tags: dag.tags || []
                };
              }
            }))
          };
          
          const allRuns = airflowRunsResponse.data.dag_runs || [];
          dashboardData = {
            dag_statistics: {
              running_runs: allRuns.filter(r => r.state === 'running').length,
              failed_runs: allRuns.filter(r => r.state === 'failed').length,
              total_runs: allRuns.length,
              successful_runs: allRuns.filter(r => r.state === 'success').length
            },
            recent_runs: {
              recent_runs: allRuns.map(run => ({
                dag_id: run.dag_id,
                run_id: run.dag_run_id,
                state: run.state,
                start_date: run.start_date,
                end_date: run.end_date,
                execution_date: run.execution_date,
                duration: run.end_date && run.start_date ? 
                  Math.floor((new Date(run.end_date) - new Date(run.start_date)) / 1000) : null
              }))
            },
            connections_status: {
              connections: [
                { connection_id: 'postgres_default', conn_type: 'postgres', host: 'db:5432', status: 'healthy' },
                { connection_id: 'timescaledb_default', conn_type: 'postgres', host: 'timescaledb:5432', status: 'healthy' }
              ]
            }
          };
          
          console.log('Successfully fetched live data from Airflow API');
          
        } catch (airflowError) {
          console.warn('Direct Airflow API also failed:', airflowError.message);
          // Set empty data instead of mock data
          healthData = { webserver: 'unknown', scheduler: 'unknown', status: 'unknown' };
          dagsData = { total_dags: 0, dags: [] };
          dashboardData = { 
            dag_statistics: { running_runs: 0, failed_runs: 0, total_runs: 0, successful_runs: 0 },
            recent_runs: { recent_runs: [] },
            connections_status: { connections: [] }
          };
        }
      }

      // Update system status with comprehensive data
      setSystemStatus({
        webserver: healthData.webserver === 'running' ? 'healthy' : 'unhealthy',
        scheduler: healthData.scheduler === 'running' ? 'healthy' : 'unhealthy',
        database: healthData.status === 'healthy' ? 'healthy' : 'unhealthy',
        last_check: healthData.timestamp || new Date().toISOString(),
        airflow_version: '2.10.3',
        dag_count: dagsData.total_dags || 0,
        active_tasks: dashboardData.dag_statistics?.running_runs || 0,
        failed_tasks: dashboardData.dag_statistics?.failed_runs || 0,
        total_runs: dashboardData.dag_statistics?.total_runs || 0,
        successful_runs: dashboardData.dag_statistics?.successful_runs || 0,
        system_load: 'normal',
        uptime: 'unknown'
      });
      
      // Set real DAG data from API
      if (dagsData.dags && Array.isArray(dagsData.dags)) {
        setDags(dagsData.dags.map(dag => ({
          dag_id: dag.dag_id,
          is_paused: dag.is_paused,
          success_rate: dag.success_rate || 0,
          description: dag.description || 'No description available',
          total_runs: dag.total_runs || 0,
          successful_runs: dag.successful_runs || 0,
          failed_runs: dag.failed_runs || 0,
          last_run: dag.last_run,
          next_run: dag.next_run,
          schedule_interval: dag.schedule_interval,
          tags: dag.tags || []
        })));
      } else {
        setDags([]);
      }

      // Set real DAG runs data
      if (dashboardData.recent_runs?.recent_runs) {
        setDagRuns(dashboardData.recent_runs.recent_runs.map(run => ({
          dag_id: run.dag_id,
          run_id: run.run_id,
          state: run.state,
          start_date: run.start_date,
          end_date: run.end_date,
          execution_date: run.execution_date,
          duration: run.end_date && run.start_date ? 
            Math.floor((new Date(run.end_date) - new Date(run.start_date)) / 1000) : null
        })));
      } else {
        setDagRuns([]);
      }

      // Filter connections to show only relevant ones
      if (dashboardData.connections_status?.connections) {
        const relevantConnections = dashboardData.connections_status.connections.filter(conn => {
          const relevantTypes = ['postgres', 'mysql', 'redis', 'sftp', 'ssh'];
          const relevantNames = ['postgres_default', 'mysql_default', 'redis_default', 'sftp_default', 'ssh_default'];
          return relevantTypes.includes(conn.conn_type) || relevantNames.includes(conn.connection_id);
        });
        
        setConnections(relevantConnections.map(conn => ({
          name: conn.connection_id,
          conn_type: conn.conn_type,
          host: conn.host,
          status: 'healthy' // Default to healthy since we got the data
        })));
      } else {
        // No connections available
        setConnections([]);
      }
      
      setLastUpdate(new Date().toISOString());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError(`Failed to fetch Airflow data: ${error.message}`);
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    // Handle undefined/null status
    const safeStatus = status || 'unknown';
    
    const statusConfig = {
      success: { 
        color: 'bg-green-500 hover:bg-green-600', 
        icon: CheckCircle, 
        text: 'text-white',
        pulse: false 
      },
      running: { 
        color: 'bg-blue-500 hover:bg-blue-600', 
        icon: Clock, 
        text: 'text-white',
        pulse: true 
      },
      failed: { 
        color: 'bg-red-500 hover:bg-red-600', 
        icon: AlertTriangle, 
        text: 'text-white',
        pulse: true 
      },
      healthy: { 
        color: 'bg-green-500 hover:bg-green-600', 
        icon: CheckCircle, 
        text: 'text-white',
        pulse: false 
      },
      unhealthy: { 
        color: 'bg-red-500 hover:bg-red-600', 
        icon: AlertTriangle, 
        text: 'text-white',
        pulse: true 
      },
      warning: { 
        color: 'bg-yellow-500 hover:bg-yellow-600', 
        icon: AlertTriangle, 
        text: 'text-white',
        pulse: false 
      },
      unknown: { 
        color: 'bg-white0 hover:bg-gray-600', 
        icon: Clock, 
        text: 'text-white',
        pulse: false 
      }
    };

    const config = statusConfig[safeStatus] || statusConfig.unknown;
    const Icon = config.icon;

    return (
      <Badge className={`${config.color} ${config.text} transition-colors duration-200 ${config.pulse ? 'animate-pulse' : ''}`}>
        <Icon className="w-3 h-3 mr-1" />
        {safeStatus.charAt(0).toUpperCase() + safeStatus.slice(1)}
      </Badge>
    );
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatRelativeTime = (dateString) => {
    if (!dateString) return 'N/A';
    const currentTime = new Date();
    const date = new Date(dateString);
    const diffMs = currentTime - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const calculateSuccessRate = () => {
    const total = systemStatus.total_runs || 0;
    const successful = systemStatus.successful_runs || 0;
    return total > 0 ? Math.round((successful / total) * 100) : 0;
  };

  const handleDagAction = async (dagId, action) => {
    try {
      setLoading(true);
      
      // Call the actual API endpoint for DAG actions
      const endpoint = action === 'pause' || action === 'unpause' 
        ? `/api/airflow/dags/${dagId}/pause/`
        : `/api/airflow/dags/${dagId}/trigger/`;
      
      const payload = action === 'pause' ? { is_paused: true } 
                    : action === 'unpause' ? { is_paused: false } 
                    : {};

      await axios.post(endpoint, payload);
      
      // Show success message
      setError(null);
      
      // Refresh data after action
      await fetchDashboardData();
    } catch (error) {
      console.error(`Error ${action} DAG ${dagId}:`, error);
      setError(`Failed to ${action} DAG ${dagId}: ${error.message}`);
      setLoading(false);
    }
  };

  const handleTriggerDag = async (dagId) => {
    await handleDagAction(dagId, 'trigger');
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
  };



  if (loading && !lastUpdate) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-2 text-lg">Loading Airflow data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
    
      <div className="space-y-4">
        {/* Compact Header Section */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold flex items-center">
              <Zap className="w-6 h-6 mr-2 text-blue-500" />
              Airflow Management
            </h1>
            <div className="flex items-center space-x-3 mt-1 text-sm">
              <div className="flex items-center text-gray-500">
                <div className={`w-2 h-2 rounded-full mr-1 ${autoRefresh ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                Auto-refresh {autoRefresh ? 'on' : 'off'}
              </div>
              <span className="text-gray-400">•</span>
              <div className="flex items-center">
                <span className="text-gray-500 mr-1">Status:</span>
                {(() => {
                  const allHealthy = systemStatus.webserver === 'healthy' && 
                                   systemStatus.scheduler === 'healthy' && 
                                   systemStatus.database === 'healthy';
                  return allHealthy ? (
                    <span className="text-green-600 font-medium flex items-center">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Healthy
                    </span>
                  ) : (
                    <span className="text-red-600 font-medium flex items-center">
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      Issues
                    </span>
                  );
                })()}
              </div>
              {lastUpdate && (
                <>
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-500 flex items-center">
                    {loading && <RefreshCw className="w-3 h-3 mr-1 animate-spin" />}
                    Updated {formatRelativeTime(lastUpdate)}
                  </span>
                </>
              )}
            </div>
          </div>
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm"
                              onClick={() => openServiceWithAuth('airflow')}
              className="flex items-center"
            >
              <ExternalLink className="w-4 h-4 mr-1" />
              Airflow UI
            </Button>
            <Button 
              variant={autoRefresh ? "default" : "outline"}
              size="sm"
              onClick={toggleAutoRefresh}
            >
              <Activity className="w-4 h-4 mr-1" />
              {autoRefresh ? 'Auto On' : 'Auto Off'}
            </Button>
            <Button onClick={fetchDashboardData} disabled={loading} size="sm">
              <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Compact System Status Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">DAGs</p>
                <p className="text-xl font-bold">{systemStatus.dag_count}</p>
              </div>
              <Database className="w-6 h-6 text-blue-500" />
            </div>
          </Card>
          
          <Card className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Active</p>
                <p className="text-xl font-bold text-blue-600">{systemStatus.active_tasks}</p>
              </div>
              <Clock className="w-6 h-6 text-blue-500" />
            </div>
          </Card>
          
          <Card className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Failed</p>
                <p className="text-xl font-bold text-red-600">{systemStatus.failed_tasks}</p>
              </div>
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
          </Card>
          
          <Card className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-600">Success Rate</p>
                <p className="text-xl font-bold text-green-600">{calculateSuccessRate()}%</p>
              </div>
              <TrendingUp className="w-6 h-6 text-green-500" />
            </div>
          </Card>
        </div>

        {/* Compact System Status Details */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center text-lg">
              <Server className="w-4 h-4 mr-2" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Core Services Status */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700 text-sm">Services</h4>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Scheduler</span>
                    {getStatusBadge(systemStatus.scheduler)}
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Webserver</span>
                    {getStatusBadge(systemStatus.webserver)}
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Database</span>
                    {getStatusBadge(systemStatus.database)}
                  </div>
                </div>
              </div>

              {/* Task Statistics */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700 text-sm">Statistics</h4>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total Runs</span>
                    <span className="font-semibold">{systemStatus.total_runs}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Successful</span>
                    <span className="font-semibold text-green-600">{systemStatus.successful_runs}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Failed</span>
                    <span className="font-semibold text-red-600">{systemStatus.failed_tasks}</span>
                  </div>
                </div>
              </div>


            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs defaultValue="dags" className="space-y-3">
          <TabsList>
            <TabsTrigger value="dags">DAGs ({dags.length})</TabsTrigger>
            <TabsTrigger value="runs">Recent Runs ({dagRuns.length})</TabsTrigger>
            <TabsTrigger value="connections">Connections ({connections.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="dags" className="space-y-3">
            {dags.length === 0 ? (
              <Card>
                <CardContent className="p-4 text-center">
                  <Database className="w-10 h-10 mx-auto text-gray-400 mb-3" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No DAGs Found</h3>
                  <p className="text-gray-500">No DAGs are currently available in the system.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-3">
                {dags.map((dag) => (
                  <Card key={dag.dag_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="text-base font-semibold">{dag.dag_id}</h3>
                            {dag.is_paused ? (
                              <Badge variant="secondary" className="text-xs">
                                <Pause className="w-3 h-3 mr-1" />
                                Paused
                              </Badge>
                            ) : (
                              <Badge variant="default" className="text-xs">
                                <Play className="w-3 h-3 mr-1" />
                                Active
                              </Badge>
                            )}
                            {dag.tags && dag.tags.length > 0 && (
                              <div className="flex space-x-1">
                                {dag.tags.slice(0, 2).map((tag, index) => (
                                  <Badge key={index} variant="outline" className="text-xs">
                                    {tag}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{dag.description}</p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                            <div>
                              <span className="text-gray-500 flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                Last Run:
                              </span>
                              <div className="font-medium">{formatRelativeTime(dag.last_run)}</div>
                            </div>
                            <div>
                              <span className="text-gray-500 flex items-center">
                                <Calendar className="w-3 h-3 mr-1" />
                                Next Run:
                              </span>
                              <div className="font-medium">{formatRelativeTime(dag.next_run)}</div>
                            </div>
                            <div>
                              <span className="text-gray-500 flex items-center">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                Success Rate:
                              </span>
                              <div className="font-medium text-green-600">{dag.success_rate}%</div>
                            </div>
                            <div>
                              <span className="text-gray-500">Schedule:</span>
                              <div className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">
                                {dag.schedule_interval || 'None'}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                            <span>Total: {dag.total_runs}</span>
                            <span className="text-green-600">Success: {dag.successful_runs}</span>
                            <span className="text-red-600">Failed: {dag.failed_runs}</span>
                          </div>
                        </div>
                        <div className="flex space-x-1 ml-3">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleTriggerDag(dag.dag_id)}
                            disabled={loading}
                            title="Trigger DAG"
                            className="h-8 w-8 p-0"
                          >
                            <Play className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDagAction(dag.dag_id, dag.is_paused ? 'unpause' : 'pause')}
                            disabled={loading}
                            title={dag.is_paused ? 'Unpause DAG' : 'Pause DAG'}
                            className="h-8 w-8 p-0"
                          >
                            {dag.is_paused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.open(`http://${window.location.hostname}:8081/dags/${dag.dag_id}/graph`, '_blank')}
                            title="View in Airflow UI"
                            className="h-8 w-8 p-0"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="runs" className="space-y-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center text-lg">
                  <Activity className="w-4 h-4 mr-2" />
                  Recent DAG Runs
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                {dagRuns.length === 0 ? (
                  <div className="text-center py-6 space-y-4">
                    <Clock className="w-10 h-10 mx-auto text-gray-400 mb-3" />
                    <h3 className="text-base font-medium text-gray-900 mb-2">No Recent Runs</h3>
                    <p className="text-gray-500 text-sm">No DAG runs found in the recent history.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {dagRuns.slice(0, 10).map((run, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-white transition-colors">
                        <div className="flex items-center space-x-3">
                          <div>
                            <div className="font-medium text-sm">{run.dag_id}</div>
                            <div className="text-xs text-gray-500">{run.run_id}</div>
                          </div>
                          {getStatusBadge(run.state)}
                        </div>
                        <div className="text-right text-xs">
                          <div className="flex items-center text-gray-600">
                            <Clock className="w-3 h-3 mr-1" />
                            {formatRelativeTime(run.start_date)}
                          </div>
                          <div className="text-gray-500">
                            {formatDuration(run.duration)}
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => window.open(`http://${window.location.hostname}:8081/dags/${run.dag_id}/grid?dag_run_id=${run.run_id}`, '_blank')}
                            className="mt-1 h-6 text-xs"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            View
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="connections" className="space-y-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center text-lg">
                  <Database className="w-4 h-4 mr-2" />
                  Active Connections
                  <Badge variant="outline" className="ml-2 text-xs">
                    {connections.length} relevant
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                {connections.length === 0 ? (
                  <div className="text-center py-6 space-y-4">
                    <Database className="w-10 h-10 mx-auto text-gray-400 mb-3" />
                    <h3 className="text-base font-medium text-gray-900 mb-2">No Connections</h3>
                    <p className="text-gray-500 text-sm">No relevant connections are currently configured.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {connections.map((conn, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-white transition-colors">
                        <div className="flex items-center space-x-3">
                          <div>
                            <div className="font-medium text-sm">{conn.name}</div>
                            <div className="text-xs text-gray-500 flex items-center">
                              <span className="capitalize">{conn.conn_type}</span>
                              {conn.host && (
                                <>
                                  <span className="mx-1">•</span>
                                  <span>{conn.host}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(conn.status)}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => window.open(`http://${window.location.hostname}:8081/connection/list/`, '_blank')}
                            className="h-6 w-6 p-0"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>


        </Tabs>
      </div>
    
    </div>
  );
};

export default StaffAirflow; 