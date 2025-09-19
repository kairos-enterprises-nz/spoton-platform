import { useState, useEffect } from 'react';
import { X, Edit, Trash2, Calendar, DollarSign, User, Building, FileText, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import PropTypes from 'prop-types';
import staffApiService from '../../services/staffApi';

const ContractDetailModal = ({ isOpen, onClose, onEdit, onDelete, contractId }) => {
  const [contract, setContract] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && contractId) {
      loadContract();
    }
  }, [isOpen, contractId]);

  const loadContract = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await staffApiService.getContract(contractId);
      setContract(response);
    } catch (error) {
      console.error('Failed to load contract:', error);
      setError(error.message || 'Failed to load contract details');
      // Set minimal fallback data to prevent UI crashes
      setContract({
        id: contractId,
        contract_number: `Contract ${contractId}`,
        contract_type: 'unknown',
        service_name: 'Unknown Service',
        status: 'unknown'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'active': { color: 'green', icon: CheckCircle, text: 'Active' },
      'pending': { color: 'yellow', icon: Clock, text: 'Pending' },
      'draft': { color: 'gray', icon: FileText, text: 'Draft' },
      'cancelled': { color: 'red', icon: AlertCircle, text: 'Cancelled' },
      'expired': { color: 'gray', icon: AlertCircle, text: 'Expired' }
    };

    const config = statusConfig[status] || statusConfig['pending'];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-${config.color}-100 text-${config.color}-800`}>
        <Icon className="w-4 h-4 mr-1" />
        {config.text}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Intl.DateTimeFormat('en-NZ', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(new Date(dateString));
  };

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-NZ', {
      style: 'currency',
      currency: 'NZD'
    }).format(amount);
  };

  const handleEdit = () => {
    onEdit?.(contract);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this contract? This action cannot be undone.')) {
      onDelete?.(contract);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-6 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div>
            <h3 className="text-xl font-semibold text-gray-900">Contract Details</h3>
            {contract && (
              <p className="text-sm text-gray-600 mt-1">
                Contract #{contract.contract_number}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {contract && (
              <>
                <button
                  onClick={handleEdit}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Delete
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="mt-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <span className="ml-2 text-gray-600">Loading contract details...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          ) : contract ? (
            <div className="space-y-6">
              {/* Status and Basic Info */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                    {getStatusBadge(contract.status)}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Contract Type</label>
                    <p className="text-sm text-gray-900 capitalize">{contract.contract_type}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Service Name</label>
                    <p className="text-sm text-gray-900">{contract.service_name}</p>
                  </div>
                </div>
              </div>

              {/* Customer and Account Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                    <User className="h-5 w-5 mr-2 text-gray-500" />
                    Customer Information
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Name</label>
                      <p className="text-sm text-gray-900">
                        {contract.customer?.full_name || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Email</label>
                      <p className="text-sm text-gray-900">
                        {contract.customer?.email || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">User Type</label>
                      <p className="text-sm text-gray-900 capitalize">
                        {contract.customer?.user_type || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                    <Building className="h-5 w-5 mr-2 text-gray-500" />
                    Account & Tenant
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Account Number</label>
                      <p className="text-sm text-gray-900">
                        {contract.account?.account_number || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Account Type</label>
                      <p className="text-sm text-gray-900 capitalize">
                        {contract.account?.account_type || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Tenant</label>
                      <p className="text-sm text-gray-900">
                        {contract.tenant?.name || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Contract Terms */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                  <Calendar className="h-5 w-5 mr-2 text-gray-500" />
                  Contract Terms
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                    <p className="text-sm text-gray-900">{formatDate(contract.start_date)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <p className="text-sm text-gray-900">{formatDate(contract.end_date)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Initial Term</label>
                    <p className="text-sm text-gray-900">
                      {contract.initial_term_months} months
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Billing Frequency</label>
                    <p className="text-sm text-gray-900 capitalize">{contract.billing_frequency}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Auto Renewal</label>
                    <p className="text-sm text-gray-900">
                      {contract.auto_renewal ? 'Enabled' : 'Disabled'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Financial Details */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                  <DollarSign className="h-5 w-5 mr-2 text-gray-500" />
                  Financial Details
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Setup Fee</label>
                    <p className="text-sm text-gray-900">{formatCurrency(contract.setup_fee)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Early Termination Fee</label>
                    <p className="text-sm text-gray-900">{formatCurrency(contract.early_termination_fee)}</p>
                  </div>
                </div>
              </div>

              {/* Description */}
              {contract.description && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                    <FileText className="h-5 w-5 mr-2 text-gray-500" />
                    Description
                  </h4>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{contract.description}</p>
                </div>
              )}

              {/* Audit Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Audit Information</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Created:</span> {formatDate(contract.created_at)}
                  </div>
                  <div>
                    <span className="font-medium">Last Updated:</span> {formatDate(contract.updated_at)}
                  </div>
                  {contract.created_by && (
                    <div>
                      <span className="font-medium">Created By:</span> {contract.created_by.full_name}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No contract data available</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end pt-6 border-t border-gray-200 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

ContractDetailModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  contractId: PropTypes.string
};

export default ContractDetailModal; 