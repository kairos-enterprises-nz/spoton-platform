import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../services/apiClient';

const TenantContext = createContext();

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

export const TenantProvider = ({ children }) => {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  // Load user from localStorage on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (err) {
        console.error('Error parsing saved user:', err);
        setUser(null);
      }
    }
  }, []);

  // Load selected tenant from localStorage on mount
  useEffect(() => {
    const savedTenantId = localStorage.getItem('selectedTenantId');
    if (savedTenantId) {
      // Find the tenant in the list when tenants are loaded
      const tenant = tenants.find(t => t.id === savedTenantId);
      if (tenant) {
        setSelectedTenant(tenant);
      }
    }
  }, [tenants]);

  // Fetch tenants on mount or when user changes
  useEffect(() => {
    if (user) {
      fetchTenants();
    }
  }, [user]);

  const fetchTenants = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      setError(null);
      
      if (user.is_superuser) {
        // Super admin can see all tenants
        const response = await apiClient.get('/staff/tenants/');
        setTenants(response.data || []);
      } else if (user.tenant_id) {
        // Regular user sees only their tenant
        const response = await apiClient.get(`/staff/tenants/${user.tenant_id}/`);
        setTenants([response.data]);
        setSelectedTenant(response.data);
      } else {
        setTenants([]);
      }
    } catch (err) {
      console.error('Error fetching tenants:', err);
      setError('Failed to load tenants');
      setTenants([]);
    } finally {
      setLoading(false);
    }
  };

  const selectTenant = (tenant) => {
    setSelectedTenant(tenant);
    if (tenant) {
      localStorage.setItem('selectedTenantId', tenant.id);
    } else {
      localStorage.removeItem('selectedTenantId');
    }
  };

  const clearTenant = () => {
    setSelectedTenant(null);
    localStorage.removeItem('selectedTenantId');
  };

  // Get current tenant filter for API calls
  const getCurrentTenantFilter = () => {
    if (!user) return null;
    
    // For super admins, use selected tenant if available (null means "All Tenants")
    if (user.is_superuser) {
      return selectedTenant?.id || null;
    }
    
    // For regular staff, always use their assigned tenant (cannot view "All")
    return user.tenant_id || user.tenant?.id || null;
  };

  const value = {
    tenants,
    selectedTenant,
    loading,
    error,
    selectTenant,
    clearTenant,
    getCurrentTenantFilter,
    isSuperAdmin: user?.is_superuser || false,
    user,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}; 