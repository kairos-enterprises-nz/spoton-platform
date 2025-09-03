import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { useBills, useBulkBillAction } from '../../hooks/useBillingData';
import { billingApi } from '../../services/billingApi';

const BillManager = () => {
  const [filters, setFilters] = useState({
    status: '',
    service_type: '',
    search: '',
    page: 1
  });
  const [selectedBills, setSelectedBills] = useState([]);

  const { data: bills, isLoading, error } = useBills(filters);
  const bulkActionMutation = useBulkBillAction();

  const handleBulkAction = (action) => {
    if (selectedBills.length === 0) return;
    
    bulkActionMutation.mutate({
      bill_ids: selectedBills,
      action,
      dry_run: false
    });
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedBills(bills?.results?.map(bill => bill.id) || []);
    } else {
      setSelectedBills([]);
    }
  };

  const handleSelectBill = (billId, checked) => {
    if (checked) {
      setSelectedBills(prev => [...prev, billId]);
    } else {
      setSelectedBills(prev => prev.filter(id => id !== billId));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'issued':
        return 'bg-blue-100 text-blue-800';
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'overdue':
        return 'bg-red-100 text-red-800';
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

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Bills</h2>
          <p className="text-sm text-gray-600 mt-1">
            Review and manage customer bills
          </p>
        </div>
        {selectedBills.length > 0 && (
          <div className="flex space-x-2">
            <button
              onClick={() => handleBulkAction('generate_invoices')}
              disabled={bulkActionMutation.isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <DocumentTextIcon className="-ml-1 mr-2 h-5 w-5" />
              Generate Invoices ({selectedBills.length})
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="mb-6 bg-gray-50 p-4 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Bill number, customer..."
              />
            </div>
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
              <option value="draft">Draft</option>
              <option value="pending">Pending</option>
              <option value="issued">Issued</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>
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
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ status: '', service_type: '', search: '', page: 1 })}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <FunnelIcon className="h-4 w-4 mr-1 inline" />
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Bills Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={selectedBills.length === bills?.results?.length && bills?.results?.length > 0}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label className="ml-3 text-sm font-medium text-gray-700">
              Select all ({bills?.results?.length || 0} bills)
            </label>
          </div>
        </div>
        <ul className="divide-y divide-gray-200">
          {bills?.results?.map((bill) => (
            <li key={bill.id}>
              <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedBills.includes(bill.id)}
                    onChange={(e) => handleSelectBill(bill.id, e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <div className="ml-4">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-gray-900">
                        {bill.bill_number}
                      </p>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(bill.status)}`}>
                        {bill.status}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500 mt-1">
                      <span>{bill.customer_name}</span>
                      <span className="mx-2">•</span>
                      <span>{billingApi.formatDate(bill.issue_date)}</span>
                      <span className="mx-2">•</span>
                      <span>{billingApi.formatCurrency(bill.total_amount)}</span>
                      <span className="mx-2">•</span>
                      <span>{bill.line_items?.length || 0} items</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <EyeIcon className="-ml-0.5 mr-1 h-4 w-4" />
                    View
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Pagination */}
      {bills?.count > 20 && (
        <div className="mt-6 flex justify-between items-center">
          <p className="text-sm text-gray-700">
            Showing {((filters.page - 1) * 20) + 1} to {Math.min(filters.page * 20, bills.count)} of {bills.count} results
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
              disabled={filters.page * 20 >= bills.count}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BillManager;
