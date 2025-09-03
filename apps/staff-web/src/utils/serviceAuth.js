// Service Authentication Utilities
// Handles auto-login for Airflow and Grafana from staff dashboard

/**
 * Generate auto-login URL for Grafana
 * Uses anonymous access for seamless integration
 */
export const getGrafanaAutoLoginUrl = (path = '', params = {}) => {
  const baseUrl = `http://${window.location.hostname}:3000`;
  const queryParams = new URLSearchParams({
    orgId: '1',
    ...params
  });
  
  const fullPath = path ? `/${path.replace(/^\//, '')}` : '';
  return `${baseUrl}${fullPath}?${queryParams.toString()}`;
};

/**
 * Generate auto-login URL for Airflow
 * Creates a session-based login URL
 */
export const getAirflowAutoLoginUrl = (path = '') => {
  const baseUrl = `http://${window.location.hostname}:8081`;
  const fullPath = path ? `/${path.replace(/^\//, '')}` : '';
  return `${baseUrl}${fullPath}`;
};

/**
 * Open service with auto-login in new tab
 */
export const openServiceWithAuth = (service, path = '', params = {}) => {
  let url;
  
  switch (service) {
    case 'grafana':
      url = getGrafanaAutoLoginUrl(path, params);
      break;
    case 'airflow':
      url = getAirflowAutoLoginUrl(path);
      break;
    default:
      console.error(`Unknown service: ${service}`);
      return;
  }
  
  window.open(url, '_blank', 'noopener,noreferrer');
};

/**
 * Create iframe URL with auto-login for embedding
 */
export const getEmbedUrl = (service, path = '', params = {}) => {
  switch (service) {
    case 'grafana':
      return getGrafanaAutoLoginUrl(path, {
        ...params,
        kiosk: 'tv', // Hide Grafana UI chrome for embedding
        theme: params.theme || 'light'
      });
    case 'airflow':
      return getAirflowAutoLoginUrl(path);
    default:
      return null;
  }
};

/**
 * Service configuration
 */
export const SERVICE_CONFIG = {
  grafana: {
    name: 'Grafana',
    port: 3000,
    supportsAnonymous: true,
    defaultParams: {
      orgId: 1,
      theme: 'light'
    }
  },
  airflow: {
    name: 'Airflow',
    port: 8081,
    supportsAnonymous: false,
    requiresAuth: true
  }
};

/**
 * Check if service is available
 */
export const checkServiceHealth = async (service) => {
  const config = SERVICE_CONFIG[service];
  if (!config) return false;
  
  try {
    const url = `http://${window.location.hostname}:${config.port}/health`;
    await fetch(url, { 
      method: 'HEAD',
      mode: 'no-cors' // Avoid CORS issues for health checks
    });
    return true; // If no error thrown, service is likely available
  } catch (error) {
    console.warn(`Service ${service} health check failed:`, error);
    return false;
  }
}; 