/**
 * Keycloak Service for SpotOn Energy Frontend
 * Handles OIDC authentication with multi-realm support
 */
import Keycloak from 'keycloak-js';
import { getEnvUrl, getEnvironment } from '../utils/environment';

// Environment-based configuration using centralized utility
const getKeycloakConfig = () => {
  const env = getEnvironment();
  const baseUrl = getEnvUrl('auth');
  const realm = import.meta.env.VITE_KEYCLOAK_REALM || (env === 'live' ? 'spoton-prod' : 'spoton-uat');
  
  // Select client ID based on environment
  let clientId;
  if (env === 'live') {
    clientId = 'customer-live-portal'; // Live client (now configured in Keycloak)
  } else {
    clientId = 'customer-uat-portal';  // UAT client
  }
  
  // Allow environment variable override
  if (import.meta.env.VITE_KEYCLOAK_CLIENT_ID) {
    clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'customer-uat-portal';
  }

  console.log(`🔑 Keycloak Config: domain=${currentDomain}, clientId=${clientId}, isLive=${isLiveDomain}, isUAT=${isUATDomain}`);

  return {
    url: baseUrl,
    realm: realm,
    clientId: clientId
  };
};

// Keycloak instance
let keycloakInstance = null;

/**
 * Initialize Keycloak instance
 */
export const initKeycloak = async (options = {}) => {
  if (keycloakInstance) {
    console.log('🔑 Keycloak: Instance already initialized');
    return keycloakInstance;
  }

  console.log('🔑 Keycloak: Initializing...');
  
  const config = getKeycloakConfig();
  console.log('🔑 Keycloak: Config:', { ...config, clientId: config.clientId });

  keycloakInstance = new Keycloak(config);

  try {
    // Check if we're returning from Keycloak login (has OAuth callback parameters)
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const hasAuthCallback = urlParams.has('code') || urlParams.has('state') || 
                           hashParams.has('code') || hashParams.has('state');
    
    let onLoad = options.onLoad || 'check-sso';
    
    // If we have callback parameters, process them
    if (hasAuthCallback) {
      console.log('🔑 Keycloak: Detected OAuth callback, processing...');
      onLoad = 'check-sso'; // Process the callback
    }
    
    const authenticated = await keycloakInstance.init({
      onLoad: onLoad,
      pkceMethod: 'S256',
      checkLoginIframe: false, // Disable iframe check to avoid X-Frame-Options issues
      silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
    });

    console.log('🔑 Keycloak: Initialization completed', { authenticated, hasAuthCallback });

    // Set up token refresh
    if (authenticated) {
      setupTokenRefresh();
      
      // Clean up URL if we processed OAuth callback
      if (hasAuthCallback) {
        console.log('🔑 Keycloak: Cleaning up OAuth callback URL...');
        // Remove OAuth parameters from URL
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
      }
    }

    return keycloakInstance;
  } catch (error) {
    console.error('🔑 Keycloak: Initialization failed:', error);
    throw error;
  }
};

/**
 * Get current Keycloak instance
 */
export const getKeycloak = () => {
  if (!keycloakInstance) {
    throw new Error('Keycloak not initialized. Call initKeycloak() first.');
  }
  return keycloakInstance;
};

/**
 * Check if user is authenticated via Keycloak
 */
export const isKeycloakAuthenticated = () => {
  return keycloakInstance?.authenticated || false;
};

/**
 * Get user profile from Keycloak token
 */
export const getKeycloakUser = async () => {
  if (!keycloakInstance?.authenticated) {
    return null;
  }

  try {
    // Extract information from token only (avoid user profile API call that may fail)
    const token = keycloakInstance.tokenParsed;
    
    if (!token) {
      console.warn('🔑 Keycloak: No token parsed available');
      return null;
    }
    
    return {
      id: token.sub,
      email: token.email || token.preferred_username,
      firstName: token.given_name || '',
      lastName: token.family_name || '',
      fullName: `${token.given_name || ''} ${token.family_name || ''}`.trim() || token.preferred_username || token.email,
      emailVerified: token.email_verified || false,
      roles: token.realm_access?.roles || [],
      groups: token.groups || [],
      realm: token.iss?.split('/realms/')?.pop() || '',
      isStaff: (token.groups || []).some(group => group.startsWith('staff-')),
      userType: (token.groups || []).some(group => group.startsWith('staff-')) ? 'staff' : 'residential'
    };
  } catch (error) {
    console.error('🔑 Keycloak: Failed to load user profile:', error);
    return null;
  }
};

/**
 * Login via Keycloak
 */
export const keycloakLogin = async (options = {}) => {
  if (!keycloakInstance) {
    throw new Error('Keycloak not initialized');
  }

  console.log('🔑 Keycloak: Starting login...');
  
  // Determine redirect URI based on current location or options
  let redirectUri = options.redirectUri;
  
  if (!redirectUri) {
    // If we're on the login page, redirect to portal after login
    if (window.location.pathname === '/login' || window.location.pathname === '/') {
      redirectUri = `${getEnvUrl('portal')}/dashboard`;
    } else {
      // Otherwise, redirect back to current page
      redirectUri = window.location.href;
    }
  }
  
  console.log('🔑 Keycloak: Redirecting to:', redirectUri);
  
  try {
    await keycloakInstance.login({
      redirectUri: redirectUri,
      ...options
    });
  } catch (error) {
    console.error('🔑 Keycloak: Login failed:', error);
    throw error;
  }
};

/**
 * Logout via Keycloak
 */
export const keycloakLogout = async (options = {}) => {
  if (!keycloakInstance) {
    return;
  }

  console.log('🔑 Keycloak: Starting logout...');
  
  try {
    await keycloakInstance.logout({
      redirectUri: window.location.origin,
      ...options
    });
  } catch (error) {
    console.error('🔑 Keycloak: Logout failed:', error);
    throw error;
  }
};

/**
 * Get access token for API calls
 */
export const getKeycloakToken = () => {
  if (!keycloakInstance?.authenticated) {
    return null;
  }
  return keycloakInstance.token;
};

/**
 * Refresh token if needed
 */
export const refreshKeycloakToken = async (minValidity = 30) => {
  if (!keycloakInstance?.authenticated) {
    return false;
  }

  try {
    const refreshed = await keycloakInstance.updateToken(minValidity);
    if (refreshed) {
      console.log('🔑 Keycloak: Token refreshed');
      // Dispatch event for other parts of the app
      window.dispatchEvent(new CustomEvent('keycloak-token-refreshed', {
        detail: { token: keycloakInstance.token }
      }));
    }
    return refreshed;
  } catch (error) {
    console.error('🔑 Keycloak: Token refresh failed:', error);
    // Token refresh failed, user needs to login again
    window.dispatchEvent(new CustomEvent('keycloak-token-expired'));
    return false;
  }
};

/**
 * Setup automatic token refresh
 */
const setupTokenRefresh = () => {
  if (!keycloakInstance) return;

  // Refresh token every 5 minutes if it expires within 30 seconds
  const refreshInterval = setInterval(async () => {
    if (!keycloakInstance.authenticated) {
      clearInterval(refreshInterval);
      return;
    }

    try {
      await refreshKeycloakToken(30);
    } catch (error) {
      console.error('🔑 Keycloak: Auto refresh failed:', error);
      clearInterval(refreshInterval);
    }
  }, 5 * 60 * 1000); // 5 minutes

  // Clear interval on logout
  keycloakInstance.onAuthLogout = () => {
    clearInterval(refreshInterval);
  };
};

/**
 * Check if user has specific role
 */
export const hasKeycloakRole = (role) => {
  if (!keycloakInstance?.authenticated) {
    return false;
  }
  
  const roles = keycloakInstance.tokenParsed?.realm_access?.roles || [];
  return roles.includes(role);
};

/**
 * Check if user is in specific group
 */
export const hasKeycloakGroup = (group) => {
  if (!keycloakInstance?.authenticated) {
    return false;
  }
  
  const groups = keycloakInstance.tokenParsed?.groups || [];
  return groups.includes(group);
};

/**
 * Get user's realm from token
 */
export const getKeycloakRealm = () => {
  if (!keycloakInstance?.authenticated) {
    return null;
  }
  
  const issuer = keycloakInstance.tokenParsed?.iss || '';
  return issuer.split('/realms/')?.pop() || null;
};

/**
 * Check if Keycloak is available and configured
 */
export const isKeycloakAvailable = async () => {
  try {
    const config = getKeycloakConfig();
    const response = await fetch(`${config.url}/realms/${config.realm}/.well-known/openid-configuration`);
    return response.ok;
  } catch (error) {
    console.warn('🔑 Keycloak: Not available:', error.message);
    return false;
  }
};

/**
 * Account management - redirect to Keycloak account page
 */
export const openKeycloakAccount = () => {
  if (!keycloakInstance) {
    throw new Error('Keycloak not initialized');
  }
  
  keycloakInstance.accountManagement();
};

export default {
  initKeycloak,
  getKeycloak,
  isKeycloakAuthenticated,
  getKeycloakUser,
  keycloakLogin,
  keycloakLogout,
  getKeycloakToken,
  refreshKeycloakToken,
  hasKeycloakRole,
  hasKeycloakGroup,
  getKeycloakRealm,
  isKeycloakAvailable,
};
