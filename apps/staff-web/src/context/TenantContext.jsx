import React, { createContext, useContext, useState, useEffect } from 'react';
import staffApi from '../services/staffApi';
import { useAuth } from '../hooks/useAuth';

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
  const { user } = useAuth();

  // Load selected tenant from localStorage on mount; null means All Tenants
  useEffect(() => {
    const savedTenantId = localStorage.getItem('selectedTenantId');
    if (savedTenantId && Array.isArray(tenants)) {
      const tenant = tenants.find(t => String(t.id) === String(savedTenantId));
      if (tenant) {
        setSelectedTenant(tenant);
      }
    }
  }, [tenants]);

  // Fetch tenants when authenticated user changes
  useEffect(() => {
    fetchTenants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, user?.is_superuser, user?.tenant_id]);

  // Whenever selectedTenant changes, trigger a soft refresh of data by emitting a storage event
  useEffect(() => {
    try {
      const event = new Event('storage');
      window.dispatchEvent(event);
    } catch {}
  }, [selectedTenant?.id]);

  const fetchTenants = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (user?.is_superuser) {
        // Super admin can see all tenants
        const data = await staffApi.getTenants();
        const list = data?.results || data || [];
        setTenants(list);
      } else if (user.tenant_id) {
        // Regular user sees only their tenant
        const data = await staffApi.getTenant(user.tenant_id);
        setTenants([data]);
        setSelectedTenant(data);
      } else {
        // If no explicit tenant on user (e.g., initial setup), try to fetch tenants
        const data = await staffApi.getTenants();
        const list = data?.results || data || [];
        setTenants(list);
        if (list.length === 1) {
          setSelectedTenant(list[0]);
          try { localStorage.setItem('selectedTenantId', list[0].id); } catch {}
        }
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

  // Global refresh trigger so pages can refresh their data consistently
  const triggerRefresh = () => {
    try {
      const ev = new CustomEvent('staff:refresh', { detail: { source: 'tenant-sidebar', ts: Date.now() } });
      window.dispatchEvent(ev);
    } catch {}
  };

  // Get current tenant filter for API calls
  const getCurrentTenantFilter = () => {
    if (!user) return null;
    
    // Super admins: honor explicit selection; null => All Tenants
    if (user.is_superuser) return selectedTenant?.id || null;
    
    // For regular staff, use their assigned tenant; if missing, fall back to selectedTenant (single-tenant setups)
    return user.tenant_id || selectedTenant?.id || user.tenant?.id || null;
  };

  const value = {
    tenants,
    selectedTenant,
    loading,
    selectTenant,
    clearTenant,
    triggerRefresh,
    getCurrentTenantFilter,
    isSuperAdmin: user?.is_superuser || false,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}; 