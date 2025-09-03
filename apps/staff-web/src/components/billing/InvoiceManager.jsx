import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  EnvelopeIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { 
  useInvoices, 
  useBulkInvoiceAction, 
  useDownloadInvoicePDF 
} from '../../hooks/useBillingData';
import { billingApi } from '../../services/billingApi';

const InvoiceManager = () => {
  const [filters, setFilters] = useState({
    status: '',
    payment_status: '',
    search: '',
    page: 1
  });
  const [selectedInvoices, setSelectedInvoices] = useState([]);

  const { data: invoices, isLoading, error } = useInvoices(filters);
  const bulkActionMutation = useBulkInvoiceAction();
  const downloadPDFMutation = useDownloadInvoicePDF();

  const handleBulkAction = (action, approved = true) => {
    if (selectedInvoices.length === 0) return;
    
    bulkActionMutation.mutate({
      invoice_ids: selectedInvoices,
      action,
      approved,
      dry_run: false
    });
  };

  const handleDownloadPDF = (invoiceId) => {
    downloadPDFMutation.mutate(invoiceId);
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedInvoices(invoices?.results?.map(invoice => invoice.id) || []);
    } else {
      setSelectedInvoices([]);
    }
  };

  const handleSelectInvoice = (invoiceId, checked) => {
    if (checked) {
      setSelectedInvoices(prev => [...prev, invoiceId]);
    } else {
      setSelectedInvoices(prev => prev.filter(id => id !== invoiceId));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'review':
        return 'bg-yellow-100 text-yellow-800';
      case 'finalized':
        return 'bg-blue-100 text-blue-800';
      case 'booked':
        return 'bg-indigo-100 text-indigo-800';
      case 'emailed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentStatusColor = (status) => {
    switch (status) {
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'partial':
        return 'bg-yellow-100 text-yellow-800';
      case 'overdue':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const canPerformAction = (action, invoiceStatuses) => {
    switch (action) {
      case 'review':
        return invoiceStatuses.every(status => status === 'draft');
      case 'finalize':
        return invoiceStatuses.every(status => status === 'review');
      case 'generate_pdf':
        return invoiceStatuses.every(status => status === 'finalized');
      case 'send_email':
        return invoiceStatuses.every(status => status === 'finalized');
      default:
        return false;
    }
  };

  const selectedStatuses = selectedInvoices.map(id => 
    invoices?.results?.find(inv => inv.id === id)?.status
  ).filter(Boolean);

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
          <h2 className="text-2xl font-bold text-gray-900">Invoices</h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage invoice lifecycle and delivery
          </p>
        </div>
        {selectedInvoices.length > 0 && (
          <div className="flex space-x-2">
            {canPerformAction('review', selectedStatuses) && (
              <>
                <button
                  onClick={() => handleBulkAction('review', true)}
                  disabled={bulkActionMutation.isLoading}
                  className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                >
                  <CheckIcon className="-ml-1 mr-2 h-4 w-4" />
                  Approve ({selectedInvoices.length})
                </button>
                <button
                  onClick={() => handleBulkAction('review', false)}
                  disabled={bulkActionMutation.isLoading}
                  className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  <XMarkIcon className="-ml-1 mr-2 h-4 w-4" />
                  Reject ({selectedInvoices.length})
                </button>
              </>
            )}
            {canPerformAction('finalize', selectedStatuses) && (
              <button
                onClick={() => handleBulkAction('finalize')}
                disabled={bulkActionMutation.isLoading}
                className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                Finalize ({selectedInvoices.length})
              </button>
            )}
            {canPerformAction('generate_pdf', selectedStatuses) && (
              <button
                onClick={() => handleBulkAction('generate_pdf')}
                disabled={bulkActionMutation.isLoading}
                className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <DocumentArrowDownIcon className="-ml-1 mr-2 h-4 w-4" />
                Generate PDFs ({selectedInvoices.length})
              </button>
            )}
            {canPerformAction('send_email', selectedStatuses) && (
              <button
                onClick={() => handleBulkAction('send_email')}
                disabled={bulkActionMutation.isLoading}
                className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
              >
                <EnvelopeIcon className="-ml-1 mr-2 h-4 w-4" />
                Send Emails ({selectedInvoices.length})
              </button>
            )}
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
                placeholder="Invoice number, customer..."
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
              <option value="review">Under Review</option>
              <option value="finalized">Finalized</option>
              <option value="booked">Booked</option>
              <option value="emailed">Emailed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Payment Status
            </label>
            <select
              value={filters.payment_status}
              onChange={(e) => setFilters(prev => ({ ...prev, payment_status: e.target.value }))}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">All Payment Statuses</option>
              <option value="unpaid">Unpaid</option>
              <option value="partial">Partially Paid</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ status: '', payment_status: '', search: '', page: 1 })}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <FunnelIcon className="h-4 w-4 mr-1 inline" />
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={selectedInvoices.length === invoices?.results?.length && invoices?.results?.length > 0}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label className="ml-3 text-sm font-medium text-gray-700">
              Select all ({invoices?.results?.length || 0} invoices)
            </label>
          </div>
        </div>
        <ul className="divide-y divide-gray-200">
          {invoices?.results?.map((invoice) => (
            <li key={invoice.id}>
              <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedInvoices.includes(invoice.id)}
                    onChange={(e) => handleSelectInvoice(invoice.id, e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <div className="ml-4">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-gray-900">
                        {invoice.invoice_number}
                      </p>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
                        {invoice.status}
                      </span>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPaymentStatusColor(invoice.payment_status)}`}>
                        {invoice.payment_status}
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500 mt-1">
                      <span>{invoice.customer_name}</span>
                      <span className="mx-2">•</span>
                      <span>{billingApi.formatDate(invoice.issue_date)}</span>
                      <span className="mx-2">•</span>
                      <span>Due: {billingApi.formatDate(invoice.due_date)}</span>
                      <span className="mx-2">•</span>
                      <span>{billingApi.formatCurrency(invoice.total_amount)}</span>
                    </div>
                    <div className="flex items-center text-xs text-gray-400 mt-1">
                      {invoice.is_pdf_generated && (
                        <span className="inline-flex items-center text-green-600 mr-3">
                          <CheckIcon className="h-3 w-3 mr-1" />
                          PDF
                        </span>
                      )}
                      {invoice.is_emailed && (
                        <span className="inline-flex items-center text-green-600 mr-3">
                          <CheckIcon className="h-3 w-3 mr-1" />
                          Emailed
                        </span>
                      )}
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
                  {invoice.is_pdf_generated && (
                    <button
                      onClick={() => handleDownloadPDF(invoice.id)}
                      disabled={downloadPDFMutation.isLoading}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      <DocumentArrowDownIcon className="-ml-0.5 mr-1 h-4 w-4" />
                      PDF
                    </button>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Pagination */}
      {invoices?.count > 20 && (
        <div className="mt-6 flex justify-between items-center">
          <p className="text-sm text-gray-700">
            Showing {((filters.page - 1) * 20) + 1} to {Math.min(filters.page * 20, invoices.count)} of {invoices.count} results
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
              disabled={filters.page * 20 >= invoices.count}
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

export default InvoiceManager;
