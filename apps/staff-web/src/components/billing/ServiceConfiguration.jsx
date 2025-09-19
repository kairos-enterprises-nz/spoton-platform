import React, { useState } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import { 
  useServiceRegistry, 
  useCreateServiceRegistry, 
  useUpdateServiceRegistry 
} from '../../hooks/useBillingData';

const ServiceConfiguration = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingService, setEditingService] = useState(null);

  const { data: serviceRegistry, isLoading, error, refetch } = useServiceRegistry();
  const createMutation = useCreateServiceRegistry({
    onSuccess: () => {
      setShowCreateForm(false);
      refetch();
    }
  });
  const updateMutation = useUpdateServiceRegistry({
    onSuccess: () => {
      setEditingService(null);
      refetch();
    }
  });

  const handleCreateService = (formData) => {
    createMutation.mutate(formData);
  };

  const handleUpdateService = (formData) => {
    updateMutation.mutate({
      id: editingService.id,
      data: formData
    });
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-24 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Service Configuration</h2>
          <p className="text-sm text-gray-600 mt-1">
            Configure billing services and their handlers
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
          Add Service
        </button>
      </div>

      {/* Service Registry List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {Array.isArray(serviceRegistry) && serviceRegistry.length > 0 ? serviceRegistry.map((service) => (
            <li key={service.id}>
              <div className="px-4 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <CogIcon className="h-8 w-8 text-gray-400" />
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">
                          {service.name}
                        </p>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          service.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {service.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="flex items-center text-sm text-gray-500 mt-1">
                        <span className="uppercase">{service.service_code}</span>
                        <span className="mx-2">•</span>
                        <span className="capitalize">{service.billing_type}</span>
                        <span className="mx-2">•</span>
                        <span className="capitalize">{service.frequency}</span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        Handler: {service.billing_handler}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setEditingService(service)}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <PencilIcon className="-ml-0.5 mr-1 h-4 w-4" />
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            </li>
          )) : (
            <li>
              <div className="px-4 py-8 text-center">
                <CogIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-sm text-gray-500 mb-2">No service configurations found</p>
                <p className="text-xs text-gray-400">Add your first service to get started</p>
              </div>
            </li>
          )}
        </ul>
      </div>

      {/* Create Service Modal */}
      {showCreateForm && (
        <ServiceFormModal
          title="Add Service"
          onClose={() => setShowCreateForm(false)}
          onSubmit={handleCreateService}
          isLoading={createMutation.isLoading}
        />
      )}

      {/* Edit Service Modal */}
      {editingService && (
        <ServiceFormModal
          title="Edit Service"
          service={editingService}
          onClose={() => setEditingService(null)}
          onSubmit={handleUpdateService}
          isLoading={updateMutation.isLoading}
        />
      )}
    </div>
  );
};

// Service Form Modal Component
const ServiceFormModal = ({ title, service, onClose, onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    service_code: service?.service_code || '',
    name: service?.name || '',
    billing_type: service?.billing_type || 'prepaid',
    frequency: service?.frequency || 'monthly',
    is_active: service?.is_active ?? true,
    billing_handler: service?.billing_handler || '',
    tariff_handler: service?.tariff_handler || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                {title}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Service Code
                  </label>
                  <input
                    type="text"
                    value={formData.service_code}
                    onChange={(e) => setFormData(prev => ({ ...prev, service_code: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., electricity"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., Electricity"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Billing Type
                  </label>
                  <select
                    value={formData.billing_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, billing_type: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    required
                  >
                    <option value="prepaid">Prepaid</option>
                    <option value="postpaid">Postpaid</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Frequency
                  </label>
                  <select
                    value={formData.frequency}
                    onChange={(e) => setFormData(prev => ({ ...prev, frequency: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    required
                  >
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Billing Handler
                  </label>
                  <input
                    type="text"
                    value={formData.billing_handler}
                    onChange={(e) => setFormData(prev => ({ ...prev, billing_handler: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., finance.billing.handlers.electricity_handler.calculate_bill"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tariff Handler (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.tariff_handler}
                    onChange={(e) => setFormData(prev => ({ ...prev, tariff_handler: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., finance.pricing.handlers.electricity_tariff.calculate_tariff"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    id="is-active"
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is-active" className="ml-2 block text-sm text-gray-900">
                    Service is active
                  </label>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Save'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ServiceConfiguration;
