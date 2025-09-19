/**
 * Keycloak Service for SpotOn Energy Frontend
 * Handles OIDC authentication with multi-realm support
 */
import Keycloak from 'keycloak-js';
import { getEnvUrl, getEnvironment } from '../utils/environment';

const decodeJwt = (jwt) => {
  try {
    const base64Url = jwt.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
};

// Environment-based configuration with domain detection
const getKeycloakConfig = () => {
  const currentDomain = window.location.hostname;
  const env = getEnvironment();
  // Using centralized environment detection

  const baseUrl = getEnvUrl('auth');
  // Align to backend UAT realm configuration
  const realm = 'spoton-uat';

  // Select client ID based on environment (staff clients)
  const clientId = env === 'live' ? 'staff-portal' : 'staff-portal-uat';

  console.log(`🔑 Keycloak Config: domain=${currentDomain}, clientId=${clientId}, env=${env}`);

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
    
    const groups = token.groups || [];
    const roles = token.realm_access?.roles || [];
    
    // Check if user is admin (Admin group or admin role)
    const isAdmin = groups.includes('Admin') || roles.includes('admin') || groups.some(group => group.toLowerCase().includes('admin'));
    
    return {
      id: token.sub,
      email: token.email || token.preferred_username,
      firstName: token.given_name || '',
      lastName: token.family_name || '',
      fullName: `${token.given_name || ''} ${token.family_name || ''}`.trim() || token.preferred_username || token.email,
      emailVerified: token.email_verified || false,
      roles: roles,
      groups: groups,
      realm: token.iss?.split('/realms/')?.pop() || '',
      isStaff: groups.some(group => group.toLowerCase().includes('staff')),
      isAdmin: isAdmin,
      is_superuser: isAdmin, // Add Django-compatible field
      userType: groups.some(group => group.toLowerCase().includes('staff')) ? 'staff' : 'residential'
    };
  } catch (error) {
    console.error('🔑 Keycloak: Failed to extract user from token:', error);
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
    // On login pages or root, send staff users to the users page
    const path = window.location.pathname;
    if (path === '/' || path === '/login') {
      redirectUri = `${window.location.origin}/users`;
    } else {
      // Otherwise, redirect back to current page within staff domain
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
 * Password-based login via Direct Access Grants (ROPC)
 * Keeps Keycloak UI hidden by exchanging credentials for tokens and
 * initializing the Keycloak JS instance with those tokens.
 */
export const keycloakPasswordLogin = async (identifier, password) => {
  const config = getKeycloakConfig();
  const tokenUrl = `${config.url}/realms/${config.realm}/protocol/openid-connect/token`;

  // Clean stale OAuth parameters that may cause KC to try code exchange
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    if (urlParams.has('code') || urlParams.has('state') || hashParams.has('code') || hashParams.has('state')) {
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  } catch (_) {}

  const form = new URLSearchParams();
  form.set('grant_type', 'password');
  form.set('client_id', config.clientId);
  form.set('username', identifier);
  form.set('password', password);

  const resp = await fetch(tokenUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
    credentials: 'omit'
  });

  if (!resp.ok) {
    const errTxt = await resp.text();
    console.error('🔑 Keycloak: Password login failed:', resp.status, errTxt);
    throw new Error(`Keycloak password login failed (${resp.status})`);
  }

  const data = await resp.json();

  if (!keycloakInstance) {
    keycloakInstance = new Keycloak(config);
  }
  // Ensure base urls/realm/clientId are present for SDK helpers
  keycloakInstance.authServerUrl = config.url;
  keycloakInstance.realm = config.realm;
  keycloakInstance.clientId = config.clientId;

  // Always set tokens directly to avoid re-initialization collisions
  keycloakInstance.token = data.access_token;
  keycloakInstance.refreshToken = data.refresh_token;
  keycloakInstance.idToken = data.id_token;
  keycloakInstance.authenticated = true;
  keycloakInstance.tokenParsed = decodeJwt(data.access_token);
  keycloakInstance.refreshTokenParsed = decodeJwt(data.refresh_token);
  keycloakInstance.idTokenParsed = data.id_token ? decodeJwt(data.id_token) : undefined;

  try {
    // Persist tokens for reload continuity
    sessionStorage.setItem('kc_access_token', data.access_token || '');
    sessionStorage.setItem('kc_refresh_token', data.refresh_token || '');
    if (data.id_token) sessionStorage.setItem('kc_id_token', data.id_token);
  } catch (_) {}

  setupTokenRefresh();
  return { authenticated: true, tokenPreview: (data.access_token || '').slice(0, 12) + '...' };
};

/**
 * Adopt tokens from sessionStorage (when page reloaded after background login)
 */
export const adoptStoredTokensIfAvailable = async () => {
  const config = getKeycloakConfig();
  const accessToken = sessionStorage.getItem('kc_access_token');
  const refreshToken = sessionStorage.getItem('kc_refresh_token');
  const idToken = sessionStorage.getItem('kc_id_token');
  if (!accessToken || !refreshToken) return false;
  if (!keycloakInstance) {
    keycloakInstance = new Keycloak(config);
  }
  keycloakInstance.token = accessToken;
  keycloakInstance.refreshToken = refreshToken;
  if (idToken) keycloakInstance.idToken = idToken;
  keycloakInstance.authenticated = true;
  setupTokenRefresh();
  return true;
};

/**
 * Logout via Keycloak with enhanced cleanup
 */
export const keycloakLogout = async (options = {}) => {
  if (!keycloakInstance) {
    console.log('🔑 Keycloak: No instance available for logout');
    return;
  }

  console.log('🔑 Keycloak: Starting logout...');
  
  try {
    // Dispatch logout event before redirect
    window.dispatchEvent(new CustomEvent('auth-logout-complete', {
      detail: { reason: 'keycloak_service_logout' }
    }));
    
    await keycloakInstance.logout({
      redirectUri: window.location.origin,
      ...options
    });
  } catch (error) {
    console.error('🔑 Keycloak: Logout failed:', error);
    // Still dispatch event for cleanup even if logout fails
    window.dispatchEvent(new CustomEvent('auth-logout-complete', {
      detail: { reason: 'keycloak_service_logout_failed', error: error.message }
    }));
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
      try {
        sessionStorage.setItem('kc_access_token', keycloakInstance.token || '');
        sessionStorage.setItem('kc_refresh_token', keycloakInstance.refreshToken || '');
        if (keycloakInstance.idToken) sessionStorage.setItem('kc_id_token', keycloakInstance.idToken);
      } catch (_) {}
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
  keycloakPasswordLogin,
  hasKeycloakRole,
  hasKeycloakGroup,
  getKeycloakRealm,
  isKeycloakAvailable,
  openKeycloakAccount
}; 