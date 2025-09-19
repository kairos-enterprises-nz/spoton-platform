import { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useAuth } from '../hooks/useAuth';
import { useApiLoader } from './LoaderContext';
import { getContractedServices, getUserPortalData } from '../services/portalService';

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
      support: true,
      network_status_tile: true
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
  },
  billing: {
    enabled: true,
    visible: true,
    features: {
      next_bill_tile: false,
      billing_schedule_tile: true
    }
  },
  support: {
    enabled: true,
    visible: true,
    features: {
      consolidated_options: true,
      tickets: true,
      faqs: true
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
  const { withLoading, updateMessage, updateProgress } = useApiLoader();
  const [loading, setLoading] = useState(true);
  const [componentConfig, setComponentConfig] = useState(DEFAULT_COMPONENT_CONFIG);
  const [dashboardData, setDashboardData] = useState({});
  const [portalData, setPortalData] = useState(null);
  const [userServices, setUserServices] = useState([]);
  const [useLiveData, setUseLiveData] = useState(true); // Enable real data by default

  // Initialize dashboard data when user is available
  useEffect(() => {
    if (!authLoading && user) {
      // Fetch real dashboard data from user's onboarding
      const initializeDashboard = async () => {
        try {
          await withLoading(async () => {
            updateMessage('Loading your dashboard...');
            updateProgress(20);
            
            console.log('🔄 [DashboardContext] Fetching real user portal data...');
            
            updateMessage('Fetching your services...');
            updateProgress(50);
            
            // Fetch comprehensive user portal data
            const realPortalData = await getUserPortalData();
            
            updateProgress(80);
            
            if (realPortalData) {
              console.log('✅ [DashboardContext] Received portal data:', realPortalData);
              setPortalData(realPortalData);
              
              // Set user services from real data
              const services = realPortalData.services?.active_services || [];
              setUserServices(services);
              console.log('📋 [DashboardContext] User services:', services);
              
              updateMessage('Setting up your dashboard...');
              updateProgress(90);
              
              // Transform portal data to dashboard format with real service statuses
              const transformedData = {
              // Power/Electricity data
              power: {
                plan: realPortalData.services?.selected_plans?.electricity?.name || 'No plan selected',
                rate: realPortalData.services?.selected_plans?.electricity?.rate || 0,
                monthlyCharge: realPortalData.services?.selected_plans?.electricity?.monthly_charge || realPortalData.services?.selected_plans?.electricity?.rate || 0,
                status: realPortalData.services?.service_statuses?.electricity?.status || 'not_active',
                statusText: _getServiceStatusText('electricity', realPortalData.services?.service_statuses?.electricity?.status),
                contractId: realPortalData.services?.selected_plans?.electricity?.contract_id,
                currentUsage: 0, // Would come from usage API
                monthlyUsage: 0, // Would come from usage API
                costEstimate: realPortalData.services?.selected_plans?.electricity?.monthly_charge || 0,
                trend: 'stable',
                trendValue: 'No usage data yet'
              },
              // Broadband data
              broadband: {
                plan: realPortalData.services?.selected_plans?.broadband?.name || 'No plan selected',
                rate: realPortalData.services?.selected_plans?.broadband?.rate || 0,
                monthlyCharge: realPortalData.services?.selected_plans?.broadband?.monthly_charge || realPortalData.services?.selected_plans?.broadband?.rate || 0,
                status: realPortalData.services?.service_statuses?.broadband?.status || 'not_active',
                statusText: _getServiceStatusText('broadband', realPortalData.services?.service_statuses?.broadband?.status),
                contractId: realPortalData.services?.selected_plans?.broadband?.contract_id,
                downloadSpeed: realPortalData.services?.selected_plans?.broadband?.download_speed || 'N/A',
                uploadSpeed: realPortalData.services?.selected_plans?.broadband?.upload_speed || 'N/A',
                dataAllowance: realPortalData.services?.selected_plans?.broadband?.data_allowance || 'N/A',
                speed: 0, // Would come from speed test API
                latency: 0, // Would come from speed test API
                dataUsed: 0, // Would come from usage API
                contractUntil: 'TBD' // Would be calculated from service start date
              },
              // Mobile data
              mobile: {
                plan: realPortalData.services?.selected_plans?.mobile?.name || 'No plan selected',
                rate: realPortalData.services?.selected_plans?.mobile?.rate || 0,
                monthlyCharge: realPortalData.services?.selected_plans?.mobile?.monthly_charge || realPortalData.services?.selected_plans?.mobile?.rate || 0,
                status: realPortalData.services?.service_statuses?.mobile?.status || 'not_active',
                statusText: _getServiceStatusText('mobile', realPortalData.services?.service_statuses?.mobile?.status),
                contractId: realPortalData.services?.selected_plans?.mobile?.contract_id,
                dataAllowance: realPortalData.services?.selected_plans?.mobile?.charges?.data_allowance || realPortalData.services?.selected_plans?.mobile?.data_allowance || 'N/A',
                dataUsed: 0, // Would come from usage API
                dataLimit: realPortalData.services?.selected_plans?.mobile?.charges?.data_allowance || realPortalData.services?.selected_plans?.mobile?.data_allowance || 'Unlimited',
                minutesUsed: 0, // Would come from usage API
                minutesLimit: realPortalData.services?.selected_plans?.mobile?.charges?.minutes || 'Unlimited',
                textsUsed: 0 // Would come from usage API
              },
              // Billing data
              billing: {
                nextBillAmount: realPortalData.billing?.estimated_monthly_bill || 0,
                dueDate: realPortalData.billing?.next_bill_date || null,
                paymentMethod: realPortalData.billing?.payment_method || 'Not specified',
                accountBalance: realPortalData.billing?.account_balance || 0,
                lastPayment: {
                  amount: 0, // Would come from billing API
                  date: null, // Would come from billing API
                  method: realPortalData.billing?.payment_method || 'Not specified'
                }
              }
            };
            
              setDashboardData(transformedData);
              console.log('🎯 [DashboardContext] Transformed dashboard data:', transformedData);
              
              updateProgress(100);
              
            } else {
              console.warn('⚠️ [DashboardContext] No portal data received, falling back to empty data');
              setUserServices([]);
              setDashboardData({
                power: { plan: 'No plan selected', costEstimate: 0 },
                broadband: { plan: 'No plan selected', downloadSpeed: 'N/A' },
                mobile: { plan: 'No plan selected', dataLimit: 'N/A' },
                billing: { nextBillAmount: 0, paymentMethod: 'Not specified' }
              });
            }
          }, 'Loading your dashboard...');
          
        } catch (error) {
          console.error('Failed to initialize dashboard:', error);
          // Don't throw the error to prevent ErrorBoundary from catching it
          // Set fallback data instead
          setPortalData(null);
          setUserServices([]);
          setDashboardData({
            power: { plan: 'No plan selected', costEstimate: 0 },
            broadband: { plan: 'No plan selected', downloadSpeed: 'N/A' },
            mobile: { plan: 'No plan selected', dataLimit: 'N/A' },
            billing: { nextBillAmount: 0, paymentMethod: 'Not specified' }
          });
        } finally {
          setLoading(false);
        }
      };

      initializeDashboard();
    } else if (!authLoading && !user) {
      setLoading(false);
    }
  }, [user, authLoading, withLoading, updateMessage, updateProgress]);

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

  const _getServiceStatusText = (serviceType, status) => {
    const statusMap = {
      'pending': 'Pending Activation',
      'pending_activation': 'Pending SIM Activation',
      'pending_switch': 'Pending Retailer Switch',
      'active': 'Active',
      'suspended': 'Suspended',
      'terminated': 'Terminated',
      'not_active': 'Not Active'
    };
    
    return statusMap[status] || 'Unknown Status';
  };

  const refreshDashboardData = async () => {
    if (!user) return;
    
    try {
      await withLoading(async () => {
        updateMessage('Refreshing your data...');
        updateProgress(30);
        
        // In real app, this would be an API call
        // const data = await fetchDashboardData(user.id);
        // setDashboardData(data);
        
        updateProgress(70);
        
        // Mock refresh
        await new Promise(resolve => setTimeout(resolve, 500));
        
        updateProgress(100);
      }, 'Refreshing dashboard...');
      
    } catch (error) {
      console.error('Failed to refresh dashboard data:', error);
      // Don't throw the error to prevent ErrorBoundary from catching it
    } finally {
      setLoading(false);
    }
  };

  const value = {
    // User data
    user,
    getUserDisplayName,
    getUserInitials,
    
    // Portal data (from onboarding)
    portalData,
    
    // Services and configuration
    userServices,
    componentConfig,
    isComponentVisible,
    isFeatureEnabled,
    updateComponentConfig,
    useLiveData,
    setUseLiveData,
    
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