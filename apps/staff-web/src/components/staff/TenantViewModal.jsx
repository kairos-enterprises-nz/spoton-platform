import { useState, useEffect } from 'react';
import { X, Building2, Mail, Phone, Globe, MapPin, CreditCard, Calendar, Users, FileText } from 'lucide-react';
import staffApiService from '../../services/staffApi';

const TenantViewModal = ({ isOpen, onClose, tenantId }) => {
  const [tenant, setTenant] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && tenantId) {
      loadTenant();
    }
  }, [isOpen, tenantId]);

  const loadTenant = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const tenantData = await staffApiService.getTenant(tenantId);
      setTenant(tenantData);
    } catch (error) {
      console.error('Failed to load tenant:', error);
      setError(error.message || 'Failed to load tenant data');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Intl.DateTimeFormat('en-NZ', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between pb-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Building2 className="w-5 h-5 mr-2 text-indigo-600" />
            Tenant Details
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
            <span className="ml-2 text-gray-600">Loading tenant details...</span>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mt-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : tenant ? (
          <div className="mt-4 space-y-6">
            {/* Header with tenant name and status */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl text-left font-bold text-gray-900">{tenant.name}</h2>
                  <p className="text-gray-600 text-left mt-1">{tenant.slug}</p>
                  {tenant.description && (
                    <p className="text-gray-700 mt-2">{tenant.description}</p>
                  )}
                </div>
                <div className="text-right">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    tenant.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {tenant.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </div>

            {/* Two column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-6">
                {/* Basic Information */}
                <div className="bg-white border rounded-lg p-4">
                  <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Basic Information
                  </h4>
                  <div className="space-y-3 text-left">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Business Number</label>
                      <p className="text-gray-900">{tenant.business_number || 'Not provided'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Currency</label>
                      <p className="text-gray-900 flex items-center">
                        <CreditCard className="w-4 h-4 mr-1" />
                        {tenant.currency || 'NZD'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Timezone</label>
                      <p className="text-gray-900">{tenant.timezone || 'Pacific/Auckland'}</p>
                    </div>
                  </div>
                </div>

                {/* Contact Information */}
                <div className="bg-white text-left border rounded-lg p-4">
                  <h4 className="text-md font-semibold text-gray-900 mb-4">Contact Information</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Email</label>
                      <p className="text-gray-900 flex items-center">
                        <Mail className="w-4 h-4 mr-1" />
                        <a href={`mailto:${tenant.contact_email}`} className="text-indigo-600 hover:text-indigo-800">
                          {tenant.contact_email || 'Not provided'}
                        </a>
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Phone</label>
                      <p className="text-gray-900 flex items-center">
                        <Phone className="w-4 h-4 mr-1" />
                        {tenant.contact_phone || 'Not provided'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Website</label>
                      <p className="text-gray-900 flex items-center">
                        <Globe className="w-4 h-4 mr-1" />
                        {tenant.website ? (
                          <a 
                            href={tenant.website} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-800"
                          >
                            {tenant.website}
                          </a>
                        ) : (
                          'Not provided'
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                {/* Address Information */}
                <div className="bg-white text-left border rounded-lg p-4">
                  <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    Address Information
                  </h4>
                  <div className="space-y-2">
                    {tenant.address && (
                      <p className="text-gray-900">{tenant.address}</p>
                    )}
                    <div className="flex space-x-4">
                      {tenant.city && (
                        <span className="text-gray-900">{tenant.city}</span>
                      )}
                      {tenant.state && (
                        <span className="text-gray-900">{tenant.state}</span>
                      )}
                      {tenant.postal_code && (
                        <span className="text-gray-900">{tenant.postal_code}</span>
                      )}
                    </div>
                    {tenant.country && (
                      <p className="text-gray-600">{tenant.country}</p>
                    )}
                    {!tenant.address && !tenant.city && !tenant.state && (
                      <p className="text-gray-500 italic">No address information provided</p>
                    )}
                  </div>
                </div>

                {/* System Information */}
                <div className="bg-white text-left border rounded-lg p-4">
                  <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    System Information
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Created</label>
                      <p className="text-gray-900">{formatDate(tenant.created_at)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Last Updated</label>
                      <p className="text-gray-900">{formatDate(tenant.updated_at)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Tenant ID</label>
                      <p className="text-gray-900 font-mono text-sm">{tenant.id}</p>
                    </div>
                  </div>
                </div>

                {/* Statistics */}
                {tenant.user_count !== undefined && (
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                      <Users className="w-4 h-4 mr-2" />
                      Statistics
                    </h4>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Total Users</label>
                        <p className="text-gray-900 text-lg font-semibold">{tenant.user_count || 0}</p>
                      </div>
                      {tenant.active_users !== undefined && (
                        <div>
                          <label className="text-sm font-medium text-gray-500">Active Users</label>
                          <p className="text-gray-900 text-lg font-semibold">{tenant.active_users || 0}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end pt-4 border-t">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Close
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default TenantViewModal; 