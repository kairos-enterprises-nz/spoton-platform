import { useState, useEffect, useContext, createContext } from 'react';
import staffApiService from '../services/staffApi';

// Create Staff Auth Context
const StaffAuthContext = createContext();

// Staff Auth Provider Component
export const StaffAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('staff_access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      // Verify token by making a request to get user profile
      const response = await fetch('/staff/profile/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('staff_access_token');
        localStorage.removeItem('staff_refresh_token');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('staff_access_token');
      localStorage.removeItem('staff_refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      setLoading(true);
      const result = await staffApiService.login(credentials);
      
      if (result.success) {
        setUser(result.user);
        setIsAuthenticated(true);
        return { success: true };
      } else {
        return { success: false, message: result.message };
      }
    } catch (error) {
      return { success: false, message: error.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      await staffApiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
    }
  };

  const refreshToken = async () => {
    try {
      const result = await staffApiService.refreshToken();
      return result;
    } catch (error) {
      // Refresh failed, logout user
      await logout();
      throw error;
    }
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    if (user.is_superuser) return true;
    
    // Check if user has the specific permission through groups
    return user.groups?.some(group => 
      group.permissions?.includes(permission)
    ) || false;
  };

  const hasRole = (roleName) => {
    if (!user) return false;
    return user.groups?.some(group => 
      group.name.toLowerCase().includes(roleName.toLowerCase())
    ) || false;
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshToken,
    hasPermission,
    hasRole,
    checkAuthStatus
  };

  return (
    <StaffAuthContext.Provider value={value}>
      {children}
    </StaffAuthContext.Provider>
  );
};

// Custom hook to use staff auth
export const useStaffAuth = () => {
  const context = useContext(StaffAuthContext);
  if (!context) {
    throw new Error('useStaffAuth must be used within a StaffAuthProvider');
  }
  return context;
};

// HOC for staff route protection
export const withStaffAuth = (Component) => {
  return function StaffAuthenticatedComponent(props) {
    const { isAuthenticated, loading } = useStaffAuth();
    
    if (loading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
        </div>
      );
    }
    
    if (!isAuthenticated) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Access Denied
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                You need to be logged in as a staff member to access this page.
              </p>
              <div className="mt-6">
                <a
                  href="/staff/login"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Go to Staff Login
                </a>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
};

export default useStaffAuth; 