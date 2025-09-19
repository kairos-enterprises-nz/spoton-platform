import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { X, Building2, Mail, Phone, MapPin, CreditCard, FileText, Settings } from 'lucide-react';
import staffApiService from '../../services/staffApi';

const TenantEditModal = ({ isOpen, onClose, onSuccess, tenantId }) => {
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    business_number: '',
    tax_number: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    currency: 'NZD',
    timezone: 'Pacific/Auckland',
    service_limits: {},
    is_active: true
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [serviceLimitsJson, setServiceLimitsJson] = useState('{}');

  useEffect(() => {
    if (isOpen && tenantId) {
      loadTenant();
    } else if (isOpen && !tenantId) {
      // Reset form data when modal opens without tenantId
      setFormData({
        name: '',
        slug: '',
        business_number: '',
        tax_number: '',
        contact_email: '',
        contact_phone: '',
        address: '',
        currency: 'NZD',
        timezone: 'Pacific/Auckland',
        service_limits: {},
        is_active: true
      });
      setServiceLimitsJson('{}');
      setErrors({});
    }
  }, [isOpen, tenantId]);

  const loadTenant = async () => {
    setIsLoading(true);
    try {
      const tenant = await staffApiService.getTenant(tenantId);
      setFormData({
        name: tenant.name || '',
        slug: tenant.slug || '',
        business_number: tenant.business_number || '',
        tax_number: tenant.tax_number || '',
        contact_email: tenant.contact_email || '',
        contact_phone: tenant.contact_phone || '',
        address: tenant.address || '',
        currency: tenant.currency || 'NZD',
        timezone: tenant.timezone || 'Pacific/Auckland',
        service_limits: tenant.service_limits || {},
        is_active: tenant.is_active !== undefined ? tenant.is_active : true
      });
      setServiceLimitsJson(JSON.stringify(tenant.service_limits || {}, null, 2));
    } catch (error) {
      console.error('Failed to load tenant:', error);
      setErrors({ submit: error.message || 'Failed to load tenant data' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleServiceLimitsChange = (e) => {
    const value = e.target.value;
    setServiceLimitsJson(value);
    
    try {
      const parsed = JSON.parse(value);
      setFormData(prev => ({ ...prev, service_limits: parsed }));
      if (errors.service_limits) {
        setErrors(prev => ({ ...prev, service_limits: '' }));
      }
          } catch {
        setErrors(prev => ({ ...prev, service_limits: 'Invalid JSON format' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) newErrors.name = 'Company name is required';
    if (!formData.slug.trim()) newErrors.slug = 'Slug is required';
    if (!formData.business_number.trim()) newErrors.business_number = 'Business number is required';
    if (!formData.tax_number.trim()) newErrors.tax_number = 'Tax number is required';
    if (!formData.contact_email.trim()) newErrors.contact_email = 'Contact email is required';
    if (!formData.contact_phone.trim()) newErrors.contact_phone = 'Contact phone is required';
    if (!formData.address.trim()) newErrors.address = 'Address is required';
    
    if (formData.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = 'Please enter a valid email address';
    }
    if (formData.slug && !/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
    }

    // Validate service_limits JSON
    try {
      JSON.parse(serviceLimitsJson);
    } catch {
      newErrors.service_limits = 'Invalid JSON format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!tenantId) {
      setErrors({ submit: 'No tenant selected for editing' });
      return;
    }
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const response = await staffApiService.updateTenant(tenantId, formData);
      onSuccess?.(response);
      onClose();
    } catch (error) {
      console.error('Failed to update tenant:', error);
      setErrors({ submit: error.message || 'Failed to update tenant' });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between pb-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Building2 className="w-5 h-5 mr-2 text-indigo-600" />
            Edit Tenant
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="ml-2 text-gray-600">Loading tenant data...</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-6">
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-sm text-red-600">{errors.submit}</p>
              </div>
            )}

            {/* Basic Information */}
            <div className="space-y-4">
              <h4 className="text-md text-left font-medium text-gray-900">Basic Information</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      errors.name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter company name"
                  />
                  {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
                </div>

                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    Slug *
                  </label>
                  <input
                    type="text"
                    name="slug"
                    value={formData.slug}
                    onChange={handleChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      errors.slug ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="company-slug"
                  />
                  {errors.slug && <p className="mt-1 text-sm text-red-600">{errors.slug}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    <FileText className="w-4 h-4 inline mr-1" />
                    Business Number *
                </label>
                <input
                  type="text"
                  name="business_number"
                  value={formData.business_number}
                  onChange={handleChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      errors.business_number ? 'border-red-300' : 'border-gray-300'
                    }`}
                  placeholder="Business registration number"
                />
                  {errors.business_number && <p className="mt-1 text-sm text-red-600">{errors.business_number}</p>}
                </div>

                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    <FileText className="w-4 h-4 inline mr-1" />
                    Tax Number *
                  </label>
                  <input
                    type="text"
                    name="tax_number"
                    value={formData.tax_number}
                    onChange={handleChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      errors.tax_number ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Tax identification number"
                  />
                  {errors.tax_number && <p className="mt-1 text-sm text-red-600">{errors.tax_number}</p>}
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-4">
              <h4 className="text-md text-left font-medium text-gray-900">Contact Information</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    <Mail className="w-4 h-4 inline mr-1" />
                    Contact Email *
                  </label>
                  <input
                    type="email"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      errors.contact_email ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="contact@company.com"
                  />
                  {errors.contact_email && <p className="mt-1 text-sm text-red-600">{errors.contact_email}</p>}
                </div>

                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    <Phone className="w-4 h-4 inline mr-1" />
                    Contact Phone *
                  </label>
                  <input
                    type="tel"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleChange}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      errors.contact_phone ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="+64 9 123 4567"
                  />
                  {errors.contact_phone && <p className="mt-1 text-sm text-red-600">{errors.contact_phone}</p>}
                </div>
              </div>

              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                <MapPin className="w-4 h-4 inline mr-1" />
                  Address *
                </label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  rows={3}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                    errors.address ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Full business address"
                />
                {errors.address && <p className="mt-1 text-sm text-red-600">{errors.address}</p>}
              </div>
            </div>

            {/* Settings */}
            <div className="space-y-4">
              <h4 className="text-md text-left font-medium text-gray-900">Settings</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    <CreditCard className="w-4 h-4 inline mr-1" />
                    Currency *
                  </label>
                  <select
                    name="currency"
                    value={formData.currency}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="NZD">NZD - New Zealand Dollar</option>
                    <option value="AUD">AUD - Australian Dollar</option>
                    <option value="USD">USD - US Dollar</option>
                    <option value="EUR">EUR - Euro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    Timezone *
                  </label>
                  <select
                    name="timezone"
                    value={formData.timezone}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="Pacific/Auckland">Pacific/Auckland</option>
                    <option value="Australia/Sydney">Australia/Sydney</option>
                    <option value="America/New_York">America/New_York</option>
                    <option value="Europe/London">Europe/London</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                  <Settings className="w-4 h-4 inline mr-1" />
                  Service Limits (JSON)
                </label>
                <textarea
                  value={serviceLimitsJson}
                  onChange={handleServiceLimitsChange}
                  rows={4}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm ${
                    errors.service_limits ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder='{"max_users": 100, "max_connections": 50, "storage_gb": 10}'
                />
                {errors.service_limits && <p className="mt-1 text-sm text-red-600">{errors.service_limits}</p>}
                <p className="mt-1 text-xs text-gray-500">
                  Define service limits as JSON (e.g., max users, connections, storage)
                </p>
              </div>

              <div className="flex items-center mt-2 text-left text-sm text-gray-700">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label className="ml-2 text-sm text-gray-700">
                  Active (tenant can access the system)
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Updating...' : 'Update Tenant'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

TenantEditModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  tenantId: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
}; 

export default TenantEditModal; 