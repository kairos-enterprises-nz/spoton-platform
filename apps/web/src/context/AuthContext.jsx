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
import { getEnvUrl } from '../utils/environment';

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

  // Initialize Keycloak on component mount
  useEffect(() => {
    // Don't initialize Keycloak on login page to avoid iframe issues
    if (window.location.pathname === '/login') {
      console.log('🔐 AuthContext: Skipping Keycloak initialization on login page');
      return;
    }
    
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
    if (!keycloakAvailable) return null;

    try {
      const authenticated = isKeycloakAuthenticated();
      if (authenticated) {
        const keycloakUser = await getKeycloakUser();
        if (keycloakUser) {
          console.log('🔐 AuthContext: Keycloak user found:', keycloakUser.email);
          
          // Handle post-login redirect
          const currentPath = window.location.pathname;
          if (currentPath === '/login' || currentPath === '/') {
            console.log('🔐 AuthContext: User authenticated, redirecting to portal...');
            window.location.href = `${getEnvUrl('portal')}/dashboard`;
            return null; // Don't update state as we're redirecting
          }
          
          return {
            id: keycloakUser.id,
            email: keycloakUser.email,
            first_name: keycloakUser.firstName,
            last_name: keycloakUser.lastName,
            full_name: keycloakUser.fullName,
            is_staff: keycloakUser.isStaff,
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
    try {
      // Use the correct API URL with environment awareness
      const apiUrl = getEnvUrl('api');
      const response = await fetch(`${apiUrl}/auth/me/`, {
        method: 'GET',
        credentials: 'include', // Important: include cookies for cross-domain
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Check if user is authenticated
        if (data.user && data.user.isAuthenticated) {
          console.log('🔐 Marketing AuthContext: Cookie authentication successful via /auth/me/');
          return data.user; // Return the user object
        }
      }
      return null;
    } catch (error) {
      console.warn('🔐 Marketing AuthContext: Cookie auth check failed:', error);
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
        setUser(keycloakUser);
        setIsAuthenticated(true);
        console.log('🔐 AuthContext: User authenticated via Keycloak');
        return;
      }

      // Check token-based authentication
      const tokenUser = await checkTokenAuth();
      if (tokenUser) {
        setUser(tokenUser);
        setIsAuthenticated(true);
        console.log('🔐 AuthContext: User authenticated via token');
        return;
      }

      // No authentication found
      setUser(null);
      setIsAuthenticated(false);
      console.log('🔐 AuthContext: User not authenticated');
      
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

  useEffect(() => {
    let isMounted = true;

    // Wait for Keycloak initialization before checking auth
    const checkAuth = async () => {
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
    
    console.log('🚪 Marketing AuthContext: Starting global logout');
    setIsAuthenticated(false);
    setUser(null);

    try {
      // Use global logout endpoint for proper cross-domain coordination
      const apiUrl = getEnvUrl('api');
      const response = await fetch(`${apiUrl}/auth/global-logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Marketing: Global logout successful:', data);
        
        // Dispatch logout event for local cleanup
        window.dispatchEvent(new CustomEvent('auth-logout-event', {
          detail: { reason: 'global_logout_success', fromPath: currentPath }
        }));
        
        // Redirect to login page
        window.location.href = '/login';
      } else {
        throw new Error(`Global logout failed: ${response.status}`);
      }
    } catch (error) {
      console.error('🔐 Marketing AuthContext: Global logout failed, falling back to Keycloak logout:', error);
      
      // Fallback to Keycloak logout if global logout fails
      try {
        if (keycloakAvailable) {
          await keycloakLogout();
        }
      } catch (keycloakError) {
        console.error('🔐 Marketing AuthContext: Keycloak logout also failed:', keycloakError);
      }
      
      // Always dispatch logout event and redirect
      window.dispatchEvent(new CustomEvent('auth-logout-event', {
        detail: { reason: 'logout_fallback', fromPath: currentPath, error: error.message }
      }));
      
      window.location.href = '/login';
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
