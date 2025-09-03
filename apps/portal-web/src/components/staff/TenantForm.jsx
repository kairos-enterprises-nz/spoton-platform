import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLoader } from '../../context/LoaderContext';
import staffApiService from '../../services/staffApi';
import { 
  Building2, 
  Mail, 
  Phone, 
  MapPin, 
  Globe, 
  DollarSign,
  Clock,
  AlertCircle,
  CheckCircle,
  Save,
  X
} from 'lucide-react';

const TenantForm = ({ tenantId = null, onSubmit, onCancel }) => {
  const navigate = useNavigate();
  const { setLoading } = useLoader();
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    contact_email: '',
    contact_phone: '',
    website: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'New Zealand',
    timezone: 'Pacific/Auckland',
    currency: 'NZD',
    business_type: '',
    license_number: '',
    is_active: true,
    settings: {
      max_users: 1000,
      max_contracts: 5000,
      features: {
        energy_management: true,
        billing: true,
        analytics: true
      }
    }
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditing, setIsEditing] = useState(!!tenantId);

  useEffect(() => {
    if (tenantId) {
      loadTenant();
    }
  }, [tenantId]);

  const loadTenant = async () => {
    setLoading(true);
    try {
      const tenant = await staffApiService.getTenant(tenantId);
      setFormData({
        ...tenant,
        settings: tenant.settings || formData.settings
      });
    } catch (error) {
      console.error('Failed to load tenant:', error);
      setErrors({ general: 'Failed to load tenant data' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (name.includes('.')) {
      // Handle nested properties
      const [parent, child] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: type === 'checkbox' ? checked : value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
    
    // Clear errors for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const generateSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim('-');
  };

  const handleNameChange = (e) => {
    const name = e.target.value;
    setFormData(prev => ({
      ...prev,
      name,
      slug: !isEditing ? generateSlug(name) : prev.slug
    }));
    
    if (errors.name) {
      setErrors(prev => ({ ...prev, name: null }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Company name is required';
    }

    if (!formData.slug.trim()) {
      newErrors.slug = 'Slug is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
    }

    if (!formData.contact_email.trim()) {
      newErrors.contact_email = 'Contact email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = 'Please enter a valid email address';
    }

    if (formData.contact_phone && !/^[\+]?[0-9\s\-\(\)]+$/.test(formData.contact_phone)) {
      newErrors.contact_phone = 'Please enter a valid phone number';
    }

    if (formData.website && !/^https?:\/\/.+/.test(formData.website)) {
      newErrors.website = 'Website must start with http:// or https://';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      let result;
      if (isEditing) {
        result = await staffApiService.updateTenant(tenantId, formData);
      } else {
        result = await staffApiService.createTenant(formData);
      }

      if (onSubmit) {
        onSubmit(result);
      } else {
        navigate('/staff/tenants');
      }
    } catch (error) {
      console.error('Failed to save tenant:', error);
      if (error.message.includes('already exists')) {
        setErrors({ slug: 'This slug is already taken' });
      } else {
        setErrors({ general: error.message || 'Failed to save tenant' });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate('/staff/tenants');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900 flex items-center">
                <Building2 className="w-5 h-5 mr-2 text-indigo-600" />
                {isEditing ? 'Edit Tenant' : 'Create New Tenant'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {isEditing ? 'Update tenant information and settings' : 'Add a new utility company to the platform'}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleCancel}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4 mr-2" />
                {isSubmitting ? 'Saving...' : 'Save Tenant'}
              </button>
            </div>
          </div>
        </div>

        {/* General Error */}
        {errors.general && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{errors.general}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Basic Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Company Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleNameChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.name ? 'border-red-300 focus:border-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="e.g., Auckland Energy"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="slug" className="block text-sm font-medium text-gray-700 mb-1">
                Slug *
              </label>
              <input
                type="text"
                id="slug"
                name="slug"
                value={formData.slug}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.slug ? 'border-red-300 focus:border-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="e.g., auckland-energy"
              />
              {errors.slug && <p className="mt-1 text-sm text-red-600">{errors.slug}</p>}
              <p className="mt-1 text-xs text-gray-500">Used in URLs and API endpoints</p>
            </div>

            <div>
              <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700 mb-1">
                <Mail className="w-4 h-4 inline mr-1" />
                Contact Email *
              </label>
              <input
                type="email"
                id="contact_email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.contact_email ? 'border-red-300 focus:border-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="admin@company.com"
              />
              {errors.contact_email && <p className="mt-1 text-sm text-red-600">{errors.contact_email}</p>}
            </div>

            <div>
              <label htmlFor="contact_phone" className="block text-sm font-medium text-gray-700 mb-1">
                <Phone className="w-4 h-4 inline mr-1" />
                Contact Phone
              </label>
              <input
                type="tel"
                id="contact_phone"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.contact_phone ? 'border-red-300 focus:border-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="+64 9 123 4567"
              />
              {errors.contact_phone && <p className="mt-1 text-sm text-red-600">{errors.contact_phone}</p>}
            </div>

            <div>
              <label htmlFor="website" className="block text-sm font-medium text-gray-700 mb-1">
                <Globe className="w-4 h-4 inline mr-1" />
                Website
              </label>
              <input
                type="url"
                id="website"
                name="website"
                value={formData.website}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  errors.website ? 'border-red-300 focus:border-red-500' : 'border-gray-300 focus:border-indigo-500'
                }`}
                placeholder="https://www.company.com"
              />
              {errors.website && <p className="mt-1 text-sm text-red-600">{errors.website}</p>}
            </div>

            <div>
              <label htmlFor="business_type" className="block text-sm font-medium text-gray-700 mb-1">
                Business Type
              </label>
              <select
                id="business_type"
                name="business_type"
                value={formData.business_type}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select business type</option>
                <option value="electricity_distributor">Electricity Distributor</option>
                <option value="electricity_retailer">Electricity Retailer</option>
                <option value="gas_distributor">Gas Distributor</option>
                <option value="gas_retailer">Gas Retailer</option>
                <option value="broadband_provider">Broadband Provider</option>
                <option value="mobile_provider">Mobile Provider</option>
                <option value="multi_utility">Multi-Utility</option>
              </select>
            </div>
          </div>
        </div>

        {/* Address Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <MapPin className="w-5 h-5 mr-2" />
            Address Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
                Street Address
              </label>
              <input
                type="text"
                id="address"
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="123 Main Street"
              />
            </div>

            <div>
              <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                City
              </label>
              <input
                type="text"
                id="city"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Auckland"
              />
            </div>

            <div>
              <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                State/Region
              </label>
              <input
                type="text"
                id="state"
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Auckland"
              />
            </div>

            <div>
              <label htmlFor="postal_code" className="block text-sm font-medium text-gray-700 mb-1">
                Postal Code
              </label>
              <input
                type="text"
                id="postal_code"
                name="postal_code"
                value={formData.postal_code}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="1010"
              />
            </div>

            <div>
              <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
                Country
              </label>
              <select
                id="country"
                name="country"
                value={formData.country}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="New Zealand">New Zealand</option>
                <option value="Australia">Australia</option>
                <option value="United States">United States</option>
                <option value="Canada">Canada</option>
                <option value="United Kingdom">United Kingdom</option>
              </select>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            System Settings
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-1">
                Timezone
              </label>
              <select
                id="timezone"
                name="timezone"
                value={formData.timezone}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="Pacific/Auckland">Pacific/Auckland</option>
                <option value="Australia/Sydney">Australia/Sydney</option>
                <option value="America/New_York">America/New_York</option>
                <option value="Europe/London">Europe/London</option>
                <option value="UTC">UTC</option>
              </select>
            </div>

            <div>
              <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Currency
              </label>
              <select
                id="currency"
                name="currency"
                value={formData.currency}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="NZD">NZD - New Zealand Dollar</option>
                <option value="AUD">AUD - Australian Dollar</option>
                <option value="USD">USD - US Dollar</option>
                <option value="GBP">GBP - British Pound</option>
                <option value="EUR">EUR - Euro</option>
              </select>
            </div>

            <div>
              <label htmlFor="license_number" className="block text-sm font-medium text-gray-700 mb-1">
                License Number
              </label>
              <input
                type="text"
                id="license_number"
                name="license_number"
                value={formData.license_number}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="e.g., NZ-ELEC-001"
              />
            </div>
          </div>

          {/* Status Toggle */}
          <div className="mt-6">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                name="is_active"
                checked={formData.is_active}
                onChange={handleInputChange}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                <CheckCircle className="w-4 h-4 inline mr-1 text-green-500" />
                Active tenant (users can log in and access services)
              </label>
            </div>
          </div>
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={handleCancel}
            className="px-6 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Saving...' : (isEditing ? 'Update Tenant' : 'Create Tenant')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TenantForm; 