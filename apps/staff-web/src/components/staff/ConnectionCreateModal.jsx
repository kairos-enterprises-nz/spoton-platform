import { useState, useEffect } from 'react';
import { X, Zap, Wifi, Phone } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const ConnectionCreateModal = ({ isOpen, onClose, onSuccess, connection = null, editingConnection = null, accounts = [], plans = [] }) => {
  const [formData, setFormData] = useState({
    service_type: '',
    connection_identifier: '',
    status: 'active',
    account_id: '',
    plan_id: '',
    icp_code: '',
    mobile_number: '',
    ont_serial: '',
    circuit_id: '',
    connection_type: '',
    service_details: {}
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const currentConnection = editingConnection || connection;
  const isEditing = !!currentConnection;

  useEffect(() => {
    if (currentConnection) {
              setFormData({
          service_type: currentConnection.service_type || '',
          connection_identifier: currentConnection.connection_identifier || '',
          status: currentConnection.status || 'active',
          account_id: currentConnection.account?.id || '',
          plan_id: currentConnection.plan?.id || '',
          icp_code: currentConnection.icp_code || '',
          mobile_number: currentConnection.mobile_number || '',
          ont_serial: currentConnection.ont_serial || '',
          circuit_id: currentConnection.circuit_id || '',
          connection_type: currentConnection.connection_type || '',
          service_details: currentConnection.service_details || {}
        });
    } else {
      setFormData({
        service_type: '',
        connection_identifier: '',
        status: 'active',
        account_id: '',
        plan_id: '',
        icp_code: '',
        mobile_number: '',
        ont_serial: '',
        circuit_id: '',
        connection_type: '',
        service_details: {}
      });
    }
    setError(null);
  }, [currentConnection, isOpen]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      if (isEditing) {
        await staffApiService.updateConnection(currentConnection.id, formData);
      } else {
        await staffApiService.createConnection(formData);
      }
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'An error occurred while saving the connection');
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
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between pb-4 border-b">
          <div className="flex items-center space-x-2">
            {getServiceIcon(formData.service_type)}
            <h3 className="text-lg font-medium text-gray-900">
              {isEditing ? 'Edit Connection' : 'Create New Connection'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Service Type */}
          <div>
            <label htmlFor="service_type" className="block text-sm font-medium text-gray-700">
              Service Type *
            </label>
            <select
              id="service_type"
              name="service_type"
              value={formData.service_type}
              onChange={handleInputChange}
              required
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select service type</option>
              <option value="electricity">Electricity</option>
              <option value="broadband">Broadband</option>
              <option value="mobile">Mobile</option>
            </select>
          </div>

          {/* Connection Identifier */}
          <div>
            <label htmlFor="connection_identifier" className="block text-sm font-medium text-gray-700">
              Connection Identifier *
            </label>
            <input
              type="text"
              id="connection_identifier"
              name="connection_identifier"
              value={formData.connection_identifier}
              onChange={handleInputChange}
              required
              placeholder={
                formData.service_type === 'electricity' ? 'ICP Number (e.g., ICP001024001)' :
                formData.service_type === 'broadband' ? 'ONT Serial (e.g., ONT001024BB)' :
                formData.service_type === 'mobile' ? 'Mobile Number (e.g., +64 21 001024)' :
                'Connection identifier'
              }
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Account */}
          <div>
            <label htmlFor="account_id" className="block text-sm font-medium text-gray-700">
              Account
            </label>
            <select
              id="account_id"
              name="account_id"
              value={formData.account_id}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select account</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_number} - {account.user?.email}
                </option>
              ))}
            </select>
          </div>

          {/* Plan Assignment */}
          <div>
            <label htmlFor="plan_id" className="block text-sm font-medium text-gray-700">
              Service Plan
            </label>
            <select
              id="plan_id"
              name="plan_id"
              value={formData.plan_id}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select service plan</option>
              {plans.filter(plan => plan.service_type === formData.service_type).map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} - ${plan.monthly_charge}/month
                </option>
              ))}
            </select>
            {formData.service_type && plans.filter(plan => plan.service_type === formData.service_type).length === 0 && (
              <p className="mt-1 text-sm text-gray-500">No plans available for {formData.service_type}</p>
            )}
          </div>

          {/* Status */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">
              Status
            </label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleInputChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="suspended">Suspended</option>
              <option value="disconnected">Disconnected</option>
            </select>
          </div>

          {/* Service-specific fields */}
          {formData.service_type === 'electricity' && (
            <div>
              <label htmlFor="icp_code" className="block text-sm font-medium text-gray-700">
                ICP Code
              </label>
              <input
                type="text"
                id="icp_code"
                name="icp_code"
                value={formData.icp_code}
                onChange={handleInputChange}
                placeholder="ICP001024001"
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          )}

          {formData.service_type === 'broadband' && (
            <>
              <div>
                <label htmlFor="ont_serial" className="block text-sm font-medium text-gray-700">
                  ONT Serial
                </label>
                <input
                  type="text"
                  id="ont_serial"
                  name="ont_serial"
                  value={formData.ont_serial}
                  onChange={handleInputChange}
                  placeholder="ONT001024BB"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="circuit_id" className="block text-sm font-medium text-gray-700">
                  Circuit ID
                </label>
                <input
                  type="text"
                  id="circuit_id"
                  name="circuit_id"
                  value={formData.circuit_id}
                  onChange={handleInputChange}
                  placeholder="CIR1024"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="connection_type" className="block text-sm font-medium text-gray-700">
                  Connection Type
                </label>
                <select
                  id="connection_type"
                  name="connection_type"
                  value={formData.connection_type}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select connection type</option>
                  <option value="fibre">Fibre</option>
                  <option value="adsl">ADSL</option>
                  <option value="vdsl">VDSL</option>
                  <option value="cable">Cable</option>
                </select>
              </div>
            </>
          )}

          {formData.service_type === 'mobile' && (
            <div>
              <label htmlFor="mobile_number" className="block text-sm font-medium text-gray-700">
                Mobile Number
              </label>
              <input
                type="text"
                id="mobile_number"
                name="mobile_number"
                value={formData.mobile_number}
                onChange={handleInputChange}
                placeholder="+64 21 001024"
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : (isEditing ? 'Update Connection' : 'Create Connection')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

ConnectionCreateModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func.isRequired,
  connection: PropTypes.object,
  editingConnection: PropTypes.object,
  accounts: PropTypes.array,
  plans: PropTypes.array
};

export default ConnectionCreateModal; 