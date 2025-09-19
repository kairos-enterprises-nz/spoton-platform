import { useState, useEffect } from 'react';
import { X, Zap, Wifi, Phone, Calendar, DollarSign } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const ConnectionPlanModal = ({ isOpen, onClose, onSuccess, connection = null }) => {
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [planHistory, setPlanHistory] = useState([]);

  useEffect(() => {
    if (isOpen && connection) {
      loadPlans();
      setSelectedPlan(connection.plan?.id || '');
      loadPlanHistory();
    }
  }, [isOpen, connection]);

  const loadPlans = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const plansData = await staffApiService.getPlans();
      // Filter plans by service type to match the connection
      const filteredPlans = (plansData || []).filter(plan => 
        plan.service_type === connection?.service_type
      );
      setPlans(filteredPlans);
      
      // If no API data, use sample plans
      if (!plansData || filteredPlans.length === 0) {
        const samplePlans = getSamplePlansForService(connection?.service_type);
        setPlans(samplePlans);
      }
    } catch (err) {
      setError(err.message || 'Failed to load plans');
      const samplePlans = getSamplePlansForService(connection?.service_type);
      setPlans(samplePlans);
    } finally {
      setIsLoading(false);
    }
  };

  const getSamplePlansForService = (serviceType) => {
    const allPlans = [
      { 
        id: '1', 
        service_type: 'electricity', 
        name: 'SpotOn Fixed Electricity', 
        monthly_charge: 150.00,
        base_rate: 0.25,
        description: 'Fixed rate electricity plan with competitive pricing',
        features: ['Fixed daily charge: $1.50', 'Unit rate: $0.25/kWh', '24/7 support']
      },
      { 
        id: '2', 
        service_type: 'electricity', 
        name: 'SpotOn Green Electricity', 
        monthly_charge: 165.00,
        base_rate: 0.28,
        description: '100% renewable electricity plan',
        features: ['100% renewable energy', 'Carbon neutral', 'Fixed daily charge: $1.60']
      },
      { 
        id: '3', 
        service_type: 'broadband', 
        name: 'SpotOn Fibre Basic', 
        monthly_charge: 69.99,
        download_speed: '100 Mbps',
        upload_speed: '20 Mbps',
        data_allowance: 'Unlimited',
        description: 'Basic fibre broadband for everyday use',
        features: ['100/20 Mbps speeds', 'Unlimited data', 'Free router']
      },
      { 
        id: '4', 
        service_type: 'broadband', 
        name: 'SpotOn Fibre Pro', 
        monthly_charge: 89.99,
        download_speed: '300 Mbps',
        upload_speed: '100 Mbps',
        data_allowance: 'Unlimited',
        description: 'High-speed fibre for families and professionals',
        features: ['300/100 Mbps speeds', 'Unlimited data', 'Premium router', 'Priority support']
      },
      { 
        id: '5', 
        service_type: 'mobile', 
        name: 'SpotOn Mobile Essential', 
        monthly_charge: 29.99,
        data_allowance: '5GB',
        call_minutes: 'Unlimited',
        text_messages: 'Unlimited',
        description: 'Essential mobile plan with good data allowance',
        features: ['5GB data', 'Unlimited calls & texts', 'No contract']
      },
      { 
        id: '6', 
        service_type: 'mobile', 
        name: 'SpotOn Mobile Plus', 
        monthly_charge: 49.99,
        data_allowance: '20GB',
        call_minutes: 'Unlimited',
        text_messages: 'Unlimited',
        description: 'Popular mobile plan with generous data',
        features: ['20GB data', 'Unlimited calls & texts', 'International roaming']
      }
    ];
    
    return allPlans.filter(plan => plan.service_type === serviceType);
  };

  const loadPlanHistory = () => {
    // Sample plan history for the connection
    const sampleHistory = [
      {
        plan_name: connection?.plan?.name || 'No Plan',
        assigned_date: connection?.assigned_date || '2024-06-01',
        monthly_charge: connection?.plan?.monthly_charge || 0,
        status: 'current'
      },
      {
        plan_name: 'SpotOn Starter Plan',
        assigned_date: '2024-01-15',
        end_date: connection?.assigned_date || '2024-06-01',
        monthly_charge: 39.99,
        status: 'previous'
      }
    ];
    setPlanHistory(sampleHistory);
  };

  const handlePlanChange = async () => {
    if (!selectedPlan) {
      setError('Please select a plan');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // API call to update connection plan
      await staffApiService.updateConnection(connection.id, {
        plan_id: selectedPlan
      });
      
      console.log(`Assigned plan ${selectedPlan} to connection ${connection.id}`);
      
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to update connection plan');
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

  if (!isOpen || !connection) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between pb-4 border-b">
          <div className="flex items-center space-x-3">
            {getServiceIcon(connection.service_type)}
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Manage Plan for Connection
              </h3>
              <p className="text-sm text-gray-500">
                {connection.connection_identifier} - {connection.account?.account_number}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="mt-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Current Connection Info */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Connection Details</h4>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Service Type:</span>
                  <span className="text-sm font-medium text-gray-900 capitalize">{connection.service_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Connection ID:</span>
                  <span className="text-sm font-medium text-gray-900">{connection.connection_identifier}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Account:</span>
                  <span className="text-sm font-medium text-gray-900">{connection.account?.account_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Status:</span>
                  <span className={`text-sm font-medium capitalize ${
                    connection.status === 'active' ? 'text-green-600' : 'text-yellow-600'
                  }`}>
                    {connection.status}
                  </span>
                </div>
                {connection.plan && (
                  <>
                    <div className="border-t pt-3 mt-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Current Plan:</span>
                        <span className="text-sm font-medium text-gray-900">{connection.plan.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Monthly Charge:</span>
                        <span className="text-sm font-medium text-gray-900">${connection.plan.monthly_charge}/month</span>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Plan History */}
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
                  <Calendar className="h-4 w-4 mr-2" />
                  Plan History
                </h4>
                <div className="space-y-3">
                  {planHistory.map((history, index) => (
                    <div key={index} className={`p-3 rounded-lg border ${
                      history.status === 'current' ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{history.plan_name}</div>
                          <div className="text-xs text-gray-500">
                            {history.status === 'current' ? 'Current' : 'Previous'} Plan
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">${history.monthly_charge}/month</div>
                          <div className="text-xs text-gray-500">
                            {new Date(history.assigned_date).toLocaleDateString()}
                            {history.end_date && ` - ${new Date(history.end_date).toLocaleDateString()}`}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Plan Selection */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-4">Available Plans</h4>
              
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                  <p className="mt-2 text-sm text-gray-500">Loading plans...</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {plans.map((plan) => (
                    <div
                      key={plan.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedPlan === plan.id
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedPlan(plan.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            <input
                              type="radio"
                              checked={selectedPlan === plan.id}
                              onChange={() => setSelectedPlan(plan.id)}
                              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                            />
                            <label className="ml-3 text-sm font-medium text-gray-900">
                              {plan.name}
                            </label>
                          </div>
                          <p className="mt-1 text-xs text-gray-500 ml-7">{plan.description}</p>
                          
                          {/* Plan Features */}
                          <div className="mt-2 ml-7">
                            {plan.features && plan.features.length > 0 && (
                              <ul className="text-xs text-gray-600 space-y-1">
                                {plan.features.slice(0, 3).map((feature, index) => (
                                  <li key={index} className="flex items-center">
                                    <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                                    {feature}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                        
                        <div className="text-right ml-4">
                          <div className="flex items-center text-lg font-semibold text-gray-900">
                            <DollarSign className="h-4 w-4" />
                            {plan.monthly_charge}
                          </div>
                          <div className="text-xs text-gray-500">per month</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end space-x-3 pt-6 mt-6 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              onClick={handlePlanChange}
              disabled={isLoading || !selectedPlan || selectedPlan === connection.plan?.id}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Updating...' : 'Update Plan'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

ConnectionPlanModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func.isRequired,
  connection: PropTypes.object
};

export default ConnectionPlanModal; 