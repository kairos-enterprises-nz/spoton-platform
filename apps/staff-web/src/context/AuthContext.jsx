import {
  useState,
  useEffect,
  useCallback,
  useRef,
  createContext
} from 'react';
import PropTypes from 'prop-types';
import {
  initKeycloak,
  isKeycloakAuthenticated,
  getKeycloakUser,
  keycloakLogin,
  keycloakLogout,
  getKeycloakToken,
  isKeycloakAvailable
} from '../services/keycloakService';
import keycloakCookieService from '../services/keycloakCookieService';
import { getEnvUrl } from '../utils/environment';
import staffApiService from '../services/staffApi';

const AuthContext = createContext(null);
export default AuthContext;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [initialCheckComplete, setInitialCheckComplete] = useState(false);
  const [keycloakAvailable, setKeycloakAvailable] = useState(false);
  const authCheckInProgressRef = useRef(false);
  const keycloakInitialized = useRef(false);

  // Initialize Keycloak on component mount (skip on /login to avoid double init during ROPC)
  useEffect(() => {
    const initializeKeycloak = async () => {
      if (keycloakInitialized.current) return;
      
      try {
        console.log('🔐 AuthContext: Checking Keycloak availability...');
        const available = await isKeycloakAvailable();
        setKeycloakAvailable(available);
        
        if (available) {
          console.log('🔐 AuthContext: Initializing Keycloak...');
          await initKeycloak({
            onLoad: 'check-sso',
            silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
          });
          keycloakInitialized.current = true;
          console.log('🔐 AuthContext: Keycloak initialized successfully');
        } else {
          console.log('🔐 AuthContext: Keycloak not available');
        }
      } catch (error) {
        console.warn('🔐 AuthContext: Keycloak initialization failed:', error);
        setKeycloakAvailable(false);
      }
    };

    initializeKeycloak();
  }, []);

  const checkKeycloakAuth = useCallback(async () => {
    // Try even if keycloakAvailable is false; background login may have initialized the instance

    try {
      const authenticated = isKeycloakAuthenticated();
      if (authenticated) {
        const keycloakUser = await getKeycloakUser();
    if (keycloakUser) {
          console.log('🔐 AuthContext: Keycloak user found:', keycloakUser.email);
          
      // Handle post-login redirect (stay within staff app)
          const currentPath = window.location.pathname;
      if (currentPath === '/login' || currentPath === '/') {
        console.log('🔐 AuthContext: User authenticated, redirecting to staff portal...');
        window.location.href = '/users';
        return null; // Avoid state update while navigating
      }
          
          return {
            id: keycloakUser.id,
            email: keycloakUser.email,
            first_name: keycloakUser.firstName,
            last_name: keycloakUser.lastName,
            full_name: keycloakUser.fullName,
            is_staff: keycloakUser.isStaff,
            is_superuser: keycloakUser.is_superuser,
            isAdmin: keycloakUser.isAdmin,
            user_type: keycloakUser.userType,
            is_email_verified: keycloakUser.emailVerified,
            groups: keycloakUser.groups,
            roles: keycloakUser.roles,
            realm: keycloakUser.realm,
            is_onboarding_complete: true // Assume Keycloak users are onboarded
          };
        }
      }
    } catch (error) {
      console.warn('🔐 AuthContext: Keycloak auth check failed:', error);
    }
    
    return null;
  }, [keycloakAvailable]);

  // Check token-based authentication (from login API)
  const checkTokenAuth = useCallback(async () => {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) return null;

    try {
      // Verify token with backend
      const response = await fetch('/api/auth/verify/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const userData = await response.json();
        console.log('🔐 AuthContext: Token authentication successful');
        return {
          id: userData.user.id,
          email: userData.user.email,
          first_name: userData.user.first_name,
          last_name: userData.user.last_name,
          full_name: `${userData.user.first_name} ${userData.user.last_name}`.trim(),
          is_staff: userData.user.is_staff,
          is_email_verified: true,
          is_onboarding_complete: true
        };
      } else {
        // Token invalid, remove it
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return null;
      }
    } catch (error) {
      console.warn('🔐 AuthContext: Token auth check failed:', error);
      return null;
    }
  }, []);

  const checkAuthStatus = useCallback(async () => {
    // Prevent duplicate auth checks (especially in React StrictMode)
    if (authCheckInProgressRef.current) {
      console.log('🔐 AuthContext: Auth check already in progress, skipping');
      return;
    }

    console.log('🔐 AuthContext: Starting Keycloak auth status check');
    authCheckInProgressRef.current = true;
    setLoading(true);
    
    try {
      // Check Keycloak authentication
      const keycloakUser = await checkKeycloakAuth();
      if (keycloakUser) {
        try { localStorage.setItem('user', JSON.stringify(keycloakUser)); } catch {}
        setUser(keycloakUser);
        setIsAuthenticated(true);
        console.log('🔐 AuthContext: User authenticated via Keycloak');
        // Verify super admin flag with backend (Keycloak token doesn't carry Django is_superuser)
        try {
          const stats = await staffApiService.getUsersStats();
          if (stats?.is_super_admin && !keycloakUser.is_superuser) {
            const updated = { ...keycloakUser, is_superuser: true, isAdmin: true };
            try { localStorage.setItem('user', JSON.stringify(updated)); } catch {}
            setUser(updated);
          }
        } catch (error) {
          // Silently ignore API errors during auth check to prevent infinite loops
          console.warn('🔐 AuthContext: Failed to fetch user stats during auth check:', error.message);
        }
        // Ensure a tenant is selected early for filtering
        try {
          const existing = localStorage.getItem('selectedTenantId');
          if (!existing) {
            const tenantsResp = await staffApiService.getTenants({ page_size: 100 });
            const list = tenantsResp?.results || tenantsResp || [];
            if (Array.isArray(list) && list.length === 1) {
              localStorage.setItem('selectedTenantId', list[0].id);
            }
          }
        } catch (error) {
          // Silently ignore API errors during auth check to prevent infinite loops
          console.warn('🔐 AuthContext: Failed to fetch tenants during auth check:', error.message);
        }
        return;
      }

      // Check token-based authentication
      const tokenUser = await checkTokenAuth();
      if (tokenUser) {
        try { localStorage.setItem('user', JSON.stringify(tokenUser)); } catch {}
        setUser(tokenUser);
        setIsAuthenticated(true);
        console.log('🔐 AuthContext: User authenticated via token');
        try {
          const stats = await staffApiService.getUsersStats();
          if (stats?.is_super_admin && !tokenUser.is_superuser) {
            const updated = { ...tokenUser, is_superuser: true, isAdmin: true };
            try { localStorage.setItem('user', JSON.stringify(updated)); } catch {}
            setUser(updated);
          }
        } catch (error) {
          // Silently ignore API errors during auth check to prevent infinite loops
          console.warn('🔐 AuthContext: Failed to fetch user stats for token user:', error.message);
        }
        try {
          const existing = localStorage.getItem('selectedTenantId');
          if (!existing) {
            const tenantsResp = await staffApiService.getTenants({ page_size: 100 });
            const list = tenantsResp?.results || tenantsResp || [];
            if (Array.isArray(list) && list.length === 1) {
              localStorage.setItem('selectedTenantId', list[0].id);
            }
          }
        } catch (error) {
          // Silently ignore API errors during auth check to prevent infinite loops
          console.warn('🔐 AuthContext: Failed to fetch tenants for token user:', error.message);
        }
        return;
      }

      // No authentication found
      setUser(null);
      setIsAuthenticated(false);
      console.log('🔐 AuthContext: User not authenticated');
      // If we have tokens in session but profile fetch failed, fallback to client-side claim parse
      try {
        const access = sessionStorage.getItem('kc_access_token');
        if (access) {
          const payload = JSON.parse(atob(access.split('.')[1]));
          if (payload && (payload.email || payload.preferred_username)) {
            const groups = payload.groups || [];
            const roles = payload.realm_access?.roles || [];
            const isAdmin = groups.includes('Admin') || roles?.includes('admin') || groups.some(g => String(g).toLowerCase().includes('admin'));
            const fallbackUser = {
              id: payload.sub,
              email: payload.email || payload.preferred_username,
              first_name: payload.given_name,
              last_name: payload.family_name,
              full_name: `${payload.given_name || ''} ${payload.family_name || ''}`.trim() || payload.preferred_username || payload.email,
              is_staff: true,
              is_superuser: isAdmin,
              isAdmin,
              groups,
              roles,
              is_email_verified: !!payload.email_verified,
              is_onboarding_complete: true
            };
            try { localStorage.setItem('user', JSON.stringify(fallbackUser)); } catch {}
            setUser(fallbackUser);
            setIsAuthenticated(true);
            console.log('🔐 AuthContext: Fallback user from token claims');
            // Probe backend for super admin flag
            try {
              const stats = await staffApiService.getUsersStats();
              if (stats?.is_super_admin) {
                const updated = { ...fallbackUser, is_superuser: true, isAdmin: true };
                try { localStorage.setItem('user', JSON.stringify(updated)); } catch {}
                setUser(updated);
              }
            } catch (error) {
              // Silently ignore API errors during auth check to prevent infinite loops
              console.warn('🔐 AuthContext: Failed to fetch user stats for fallback user:', error.message);
            }
            try {
              const existing = localStorage.getItem('selectedTenantId');
              if (!existing) {
                const tenantsResp = await staffApiService.getTenants({ page_size: 100 });
                const list = tenantsResp?.results || tenantsResp || [];
                if (Array.isArray(list) && list.length === 1) {
                  localStorage.setItem('selectedTenantId', list[0].id);
                }
              }
            } catch (error) {
              // Silently ignore API errors during auth check to prevent infinite loops
              console.warn('🔐 AuthContext: Failed to fetch tenants for fallback user:', error.message);
            }
            return;
          }
        }
      } catch {}
      
    } catch (error) {
      console.error('🔐 AuthContext: Auth check error:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
      setInitialCheckComplete(true);
      authCheckInProgressRef.current = false;
      console.log('🔐 AuthContext: Auth check completed');
    }
  }, [checkKeycloakAuth, checkTokenAuth]);

  const refreshUser = useCallback(async () => {
    try {
      const keycloakUser = await checkKeycloakAuth();
      if (keycloakUser) {
        setUser(keycloakUser);
        setIsAuthenticated(true);
        return;
      }

      // No authentication
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('🔐 AuthContext: Refresh user failed:', error);
      setUser(null);
      setIsAuthenticated(false);
    }
  }, [checkKeycloakAuth]);

  // Keep localStorage user synchronized for services (tenant filter reads from it)
  useEffect(() => {
    try {
      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      } else {
        localStorage.removeItem('user');
      }
    } catch {}
  }, [user]);

  useEffect(() => {
    let isMounted = true;

    // Attempt to adopt stored tokens before checking auth
    const checkAuth = async () => {
      // Try adopting tokens if present (best effort)
      // No await to avoid blocking initial checks
      import('../services/keycloakService').then(m => m.adoptStoredTokensIfAvailable?.()).then((adopted) => {
        if (adopted) console.log('🔐 AuthContext: Adopted stored tokens');
      }).catch(() => {});
      if (keycloakAvailable && !keycloakInitialized.current) {
        // Wait a bit for Keycloak to initialize
        setTimeout(() => {
          if (isMounted) checkAuthStatus();
        }, 100);
      } else {
        if (isMounted) checkAuthStatus();
      }
    };

    checkAuth();

    const handleKeycloakTokenRefresh = () => {
      if (isMounted) {
        console.log('🔐 AuthContext: Keycloak token refreshed');
        refreshUser();
      }
    };

    const handleKeycloakTokenExpired = () => {
      if (isMounted) {
        console.log('🔐 AuthContext: Keycloak token expired, logging out');
        setUser(null);
        setIsAuthenticated(false);
      }
    };

    // Listen for Keycloak events
    window.addEventListener('keycloak-token-refreshed', handleKeycloakTokenRefresh);
    window.addEventListener('keycloak-token-expired', handleKeycloakTokenExpired);

    return () => {
      isMounted = false;
      window.removeEventListener('keycloak-token-refreshed', handleKeycloakTokenRefresh);
      window.removeEventListener('keycloak-token-expired', handleKeycloakTokenExpired);
    };
  }, [checkAuthStatus, refreshUser, keycloakAvailable]);

  const login = useCallback(async () => {
    if (!keycloakAvailable) {
      throw new Error('Authentication not available');
    }
    
    console.log('🔐 AuthContext: Starting Keycloak login');
    
    try {
      // If Keycloak wasn't initialized due to iframe issues, try to initialize it now
      if (!keycloakInitialized.current) {
        console.log('🔐 AuthContext: Initializing Keycloak for login...');
        await initKeycloak({
          onLoad: 'login-required'
        });
        keycloakInitialized.current = true;
      }
      
      // Pass redirect to portal
      await keycloakLogin({
        redirectUri: `${getEnvUrl('portal')}/dashboard`
      });
      // Keycloak login redirects, so this won't return normally
      return { success: true };
    } catch (error) {
      console.error('🔐 AuthContext: Login failed:', error);
      throw error;
    }
  }, [keycloakAvailable]);

  const logout = useCallback(async () => {
    const currentPath = window.location.pathname;
    console.log('🔐 AuthContext: Starting logout process');

    // Clear local state immediately
    setIsAuthenticated(false);
    setUser(null);

    try {
      // Use enhanced Keycloak cookie service for comprehensive logout
      await keycloakCookieService.logout();
      
      // Note: keycloakCookieService.logout() handles redirection
      // so the code below may not execute due to the redirect
      
    } catch (error) {
      console.error('🔐 AuthContext: Enhanced logout error:', error);
      
      // Fallback to original Keycloak logout if available
      try {
        if (keycloakAvailable) {
          console.log('🔐 AuthContext: Fallback to Keycloak logout');
          await keycloakLogout();
          // Keycloak logout redirects, so this won't return normally
        }
      } catch (fallbackError) {
        console.error('🔐 AuthContext: Fallback logout error:', fallbackError);
      }
      
      // Dispatch logout event for cleanup
      window.dispatchEvent(new CustomEvent('auth-logout-event', {
        detail: { reason: 'user_initiated', fromPath: currentPath }
      }));
    }
  }, [keycloakAvailable]);

  const contextValue = {
    user,
    isAuthenticated,
    loading,
    initialCheckComplete,
    keycloakAvailable,
    login,
    logout,
    refreshUser,
    // Helper methods
    getAccessToken: () => getKeycloakToken()
  };

  // Show loading until initial check is complete
  if (!initialCheckComplete) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        zIndex: 9999
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #3498db',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          <p style={{ margin: 0, color: '#666' }}>
            {keycloakAvailable ? 'Initializing SSO...' : 'Authentication not available'}
          </p>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};
