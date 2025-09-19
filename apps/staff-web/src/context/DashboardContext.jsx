import { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useAuth } from '../hooks/useAuth';

const DashboardContext = createContext(null);

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};

// Component visibility configuration - can be controlled from backend
const DEFAULT_COMPONENT_CONFIG = {
  power: {
    enabled: true,
    visible: true,
    features: {
      usage_charts: true,
      billing: true,
      insights: true,
      plan_management: true
    }
  },
  broadband: {
    enabled: true,
    visible: true,
    features: {
      speed_test: true,
      usage_monitoring: true,
      plan_management: true,
      support: true
    }
  },
  mobile: {
    enabled: true,
    visible: true,
    features: {
      data_usage: true,
      call_history: true,
      plan_management: true,
      roaming: true
    }
  }
};

// Mock dashboard data - in real app, this would come from API
const MOCK_DASHBOARD_DATA = {
  power: {
    currentUsage: 2.4,
    monthlyUsage: 142,
    plan: 'Standard Variable Rate',
    costEstimate: 86.42,
    trend: 'down',
    trendValue: '12% below average'
  },
  broadband: {
    speed: 285,
    uploadSpeed: 42,
    latency: 18,
    dataUsed: 428,
    plan: 'Fiber Optic 300',
    contractUntil: '2025-11-12'
  },
  mobile: {
    dataUsed: 8.5,
    dataLimit: 25,
    minutesUsed: 420,
    minutesLimit: 'Unlimited',
    textsUsed: 1250,
    plan: 'Unlimited Plus'
  },
  billing: {
    nextBillAmount: 247.83,
    dueDate: '2025-06-05',
    paymentMethod: 'Auto-pay enabled',
    accountBalance: 0,
    lastPayment: {
      amount: 235.67,
      date: '2025-05-05',
      method: 'Credit Card'
    }
  }
};

export const DashboardProvider = ({ children }) => {
  const { user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [componentConfig, setComponentConfig] = useState(DEFAULT_COMPONENT_CONFIG);
  const [dashboardData, setDashboardData] = useState(MOCK_DASHBOARD_DATA);
  const [userServices, setUserServices] = useState([]);

  // Initialize dashboard data when user is available
  useEffect(() => {
    if (!authLoading && user) {
      // Simulate API call to fetch dashboard configuration and data
      const initializeDashboard = async () => {
        try {
          setLoading(true);
          
          // In real app, these would be API calls
          // const [configResponse, dataResponse, servicesResponse] = await Promise.all([
          //   fetchComponentConfig(user.id),
          //   fetchDashboardData(user.id),
          //   fetchUserServices(user.id)
          // ]);
          
          // Mock delay to simulate API call
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Determine user services based on user data or mock data
          const services = [];
          if (componentConfig.power.enabled) services.push('power');
          if (componentConfig.broadband.enabled) services.push('broadband');
          if (componentConfig.mobile.enabled) services.push('mobile');
          
          setUserServices(services);
          
          // Set dashboard data (in real app, this would come from API)
          setDashboardData(MOCK_DASHBOARD_DATA);
          
        } catch (error) {
          console.error('Failed to initialize dashboard:', error);
        } finally {
          setLoading(false);
        }
      };

      initializeDashboard();
    } else if (!authLoading && !user) {
      setLoading(false);
    }
  }, [user, authLoading, componentConfig]);

  // Helper functions
  const getUserDisplayName = () => {
    if (!user) return 'User';
    
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    
    if (user.first_name) {
      return user.first_name;
    }
    
    if (user.email) {
      return user.email.split('@')[0];
    }
    
    return 'User';
  };

  const getUserInitials = () => {
    if (!user) return 'U';
    
    if (user.first_name && user.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    
    if (user.first_name) {
      return user.first_name[0].toUpperCase();
    }
    
    if (user.email) {
      return user.email[0].toUpperCase();
    }
    
    return 'U';
  };

  const isComponentVisible = (componentKey) => {
    return componentConfig[componentKey]?.visible && componentConfig[componentKey]?.enabled;
  };

  const isFeatureEnabled = (componentKey, featureKey) => {
    return componentConfig[componentKey]?.features?.[featureKey] || false;
  };

  const updateComponentConfig = (newConfig) => {
    setComponentConfig(prev => ({
      ...prev,
      ...newConfig
    }));
  };

  const refreshDashboardData = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      
      // In real app, this would be an API call
      // const data = await fetchDashboardData(user.id);
      // setDashboardData(data);
      
      // Mock refresh
      await new Promise(resolve => setTimeout(resolve, 500));
      
    } catch (error) {
      console.error('Failed to refresh dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    // User data
    user,
    getUserDisplayName,
    getUserInitials,
    
    // Services and configuration
    userServices,
    componentConfig,
    isComponentVisible,
    isFeatureEnabled,
    updateComponentConfig,
    
    // Dashboard data
    dashboardData,
    refreshDashboardData,
    
    // Loading state
    loading: loading || authLoading
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

DashboardProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default DashboardContext; 