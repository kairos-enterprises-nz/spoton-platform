/**
 * Keycloak Service for SpotOn Energy Frontend
 * Handles OIDC authentication with multi-realm support
 */
import Keycloak from 'keycloak-js';
import { getEnvUrl, getEnvironment } from '../utils/environment';
import { getBaseUrl } from '../utils/environment';

class KeycloakService {
  constructor() {
    this.keycloak = null;
    this.authenticated = false;
    this.baseUrl = getBaseUrl();
    this.initPromise = null;
  }

  init() {
    if (this.initPromise) {
      return this.initPromise;
    }

    const environment = getEnvironment();
    const keycloakConfig = {
      url: getEnvUrl('auth'),
      realm: environment === 'live' ? 'spoton-prod' : 'spoton-uat',
      clientId: environment === 'live' ? 'customer-live-portal' : 'customer-uat-portal'
    };

    this.keycloak = new Keycloak(keycloakConfig);

    this.initPromise = new Promise((resolve, reject) => {
      this.keycloak.init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
        pkceMethod: 'S256',
        checkLoginIframe: false,
      })
        .then(authenticated => {
          this.authenticated = authenticated;
          if (authenticated) {
            console.log('User is authenticated with Keycloak');
            this.scheduleTokenRefresh();
          } else {
            console.log('User is not authenticated with Keycloak');
          }
          resolve(authenticated);
        })
        .catch(error => {
          console.error('Failed to initialize Keycloak:', error);
          reject(error);
        });
    });

    return this.initPromise;
  }

  login(redirectUri = window.location.href) {
    if (this.keycloak) {
      this.keycloak.login({
        redirectUri: redirectUri,
      });
    } else {
      console.error('Keycloak not initialized');
    }
  }

  loginWithCredentials(email, password) {
    return fetch(`${this.baseUrl}/api/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Login failed');
        }
        return response.json();
      })
      .then(data => {
        // After successful login with credentials, check if Keycloak is authenticated
        return this.init().then(() => data);
      });
  }

  logout() {
    console.log('🔐 KeycloakService: Starting logout process');
    
    if (this.keycloak && this.authenticated) {
      console.log('🔐 KeycloakService: Using Keycloak logout');
      const logoutUrl = window.location.origin;
      this.keycloak.logout({ redirectUri: logoutUrl });
    } else {
      console.log('🔐 KeycloakService: Using traditional logout');
      // Fallback to traditional logout
      return fetch(`${this.baseUrl}/api/auth/logout/`, {
        method: 'POST',
        credentials: 'include',
      })
        .then(() => {
          // Clear authentication state
          this.authenticated = false;
          
          // Dispatch logout event
          window.dispatchEvent(new CustomEvent('auth-logout-complete', {
            detail: { reason: 'keycloak_service_logout' }
          }));
          
          window.location.href = '/login';
        })
        .catch((error) => {
          console.error('🔐 KeycloakService: Traditional logout error:', error);
          // Clear state even if logout fails
          this.authenticated = false;
          window.location.href = '/login';
        });
    }
  }

  register(userData) {
    return fetch(`${this.baseUrl}/api/users/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
      credentials: 'include',
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Registration failed');
        }
        return response.json();
      });
  }

  getToken() {
    // For PKCE flow, read token from cookies instead of Keycloak SDK
    const getCookie = (name) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return null;
    };
    
    return getCookie('access_token') || (this.keycloak ? this.keycloak.token : null);
  }

  isAuthenticated() {
    return this.authenticated || false;
  }

  getUsername() {
    return this.keycloak ? this.keycloak.tokenParsed?.preferred_username : null;
  }

  getEmail() {
    return this.keycloak ? this.keycloak.tokenParsed?.email : null;
  }

  getUserRoles() {
    if (!this.keycloak || !this.keycloak.tokenParsed) return [];
    return this.keycloak.tokenParsed.realm_access?.roles || [];
  }

  hasRole(role) {
    const roles = this.getUserRoles();
    return roles.includes(role);
  }

  scheduleTokenRefresh() {
    if (this.keycloak) {
      // Refresh token 1 minute before it expires
      const expiresIn = this.keycloak.tokenParsed.exp - Math.floor(Date.now() / 1000);
      const refreshTime = (expiresIn - 60) * 1000; // Convert to milliseconds
      
      if (refreshTime > 0) {
        setTimeout(() => {
          this.keycloak.updateToken(70)
            .then(refreshed => {
              if (refreshed) {
                console.log('Token refreshed');
              }
              this.scheduleTokenRefresh();
            })
            .catch(() => {
              console.error('Failed to refresh token');
            });
        }, refreshTime);
      }
    }
  }

  // Method to initiate social login
  loginWithSocial(provider) {
    if (this.keycloak) {
      this.keycloak.login({
        redirectUri: window.location.origin,
        idpHint: provider // 'google', 'facebook', etc.
      });
    } else {
      console.error('Keycloak not initialized');
    }
  }
}

// Create a single instance for both default and named exports
const keycloakServiceInstance = new KeycloakService();

// Named exports for backward compatibility with apiClient.js
export const getKeycloakToken = () => {
  return keycloakServiceInstance.getToken();
};

export const refreshKeycloakToken = async () => {
  if (keycloakServiceInstance.keycloak) {
    try {
      const refreshed = await keycloakServiceInstance.keycloak.updateToken(30);
      return refreshed;
    } catch (error) {
      console.error('Failed to refresh token:', error);
      return false;
    }
  }
  return false;
};

export default keycloakServiceInstance; 