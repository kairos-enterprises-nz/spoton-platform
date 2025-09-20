// Environment-aware URL utilities
export const getEnvironment = () => {
  const hostname = window.location.hostname;
  
  if (hostname.startsWith('uat.') || hostname.includes('-uat.')) {
    return 'uat';
  } else if (hostname.startsWith('live.') || hostname === 'spoton.co.nz' || hostname === 'www.spoton.co.nz' || 
             hostname === 'portal.spoton.co.nz' || hostname === 'staff.spoton.co.nz' || hostname === 'api.spoton.co.nz') {
    return 'live';
  }
  
  // Default to UAT for development
  return 'uat';
};

export const getBaseUrls = () => {
  const env = getEnvironment();
  
  if (env === 'live') {
    return {
      web: 'https://spoton.co.nz',
      portal: 'https://portal.spoton.co.nz',
      staff: 'https://staff.spoton.co.nz',
      api: 'https://api.spoton.co.nz',
      auth: 'https://auth.spoton.co.nz'
    };
  } else {
    return {
      web: 'https://uat.spoton.co.nz',
      portal: 'https://uat.portal.spoton.co.nz',
      staff: 'https://uat.staff.spoton.co.nz',
      api: 'https://uat.api.spoton.co.nz',
      auth: 'https://auth.spoton.co.nz'
    };
  }
};

// Fallback to environment variables if needed
export const getEnvUrl = (service) => {
  const baseUrls = getBaseUrls();
  const envVarMap = {
    web: import.meta.env.VITE_WEB_URL,
    portal: import.meta.env.VITE_PORTAL_URL,
    staff: import.meta.env.VITE_STAFF_URL,
    api: import.meta.env.VITE_API_URL,
    auth: import.meta.env.VITE_KEYCLOAK_URL
  };
  
  return envVarMap[service] || baseUrls[service];
};

// Alias for backward compatibility
export const getBaseUrl = () => {
  const baseUrls = getBaseUrls();
  return baseUrls.api; // Return API URL as the base URL
};

export default {
  getEnvironment,
  getBaseUrls,
  getBaseUrl,
  getEnvUrl
}; 