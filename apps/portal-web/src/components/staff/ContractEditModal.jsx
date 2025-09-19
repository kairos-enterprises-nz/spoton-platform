import { useState, useEffect } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const ContractEditModal = ({ isOpen, onClose, onSuccess, contract }) => {
  const [formData, setFormData] = useState({
    contract_type: '',
    service_name: '',
    description: '',
    status: '',
    start_date: '',
    end_date: '',
    initial_term_months: 12,
    auto_renewal: true,
    billing_frequency: 'monthly',
    setup_fee: 0,
    early_termination_fee: 0,
    customer: '',
    tenant: '',
    account: ''
  });
  
  const [customers, setCustomers] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && contract) {
      loadInitialData();
      // Populate form with contract data
      setFormData({
        contract_type: contract.contract_type || '',
        service_name: contract.service_name || '',
        description: contract.description || '',
        status: contract.status || '',
        start_date: contract.start_date || '',
        end_date: contract.end_date || '',
        initial_term_months: contract.initial_term_months || 12,
        auto_renewal: contract.auto_renewal !== undefined ? contract.auto_renewal : true,
        billing_frequency: contract.billing_frequency || 'monthly',
        setup_fee: contract.setup_fee || 0,
        early_termination_fee: contract.early_termination_fee || 0,
        customer: contract.customer?.id || '',
        tenant: contract.tenant?.id || '',
        account: contract.account?.id || ''
      });
      setErrors({});
    }
  }, [isOpen, contract]);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [tenantsResponse, usersResponse, accountsResponse] = await Promise.all([
        staffApiService.getTenants(),
        staffApiService.getUsers(),
        staffApiService.getAccounts()
      ]);
      
      setTenants(tenantsResponse.results || []);
      setCustomers(usersResponse.results || []);
      setAccounts(accountsResponse.results || []);
    } catch (error) {
      console.error('Failed to load initial data:', error);
      setErrors({ submit: 'Failed to load required data' });
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.service_name?.trim()) {
      newErrors.service_name = 'Service name is required';
    }

    if (!formData.customer) {
      newErrors.customer = 'Customer is required';
    }

    if (!formData.tenant) {
      newErrors.tenant = 'Tenant is required';
    }

    if (!formData.account) {
      newErrors.account = 'Account is required';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (formData.initial_term_months < 1) {
      newErrors.initial_term_months = 'Initial term must be at least 1 month';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : 
               type === 'number' ? parseFloat(value) || 0 : 
               value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await staffApiService.updateContract(contract.id, formData);
      onSuccess?.(response);
      onClose();
    } catch (error) {
      console.error('Failed to update contract:', error);
      if (error.status === 400 && error.data) {
        setErrors(error.data);
      } else {
        setErrors({ 
          submit: error.message || 'Failed to update contract. Please try again.' 
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  if (!isOpen || !contract) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Edit Contract - {contract.contract_number}
          </h3>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-6">
          {/* Submit Error */}
          {errors.submit && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-700">{errors.submit}</p>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Contract Type */}
            <div>
              <label htmlFor="contract_type" className="block text-sm font-medium text-gray-700">
                Contract Type *
              </label>
              <select
                id="contract_type"
                name="contract_type"
                value={formData.contract_type}
                onChange={handleInputChange}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.contract_type ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="electricity">Electricity</option>
                <option value="broadband">Broadband</option>
                <option value="mobile">Mobile</option>
                <option value="gas">Gas</option>
              </select>
              {errors.contract_type && (
                <p className="mt-1 text-sm text-red-600">{errors.contract_type}</p>
              )}
            </div>

            {/* Service Name */}
            <div>
              <label htmlFor="service_name" className="block text-sm font-medium text-gray-700">
                Service Name *
              </label>
              <input
                type="text"
                id="service_name"
                name="service_name"
                value={formData.service_name}
                onChange={handleInputChange}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.service_name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter service name"
              />
              {errors.service_name && (
                <p className="mt-1 text-sm text-red-600">{errors.service_name}</p>
              )}
            </div>

            {/* Customer */}
            <div>
              <label htmlFor="customer" className="block text-sm font-medium text-gray-700">
                Customer *
              </label>
              <select
                id="customer"
                name="customer"
                value={formData.customer}
                onChange={handleInputChange}
                disabled={isLoading}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.customer ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select customer...</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.full_name} ({customer.email})
                  </option>
                ))}
              </select>
              {errors.customer && (
                <p className="mt-1 text-sm text-red-600">{errors.customer}</p>
              )}
            </div>

            {/* Tenant */}
            <div>
              <label htmlFor="tenant" className="block text-sm font-medium text-gray-700">
                Tenant *
              </label>
              <select
                id="tenant"
                name="tenant"
                value={formData.tenant}
                onChange={handleInputChange}
                disabled={isLoading}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.tenant ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select tenant...</option>
                {tenants.map((tenant) => (
                  <option key={tenant.id} value={tenant.id}>
                    {tenant.name}
                  </option>
                ))}
              </select>
              {errors.tenant && (
                <p className="mt-1 text-sm text-red-600">{errors.tenant}</p>
              )}
            </div>

            {/* Account */}
            <div>
              <label htmlFor="account" className="block text-sm font-medium text-gray-700">
                Account *
              </label>
              <select
                id="account"
                name="account"
                value={formData.account}
                onChange={handleInputChange}
                disabled={isLoading}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.account ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select account...</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.account_number} - {account.account_type}
                  </option>
                ))}
              </select>
              {errors.account && (
                <p className="mt-1 text-sm text-red-600">{errors.account}</p>
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
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="draft">Draft</option>
                <option value="pending">Pending</option>
                <option value="active">Active</option>
                <option value="cancelled">Cancelled</option>
                <option value="expired">Expired</option>
              </select>
            </div>

            {/* Start Date */}
            <div>
              <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                Start Date *
              </label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                value={formData.start_date}
                onChange={handleInputChange}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.start_date ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.start_date && (
                <p className="mt-1 text-sm text-red-600">{errors.start_date}</p>
              )}
            </div>

            {/* End Date */}
            <div>
              <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                End Date
              </label>
              <input
                type="date"
                id="end_date"
                name="end_date"
                value={formData.end_date}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            {/* Initial Term Months */}
            <div>
              <label htmlFor="initial_term_months" className="block text-sm font-medium text-gray-700">
                Initial Term (Months)
              </label>
              <input
                type="number"
                id="initial_term_months"
                name="initial_term_months"
                value={formData.initial_term_months}
                onChange={handleInputChange}
                min="1"
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.initial_term_months ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.initial_term_months && (
                <p className="mt-1 text-sm text-red-600">{errors.initial_term_months}</p>
              )}
            </div>

            {/* Billing Frequency */}
            <div>
              <label htmlFor="billing_frequency" className="block text-sm font-medium text-gray-700">
                Billing Frequency
              </label>
              <select
                id="billing_frequency"
                name="billing_frequency"
                value={formData.billing_frequency}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="annually">Annually</option>
              </select>
            </div>

            {/* Setup Fee */}
            <div>
              <label htmlFor="setup_fee" className="block text-sm font-medium text-gray-700">
                Setup Fee (NZD)
              </label>
              <input
                type="number"
                id="setup_fee"
                name="setup_fee"
                value={formData.setup_fee}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            {/* Early Termination Fee */}
            <div>
              <label htmlFor="early_termination_fee" className="block text-sm font-medium text-gray-700">
                Early Termination Fee (NZD)
              </label>
              <input
                type="number"
                id="early_termination_fee"
                name="early_termination_fee"
                value={formData.early_termination_fee}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Enter contract description..."
            />
          </div>

          {/* Auto Renewal */}
          <div className="flex items-center">
            <input
              id="auto_renewal"
              name="auto_renewal"
              type="checkbox"
              checked={formData.auto_renewal}
              onChange={handleInputChange}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="auto_renewal" className="ml-2 block text-sm text-gray-900">
              Auto-renewal enabled
            </label>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end pt-6 border-t border-gray-200 space-x-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <Save className="h-4 w-4 mr-2" />
              {isSubmitting ? 'Updating...' : 'Update Contract'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

ContractEditModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  contract: PropTypes.object
};

export default ContractEditModal; 