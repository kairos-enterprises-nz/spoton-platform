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
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error('Login failed:', error);
      return { success: false, error: 'Login failed' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('staff_access_token');
    localStorage.removeItem('staff_refresh_token');
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    checkAuthStatus
  };

  return (
    <StaffAuthContext.Provider value={value}>
      {children}
    </StaffAuthContext.Provider>
  );
};

// Custom hook to use staff auth context
export const useStaffAuth = () => {
  const context = useContext(StaffAuthContext);
  if (!context) {
    throw new Error('useStaffAuth must be used within a StaffAuthProvider');
  }
  return context;
};

// Simple hook for components that just need auth status
export const useStaffAuthStatus = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('staff_access_token');
        if (token) {
          // Simple token existence check
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  return { isAuthenticated, loading };
};

export default useStaffAuth; 