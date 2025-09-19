import { useState, useEffect } from 'react';
import { Zap, Wifi, Phone, MapPin, Settings, Plus, Edit, Trash2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import staffApiService from '../../services/staffApi';

const ConnectionManagement = ({ accountId, onConnectionChange }) => {
  const [connections, setConnections] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    if (accountId) {
      loadConnections();
    }
  }, [accountId]);

  const loadConnections = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Get connections for this account
      const response = await staffApiService.getAccountConnections(accountId);
      setConnections(response.results || response || []);
    } catch (error) {
      console.error('Failed to load connections:', error);
      setError(error.message || 'Failed to load connections');
    } finally {
      setIsLoading(false);
    }
  };

  const getServiceIcon = (serviceType) => {
    switch (serviceType) {
      case 'electricity':
        return <Zap className="h-5 w-5 text-yellow-500" />;
      case 'broadband':
        return <Wifi className="h-5 w-5 text-purple-500" />;
      case 'mobile':
        return <Phone className="h-5 w-5 text-blue-500" />;
      default:
        return <Settings className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'active': { color: 'green', icon: CheckCircle, label: 'Active' },
      'pending': { color: 'yellow', icon: Clock, label: 'Pending' },
      'inactive': { color: 'red', icon: AlertCircle, label: 'Inactive' },
      'switching': { color: 'blue', icon: Clock, label: 'Switching' },
    };

    const statusInfo = statusMap[status] || statusMap['inactive'];
    const Icon = statusInfo.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${statusInfo.color}-100 text-${statusInfo.color}-800`}>
        <Icon className="w-3 h-3 mr-1" />
        {statusInfo.label}
      </span>
    );
  };

  const handleCreateConnection = () => {
    setShowCreateModal(true);
  };

  const handleEditConnection = (connection) => {
    setSelectedConnection(connection);
    setShowEditModal(true);
  };

  const handleDeleteConnection = async (connectionId) => {
    if (!confirm('Are you sure you want to delete this connection?')) return;
    
    try {
      await staffApiService.deleteConnection(connectionId);
      loadConnections();
      if (onConnectionChange) onConnectionChange();
    } catch (error) {
      console.error('Failed to delete connection:', error);
      setError(error.message || 'Failed to delete connection');
    }
  };

  const handleConnectionSuccess = () => {
    loadConnections();
    if (onConnectionChange) onConnectionChange();
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedConnection(null);
  };

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Service Connections</h3>
          <button
            onClick={handleCreateConnection}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Connection
          </button>
        </div>
      </div>

      {error && (
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="divide-y divide-gray-200">
        {connections.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <Settings className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No connections</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new service connection.
            </p>
            <div className="mt-6">
              <button
                onClick={handleCreateConnection}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Connection
              </button>
            </div>
          </div>
        ) : (
          connections.map((connection) => (
            <div key={connection.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getServiceIcon(connection.service_type)}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 capitalize">
                      {connection.service_type} Service
                    </h4>
                    <p className="text-sm text-gray-500">
                      {connection.connection_identifier}
                    </p>
                    {connection.service_address && (
                      <p className="text-xs text-gray-400 flex items-center mt-1">
                        <MapPin className="h-3 w-3 mr-1" />
                        {connection.service_address.address_line1}, {connection.service_address.city}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  {getStatusBadge(connection.status)}
                  
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => handleEditConnection(connection)}
                      className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteConnection(connection.id)}
                      className="p-1 text-gray-400 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Service-specific details */}
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-500">
                {connection.service_type === 'electricity' && connection.service_details && (
                  <>
                    {connection.service_details.icp_code && (
                      <div>
                        <span className="font-medium">ICP:</span> {connection.service_details.icp_code}
                      </div>
                    )}
                    {connection.service_details.gxp_code && (
                      <div>
                        <span className="font-medium">GXP:</span> {connection.service_details.gxp_code}
                      </div>
                    )}
                    {connection.service_details.network_code && (
                      <div>
                        <span className="font-medium">Network:</span> {connection.service_details.network_code}
                      </div>
                    )}
                  </>
                )}
                
                {connection.service_type === 'broadband' && connection.service_details && (
                  <>
                    {connection.service_details.ont_serial && (
                      <div>
                        <span className="font-medium">ONT:</span> {connection.service_details.ont_serial}
                      </div>
                    )}
                    {connection.service_details.circuit_id && (
                      <div>
                        <span className="font-medium">Circuit:</span> {connection.service_details.circuit_id}
                      </div>
                    )}
                    {connection.service_details.connection_type && (
                      <div>
                        <span className="font-medium">Type:</span> {connection.service_details.connection_type}
                      </div>
                    )}
                  </>
                )}
                
                {connection.service_type === 'mobile' && connection.service_details && (
                  <>
                    {connection.service_details.mobile_number && (
                      <div>
                        <span className="font-medium">Number:</span> {connection.service_details.mobile_number}
                      </div>
                    )}
                    {connection.service_details.sim_id && (
                      <div>
                        <span className="font-medium">SIM:</span> {connection.service_details.sim_id}
                      </div>
                    )}
                    {connection.service_details.imei && (
                      <div>
                        <span className="font-medium">IMEI:</span> {connection.service_details.imei}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Plan information */}
              {connection.plan && (
                <div className="mt-3 p-3 bg-gray-50 rounded-md">
                  <h5 className="text-xs font-medium text-gray-900 mb-1">Current Plan</h5>
                  <div className="text-xs text-gray-600">
                    <div className="font-medium">{connection.plan.name}</div>
                    <div className="flex items-center justify-between mt-1">
                      <span>Type: {connection.plan.plan_type}</span>
                      {connection.plan.base_rate && (
                        <span className="font-medium">${connection.plan.base_rate}/month</span>
                      )}
                    </div>
                    {connection.plan.download_speed && (
                      <div className="mt-1">
                        Speed: {connection.plan.download_speed} down / {connection.plan.upload_speed} up
                      </div>
                    )}
                    {connection.plan.data_allowance && (
                      <div className="mt-1">
                        Data: {connection.plan.data_allowance}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Create Connection Modal */}
      {showCreateModal && (
        <ConnectionCreateModal
          accountId={accountId}
          onSuccess={handleConnectionSuccess}
          onCancel={() => setShowCreateModal(false)}
        />
      )}

      {/* Edit Connection Modal */}
      {showEditModal && selectedConnection && (
        <ConnectionEditModal
          connection={selectedConnection}
          onSuccess={handleConnectionSuccess}
          onCancel={() => {
            setShowEditModal(false);
            setSelectedConnection(null);
          }}
        />
      )}
    </div>
  );
};

// Placeholder modals - would be implemented separately
const ConnectionCreateModal = ({ accountId, onSuccess, onCancel }) => (
  <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Create New Connection</h3>
      <p className="text-gray-600 mb-4">Connection creation modal would be implemented here.</p>
      <div className="flex justify-end space-x-3">
        <button onClick={onCancel} className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400">
          Cancel
        </button>
        <button onClick={onSuccess} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
          Create
        </button>
      </div>
    </div>
  </div>
);

const ConnectionEditModal = ({ connection, onSuccess, onCancel }) => (
  <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Edit Connection</h3>
      <p className="text-gray-600 mb-4">Editing {connection.service_type} connection.</p>
      <div className="flex justify-end space-x-3">
        <button onClick={onCancel} className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400">
          Cancel
        </button>
        <button onClick={onSuccess} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
          Update
        </button>
      </div>
    </div>
  </div>
);

export default ConnectionManagement; 