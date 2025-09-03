import React, { createContext, useState, useEffect, useCallback } from 'react';
import { getEnvUrl } from '../utils/environment';
import keycloakService from '../services/keycloakService';
import keycloakCookieService from '../services/keycloakCookieService';
import { getBaseUrl } from '../utils/environment';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialCheckComplete, setInitialCheckComplete] = useState(false);
  const [error, setError] = useState(null);
  const baseUrl = getBaseUrl();

  // Helpers to keep flow rules consistent everywhere
  const isSocialUser = useCallback((u) => {
    if (!u) return false;
    // Fallback inference: email is verified by IdP but phone is not → treat as social
    return (
      u.registration_method === 'social' ||
      !!u.social_provider ||
      (u.email_verified === true && u.phone_verified === false)
    );
  }, []);

  const isOnboardingDone = useCallback((u) => {
    if (!u) return false;
    return Boolean(u.is_onboarding_complete ?? u.onboarding_complete ?? false);
  }, []);

  // Allow other parts of the app to force-refresh the user from the API
  const refreshUser = useCallback(async () => {
    try {
      const response = await fetch(`${baseUrl}/auth/me/`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
        cache: 'no-store'
      });
      if (!response.ok) {
        if (response.status === 401) {
          // Try token refresh before giving up
          console.log('🔄 AuthContext: /auth/me/ failed with 401, attempting token refresh...');
          try {
            const refreshResponse = await fetch(`${baseUrl}/auth/refresh/`, {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
            });
            
            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json();
              console.log('✅ AuthContext: Token refresh successful');
              setUser(refreshData.user || null);
              return refreshData.user || null;
            } else {
              console.log('❌ AuthContext: Token refresh also failed');
              setUser(null);
              return null;
            }
          } catch (refreshError) {
            console.warn('AuthContext: Token refresh error', refreshError);
            setUser(null);
            return null;
          }
        }
        throw new Error(`Auth refresh failed: ${response.status}`);
      }
      const data = await response.json();
      setUser(data.user || null);
      return data.user || null;
    } catch (e) {
      console.warn('AuthContext: refreshUser failed', e);
      setUser(null);
      return null;
    }
  }, [baseUrl]);

  // Helper function to exchange authorization code for tokens using PKCE
  const exchangeCodeForTokens = async (authorizationCode, codeVerifier) => {
    const environment = window.location.hostname.includes('uat.') ? 'uat' : 'live';
    const realm = environment === 'live' ? 'spoton-prod' : 'spoton-uat';
    const clientId = environment === 'live' ? 'customer-live-portal' : 'customer-uat-portal';

    const tokenUrl = `${getEnvUrl('auth')}/realms/${realm}/protocol/openid-connect/token`;

    const tokenData = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: clientId,
      code: authorizationCode,
      redirect_uri: window.location.origin + '/',
      code_verifier: codeVerifier
    });

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: tokenData
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Token exchange failed: ${response.status} - ${errorData}`);
    }

    return await response.json();
  };

  // Initialize authentication
  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');

        // Skip OAuth callback handling - this is handled by OAuthCallback component
        if (code && state) {
          console.log('🔄 AuthContext: OAuth callback detected, skipping auth init to let OAuthCallback handle it');
          setLoading(false);
          setInitialCheckComplete(true);
          return;
        }

        // After handling potential PKCE callback, check session status
        const response = await fetch(`${baseUrl}/auth/me/`, {
          method: 'GET',
          credentials: 'include',
          headers: { 'Accept': 'application/json' },
          cache: 'no-store'
        });

        if (!response.ok) {
          if (response.status === 401) {
            setUser(null);
          } else {
            console.error(`Auth check failed with status: ${response.status}`);
            setUser(null);
          }
          setInitialCheckComplete(true);
          return;
        }

        const data = await response.json();
        setUser(data.user || null);
        setError(null);
        
        // All routing logic is now handled by the PrivateRoute component.
        // AuthContext is only responsible for fetching and setting the user state.
        console.log('🔍 AuthContext: User state initialized.', data.user || {});

      } catch (err) {
        console.error('Auth initialization error:', err);
        setError(err.message);
        setUser(null);
      } finally {
        setLoading(false);
        setInitialCheckComplete(true);
      }
    };

    initAuth();
  }, [baseUrl]);

  // Listen for cross-app auth updates (e.g., after OTP verify or profile changes)
  useEffect(() => {
    const handleAuthUpdated = async () => {
      await refreshUser();
    };
    const handleAuthRefreshRequest = async () => {
      await refreshUser();
    };
    window.addEventListener('auth-user-updated', handleAuthUpdated);
    window.addEventListener('auth-refresh-request', handleAuthRefreshRequest);
    return () => {
      window.removeEventListener('auth-user-updated', handleAuthUpdated);
      window.removeEventListener('auth-refresh-request', handleAuthRefreshRequest);
    };
  }, [refreshUser]);

  // Login with email/password (PKCE-enabled)
  const login = useCallback(async (credentials) => {
    const { email, password } = credentials;
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${baseUrl}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Login failed');
      }
      
        const data = await response.json();
      
      // Handle PKCE redirect response from backend
      if (data.redirect_required && data.login_url && data.pkce) {
        console.log('🔐 PKCE Login: Storing PKCE parameters and redirecting to Keycloak');
        
        // Store PKCE parameters for OAuth callback
        sessionStorage.setItem('pkce_code_verifier', data.pkce.code_verifier);
        sessionStorage.setItem('pkce_state', data.pkce.state);
        sessionStorage.setItem('login_email', email);
        
        // Redirect to Keycloak login with PKCE parameters
        window.location.href = data.login_url;
        
        // Return success but don't set user yet (will be set after callback)
        return { success: true, redirect: true };
      }
      
      // Handle direct login response (fallback)
      if (data.user) {
        setUser(data.user);
        
        // After setting user, redirect to appropriate page
        const user = data.user;
        const isSocial = isSocialUser(user);
        const isOnboardingComplete = isOnboardingDone(user);
        
        if (isSocial && !user?.phone_verified) {
          window.location.href = '/auth/verify-phone';
        } else if (!isOnboardingComplete) {
          window.location.href = '/onboarding';
        } else {
          window.location.href = '/';
        }
        
        return { success: true };
      }
      
      throw new Error('Invalid login response');
      
    } catch (err) {
      setError(err.message || 'Login failed');
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  // Login with Keycloak (SSO/Social)
  const loginWithKeycloak = useCallback((redirectUri) => {
    keycloakService.login(redirectUri);
  }, []);

  // PKCE helper functions
  const generateCodeVerifier = () => {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode.apply(null, array))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  };

  const generateCodeChallenge = async (codeVerifier) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(codeVerifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  };

  // Login with social provider
  const loginWithSocial = useCallback(async (provider) => {
    // Generate OAuth URL for social login with PKCE
    const generateSocialLoginUrl = async (provider) => {
      const environment = window.location.hostname.includes('uat.') ? 'uat' : 'live';
      const realm = environment === 'live' ? 'spoton-prod' : 'spoton-uat';
      const clientId = environment === 'live' ? 'customer-live-portal' : 'customer-uat-portal';
      const authUrl = 'https://auth.spoton.co.nz'; // Same auth domain for both UAT and Live
      
      const redirectUri = window.location.origin + '/auth/callback';
      const state = Math.random().toString(36).substring(2, 15);
      const nonce = Math.random().toString(36).substring(2, 15);
      
      // Generate PKCE parameters
      const codeVerifier = generateCodeVerifier();
      const codeChallenge = await generateCodeChallenge(codeVerifier);
      
      // Store PKCE parameters and state for validation
      sessionStorage.setItem('oauth_state', state);
      sessionStorage.setItem('oauth_nonce', nonce);
      sessionStorage.setItem('oauth_code_verifier', codeVerifier);
      
      // Store PKCE parameters in backend for token exchange
      try {
        const storageResponse = await fetch(`${baseUrl}/auth/keycloak/store-pkce/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            state: state,
            code_verifier: codeVerifier
          })
        });

        if (!storageResponse.ok) {
          console.error('Failed to store PKCE parameters');
          throw new Error('Failed to store PKCE parameters');
        }

        console.log('✅ PKCE parameters stored successfully');
      } catch (error) {
        console.error('❌ Error storing PKCE parameters:', error);
        throw error;
      }
      
      const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: 'openid profile email',
        state: state,
        nonce: nonce,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
        prompt: 'login',
        kc_idp_hint: provider // This tells Keycloak to use the specific identity provider
      });
      
      return `${authUrl}/realms/${realm}/protocol/openid-connect/auth?${params.toString()}`;
    };

    try {
      // Generate and redirect to social login
      const loginUrl = await generateSocialLoginUrl(provider);
      console.log(`🔐 Generated ${provider} login URL:`, loginUrl);
      console.log(`🔐 Redirect URI in URL:`, new URL(loginUrl).searchParams.get('redirect_uri'));
      console.log(`🔐 Redirecting to ${provider} login...`);
      window.location.href = loginUrl;
    } catch (error) {
      console.error('❌ Error initiating social login:', error);
      setError('Failed to initiate social login');
    }
  }, [baseUrl]);

  // Register new user
  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      await keycloakService.register(userData);
      
      // After registration, login with the provided credentials
      return login({ email: userData.email, password: userData.password });
    } catch (err) {
      setError(err.message || 'Registration failed');
      return { success: false, message: err.message };
    } finally {
      setLoading(false);
    }
  }, [login]);

  // Logout with enhanced Keycloak cookie handling
  const logout = useCallback(async () => {
    console.log('🔐 AuthContext: Starting logout process');
    const currentPath = window.location.pathname;
    
    try {
      setLoading(true);
      setUser(null);
      setError(null);
      
      // Use the enhanced Keycloak cookie service for comprehensive logout
      await keycloakCookieService.logout();
      
      // Note: keycloakCookieService.logout() handles redirection
      // so the code below may not execute due to the redirect
      
    } catch (err) {
      console.error('🔐 AuthContext: Logout error:', err);
      
      // Fallback logout if cookie service fails
      try {
        await fetch(`${baseUrl}/auth/logout/`, {
          method: 'POST',
          credentials: 'include',
        });
      } catch (fallbackErr) {
        console.error('🔐 AuthContext: Fallback logout error:', fallbackErr);
      }
      
      // Clear local state regardless of server response
      setUser(null);
      setError(null);
      
      // Dispatch logout event
      window.dispatchEvent(new CustomEvent('auth-logout-event', {
        detail: { reason: 'user_initiated', fromPath: currentPath }
      }));
      
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  const value = {
    user,
    setUser,
    loading,
    initialCheckComplete,
    error,
    refreshUser,
    login,
    loginWithKeycloak,
    loginWithSocial,
    register,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
