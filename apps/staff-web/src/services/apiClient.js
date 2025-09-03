import axios from "axios";
import { getEnvUrl } from '../utils/environment';
import { getKeycloakToken, refreshKeycloakToken } from './keycloakService';

// Use Vite proxy in development, fallback to environment variable or domain-based API URL
const base = import.meta.env.VITE_API_BASE_URL;
const isDevelopment = import.meta.env.DEV;

// Determine API URL based on current domain
const getApiUrl = () => {
  // Always prefer environment variable if set
  if (base && base !== 'undefined') {
    return base;
  }
  
  // Use centralized environment utility (returns direct API URL)
  return getEnvUrl('api');
};

const baseURL = getApiUrl();

// Request deduplication
const pendingRequests = new Map();

const apiClient = axios.create({
  baseURL,
  withCredentials: true, // For CSRF cookies
  headers: {
    'Content-Type': 'application/json',
  },
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  // Increase timeout to tolerate UAT warm starts and network latency
  timeout: 20000,
});

// --- Token Refresh Handling ---
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => (error ? prom.reject(error) : prom.resolve(token)));
  failedQueue = [];
};

const refreshAccessToken = async () => {
  try {
    console.log('🔄 API Client: Attempting Keycloak token refresh');
    const refreshed = await refreshKeycloakToken(30);
    if (refreshed) {
      console.log('🔄 API Client: Keycloak token refreshed successfully');
      window.dispatchEvent(new CustomEvent('keycloak-token-refreshed'));
      return { success: true };
    } else {
      console.log('🔄 API Client: Keycloak token refresh failed');
      return { success: false, detail: 'Keycloak token refresh failed' };
    }
  } catch (error) {
    const detail = error.message || 'Token refresh failed';
    console.error('🔄 API Client: Token refresh error:', detail);
    return { success: false, detail };
  }
};

// Request interceptor for token handling and deduplication
apiClient.interceptors.request.use(
  config => {
    // Add Keycloak token if available
    const keycloakToken = getKeycloakToken();
    if (keycloakToken) {
      config.headers.Authorization = `Bearer ${keycloakToken}`;
      console.log('🔑 API Client: Added Keycloak Bearer token to request');
    }
    
    // Create a unique key for this request
    const requestKey = `${config.method}-${config.url}-${JSON.stringify(config.data || {})}`;
    
    // If there's already a pending request with the same key, return its promise
    if (pendingRequests.has(requestKey)) {
      return Promise.reject({
        __deduplicated: true,
        promise: pendingRequests.get(requestKey)
      });
    }
    
    // Create a promise for this request
    const requestPromise = new Promise((resolve, reject) => {
      config.__resolve = resolve;
      config.__reject = reject;
    });
    
    // Store the promise
    pendingRequests.set(requestKey, requestPromise);
    
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling responses and errors
apiClient.interceptors.response.use(
  response => {
    // Remove the request from pending requests
    const requestKey = `${response.config.method}-${response.config.url}-${JSON.stringify(response.config.data || {})}`;
    pendingRequests.delete(requestKey);
    
    // Resolve the request promise
    if (response.config.__resolve) {
      response.config.__resolve(response);
    }
    
    return response;
  },
  async error => {
    // Handle deduplicated requests
    if (error.__deduplicated) {
      return error.promise;
    }
    
    const originalRequest = error.config;
    
    // Remove the request from pending requests
    if (originalRequest) {
      const requestKey = `${originalRequest.method}-${originalRequest.url}-${JSON.stringify(originalRequest.data || {})}`;
      pendingRequests.delete(requestKey);
      
      // Reject the request promise
      if (originalRequest.__reject) {
        originalRequest.__reject(error);
      }
    }

    // Handle 401 errors with token refresh
    if (
      error.response?.status === 401 &&
      !originalRequest?._retry &&
      getKeycloakToken() // Only try refresh if we have a Keycloak token
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          originalRequest._retry = true;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const result = await refreshAccessToken();
        if (result.success) {
          console.log('🔄 API Client: Token refresh successful');
          processQueue(null);
          
          // Update the Authorization header with the new token
          const newToken = getKeycloakToken();
          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          
          return apiClient(originalRequest);
        } else {
          console.log('🔄 API Client: Token refresh failed:', result.detail);
          // Dispatch logout event for refresh failures
          window.dispatchEvent(new CustomEvent('keycloak-token-expired'));
          processQueue(new Error("Token refresh failed"));
          return Promise.reject(error);
        }
      } catch (err) {
        console.error('🔄 API Client: Token refresh exception:', err);
        window.dispatchEvent(new CustomEvent('keycloak-token-expired'));
        processQueue(err);
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export { refreshAccessToken };
export default apiClient;
