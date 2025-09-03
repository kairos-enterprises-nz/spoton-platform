import React, { useState } from 'react';
import {
  PlayIcon,
  PlusIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { 
  useBillingRuns, 
  useCreateBillingRun, 
  useExecuteBillingRun 
} from '../../hooks/useBillingData';
import { billingApi } from '../../services/billingApi';

const BillingRunManager = () => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [filters, setFilters] = useState({
    service_type: '',
    status: '',
    page: 1
  });

  const { 
    data: billingRuns, 
    isLoading, 
    error,
    refetch 
  } = useBillingRuns(filters);

  const createBillingRunMutation = useCreateBillingRun({
    onSuccess: () => {
      setShowCreateForm(false);
      refetch();
    }
  });

  const executeBillingRunMutation = useExecuteBillingRun({
    onSuccess: () => {
      refetch();
    }
  });

  const handleCreateRun = (formData) => {
    createBillingRunMutation.mutate(formData);
  };

  const handleExecuteRun = (runId, dryRun = false) => {
    executeBillingRunMutation.mutate({ id: runId, dryRun });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'running':
        return <ClockIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-16 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Failed to load billing runs
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {error.message}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Billing Runs</h2>
          <p className="text-sm text-gray-600 mt-1">
            Create and manage billing runs for different services
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
          Create Billing Run
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Service Type
            </label>
            <select
              value={filters.service_type}
              onChange={(e) => setFilters(prev => ({ ...prev, service_type: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">All Services</option>
              <option value="electricity">Electricity</option>
              <option value="broadband">Broadband</option>
              <option value="mobile">Mobile</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={refetch}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Billing Runs List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {billingRuns?.results?.map((run) => (
            <li key={run.id}>
              <div className="px-4 py-4 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0 mr-4">
                    {getStatusIcon(run.status)}
                  </div>
                  <div>
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-gray-900">
                        {run.run_name}
                      </p>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500 mt-1">
                      <span className="capitalize">{run.service_type}</span>
                      <span className="mx-2">•</span>
                      <span>{billingApi.formatDate(run.period_start)} - {billingApi.formatDate(run.period_end)}</span>
                      <span className="mx-2">•</span>
                      <span>{run.bills_generated} bills</span>
                      <span className="mx-2">•</span>
                      <span>{billingApi.formatCurrency(run.total_billed_amount)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedRun(run)}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <EyeIcon className="-ml-0.5 mr-1 h-4 w-4" />
                    View
                  </button>
                  {run.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleExecuteRun(run.id, true)}
                        disabled={executeBillingRunMutation.isLoading}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                      >
                        Dry Run
                      </button>
                      <button
                        onClick={() => handleExecuteRun(run.id, false)}
                        disabled={executeBillingRunMutation.isLoading}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                      >
                        <PlayIcon className="-ml-0.5 mr-1 h-4 w-4" />
                        Execute
                      </button>
                    </>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Pagination */}
      {billingRuns?.count > 20 && (
        <div className="mt-6 flex justify-between items-center">
          <p className="text-sm text-gray-700">
            Showing {((filters.page - 1) * 20) + 1} to {Math.min(filters.page * 20, billingRuns.count)} of {billingRuns.count} results
          </p>
          <div className="flex space-x-2">
            <button
              onClick={() => setFilters(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
              disabled={filters.page === 1}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
              disabled={filters.page * 20 >= billingRuns.count}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Create Billing Run Modal */}
      {showCreateForm && (
        <CreateBillingRunModal
          onClose={() => setShowCreateForm(false)}
          onSubmit={handleCreateRun}
          isLoading={createBillingRunMutation.isLoading}
        />
      )}

      {/* Billing Run Details Modal */}
      {selectedRun && (
        <BillingRunDetailsModal
          run={selectedRun}
          onClose={() => setSelectedRun(null)}
        />
      )}
    </div>
  );
};

// Create Billing Run Modal Component
const CreateBillingRunModal = ({ onClose, onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    service_type: 'broadband',
    period_start: '',
    period_end: '',
    dry_run: true,
    execute_immediately: false
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
                Create Billing Run
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Service Type
                  </label>
                  <select
                    value={formData.service_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, service_type: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    required
                  >
                    <option value="electricity">Electricity</option>
                    <option value="broadband">Broadband</option>
                    <option value="mobile">Mobile</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Period Start
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.period_start}
                    onChange={(e) => setFormData(prev => ({ ...prev, period_start: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Period End
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.period_end}
                    onChange={(e) => setFormData(prev => ({ ...prev, period_end: e.target.value }))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    required
                  />
                </div>

                <div className="flex items-center">
                  <input
                    id="dry-run"
                    type="checkbox"
                    checked={formData.dry_run}
                    onChange={(e) => setFormData(prev => ({ ...prev, dry_run: e.target.checked }))}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="dry-run" className="ml-2 block text-sm text-gray-900">
                    Dry run (no actual changes)
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="execute-immediately"
                    type="checkbox"
                    checked={formData.execute_immediately}
                    onChange={(e) => setFormData(prev => ({ ...prev, execute_immediately: e.target.checked }))}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="execute-immediately" className="ml-2 block text-sm text-gray-900">
                    Execute immediately after creation
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
                {isLoading ? 'Creating...' : 'Create Run'}
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

// Billing Run Details Modal Component
const BillingRunDetailsModal = ({ run, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Billing Run Details
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Run Name</label>
                <p className="text-sm text-gray-900">{run.run_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Service Type</label>
                <p className="text-sm text-gray-900 capitalize">{run.service_type}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Status</label>
                <p className="text-sm text-gray-900 capitalize">{run.status}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Bills Generated</label>
                <p className="text-sm text-gray-900">{run.bills_generated}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Bills Failed</label>
                <p className="text-sm text-gray-900">{run.bills_failed}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Total Amount</label>
                <p className="text-sm text-gray-900">{billingApi.formatCurrency(run.total_billed_amount)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Created</label>
                <p className="text-sm text-gray-900">{billingApi.formatDate(run.created_at)}</p>
              </div>
              {run.duration_minutes && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Duration</label>
                  <p className="text-sm text-gray-900">{run.duration_minutes} minutes</p>
                </div>
              )}
            </div>

            {run.error_log && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-500">Error Log</label>
                <pre className="mt-1 text-sm text-red-600 bg-red-50 p-2 rounded-md overflow-auto max-h-32">
                  {run.error_log}
                </pre>
              </div>
            )}

            <div className="mt-6 flex justify-end">
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
    </div>
  );
};

export default BillingRunManager;
