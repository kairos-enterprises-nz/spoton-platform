import { useState, useEffect } from 'react';
import { X, User, Building, FileText, Search } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const PlanAssignmentModal = ({ isOpen, onClose, plan = null }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [searchTerm, setSearchTerm] = useState('');
  const [assignments, setAssignments] = useState({
    users: [],
    accounts: [],
    contracts: []
  });
  const [availableItems, setAvailableItems] = useState({
    users: [],
    accounts: [],
    contracts: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && plan) {
      loadData();
    }
  }, [isOpen, plan]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load current assignments and available items
      const [users, accounts, contracts] = await Promise.all([
        staffApiService.getUsers(),
        staffApiService.getAccounts(),
        staffApiService.getContracts()
      ]);

      console.log('PlanAssignmentModal - API responses:', { users, accounts, contracts });

      // Initialize empty assignments - in a real app, this would come from API
      setAssignments({
        users: [],
        accounts: [],
        contracts: []
      });
      
      // Use API data directly, set empty arrays if no data
      setAvailableItems({
        users: Array.isArray(users) ? users : [],
        accounts: Array.isArray(accounts) ? accounts : [],
        contracts: Array.isArray(contracts) ? contracts : []
      });

      console.log('PlanAssignmentModal - Using API data:', { 
        users: Array.isArray(users) ? users.length : 0, 
        accounts: Array.isArray(accounts) ? accounts.length : 0, 
        contracts: Array.isArray(contracts) ? contracts.length : 0
      });

    } catch (err) {
      console.error('PlanAssignmentModal - Error loading data:', err);
      setError(err.message || 'Failed to load assignment data');
      
      // Set empty arrays on error
      setAvailableItems({
        users: [],
        accounts: [],
        contracts: []
      });
      setAssignments({
        users: [],
        accounts: [],
        contracts: []
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssign = async (itemId, type) => {
    try {
      // API call to assign plan
      console.log(`Assigning plan ${plan.id} to ${type} ${itemId}`);
      
      // Update local state
      const available = availableItems[type];
      if (!Array.isArray(available)) {
        console.error(`PlanAssignmentModal - Cannot assign: availableItems[${type}] is not an array:`, available);
        setError(`Cannot assign ${type}: invalid data structure`);
        return;
      }

      const item = available.find(i => i.id === itemId);
      if (item) {
        const newAssignment = {
          ...item,
          assigned_date: new Date().toISOString().split('T')[0]
        };
        
        setAssignments(prev => ({
          ...prev,
          [type]: [...(prev[type] || []), newAssignment]
        }));
      }
    } catch (err) {
      setError(err.message || 'Failed to assign plan');
    }
  };

  const handleUnassign = async (itemId, type) => {
    try {
      // API call to unassign plan
      console.log(`Unassigning plan ${plan.id} from ${type} ${itemId}`);
      
      // Update local state
      setAssignments(prev => ({
        ...prev,
        [type]: prev[type].filter(item => item.id !== itemId)
      }));
    } catch (err) {
      setError(err.message || 'Failed to unassign plan');
    }
  };

  const getFilteredItems = (type) => {
    const assigned = assignments[type] || [];
    const assignedIds = assigned.map(item => item.id);
    const available = availableItems[type];
    
    // Additional safety check to ensure we have an array
    if (!Array.isArray(available)) {
      console.warn(`PlanAssignmentModal - availableItems[${type}] is not an array:`, available);
      return [];
    }
    
    return available.filter(item => {
      const isNotAssigned = !assignedIds.includes(item.id);
      const matchesSearch = searchTerm === '' || 
        (item.email && item.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.name && item.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.account_number && item.account_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.contract_number && item.contract_number.toLowerCase().includes(searchTerm.toLowerCase()));
      
      return isNotAssigned && matchesSearch;
    });
  };

  const getFilteredAssignments = (type) => {
    const assigned = assignments[type] || [];
    
    // Additional safety check to ensure we have an array
    if (!Array.isArray(assigned)) {
      console.warn(`PlanAssignmentModal - assignments[${type}] is not an array:`, assigned);
      return [];
    }
    
    return assigned.filter(item => {
      const matchesSearch = searchTerm === '' || 
        (item.email && item.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.name && item.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.account_number && item.account_number.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.contract_number && item.contract_number.toLowerCase().includes(searchTerm.toLowerCase()));
      
      return matchesSearch;
    });
  };

  const renderTabContent = () => {
    const filteredAvailable = getFilteredItems(activeTab);
    const filteredAssigned = getFilteredAssignments(activeTab);

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Available Items */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">
            Available {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {filteredAvailable.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No available {activeTab} found
              </p>
            ) : (
              filteredAvailable.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    {activeTab === 'users' && (
                      <>
                        <div className="text-sm font-medium text-gray-900">{item.name || item.email}</div>
                        <div className="text-xs text-gray-500">{item.email}</div>
                      </>
                    )}
                    {activeTab === 'accounts' && (
                      <>
                        <div className="text-sm font-medium text-gray-900">{item.account_number}</div>
                        <div className="text-xs text-gray-500">{item.user?.email}</div>
                      </>
                    )}
                    {activeTab === 'contracts' && (
                      <>
                        <div className="text-sm font-medium text-gray-900">{item.contract_number}</div>
                        <div className="text-xs text-gray-500">{item.service_name} - {item.customer?.email}</div>
                      </>
                    )}
                  </div>
                  <button
                    onClick={() => handleAssign(item.id, activeTab)}
                    className="ml-3 px-3 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100"
                  >
                    Assign
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Assigned Items */}
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">
            Assigned {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} ({filteredAssigned.length})
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {filteredAssigned.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No {activeTab} assigned to this plan
              </p>
            ) : (
              filteredAssigned.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 border border-green-200 bg-green-50 rounded-lg">
                  <div className="flex-1">
                    {activeTab === 'users' && (
                      <>
                        <div className="text-sm font-medium text-gray-900">{item.name || item.email}</div>
                        <div className="text-xs text-gray-500">{item.email}</div>
                        <div className="text-xs text-gray-400">Assigned: {item.assigned_date}</div>
                      </>
                    )}
                    {activeTab === 'accounts' && (
                      <>
                        <div className="text-sm font-medium text-gray-900">{item.account_number}</div>
                        <div className="text-xs text-gray-500">{item.user?.email}</div>
                        <div className="text-xs text-gray-400">Assigned: {item.assigned_date}</div>
                      </>
                    )}
                    {activeTab === 'contracts' && (
                      <>
                        <div className="text-sm font-medium text-gray-900">{item.contract_number}</div>
                        <div className="text-xs text-gray-500">{item.service_name} - {item.customer?.email}</div>
                        <div className="text-xs text-gray-400">Assigned: {item.assigned_date}</div>
                      </>
                    )}
                  </div>
                  <button
                    onClick={() => handleUnassign(item.id, activeTab)}
                    className="ml-3 px-3 py-1 text-xs font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100"
                  >
                    Unassign
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-6xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between pb-4 border-b">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Manage Plan Assignments: {plan?.name}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Assign or unassign this plan to users, accounts, and contracts
            </p>
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

          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search users, accounts, or contracts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-4">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('users')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4" />
                  <span>Users ({(assignments.users || []).length})</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('accounts')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'accounts'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Building className="h-4 w-4" />
                  <span>Accounts ({(assignments.accounts || []).length})</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('contracts')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'contracts'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4" />
                  <span>Contracts ({(assignments.contracts || []).length})</span>
                </div>
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading assignments...</p>
            </div>
          ) : (
            renderTabContent()
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-end space-x-3 pt-6 mt-6 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

PlanAssignmentModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  plan: PropTypes.object
};

export default PlanAssignmentModal; 