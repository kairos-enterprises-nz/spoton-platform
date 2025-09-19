import { useState, useEffect } from 'react';
import { X, Zap, Wifi, Phone } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const PlanCreateModal = ({ isOpen, onClose, onSuccess, plan = null, editingPlan = null }) => {
  const [formData, setFormData] = useState({
    service_type: '',
    name: '',
    plan_type: '',
    description: '',
    base_rate: '',
    is_active: true,
    monthly_charge: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const currentPlan = editingPlan || plan;
  const isEditing = !!currentPlan;

  useEffect(() => {
    if (currentPlan) {
      setFormData({
        service_type: currentPlan.service_type || '',
        name: currentPlan.name || '',
        plan_type: currentPlan.plan_type || '',
        description: currentPlan.description || '',
        base_rate: currentPlan.base_rate || '',
        is_active: currentPlan.is_active !== undefined ? currentPlan.is_active : true,
        monthly_charge: currentPlan.monthly_charge || ''
      });
    } else {
      setFormData({
        service_type: '',
        name: '',
        plan_type: '',
        description: '',
        base_rate: '',
        is_active: true,
        monthly_charge: ''
      });
    }
    setError(null);
  }, [currentPlan, isOpen]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      if (isEditing) {
        await staffApiService.updatePlan(currentPlan.id, formData);
      } else {
        await staffApiService.createPlan(formData);
      }
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'An error occurred while saving the plan');
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
              {isEditing ? 'Edit Plan' : 'Create New Plan'}
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

          {/* Plan Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Plan Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              placeholder="e.g., SpotOn Fixed Electricity"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Plan Type */}
          <div>
            <label htmlFor="plan_type" className="block text-sm font-medium text-gray-700">
              Plan Type
            </label>
            <input
              type="text"
              id="plan_type"
              name="plan_type"
              value={formData.plan_type}
              onChange={handleInputChange}
              placeholder="e.g., Fixed Rate, Fibre, Prepaid"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description *
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              required
              rows={3}
              placeholder="Plan description..."
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Base Rate */}
          <div>
            <label htmlFor="base_rate" className="block text-sm font-medium text-gray-700">
              Base Rate * ($)
            </label>
            <input
              type="number"
              step="0.01"
              id="base_rate"
              name="base_rate"
              value={formData.base_rate}
              onChange={handleInputChange}
              required
              placeholder="0.00"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Monthly Charge */}
          <div>
            <label htmlFor="monthly_charge" className="block text-sm font-medium text-gray-700">
              Monthly Charge ($)
            </label>
            <input
              type="number"
              step="0.01"
              id="monthly_charge"
              name="monthly_charge"
              value={formData.monthly_charge}
              onChange={handleInputChange}
              placeholder="0.00"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Active Status */}
          <div className="flex items-center">
            <input
              id="is_active"
              name="is_active"
              type="checkbox"
              checked={formData.is_active}
              onChange={handleInputChange}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
              Active Plan
            </label>
          </div>

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
              {isLoading ? 'Saving...' : (isEditing ? 'Update Plan' : 'Create Plan')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

PlanCreateModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func.isRequired,
  plan: PropTypes.object,
  editingPlan: PropTypes.object
};

export default PlanCreateModal; 