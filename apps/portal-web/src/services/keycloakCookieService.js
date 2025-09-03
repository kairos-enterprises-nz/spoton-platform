/**
 * Keycloak Service using secure HTTP cookies
 * This service communicates with Django backend for Keycloak authentication
 */

import apiClient from './apiClient';

class KeycloakCookieService {
  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'https://uat.api.spoton.co.nz';
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
      // Traditional email/password login
      if (options.email && options.password) {
        return await this.traditionalLogin(options.email, options.password);
      }
      
      // Social login
      if (options.socialProvider) {
        return await this.socialLogin(options.socialProvider);
      }
      
      // Default Keycloak SSO login
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
   * Traditional email/password login
   */
  async traditionalLogin(email, password) {
    try {
                    const response = await fetch(`${this.baseUrl}/api/auth/login/`, {
         method: 'POST',
         credentials: 'include',
         headers: {
           'Content-Type': 'application/json',
           'X-CSRFToken': this.getCsrfToken(),
         },
         body: JSON.stringify({
           email,
           password
         })
       });

       if (response.ok) {
         const data = await response.json();
         // Login successful, user profile should be in response
         this.user = data.user;
         this.authenticated = true;
         
         // Redirect to dashboard
         window.location.href = '/dashboard';
         return { success: true };
       } else {
         const errorData = await response.json();
         throw new Error(errorData.error || errorData.message || 'Login failed');
       }
         } catch (error) {
       console.error('Traditional login error:', error);
       throw new Error(error.message || 'Login failed');
     }
  }

  /**
   * Social login
   */
  async socialLogin(provider) {
    try {
      const loginUrl = new URL(`${this.baseUrl}/auth/keycloak/login/`);
      
      // Add identity provider hint for social login
      loginUrl.searchParams.set('kc_idp_hint', provider);
      
      // Add state for CSRF protection
      const state = this.generateRandomString(32);
      loginUrl.searchParams.set('state', state);
      sessionStorage.setItem('oauth_state', state);
      
      // Redirect to Django backend which will handle Keycloak OAuth flow with social provider
      window.location.href = loginUrl.toString();
      
      return { success: true };
    } catch (error) {
      console.error(`Social login (${provider}) error:`, error);
      throw new Error(`Failed to initiate ${provider} login`);
    }
  }

  /**
   * Global logout - coordinate across all SpotOn applications
   */
  async logout() {
    console.log('🚪 KeycloakCookieService: Starting GLOBAL logout');
    
    // Debug: Show what cookies exist before logout
    this.debugCookies('BEFORE GLOBAL LOGOUT');
    
    try {
      // 1. Clear local state immediately for fast UX
      this.authenticated = false;
      this.user = null;
      this.tokenExpiry = null;
      this.clearLocalStorage();
      
      // 2. Call global logout endpoint for proper cross-domain coordination
      const response = await fetch(`${this.baseUrl}/auth/global-logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Portal: Global logout successful:', data);
        
        // Dispatch logout event
        window.dispatchEvent(new CustomEvent('auth-logout-complete', {
          detail: { 
            reason: 'global_logout_success',
            redirectUrls: data.redirect_urls
          }
        }));
        
        // Redirect to portal login
        const redirectUrl = data.redirect_urls?.portal || this.getEnvironmentAwareRedirectUrl();
        console.log('🔄 Redirecting to:', redirectUrl);
        window.location.href = redirectUrl;
        
      } else {
        throw new Error(`Global logout failed: ${response.status}`);
      }
      
    } catch (error) {
      console.error('❌ Global logout failed, performing local cleanup:', error);
      
      // Fallback to local cleanup
      this.clearAuthCookies();
      
      window.dispatchEvent(new CustomEvent('auth-logout-complete', {
        detail: { reason: 'global_logout_failed', error: error.message }
      }));
      
      const redirectUrl = this.getEnvironmentAwareRedirectUrl();
      console.log('🔄 Fallback redirect to:', redirectUrl);
      window.location.href = redirectUrl;
    }
  }
  
  /**
   * Debug helper to inspect cookies
   */
  debugCookies(label) {
    console.log(`🔐 === COOKIE DEBUG: ${label} ===`);
    
    if (!document.cookie) {
      console.log('🔐 No cookies found');
      return;
    }
    
    const cookies = document.cookie.split(';').map(cookie => {
      const [name, ...valueParts] = cookie.trim().split('=');
      const value = valueParts.join('=');
      return {
        name: name.trim(),
        value: value || '',
        length: value ? value.length : 0
      };
    });
    
    console.log('🔐 Cookie details:');
    cookies.forEach((cookie, index) => {
      console.log(`🔐 ${index + 1}. ${cookie.name} = ${cookie.value.substring(0, 50)}${cookie.length > 50 ? '...' : ''} (${cookie.length} chars)`);
    });
    
    console.log(`🔐 Total cookies: ${cookies.length}`);
    console.log('🔐 Raw cookie string:', document.cookie);
    console.log('🔐 === END COOKIE DEBUG ===');
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
      img.src = `${mainWebsiteUrl}/logout?source=portal&t=${Date.now()}`;
      
    } catch (error) {
      console.log('🔐 Background logout error:', error.message);
    }
  }
  
  /**
   * Clear authentication cookies - enhanced with better debugging
   */
  clearAuthCookies() {
    console.log('🔐 Starting cookie clearing process');
    
    // Get all existing cookies before clearing
    const beforeCookies = document.cookie;
    console.log('🔐 Cookies BEFORE clearing:', beforeCookies);
    
    if (!beforeCookies) {
      console.log('🔐 No cookies found to clear');
      return;
    }
    
    // Parse cookies
    const cookieEntries = beforeCookies.split(';').map(cookie => {
      const [name, value] = cookie.trim().split('=');
      return { name: name.trim(), value: value || '' };
    }).filter(entry => entry.name);
    
    console.log('🔐 Parsed cookies:', cookieEntries);
    
    // Clear each cookie with multiple approaches
    cookieEntries.forEach(({ name }) => {
      console.log(`🔐 Attempting to clear cookie: ${name}`);
      
      // Try different clearing methods
      const clearingMethods = [
        // Basic clearing
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`,
        `${name}=; max-age=0; path=/;`,
        
        // With secure flag
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; secure;`,
        `${name}=; max-age=0; path=/; secure;`,
        
        // With domain variations
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`,
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${window.location.hostname.split('.').slice(-2).join('.')};`,
        
        // With different samesite values
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax;`,
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=strict;`,
        `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; secure; samesite=none;`,
      ];
      
      clearingMethods.forEach((method, index) => {
        try {
          const beforeAttempt = document.cookie;
          document.cookie = method;
          const afterAttempt = document.cookie;
          
          if (beforeAttempt !== afterAttempt) {
            console.log(`🔐 ✅ Method ${index + 1} worked for ${name}: ${method}`);
          }
        } catch (error) {
          console.debug(`🔐 Method ${index + 1} failed for ${name}:`, error.message);
        }
      });
    });
    
    // Verify clearing after a short delay
    setTimeout(() => {
      const afterCookies = document.cookie;
      console.log('🔐 Cookies AFTER clearing:', afterCookies);
      
      if (afterCookies === beforeCookies) {
        console.warn('🔐 ⚠️ NO COOKIES WERE CLEARED! All cookies remain the same.');
        console.log('🔐 This might be due to:');
        console.log('🔐 - HttpOnly cookies (cannot be cleared by JavaScript)');
        console.log('🔐 - Secure cookies on non-HTTPS');
        console.log('🔐 - Wrong domain/path settings');
        console.log('🔐 - SameSite restrictions');
      } else if (afterCookies) {
        const remainingCookies = afterCookies.split(';').map(c => c.trim().split('=')[0]);
        console.warn('🔐 ⚠️ Some cookies still remain:', remainingCookies);
      } else {
        console.log('🔐 ✅ All cookies successfully cleared!');
      }
    }, 200);
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
   * Get environment-aware redirect URL for logout (should go to login page)
   */
  getEnvironmentAwareRedirectUrl() {
    const hostname = window.location.hostname;
    let environment = 'uat'; // default
    
    if (hostname.startsWith('uat.') || hostname.includes('-uat.')) {
      environment = 'uat';
    } else if (hostname.startsWith('live.') || hostname === 'spoton.co.nz' || 
               hostname === 'www.spoton.co.nz' || hostname === 'portal.spoton.co.nz') {
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
      const response = await apiClient.get('/api/profile/');
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
      return `${staffUrl}/staff/dashboard`;
    }

    // Regular users go to portal
    const portalUrl = import.meta.env.VITE_PORTAL_URL || 'http://uat.portal.spoton.co.nz';
    
    // Check if user needs profile completion
    if (this.needsProfileCompletion()) {
      return `${portalUrl}/profile`;
    }

    // Check if user needs onboarding
    if (!this.user.is_onboarding_complete) {
      return `${portalUrl}/onboarding`;
    }

    // Default to dashboard
    return `${portalUrl}/`;
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