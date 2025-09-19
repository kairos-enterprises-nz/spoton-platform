import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { 
  X, CreditCard, Mail, Phone, Building2, MapPin, 
  Calendar, Clock, Users, FileText, Network,
  Activity, AlertCircle, CheckCircle, Edit, Trash2,
  Hash, Zap, Wifi, Smartphone, ExternalLink, User
} from 'lucide-react';
import staffApiService from '../../services/staffApi';

const AccountDetailModal = ({ isOpen, onClose, accountId, onEdit, onDelete }) => {
  const [accountData, setAccountData] = useState(null);
  const [accountUsers, setAccountUsers] = useState([]);
  const [accountContracts, setAccountContracts] = useState([]);
  const [accountConnections, setAccountConnections] = useState([]);
  const [accountAddresses, setAccountAddresses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loadingStates, setLoadingStates] = useState({
    users: false,
    contracts: false,
    connections: false,
    addresses: false
  });

  useEffect(() => {
    if (isOpen && accountId) {
      loadAccountData();
      loadAccountUsers();
      loadAccountContracts();
      loadAccountConnections();
      loadAccountAddresses();
    }
  }, [isOpen, accountId]);

  const loadAccountData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await staffApiService.getAccount(accountId);
      console.log('Account data loaded:', data);
      setAccountData(data);
    } catch (error) {
      console.error('Failed to load account data:', error);
      setError(error.message || 'Failed to load account data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAccountUsers = async () => {
    setLoadingStates(prev => ({ ...prev, users: true }));
    try {
      const data = await staffApiService.getAccountUsers(accountId);
      console.log('Account users loaded:', data);
      setAccountUsers(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Failed to load account users:', error);
      setAccountUsers([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, users: false }));
    }
  };

  const loadAccountContracts = async () => {
    setLoadingStates(prev => ({ ...prev, contracts: true }));
    try {
      const data = await staffApiService.getAccountContracts(accountId);
      console.log('Account contracts loaded:', data);
      setAccountContracts(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Failed to load account contracts:', error);
      setAccountContracts([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, contracts: false }));
    }
    };

  const loadAccountConnections = async () => {
    setLoadingStates(prev => ({ ...prev, connections: true }));
    try {
      const data = await staffApiService.getAccountConnections(accountId);
      console.log('Account connections loaded:', data);
      setAccountConnections(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Failed to load account connections:', error);
      setAccountConnections([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, connections: false }));
    }
  };

  const loadAccountAddresses = async () => {
    setLoadingStates(prev => ({ ...prev, addresses: true }));
    try {
      const data = await staffApiService.getAccountAddresses(accountId);
      console.log('Account addresses loaded:', data);
      setAccountAddresses(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Failed to load account addresses:', error);
      setAccountAddresses([]);
    } finally {
      setLoadingStates(prev => ({ ...prev, addresses: false }));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Intl.DateTimeFormat('en-NZ', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { color: 'green', icon: CheckCircle, label: 'Active' },
      inactive: { color: 'red', icon: AlertCircle, label: 'Inactive' },
      suspended: { color: 'yellow', icon: AlertCircle, label: 'Suspended' },
      pending: { color: 'blue', icon: Clock, label: 'Pending' }
    };

    const config = statusConfig[status] || statusConfig.inactive;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${config.color}-100 text-${config.color}-800`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
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

  const tabs = [
    { id: 'overview', name: 'Overview', icon: CreditCard },
    { id: 'users', name: 'Users', icon: Users, count: accountUsers.length },
    { id: 'contracts', name: 'Contracts', icon: FileText, count: accountContracts.length },
    { id: 'connections', name: 'Connections', icon: Network, count: accountConnections.length },
    { id: 'addresses', name: 'Addresses', icon: MapPin, count: accountAddresses.length },
    { id: 'activity', name: 'Activity', icon: Activity }
  ];

  const getTotalRelationships = () => {
    return accountUsers.length + accountContracts.length + accountConnections.length + accountAddresses.length;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white mb-10" data-testid="account-detail-modal">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div>
            <h3 className="text-xl text-left font-semibold text-gray-900">Account Details</h3>
            <p className="text-sm text-left text-gray-500">
              {accountData ? `#${accountData.account_number || accountData.id}` : 'Loading...'}
              {accountData && getTotalRelationships() > 0 && (
                <span className="ml-2 text-xs text-gray-400">
                  ({getTotalRelationships()} relationships)
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            {accountData && (
              <>
            <button
                  onClick={() => onEdit?.(accountData)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </button>
            <button
                  onClick={() => onDelete?.(accountData)}
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
        <div className="mt-6">
          {isLoading && !accountData ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <span className="ml-2 text-gray-600">Loading account details...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          ) : accountData ? (
            <>
              {/* Tabs */}
              <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                        className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                        <Icon className="w-4 h-4 mr-2" />
                        {tab.name}
                    {tab.count !== undefined && (
                          <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs">
                        {tab.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
        </div>

        {/* Tab Content */}
              <div className="min-h-[400px]">
          {activeTab === 'overview' && (
                  <div data-testid="account-overview-section">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Basic Information */}
                <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Basic Information</h4>
                        <div className="space-y-3">
                          <div className="flex items-center">
                            <Hash className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Account Number:</span>
                            <span className="text-sm font-medium text-gray-900 ml-2">
                              #{accountData.account_number || accountData.id}
                      </span>
                    </div>
                          <div className="flex items-center">
                            <CreditCard className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Type:</span>
                            <span className="text-sm font-medium text-gray-900 ml-2">
                              {accountData.account_type || 'Standard'}
                      </span>
                    </div>
                          <div className="flex items-center">
                            <span className="text-sm text-gray-600">Status:</span>
                            <span className="ml-2">{getStatusBadge(accountData.status)}</span>
                    </div>
                  </div>
                </div>

                      {/* Primary User */}
                <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Primary User</h4>
                        {accountData.primary_user ? (
                          <div className="space-y-3">
                            <div className="flex items-center">
                              <User className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">
                                {accountData.primary_user.first_name} {accountData.primary_user.last_name}
                      </span>
                    </div>
                            <div className="flex items-center">
                              <Mail className="w-4 h-4 text-gray-400 mr-2" />
                              <span className="text-sm text-gray-900">
                                {accountData.primary_user.email}
                      </span>
                    </div>
                            {accountData.primary_user.phone && (
                              <div className="flex items-center">
                                <Phone className="w-4 h-4 text-gray-400 mr-2" />
                                <span className="text-sm text-gray-900">
                                  {accountData.primary_user.phone}
                      </span>
                    </div>
                            )}
                  </div>
                        ) : (
                          <p className="text-sm text-gray-500">No primary user assigned</p>
                        )}
                </div>

                      {/* Tenant Information */}
                <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Tenant</h4>
                        {accountData.tenant ? (
                          <div className="space-y-3">
                            <div className="flex items-center">
                              <Building2 className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">
                                {accountData.tenant.name}
                      </span>
                    </div>
                            <div className="flex items-center">
                              <span className="text-sm text-gray-600">Slug:</span>
                              <span className="text-sm text-gray-900 ml-2">
                                {accountData.tenant.slug}
                      </span>
                    </div>
                  </div>
                        ) : (
                          <p className="text-sm text-gray-500">No tenant assigned</p>
                        )}
                      </div>

                      {/* Timestamps */}
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Timeline</h4>
                        <div className="space-y-3">
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Created:</span>
                            <span className="text-sm text-gray-900 ml-2">
                              {formatDate(accountData.created_at)}
                            </span>
                          </div>
                          <div className="flex items-center">
                            <Clock className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="text-sm text-gray-600">Updated:</span>
                            <span className="text-sm text-gray-900 ml-2">
                              {formatDate(accountData.updated_at)}
                            </span>
                          </div>
                        </div>
                    </div>
                  </div>
                </div>
              )}

                {activeTab === 'users' && (
                  <div data-testid="account-users-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Account Users</h5>
                      {loadingStates.users && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                    </div>
                    {accountUsers.length > 0 ? (
                      <div className="space-y-3">
                        {accountUsers.map((user) => (
                          <div key={user.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                          <div className="flex items-center">
                              <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                                  <span className="text-indigo-600 font-medium text-sm">
                                    {user.first_name?.[0]}{user.last_name?.[0]}
                                  </span>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {user.first_name} {user.last_name}
                              </div>
                              <div className="text-sm text-gray-500">{user.email}</div>
                                  {user.phone && (
                                    <div className="text-xs text-gray-400">{user.phone}</div>
                                  )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                }`}>
                                  {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                                <button className="text-indigo-600 hover:text-indigo-900 text-sm">
                                  <ExternalLink className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                        </div>
                    ) : (
                      <div className="text-center py-12">
                        <Users className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          This account has no associated users.
                        </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'contracts' && (
                  <div data-testid="account-contracts-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Account Contracts</h5>
                      {loadingStates.contracts && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                </div>
                    {accountContracts.length > 0 ? (
                      <div className="space-y-3">
                        {accountContracts.map((contract) => (
                          <div key={contract.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                  {getServiceIcon(contract.service_type)}
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">
                                    Contract #{contract.contract_number || contract.id}
                                </div>
                                <div className="text-sm text-gray-500">
                                    {contract.service_type} - {contract.plan_name}
                                  </div>
                                  <div className="text-xs text-gray-400">
                                    {formatDate(contract.start_date)} - {formatDate(contract.end_date)}
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                {getStatusBadge(contract.status)}
                                <button className="text-indigo-600 hover:text-indigo-900 text-sm">
                                  <ExternalLink className="w-4 h-4" />
                                </button>
                            </div>
                            </div>
                          </div>
                        ))}
                        </div>
                    ) : (
                      <div className="text-center py-12">
                        <FileText className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No contracts found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          This account has no associated contracts.
                        </p>
                </div>
              )}
            </div>
          )}

                {activeTab === 'connections' && (
                  <div data-testid="account-connections-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Account Connections</h5>
                      {loadingStates.connections && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                </div>
                    {accountConnections.length > 0 ? (
                      <div className="space-y-3">
                        {accountConnections.map((connection) => (
                          <div key={connection.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center">
                                <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                                  {getServiceIcon(connection.service_type)}
                </div>
                                <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                                    {connection.service_address || `Connection #${connection.id}`}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    {connection.service_type} - {connection.connection_type}
                                  </div>
                                  <div className="text-xs text-gray-400">
                                    ICP: {connection.icp_number || 'N/A'}
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                {getStatusBadge(connection.status)}
                                <button className="text-indigo-600 hover:text-indigo-900 text-sm">
                                  <ExternalLink className="w-4 h-4" />
                                </button>
                              </div>
                          </div>
                          </div>
                        ))}
                        </div>
                    ) : (
                      <div className="text-center py-12">
                        <Network className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No connections found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          This account has no associated connections.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'addresses' && (
                  <div data-testid="account-addresses-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Account Addresses</h5>
                      {loadingStates.addresses && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      )}
                    </div>
                    {accountAddresses.length > 0 ? (
                      <div className="space-y-3">
                        {accountAddresses.map((address) => (
                          <div key={address.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center">
                                <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                                  <MapPin className="w-5 h-5 text-purple-600" />
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900">
                                    {address.address_line1}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    {address.city}, {address.postal_code}
                                  </div>
                                  <div className="text-xs text-gray-400">
                                    {address.address_type} address
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  address.is_primary ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {address.is_primary ? 'Primary' : 'Secondary'}
                                </span>
                              </div>
                      </div>
                    </div>
                  ))}
                </div>
                    ) : (
                      <div className="text-center py-12">
                        <MapPin className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No addresses found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          This account has no associated addresses.
                        </p>
                      </div>
              )}
            </div>
          )}

          {activeTab === 'activity' && (
                  <div data-testid="account-activity-section">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-md text-left font-medium text-gray-900">Account Activity</h5>
                    </div>
                    <div className="text-center py-12">
                <Activity className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">Activity log coming soon</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Account activity tracking will be available in a future update.
                      </p>
              </div>
            </div>
          )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

AccountDetailModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  accountId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export default AccountDetailModal; 