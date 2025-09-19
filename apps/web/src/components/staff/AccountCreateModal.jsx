import { useState, useEffect } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const AccountCreateModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    account_number: '',
    account_type: 'residential',
    billing_cycle: 'monthly',
    billing_day: 1,
    status: 'active',
    tenant: '',
    metadata: {}
  });
  
  const [tenants, setTenants] = useState([]);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadTenants();
      // Reset form when modal opens
      setFormData({
        account_number: '',
        account_type: 'residential',
        billing_cycle: 'monthly',
        billing_day: 1,
        status: 'active',
        tenant: '',
        metadata: {}
      });
      setErrors({});
    }
  }, [isOpen]);

  const loadTenants = async () => {
    setIsLoading(true);
    try {
      const response = await staffApiService.getTenants();
      setTenants(response.results || []);
    } catch (error) {
      console.error('Failed to load tenants:', error);
      setErrors({ tenant: 'Failed to load tenants' });
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.account_number?.trim()) {
      newErrors.account_number = 'Account number is required';
    }

    if (!formData.tenant) {
      newErrors.tenant = 'Tenant is required';
    }

    if (!formData.account_type) {
      newErrors.account_type = 'Account type is required';
    }

    if (!formData.billing_cycle) {
      newErrors.billing_cycle = 'Billing cycle is required';
    }

    if (formData.billing_day < 1 || formData.billing_day > 31) {
      newErrors.billing_day = 'Billing day must be between 1 and 31';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) || 0 : value
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
      const response = await staffApiService.createAccount(formData);
      onSuccess?.(response);
      onClose();
    } catch (error) {
      console.error('Failed to create account:', error);
      if (error.status === 400 && error.data) {
        // Handle validation errors from backend
        setErrors(error.data);
      } else {
        setErrors({ 
          submit: error.message || 'Failed to create account. Please try again.' 
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Create New Account</h3>
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
            {/* Account Number */}
            <div>
              <label htmlFor="account_number" className="block text-sm font-medium text-gray-700">
                Account Number *
              </label>
              <input
                type="text"
                id="account_number"
                name="account_number"
                value={formData.account_number}
                onChange={handleInputChange}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.account_number ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter account number"
              />
              {errors.account_number && (
                <p className="mt-1 text-sm text-red-600">{errors.account_number}</p>
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

            {/* Account Type */}
            <div>
              <label htmlFor="account_type" className="block text-sm font-medium text-gray-700">
                Account Type *
              </label>
              <select
                id="account_type"
                name="account_type"
                value={formData.account_type}
                onChange={handleInputChange}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.account_type ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="residential">Residential</option>
                <option value="commercial">Commercial</option>
                <option value="industrial">Industrial</option>
              </select>
              {errors.account_type && (
                <p className="mt-1 text-sm text-red-600">{errors.account_type}</p>
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
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            {/* Billing Cycle */}
            <div>
              <label htmlFor="billing_cycle" className="block text-sm font-medium text-gray-700">
                Billing Cycle *
              </label>
              <select
                id="billing_cycle"
                name="billing_cycle"
                value={formData.billing_cycle}
                onChange={handleInputChange}
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.billing_cycle ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="annually">Annually</option>
              </select>
              {errors.billing_cycle && (
                <p className="mt-1 text-sm text-red-600">{errors.billing_cycle}</p>
              )}
            </div>

            {/* Billing Day */}
            <div>
              <label htmlFor="billing_day" className="block text-sm font-medium text-gray-700">
                Billing Day
              </label>
              <input
                type="number"
                id="billing_day"
                name="billing_day"
                value={formData.billing_day}
                onChange={handleInputChange}
                min="1"
                max="31"
                className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                  errors.billing_day ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Day of month (1-31)"
              />
              {errors.billing_day && (
                <p className="mt-1 text-sm text-red-600">{errors.billing_day}</p>
              )}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
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
              disabled={isSubmitting}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Create Account
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

AccountCreateModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func
};

export default AccountCreateModal; 