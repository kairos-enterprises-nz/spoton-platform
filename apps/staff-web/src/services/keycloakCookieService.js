/**
 * Keycloak Service using secure HTTP cookies
 * This service communicates with Django backend for Keycloak authentication
 */

import apiClient from './apiClient';

class KeycloakCookieService {
  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://uat.api.spoton.co.nz';
    this.user = null;
    this.authenticated = false;
    this.tokenExpiry = null;
  }

  /**
   * Check if user is authenticated by checking secure cookies
   */
  async checkAuthentication() {
    try {
      // Check if we have the access token cookie
      const hasAccessToken = this.getCookie('keycloak_access_token');
      const tokenExpiry = this.getCookie('keycloak_token_expires');
      
      if (!hasAccessToken) {
        this.authenticated = false;
        this.user = null;
        return false;
      }

      // Check if token is expired
      if (tokenExpiry) {
        const expiryTime = new Date().getTime() + (parseInt(tokenExpiry) * 1000);
        if (expiryTime <= new Date().getTime()) {
          // Token expired, try to refresh
          const refreshed = await this.refreshToken();
          if (!refreshed) {
            this.authenticated = false;
            this.user = null;
            return false;
          }
        }
      }

      // Get user profile from backend (which will use the cookie)
      const userProfile = await this.getUserProfile();
      if (userProfile) {
        this.user = userProfile;
        this.authenticated = true;
        return true;
      }

      return false;
    } catch (error) {
      console.error('Error checking authentication:', error);
      this.authenticated = false;
      this.user = null;
      return false;
    }
  }

  /**
   * Initiate login flow
   */
  async login(options = {}) {
    try {
      const loginUrl = new URL(`${this.baseUrl}/auth/keycloak/login/`);
      
      // Add action parameter if this is registration
      if (options.action === 'register') {
        loginUrl.searchParams.set('action', 'register');
      }
      
      // Add login hint if provided
      if (options.email) {
        loginUrl.searchParams.set('login_hint', options.email);
      }
      
      // Add registration data if provided (for onboarding flow)
      if (options.registrationData) {
        loginUrl.searchParams.set('registration_data', JSON.stringify(options.registrationData));
      }
      
      // Add state for CSRF protection
      const state = this.generateRandomString(32);
      loginUrl.searchParams.set('state', state);
      sessionStorage.setItem('oauth_state', state);
      
      // Redirect to Django backend which will handle Keycloak OAuth flow
      window.location.href = loginUrl.toString();
      
    } catch (error) {
      console.error('Login error:', error);
      throw new Error('Failed to initiate login');
    }
  }

  /**
   * Fast logout - clear everything immediately and redirect
   */
  async logout() {
    console.log('🔐 KeycloakCookieService: Starting fast logout');
    
    // Clear local state immediately
    this.authenticated = false;
    this.user = null;
    this.tokenExpiry = null;
    
    // Clear cookies and storage immediately
    this.clearAuthCookies();
    this.clearLocalStorage();
    
    // Get redirect URL
    const redirectUrl = this.getEnvironmentAwareRedirectUrl();
    console.log('🔐 Redirecting to:', redirectUrl);
    
    // Dispatch logout event
    window.dispatchEvent(new CustomEvent('auth-logout-complete', {
      detail: { reason: 'user_initiated', redirectUrl }
    }));
    
    // Start background cleanup (don't wait for it)
    this.performBackgroundLogout();
    
    // Redirect immediately
    window.location.href = redirectUrl;
  }
  
  /**
   * Perform background logout cleanup without blocking redirect
   */
  async performBackgroundLogout() {
    try {
      // Server logout (non-blocking)
      fetch(`${this.baseUrl}/auth/keycloak/logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
      }).then(response => {
        console.log('🔐 Background server logout:', response.ok ? 'success' : 'failed');
      }).catch(error => {
        console.log('🔐 Background server logout error:', error.message);
      });
      
      // Simple cross-domain logout attempt (non-blocking)
      const hostname = window.location.hostname;
      const mainWebsiteUrl = hostname.startsWith('uat.') ? 'https://uat.spoton.co.nz' : 'https://spoton.co.nz';
      
      // Try a simple image-based logout trigger
      const img = new Image();
      img.src = `${mainWebsiteUrl}/logout?source=staff&t=${Date.now()}`;
      
    } catch (error) {
      console.log('🔐 Background logout error:', error.message);
    }
  }
  
  /**
   * Clear authentication cookies - simple and fast
   */
  clearAuthCookies() {
    console.log('🔐 Clearing authentication cookies');
    
    // Get all existing cookies
    const allCookies = document.cookie.split(';').map(cookie => {
      const [name] = cookie.trim().split('=');
      return name;
    }).filter(name => name);
    
    console.log('🔐 Found cookies:', allCookies);
    
    // Clear ALL cookies (simpler approach)
    allCookies.forEach(cookieName => {
      // Multiple clearing methods for maximum effectiveness
      [
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`,
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; secure;`,
        `${cookieName}=; max-age=0; path=/;`,
        `${cookieName}=; max-age=0; path=/; secure;`
      ].forEach(method => {
        try {
          document.cookie = method;
        } catch (e) {
          // Ignore failures
        }
      });
    });
    
    console.log('🔐 Cookie clearing completed');
    
    // Quick verification
    setTimeout(() => {
      const remainingCookies = document.cookie;
      if (remainingCookies) {
        console.log('🔐 Remaining cookies:', remainingCookies);
      } else {
        console.log('🔐 ✅ All cookies cleared');
      }
    }, 100);
  }
  
  /**
   * Clear local and session storage
   */
  clearLocalStorage() {
    const keysToRemove = [
      'keycloak_token',
      'keycloak_refresh_token',
      'keycloak_id_token',
      'user_data',
      'auth_state',
      'pkce_code_verifier',
      'pkce_state',
      'keycloak_session_state'
    ];
    
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
    
    console.log('🔐 Cleared local storage');
  }
  
  /**
   * Perform cross-domain logout to clear main website cookies
   */
  async performCrossDomainLogout() {
    console.log('🔐 Performing enhanced cross-domain logout');
    
    const hostname = window.location.hostname;
    let mainWebsiteUrl;
    
    // Determine the main website URL based on current environment
    if (hostname.startsWith('uat.') || hostname.includes('-uat.')) {
      mainWebsiteUrl = 'https://uat.spoton.co.nz';
    } else {
      mainWebsiteUrl = 'https://spoton.co.nz'; 
    }
    
    console.log(`🔐 Targeting main website: ${mainWebsiteUrl}`);
    
    // Method 1: Try multiple API endpoints for logout
    const logoutEndpoints = [
      `${mainWebsiteUrl}/api/auth/logout/`,
      `${mainWebsiteUrl}/api/auth/keycloak/logout/`,
      `${mainWebsiteUrl}/logout-api`,
      `${mainWebsiteUrl}/auth/logout`
    ];
    
    for (const endpoint of logoutEndpoints) {
      try {
        console.log(`🔐 Attempting logout at: ${endpoint}`);
        await fetch(endpoint, {
          method: 'POST',
          credentials: 'include',
          mode: 'no-cors', // Allow cross-origin request
          headers: {
            'Content-Type': 'application/json',
          },
        });
        console.log(`🔐 Cross-domain logout API call to ${endpoint} completed`);
      } catch (error) {
        console.debug(`🔐 Cross-domain logout API call to ${endpoint} failed:`, error.message);
      }
    }
    
    // Method 2: Enhanced iframe approach with postMessage
    return new Promise((resolve) => {
      try {
        console.log('🔐 Starting iframe-based cross-domain logout');
        
        // Listen for messages from the iframe
        const messageHandler = (event) => {
          if (event.origin === mainWebsiteUrl) {
            console.log('🔐 Received message from main website iframe:', event.data);
            if (event.data.type === 'logout-complete') {
              console.log('🔐 ✅ Cross-domain logout confirmed by main website');
              window.removeEventListener('message', messageHandler);
              cleanup();
              resolve();
            }
          }
        };
        
        window.addEventListener('message', messageHandler);
        
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = 'none';
        
        // Try multiple iframe URLs
        const iframeUrls = [
          `${mainWebsiteUrl}/logout-iframe?origin=${encodeURIComponent(window.location.origin)}&timestamp=${Date.now()}`,
          `${mainWebsiteUrl}/cross-domain-logout?from=${encodeURIComponent(window.location.hostname)}`,
          `${mainWebsiteUrl}/?logout=1&origin=${encodeURIComponent(window.location.origin)}`
        ];
        
        let currentUrlIndex = 0;
        
        const tryNextUrl = () => {
          if (currentUrlIndex >= iframeUrls.length) {
            console.log('🔐 All iframe URLs attempted, finishing');
            cleanup();
            resolve();
            return;
          }
          
          const url = iframeUrls[currentUrlIndex];
          console.log(`🔐 Trying iframe URL: ${url}`);
          iframe.src = url;
          currentUrlIndex++;
          
          // Try next URL after delay
          setTimeout(tryNextUrl, 1500);
        };
        
        const cleanup = () => {
          if (iframe.parentNode) {
            iframe.parentNode.removeChild(iframe);
          }
          window.removeEventListener('message', messageHandler);
        };
        
        // Remove iframe after total timeout
        const totalTimeoutId = setTimeout(() => {
          console.log('🔐 Cross-domain logout iframe total timeout reached');
          cleanup();
          resolve();
        }, 8000);
        
        iframe.onload = () => {
          console.log('🔐 Iframe loaded successfully');
        };
        
        iframe.onerror = () => {
          console.log('🔐 Iframe error, but continuing');
        };
        
        document.body.appendChild(iframe);
        tryNextUrl();
        
        // Override resolve to clear timeout
        const originalResolve = resolve;
        resolve = () => {
          clearTimeout(totalTimeoutId);
          originalResolve();
        };
        
      } catch (error) {
        console.debug('🔐 Cross-domain logout iframe creation failed:', error.message);
        resolve();
      }
    });
  }
  
  /**
   * Get environment-aware redirect URL for logout (should go to login page)
   */
  getEnvironmentAwareRedirectUrl() {
    const hostname = window.location.hostname;
    let environment = 'uat'; // default
    
    if (hostname.startsWith('uat.') || hostname.includes('-uat.')) {
      environment = 'uat';
    } else if (hostname.startsWith('live.') || hostname === 'spoton.co.nz' || 
               hostname === 'www.spoton.co.nz' || hostname === 'staff.spoton.co.nz') {
      environment = 'live';
    }
    
    // Logout should redirect to login page, not main website
    const loginUrls = {
      'live': 'https://spoton.co.nz/login',
      'uat': 'https://uat.spoton.co.nz/login'
    };
    
    // Use environment variable for main website URL if available
    const envWebUrl = import.meta.env.VITE_WEB_URL;
    if (envWebUrl) {
      return `${envWebUrl}/login`;
    }
    
    return loginUrls[environment];
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken() {
    try {
      const response = await fetch(`${this.baseUrl}/auth/keycloak/refresh/`, {
        method: 'POST',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data.success;
      }
      
      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }

  /**
   * Get user profile from backend
   */
  async getUserProfile() {
    try {
      const response = await apiClient.get('/users/profile/');
      if (response.data) {
        return {
          id: response.data.id,
          email: response.data.email,
          first_name: response.data.first_name,
          last_name: response.data.last_name,
          full_name: `${response.data.first_name} ${response.data.last_name}`.trim(),
          is_staff: response.data.is_staff || false,
          is_superuser: response.data.is_superuser || false,
          user_type: response.data.user_type || 'residential',
          email_verified: response.data.email_verified || false,
          phone_verified: response.data.phone_verified || false,
          mobile: response.data.mobile,
          social_provider: response.data.social_provider,
          registration_method: response.data.registration_method,
          is_onboarding_complete: response.data.is_onboarding_complete || false,
          groups: response.data.groups || [],
          roles: response.data.roles || [],
        };
      }
      return null;
    } catch (error) {
      console.error('Error getting user profile:', error);
      return null;
    }
  }

  /**
   * Get current user
   */
  getUser() {
    return this.user;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return this.authenticated;
  }

  /**
   * Utility: Get cookie value by name
   */
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return null;
  }

  /**
   * Utility: Get CSRF token from cookie
   */
  getCsrfToken() {
    return this.getCookie('csrftoken') || '';
  }

  /**
   * Utility: Generate random string for state parameter
   */
  generateRandomString(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * Handle OAuth callback (for verification)
   */
  handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const state = urlParams.get('state');
    const storedState = sessionStorage.getItem('oauth_state');
    
    if (state && state === storedState) {
      sessionStorage.removeItem('oauth_state');
      return true;
    }
    
    return false;
  }

  /**
   * Check if user needs profile completion (for social login users)
   */
  needsProfileCompletion() {
    if (!this.user) return false;
    
    return (
      this.user.registration_method === 'social' &&
      (!this.user.mobile || !this.user.phone_verified)
    );
  }

  /**
   * Get redirect URL based on user type and completion status
   */
  getRedirectUrl() {
    if (!this.user) {
      return import.meta.env.VITE_WEB_URL || 'http://uat.spoton.co.nz';
    }

    // Staff users go to staff portal
    if (this.user.is_staff) {
      const staffUrl = import.meta.env.VITE_STAFF_URL || 'http://uat.staff.spoton.co.nz';
    return `${staffUrl}/users`;
    }

    // Regular users go to portal
    const portalUrl = import.meta.env.VITE_PORTAL_URL || 'http://uat.portal.spoton.co.nz';
    
    // Check if user needs profile completion
    if (this.needsProfileCompletion()) {
      return `${portalUrl}/authenticated/complete-profile`;
    }

    // Check if user needs onboarding
    if (!this.user.is_onboarding_complete) {
      return `${portalUrl}/authenticated/onboarding`;
    }

    // Default to dashboard
    return `${portalUrl}/authenticated/dashboard`;
  }
}

// Create singleton instance
const keycloakCookieService = new KeycloakCookieService();

export default keycloakCookieService;

// Export individual methods for convenience
export const {
  checkAuthentication,
  login,
  logout,
  refreshToken,
  getUserProfile,
  getUser,
  isAuthenticated,
  handleCallback,
  needsProfileCompletion,
  getRedirectUrl
} = keycloakCookieService; 