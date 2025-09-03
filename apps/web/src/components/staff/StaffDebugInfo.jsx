import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { useAuth } from '../../hooks/useAuth';
import staffApiService from '../../services/staffApi';

const StaffDebugInfo = () => {
  const { selectedTenant, tenants, getCurrentTenantFilter, isSuperAdmin } = useTenant();
  const { user } = useAuth();
  const [apiStatus, setApiStatus] = useState({});
  const [systemInfo, setSystemInfo] = useState({});
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  useEffect(() => {
    if (isVisible) {
      collectDebugInfo();
    }
  }, [isVisible, selectedTenant]);

  const collectDebugInfo = async () => {
    setIsLoading(true);
    const startTime = performance.now();
    
    try {
      // Collect system information
      const systemData = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
        screen: {
          width: window.screen.width,
          height: window.screen.height,
          colorDepth: window.screen.colorDepth
        },
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        },
        localStorage: {
          available: typeof(Storage) !== "undefined",
          used: localStorage.length
        },
        sessionStorage: {
          available: typeof(Storage) !== "undefined",
          used: sessionStorage.length
        },
        currentUrl: window.location.href,
        referrer: document.referrer,
        timestamp: new Date().toISOString()
      };
      setSystemInfo(systemData);

      // Test API endpoints with detailed error tracking
      const endpoints = [
        { 
          name: 'Tenants', 
          call: () => staffApiService.getTenants(),
          critical: true
        },
        { 
          name: 'Users', 
          call: () => staffApiService.getUsers({ page_size: 5 }),
          critical: true
        },
        { 
          name: 'Accounts', 
          call: () => staffApiService.getAccounts({ page_size: 5 }),
          critical: true
        },
        { 
          name: 'Contracts', 
          call: () => staffApiService.getContracts({ page_size: 5 }),
          critical: false
        },
        { 
          name: 'Connections', 
          call: () => staffApiService.getConnections({ page_size: 5 }),
          critical: false
        },
        { 
          name: 'Plans', 
          call: () => staffApiService.getPlans({ page_size: 5 }),
          critical: false
        },
        {
          name: 'Dashboard Stats',
          call: () => staffApiService.getDashboardStats(),
          critical: false
        },
        {
          name: 'Health Check',
          call: () => staffApiService.healthCheck(),
          critical: true
        }
      ];

      const results = {};
      const timings = {};
      
      for (const endpoint of endpoints) {
        const endpointStartTime = performance.now();
        try {
          console.log(`🔍 Testing ${endpoint.name} API...`);
          const response = await endpoint.call();
          const endpointEndTime = performance.now();
          const duration = endpointEndTime - endpointStartTime;
          
          timings[endpoint.name] = duration;
          
          let count = 0;
          let dataStructure = 'unknown';
          
          if (response) {
            if (Array.isArray(response)) {
              count = response.length;
              dataStructure = 'array';
            } else if (response.results && Array.isArray(response.results)) {
              count = response.results.length;
              dataStructure = 'paginated';
            } else if (typeof response === 'object') {
              count = Object.keys(response).length;
              dataStructure = 'object';
            }
          }
          
          results[endpoint.name] = {
            status: 'success',
            count,
            dataStructure,
            responseTime: Math.round(duration),
            critical: endpoint.critical,
            totalCount: response?.count || count,
            hasNext: !!response?.next,
            hasPrevious: !!response?.previous,
            sampleData: Array.isArray(response) ? response.slice(0, 1) : 
                       response?.results?.slice(0, 1) || 
                       (typeof response === 'object' ? { ...response } : response)
          };
          
          console.log(`✅ ${endpoint.name} API: ${count} items in ${Math.round(duration)}ms`);
        } catch (error) {
          const endpointEndTime = performance.now();
          const duration = endpointEndTime - endpointStartTime;
          
          timings[endpoint.name] = duration;
          
          results[endpoint.name] = {
            status: 'error',
            error: error.message,
            errorType: error.constructor.name,
            responseTime: Math.round(duration),
            critical: endpoint.critical,
            statusCode: error.response?.status,
            statusText: error.response?.statusText,
            url: error.config?.url,
            method: error.config?.method?.toUpperCase()
          };
          
          console.error(`❌ ${endpoint.name} API failed:`, error);
        }
      }

      const totalTime = performance.now() - startTime;
      
      // Calculate performance metrics
      const perfMetrics = {
        totalTestTime: Math.round(totalTime),
        averageResponseTime: Math.round(Object.values(timings).reduce((a, b) => a + b, 0) / Object.values(timings).length),
        slowestEndpoint: Object.entries(timings).reduce((a, b) => timings[a[0]] > timings[b[0]] ? a : b)[0],
        fastestEndpoint: Object.entries(timings).reduce((a, b) => timings[a[0]] < timings[b[0]] ? a : b)[0],
        successRate: Math.round((Object.values(results).filter(r => r.status === 'success').length / Object.values(results).length) * 100),
        criticalFailures: Object.values(results).filter(r => r.status === 'error' && r.critical).length,
        memoryUsage: performance.memory ? {
          used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
          total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
          limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
        } : null
      };

      setApiStatus(results);
      setPerformanceMetrics(perfMetrics);
      setLastRefresh(new Date().toLocaleTimeString());
      
    } catch (error) {
      console.error('❌ Failed to collect debug info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const exportDebugInfo = () => {
    const debugData = {
      timestamp: new Date().toISOString(),
      user: {
        id: user?.id,
        email: user?.email,
        is_superuser: user?.is_superuser,
        tenant: user?.tenant?.name || user?.tenant_name
      },
      tenant: {
        selected: selectedTenant?.name,
        available: tenants.length,
        filter: getCurrentTenantFilter(),
        isSuperAdmin
      },
      system: systemInfo,
      api: apiStatus,
      performance: performanceMetrics,
      context: {
        windowContext: typeof window !== 'undefined' && window.tenantContext ? 'Available' : 'Missing',
        globalFilter: typeof window !== 'undefined' && window.tenantContext ? 
                     window.tenantContext.getCurrentTenantFilter() : 'N/A'
      }
    };

    const blob = new Blob([JSON.stringify(debugData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `staff-debug-${new Date().getTime()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsVisible(true)}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700 shadow-lg"
        >
          🔍 Debug Info
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 bg-white border border-gray-300 rounded-lg shadow-xl max-w-2xl max-h-96 overflow-y-auto">
      <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex justify-between items-center">
        <h3 className="font-semibold text-gray-900 flex items-center">
          🔍 Staff Debug Info
          {isLoading && <span className="ml-2 animate-spin">⏳</span>}
        </h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={collectDebugInfo}
            disabled={isLoading}
            className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50"
          >
            🔄 Refresh
          </button>
          <button
            onClick={exportDebugInfo}
            className="text-green-600 hover:text-green-800 text-sm"
          >
            📥 Export
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="text-gray-400 hover:text-gray-600 text-lg"
          >
            ×
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4 text-sm">
        {/* Performance Summary */}
        {Object.keys(performanceMetrics).length > 0 && (
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="font-medium text-gray-700 mb-2">🚀 Performance Summary</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>Success Rate: <span className={`font-bold ${performanceMetrics.successRate >= 80 ? 'text-green-600' : 'text-red-600'}`}>
                {performanceMetrics.successRate}%
              </span></div>
              <div>Avg Response: <span className="font-bold">{performanceMetrics.averageResponseTime}ms</span></div>
              <div>Critical Failures: <span className={`font-bold ${performanceMetrics.criticalFailures > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {performanceMetrics.criticalFailures}
              </span></div>
              <div>Total Time: <span className="font-bold">{performanceMetrics.totalTestTime}ms</span></div>
            </div>
            {performanceMetrics.memoryUsage && (
              <div className="mt-2 text-xs text-gray-600">
                Memory: {performanceMetrics.memoryUsage.used}MB / {performanceMetrics.memoryUsage.total}MB
              </div>
            )}
          </div>
        )}

        {/* User Info */}
        <div>
          <h4 className="font-medium text-gray-700 mb-2">👤 User Info</h4>
          <div className="text-gray-600 space-y-1">
            <div>Email: <span className="font-mono text-xs">{user?.email || 'Not logged in'}</span></div>
            <div>Super Admin: <span className={`font-bold ${user?.is_superuser ? 'text-green-600' : 'text-gray-600'}`}>
              {user?.is_superuser ? 'Yes' : 'No'}
            </span></div>
            <div>User Tenant: <span className="font-mono text-xs">{user?.tenant?.name || user?.tenant_name || 'None'}</span></div>
          </div>
        </div>

        {/* Tenant Info */}
        <div>
          <h4 className="font-medium text-gray-700 mb-2">🏢 Tenant Context</h4>
          <div className="text-gray-600 space-y-1">
            <div>Available: <span className="font-bold">{tenants.length}</span></div>
            <div>Selected: <span className="font-mono text-xs">{selectedTenant?.name || 'None'}</span></div>
            <div>Filter: <span className="font-mono text-xs">{getCurrentTenantFilter() || 'None'}</span></div>
            <div>Is Super Admin: <span className={`font-bold ${isSuperAdmin ? 'text-green-600' : 'text-gray-600'}`}>
              {isSuperAdmin ? 'Yes' : 'No'}
            </span></div>
          </div>
        </div>

        {/* API Status */}
        <div>
          <h4 className="font-medium text-gray-700 mb-2">🔌 API Status</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {Object.entries(apiStatus).map(([endpoint, status]) => (
              <div key={endpoint} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-2">
                  <span className={`w-2 h-2 rounded-full ${status.status === 'success' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                  <span className="font-medium">{endpoint}</span>
                  {status.critical && <span className="text-xs bg-red-100 text-red-600 px-1 rounded">Critical</span>}
                </div>
                <div className="text-right">
                  <div className={`text-xs font-bold ${status.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                    {status.status === 'success' ? 
                      `${status.count} items (${status.dataStructure})` : 
                      `${status.errorType}`
                    }
                  </div>
                  <div className="text-xs text-gray-500">{status.responseTime}ms</div>
                  {status.status === 'error' && status.statusCode && (
                    <div className="text-xs text-red-600">HTTP {status.statusCode}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Info */}
        {Object.keys(systemInfo).length > 0 && (
          <div>
            <h4 className="font-medium text-gray-700 mb-2">💻 System Info</h4>
            <div className="text-gray-600 space-y-1 text-xs">
              <div>Platform: <span className="font-mono">{systemInfo.platform}</span></div>
              <div>Online: <span className={`font-bold ${systemInfo.onLine ? 'text-green-600' : 'text-red-600'}`}>
                {systemInfo.onLine ? 'Yes' : 'No'}
              </span></div>
              <div>Viewport: <span className="font-mono">{systemInfo.viewport?.width}x{systemInfo.viewport?.height}</span></div>
              <div>LocalStorage: <span className="font-mono">{systemInfo.localStorage?.used} items</span></div>
            </div>
          </div>
        )}

        {/* Global Context */}
        <div>
          <h4 className="font-medium text-gray-700 mb-2">🌐 Global Context</h4>
          <div className="text-gray-600 space-y-1">
            <div>Window Context: <span className={`font-bold ${typeof window !== 'undefined' && window.tenantContext ? 'text-green-600' : 'text-red-600'}`}>
              {typeof window !== 'undefined' && window.tenantContext ? 'Available' : 'Missing'}
            </span></div>
            {typeof window !== 'undefined' && window.tenantContext && (
              <div>Global Filter: <span className="font-mono text-xs">{window.tenantContext.getCurrentTenantFilter() || 'None'}</span></div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 pt-3 flex justify-between items-center text-xs text-gray-500">
          <div>Last updated: {lastRefresh}</div>
          <button
            onClick={() => window.location.reload()}
            className="bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200"
          >
            🔄 Refresh Page
          </button>
        </div>
      </div>
    </div>
  );
};

export default StaffDebugInfo; 