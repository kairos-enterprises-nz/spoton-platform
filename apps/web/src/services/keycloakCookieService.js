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
   * Logout user and clear cookies
   */
  async logout() {
    try {
      const response = await fetch(`${this.baseUrl}/auth/keycloak/logout/`, {
        method: 'POST',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
      });

      if (response.ok) {
        this.authenticated = false;
        this.user = null;
        this.tokenExpiry = null;
        
        // Redirect to main website
        window.location.href = import.meta.env.VITE_WEB_URL || 'http://uat.spoton.co.nz';
      } else {
        throw new Error('Logout failed');
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Even if server logout fails, clear local state
      this.authenticated = false;
      this.user = null;
      window.location.href = import.meta.env.VITE_WEB_URL || 'http://uat.spoton.co.nz';
    }
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
      return `${staffUrl}/staff/dashboard`;
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