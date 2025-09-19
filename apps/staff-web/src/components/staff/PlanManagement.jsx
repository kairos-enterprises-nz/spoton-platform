import { useState, useEffect } from 'react';
import { Zap, Wifi, Phone, DollarSign, Calendar, Users, Plus, Edit, Trash2, CheckCircle, AlertCircle } from 'lucide-react';
import staffApiService from '../../services/staffApi';

const PlanManagement = ({ onPlanChange }) => {
  const [plans, setPlans] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await staffApiService.getPlans();
      setPlans(response.results || response || []);
    } catch (error) {
      console.error('Failed to load plans:', error);
      setError(error.message || 'Failed to load plans');
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
        return <DollarSign className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'active': { color: 'green', icon: CheckCircle, label: 'Active' },
      'inactive': { color: 'red', icon: AlertCircle, label: 'Inactive' },
      'draft': { color: 'gray', icon: AlertCircle, label: 'Draft' },
    };

    const statusInfo = statusMap[status] || statusMap['draft'];
    const Icon = statusInfo.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${statusInfo.color}-100 text-${statusInfo.color}-800`}>
        <Icon className="w-3 h-3 mr-1" />
        {statusInfo.label}
      </span>
    );
  };

  const filteredPlans = plans.filter(plan => {
    if (filterType === 'all') return true;
    return plan.service_type === filterType;
  });

  const handleCreatePlan = () => {
    setShowCreateModal(true);
  };

  const handleEditPlan = (plan) => {
    setSelectedPlan(plan);
    setShowEditModal(true);
  };

  const handleDeletePlan = async (planId) => {
    if (!confirm('Are you sure you want to delete this plan?')) return;
    
    try {
      await staffApiService.deletePlan(planId);
      loadPlans();
      if (onPlanChange) onPlanChange();
    } catch (error) {
      console.error('Failed to delete plan:', error);
      setError(error.message || 'Failed to delete plan');
    }
  };

  const handlePlanSuccess = () => {
    loadPlans();
    if (onPlanChange) onPlanChange();
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedPlan(null);
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
          <h3 className="text-lg font-medium text-gray-900">Service Plans</h3>
          <button
            onClick={handleCreatePlan}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Plan
          </button>
        </div>
        
        {/* Filter tabs */}
        <div className="mt-4">
          <nav className="flex space-x-8">
            {[
              { key: 'all', label: 'All Plans' },
              { key: 'electricity', label: 'Electricity' },
              { key: 'broadband', label: 'Broadband' },
              { key: 'mobile', label: 'Mobile' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setFilterType(tab.key)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  filterType === tab.key
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
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
        {filteredPlans.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <DollarSign className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No plans</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new service plan.
            </p>
            <div className="mt-6">
              <button
                onClick={handleCreatePlan}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Plan
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
            {filteredPlans.map((plan) => (
              <div key={plan.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    {getServiceIcon(plan.service_type)}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{plan.name}</h4>
                      <p className="text-xs text-gray-500 capitalize">{plan.service_type}</p>
                    </div>
                  </div>
                  {getStatusBadge(plan.status)}
                </div>

                <div className="mt-3">
                  <p className="text-sm text-gray-600 line-clamp-2">{plan.description}</p>
                </div>

                {/* Plan pricing */}
                <div className="mt-4 space-y-2">
                  {plan.base_rate && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Base Rate:</span>
                      <span className="font-medium text-gray-900">${plan.base_rate}/month</span>
                    </div>
                  )}
                  
                  {plan.setup_fee && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Setup Fee:</span>
                      <span className="font-medium text-gray-900">${plan.setup_fee}</span>
                    </div>
                  )}
                </div>

                {/* Service-specific details */}
                <div className="mt-4 space-y-1 text-xs text-gray-500">
                  {plan.service_type === 'broadband' && (
                    <>
                      {plan.download_speed && (
                        <div>Speed: {plan.download_speed} down / {plan.upload_speed} up</div>
                      )}
                      {plan.data_allowance && (
                        <div>Data: {plan.data_allowance}</div>
                      )}
                    </>
                  )}
                  
                  {plan.service_type === 'mobile' && (
                    <>
                      {plan.data_allowance && (
                        <div>Data: {plan.data_allowance}</div>
                      )}
                      {plan.call_minutes && (
                        <div>Minutes: {plan.call_minutes}</div>
                      )}
                      {plan.text_messages && (
                        <div>Texts: {plan.text_messages}</div>
                      )}
                    </>
                  )}
                  
                  {plan.service_type === 'electricity' && (
                    <>
                      {plan.unit_rate && (
                        <div>Unit Rate: ${plan.unit_rate}/kWh</div>
                      )}
                      {plan.daily_charge && (
                        <div>Daily Charge: ${plan.daily_charge}</div>
                      )}
                    </>
                  )}
                </div>

                {/* Plan metadata */}
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-3">
                    {plan.active_connections_count !== undefined && (
                      <span className="flex items-center">
                        <Users className="h-3 w-3 mr-1" />
                        {plan.active_connections_count} active
                      </span>
                    )}
                    {plan.created_at && (
                      <span className="flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        {new Date(plan.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => handleEditPlan(plan)}
                      className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded"
                    >
                      <Edit className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => handleDeletePlan(plan.id)}
                      className="p-1 text-gray-400 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 rounded"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Plan Modal */}
      {showCreateModal && (
        <PlanCreateModal
          onSuccess={handlePlanSuccess}
          onCancel={() => setShowCreateModal(false)}
        />
      )}

      {/* Edit Plan Modal */}
      {showEditModal && selectedPlan && (
        <PlanEditModal
          plan={selectedPlan}
          onSuccess={handlePlanSuccess}
          onCancel={() => {
            setShowEditModal(false);
            setSelectedPlan(null);
          }}
        />
      )}
    </div>
  );
};

// Placeholder modals - would be implemented separately
const PlanCreateModal = ({ onSuccess, onCancel }) => (
  <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Create New Plan</h3>
      <p className="text-gray-600 mb-4">Plan creation modal would be implemented here.</p>
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

const PlanEditModal = ({ plan, onSuccess, onCancel }) => (
  <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Edit Plan</h3>
      <p className="text-gray-600 mb-4">Editing {plan.name}.</p>
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

export default PlanManagement; 