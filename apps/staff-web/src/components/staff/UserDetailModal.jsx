import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { 
  X, User, Mail, Phone, Building2, Shield, 
  Calendar, Clock, CreditCard, FileText, 
  Activity, AlertCircle, CheckCircle, Edit, Trash2,
  Hash, Network, Zap, Wifi, Smartphone,
  MapPin, ExternalLink, Settings
} from 'lucide-react';
import staffApiService from '../../services/staffApi';

const UserDetailModal = ({ isOpen, onClose, userId, onEdit, onDelete }) => {
  const navigate = useNavigate();
  const [userData, setUserData] = useState(null);
  const [userAccounts, setUserAccounts] = useState([]);
  const [userContracts, setUserContracts] = useState([]);
  const [userConnections, setUserConnections] = useState([]);
  const [userPlans, setUserPlans] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loadingStates, setLoadingStates] = useState({
    accounts: false,
    contracts: false,
    connections: false,
    plans: false
  });

  useEffect(() => {
    if (isOpen && userId) {
      console.log('🚀 UserDetailModal opened for userId:', userId);
      console.log('🔄 Loading all user data...');
      loadUserData();
      loadUserAccounts();
      loadUserContracts();
      loadUserConnections();
      loadUserPlans();
    }
  }, [isOpen, userId]);

  const loadUserData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await staffApiService.getUser(userId);
      console.log('User data loaded:', data);
      console.log('📊 Backend relationship counts:', {
        accounts_count: data?.accounts_count,
        contracts_count: data?.contracts_count,
        connections_count: data?.connections_count,
        plans_count: data?.plans_count,
        user_number: data?.user_number,
        phone: data?.phone
      });
      setUserData(data);
    } catch (error) {
      console.error('Failed to load user data:', error);
      setError(error.message || 'Failed to load user data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserAccounts = async () => {
    setLoadingStates(prev => ({ ...prev, accounts: true }));
    try {
      console.log('🔍 Loading user accounts for userId:', userId);
      const response = await staffApiService.getUserAccounts(userId);
      console.log('✅ User accounts loaded:', response);
      console.log('✅ Response type:', typeof response, 'Is array:', Array.isArray(response));
      // Handle both direct array and paginated response
      const accounts = response.results || response || [];
      console.log('✅ Processed accounts:', accounts.length, 'items');
      setUserAccounts(accounts);
    } catch (error) {
      console.error('❌ Failed to load user accounts:', error);
      console.error('❌ Error details:', error.response?.data || error.message);
      setUserAccounts([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, accounts: false }));
    }
  };

  const loadUserContracts = async () => {
    setLoadingStates(prev => ({ ...prev, contracts: true }));
    try {
      console.log('🔍 Loading user contracts for userId:', userId);
      const response = await staffApiService.getUserContracts(userId);
      console.log('✅ User contracts loaded:', response);
      console.log('✅ Response type:', typeof response, 'Is array:', Array.isArray(response));
      // Handle both direct array and paginated response
      const contracts = response.results || response || [];
      console.log('✅ Processed contracts:', contracts.length, 'items');
      setUserContracts(contracts);
    } catch (error) {
      console.error('❌ Failed to load user contracts:', error);
      console.error('❌ Error details:', error.response?.data || error.message);
      setUserContracts([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, contracts: false }));
    }
  };

  const loadUserConnections = async () => {
    setLoadingStates(prev => ({ ...prev, connections: true }));
    try {
      console.log('🔍 Loading user connections for userId:', userId);
      const response = await staffApiService.getUserConnections(userId);
      console.log('✅ User connections loaded:', response);
      console.log('✅ Response type:', typeof response, 'Is array:', Array.isArray(response));
      // Handle both direct array and paginated response
      const connections = response.results || response || [];
      console.log('✅ Processed connections:', connections.length, 'items');
      setUserConnections(connections);
    } catch (error) {
      console.error('❌ Failed to load user connections:', error);
      console.error('❌ Error details:', error.response?.data || error.message);
      setUserConnections([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, connections: false }));
    }
  };

  const loadUserPlans = async () => {
    setLoadingStates(prev => ({ ...prev, plans: true }));
    try {
      console.log('🔍 Loading user plans for userId:', userId);
      const response = await staffApiService.getUserPlans(userId);
      console.log('✅ User plans loaded:', response);
      console.log('✅ Response type:', typeof response, 'Is array:', Array.isArray(response));
      // Handle both direct array and paginated response
      const plans = response.results || response || [];
      console.log('✅ Processed plans:', plans.length, 'items');
      setUserPlans(plans);
    } catch (error) {
      console.error('❌ Failed to load user plans:', error);
      console.error('❌ Error details:', error.response?.data || error.message);
      setUserPlans([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, plans: false }));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Intl.DateTimeFormat('en-NZ', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  const getStatusBadge = (isActive) => {
    if (isActive) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Active
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <AlertCircle className="w-3 h-3 mr-1" />
          Inactive
        </span>
      );
    }
  };

  const getRoleBadge = (isStaff, isSuperuser) => {
    if (isSuperuser) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          <Shield className="w-3 h-3 mr-1" />
          Super Admin
        </span>
      );
    } else if (isStaff) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Shield className="w-3 h-3 mr-1" />
          Staff
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          <User className="w-3 h-3 mr-1" />
          Customer
        </span>
      );
    }
  };

  const getServiceIcon = (serviceType) => {
    switch (serviceType?.toLowerCase()) {
      case 'electricity':
        return <Zap className="w-4 h-4 text-yellow-500" />;
      case 'broadband':
        return <Wifi className="w-4 h-4 text-blue-500" />;
      case 'mobile':
        return <Smartphone className="w-4 h-4 text-green-500" />;
      default:
        return <Network className="w-4 h-4 text-gray-500" />;
    }
  };

  const getContractStatusBadge = (status) => {
    const statusConfig = {
      'active': { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
      'inactive': { bg: 'bg-red-100', text: 'text-red-800', icon: AlertCircle },
      'pending': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock },
      'suspended': { bg: 'bg-orange-100', text: 'text-orange-800', icon: AlertCircle },
    };
    
    const config = statusConfig[status?.toLowerCase()] || statusConfig['inactive'];
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status || 'Unknown'}
      </span>
    );
  };

  const getConnectionStatusBadge = (status) => {
    const statusConfig = {
      'connected': { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
      'disconnected': { bg: 'bg-red-100', text: 'text-red-800', icon: AlertCircle },
      'pending': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock },
      'suspended': { bg: 'bg-orange-100', text: 'text-orange-800', icon: AlertCircle },
    };
    
    const config = statusConfig[status?.toLowerCase()] || statusConfig['disconnected'];
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status || 'Unknown'}
      </span>
    );
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: User },
    { id: 'accounts', name: 'Accounts', icon: CreditCard, count: userData?.accounts_count || userAccounts.length },
    { id: 'contracts', name: 'Contracts', icon: FileText, count: userData?.contracts_count || userContracts.length },
    { id: 'connections', name: 'Connections', icon: Network, count: userData?.connections_count || userConnections.length },
    { id: 'plans', name: 'Plans', icon: Settings, count: userData?.plans_count || userPlans.length },
    { id: 'activity', name: 'Activity', icon: Activity }
  ];

  const getTotalRelationships = () => {
    // Use backend counts if available, fallback to frontend counts
    const accountsCount = userData?.accounts_count ?? userAccounts.length;
    const contractsCount = userData?.contracts_count ?? userContracts.length;
    const connectionsCount = userData?.connections_count ?? userConnections.length;
    const plansCount = userData?.plans_count ?? userPlans.length;
    
    const total = accountsCount + contractsCount + connectionsCount + plansCount;
    console.log('📊 Relationship counts (backend first):', {
      accounts: accountsCount,
      contracts: contractsCount,
      connections: connectionsCount,
      plans: plansCount,
      total: total
    });
    return total;
  };

  // Navigation handlers
  const handleViewAccount = (accountId) => {
    onClose();
  navigate(`/accounts?selected=${accountId}`);
  };

  const handleViewContract = (contractId) => {
    onClose();
  navigate(`/contracts?selected=${contractId}`);
  };

  const handleViewConnection = (connectionId) => {
    onClose();
  navigate(`/connections?selected=${connectionId}`);
  };

  const handleViewPlan = (planId) => {
    onClose();
  navigate(`/plans?selected=${planId}`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white mb-10" data-testid="user-detail-modal">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div>
            <h3 className="text-xl text-left font-semibold text-gray-900">User Details</h3>
            <p className="text-sm text-left text-gray-500">
              {userData ? `${userData.first_name} ${userData.last_name}` : 'Loading...'}
              {userData && getTotalRelationships() > 0 && (
                <span className="ml-2 text-xs text-gray-400">
                  ({getTotalRelationships()} relationships)
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            {userData && (
              <>
                <button
                  onClick={() => onEdit?.(userData?.id)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </button>
                <button
                  onClick={() => onDelete?.(userData)}
                  className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="ml-2 text-sm text-gray-600">Loading user data...</span>
          </div>
        ) : error ? (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-400 mr-2 flex-shrink-0" />
              <div>
                <p className="text-sm text-red-600">{error}</p>
                <button
                  onClick={loadUserData}
                  className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        ) : userData ? (
          <>
            {/* User Summary */}
            <div className="mt-4 bg-gray-50 rounded-lg p-4">
              <div className="flex text-left items-center space-x-4">
                <div className="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center">
                  <span className="text-indigo-600 font-semibold text-xl">
                    {userData.first_name?.[0]}{userData.last_name?.[0]}
                  </span>
                </div>
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-gray-900">
                    {userData.first_name} {userData.last_name}
                  </h4>
                  <p className="text-sm text-gray-600">{userData.email}</p>
                  <div className="flex items-center space-x-2 mt-2">
                    {getStatusBadge(userData.is_active)}
                    {getRoleBadge(userData.is_staff, userData.is_superuser)}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">User Number</p>
                  <p className="text-sm font-medium text-gray-900">{userData.user_number || 'N/A'}</p>
                  <p className="text-xs text-gray-400 mt-1">ID: {userData.id}</p>
                  {userData.tenant_name && (
                    <div className="mt-2 flex items-center text-xs text-gray-500">
                      <Building2 className="w-3 h-3 mr-1" />
                      {userData.tenant_name}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="mt-6">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                          activeTab === tab.id
                            ? 'border-indigo-500 text-indigo-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        <Icon className="w-4 h-4 mr-2" />
                        {tab.name}
                        {tab.count !== undefined && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {tab.count}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="mt-6">
                {activeTab === 'overview' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Personal Information */}
                    <div className="space-y-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Personal Information</h5>
                      <div className="space-y-3">
                        <div className="flex items-center">
                          <Mail className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">Email:</span>
                          <span className="text-sm text-gray-900 ml-2">{userData.email}</span>
                        </div>
                        {(userData.user_number || userData.identifier) && (
                          <div className="flex items-center">
                            <Hash className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">User Number:</span>
                            <span className="text-sm text-gray-900 ml-2">{userData.user_number || userData.identifier?.substring(0, 8) || 'N/A'}</span>
                          </div>
                        )}
                        {(userData.phone_number || userData.mobile || userData.phone) && (
                          <div className="flex items-center">
                            <Phone className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Phone:</span>
                            <span className="text-sm text-gray-900 ml-2">{userData.mobile || userData.phone_number || userData.phone}</span>
                          </div>
                        )}
                        {(userData.tenant_name || userData.tenant?.name) && (
                          <div className="flex items-center">
                            <Building2 className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Tenant:</span>
                            <span className="text-sm text-gray-900 ml-2">{userData.tenant_name || userData.tenant?.name}</span>
                          </div>
                        )}
                        {userData.department && (
                          <div className="flex items-center">
                            <FileText className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Department:</span>
                            <span className="text-sm text-gray-900 ml-2">{userData.department}</span>
                          </div>
                        )}
                        {userData.job_title && (
                          <div className="flex items-center">
                            <User className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Job Title:</span>
                            <span className="text-sm text-gray-900 ml-2">{userData.job_title}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Account Information */}
                    <div className="space-y-4 text-left">
                      <h5 className="text-md font-medium text-gray-900">Account Information</h5>
                      <div className="space-y-3">
                        <div className="flex items-center">
                          <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">Created:</span>
                          <span className="text-sm text-gray-900 ml-2">{formatDate(userData.created_at)}</span>
                        </div>
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">Last Login:</span>
                          <span className="text-sm text-gray-900 ml-2">{formatDate(userData.last_login)}</span>
                        </div>
                        <div className="flex items-center">
                          <User className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">User Type:</span>
                          <span className="text-sm text-gray-900 ml-2 capitalize">{userData.user_type || 'residential'}</span>
                        </div>
                        <div className="flex items-center">
                          <CheckCircle className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">Verified:</span>
                          <span className="text-sm text-gray-900 ml-2">{userData.is_verified ? 'Yes' : 'No'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'accounts' && (
                  <div data-testid="user-accounts-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Associated Accounts</h5>
                      {loadingStates.accounts && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                    </div>
                    {userAccounts.length > 0 ? (
                      <div className="space-y-3">
                        {userAccounts.map((account) => (
                          <div key={account.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex text-left items-center justify-between mb-3">
                              <div className="flex items-center space-x-3">
                                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                  <CreditCard className="w-5 h-5 text-blue-600" />
                                </div>
                              <div>
                                <h6 className="text-sm font-medium text-gray-900">{account.account_number}</h6>
                                <p className="text-sm text-gray-600 capitalize">{account.account_type}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  account.status === 'active' 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {account.status || 'Unknown'}
                                </span>
                              </div>
                            </div>
                            
                            {account.address && (
                              <div className="flex items-center text-sm text-gray-600 mb-2">
                                <MapPin className="w-4 h-4 mr-2" />
                                <span>{account.address}</span>
                              </div>
                            )}
                            
                            <div className="flex items-center justify-between text-sm text-gray-500">
                              <span>Created: {formatDate(account.created_at)}</span>
                              <button className="text-indigo-600 hover:text-indigo-800 flex items-center" onClick={() => handleViewAccount(account.id)}>
                                <ExternalLink className="w-3 h-3 mr-1" />
                                View Details
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No accounts found</h3>
                        <p className="mt-1 text-sm text-gray-500">This user has no associated accounts.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'contracts' && (
                  <div data-testid="user-contracts-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Associated Contracts</h5>
                      {loadingStates.contracts && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                    </div>
                    {userContracts.length > 0 ? (
                      <div className="space-y-3">
                        {userContracts.map((contract) => (
                          <div key={contract.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex text-left items-center justify-between mb-3">
                              <div className="flex items-center space-x-3">
                                <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                                  {getServiceIcon(contract.service_type)}
                                </div>
                              <div>
                                <h6 className="text-sm font-medium text-gray-900">{contract.contract_number}</h6>
                                  <p className="text-sm text-gray-600 capitalize">{contract.service_type}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                {getContractStatusBadge(contract.status)}
                              </div>
                            </div>
                            
                            {contract.plan_name && (
                              <div className="flex items-center text-sm text-gray-600 mb-2">
                                <Settings className="w-4 h-4 mr-2" />
                                <span>Plan: {contract.plan_name}</span>
                              </div>
                            )}
                            
                            <div className="flex items-center justify-between text-sm text-gray-500">
                              <span>Start: {formatDate(contract.start_date)}</span>
                              <button className="text-indigo-600 hover:text-indigo-800 flex items-center" onClick={() => handleViewContract(contract.id)}>
                                <ExternalLink className="w-3 h-3 mr-1" />
                                View Details
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <FileText className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No contracts found</h3>
                        <p className="mt-1 text-sm text-gray-500">This user has no associated contracts.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'connections' && (
                  <div data-testid="user-connections-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Service Connections</h5>
                      {loadingStates.connections && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                    </div>
                    {userConnections.length > 0 ? (
                      <div className="space-y-3">
                        {userConnections.map((connection) => (
                          <div key={connection.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex text-left items-center justify-between mb-3">
                              <div className="flex items-center space-x-3">
                                <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                                  {getServiceIcon(connection.service_type)}
                                </div>
                                <div>
                                  <h6 className="text-sm font-medium text-gray-900">{connection.connection_number || connection.icp_number}</h6>
                                  <p className="text-sm text-gray-600 capitalize">{connection.service_type}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                {getConnectionStatusBadge(connection.status)}
                              </div>
                            </div>
                            
                            {connection.address && (
                              <div className="flex items-center text-sm text-gray-600 mb-2">
                                <MapPin className="w-4 h-4 mr-2" />
                                <span>{connection.address}</span>
                              </div>
                            )}
                            
                            <div className="flex items-center justify-between text-sm text-gray-500">
                              <span>Connected: {formatDate(connection.connection_date)}</span>
                              <button className="text-indigo-600 hover:text-indigo-800 flex items-center" onClick={() => handleViewConnection(connection.id)}>
                                <ExternalLink className="w-3 h-3 mr-1" />
                                View Details
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Network className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No connections found</h3>
                        <p className="mt-1 text-sm text-gray-500">This user has no service connections.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'plans' && (
                  <div data-testid="user-plans-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Service Plans</h5>
                      {loadingStates.plans && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                    </div>
                    {userPlans.length > 0 ? (
                      <div className="space-y-3">
                        {userPlans.map((plan) => (
                          <div key={plan.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex text-left items-center justify-between mb-3">
                              <div className="flex items-center space-x-3">
                                <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                                  {getServiceIcon(plan.service_type)}
                                </div>
                                <div>
                                  <h6 className="text-sm font-medium text-gray-900">{plan.plan_name}</h6>
                                  <p className="text-sm text-gray-600 capitalize">{plan.service_type}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  plan.is_active 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {plan.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </div>
                            </div>
                            
                            {plan.monthly_cost && (
                              <div className="flex items-center text-sm text-gray-600 mb-2">
                                <CreditCard className="w-4 h-4 mr-2" />
                                <span>Monthly Cost: ${plan.monthly_cost}</span>
                              </div>
                            )}
                            
                            <div className="flex items-center justify-between text-sm text-gray-500">
                              <span>Started: {formatDate(plan.start_date)}</span>
                              <button className="text-indigo-600 hover:text-indigo-800 flex items-center" onClick={() => handleViewPlan(plan.id)}>
                                <ExternalLink className="w-3 h-3 mr-1" />
                                View Details
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Settings className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No plans found</h3>
                        <p className="mt-1 text-sm text-gray-500">This user has no active service plans.</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'activity' && (
                  <div data-testid="user-activity-section">
                    <h5 className="text-md text-left font-medium text-gray-900 mb-4">Recent Activity</h5>
                    <div className="text-center py-8">
                      <Activity className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">Activity tracking coming soon</h3>
                      <p className="mt-1 text-sm text-gray-500">User activity logs will be available in a future update.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <User className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">User not found</h3>
            <p className="mt-1 text-sm text-gray-500">The requested user could not be loaded.</p>
          </div>
        )}
      </div>
    </div>
  );
};

UserDetailModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  userId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export default UserDetailModal; 