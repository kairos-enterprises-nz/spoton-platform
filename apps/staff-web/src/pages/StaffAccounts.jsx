import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Search, Filter, Plus, Download, Eye, Edit, Users, AlertCircle, 
  CheckCircle, Trash2, RefreshCw, CreditCard,
  Network, FileText, Hash, MapPin
} from 'lucide-react';
import staffApiService from '../services/staffApi';
import AccountCreateModal from '../components/staff/AccountCreateModal';
import AccountEditModal from '../components/staff/AccountEditModal';
import AccountDetailModal from '../components/staff/AccountDetailModal';
import { useLoader } from '../context/LoaderContext';
import { useAuth } from '../hooks/useAuth';

const StaffAccounts = () => {
  const { setLoading } = useLoader();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [accounts, setAccounts] = useState([]);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('account_number');
  const [sortOrder, setSortOrder] = useState('asc');
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [highlightedAccountId, setHighlightedAccountId] = useState(null);

  // Check for selected account in URL params
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const selectedId = params.get('selected');
    if (selectedId) {
      setHighlightedAccountId(selectedId);
      // Scroll to highlighted account after data loads
      setTimeout(() => {
        const element = document.getElementById(`account-${selectedId}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 500);
    }
  }, [location.search]);

  useEffect(() => {
    loadAccounts();
  }, [currentPage, pageSize, searchTerm, statusFilter, sortBy, sortOrder]);

  const loadAccounts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('🔄 Loading accounts with params:', { 
        page: currentPage, 
        page_size: pageSize, 
        search: searchTerm, 
        status: statusFilter,
        ordering: sortOrder === 'desc' ? `-${sortBy}` : sortBy
      });

      const params = {
        page: currentPage,
        page_size: pageSize,
        ordering: sortOrder === 'desc' ? `-${sortBy}` : sortBy
      };

      if (searchTerm) {
        params.search = searchTerm;
      }

      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      const response = await staffApiService.getAccounts(params);
      console.log('📊 Accounts API response:', response);

      // Handle both paginated and direct array responses
      let accountsData = [];
      let paginationData = {
        count: 0,
        next: null,
        previous: null,
        current_page: currentPage,
        total_pages: 1
      };

      if (response && typeof response === 'object') {
        if (response.results && Array.isArray(response.results)) {
          // Paginated response
          accountsData = response.results;
          paginationData = {
            count: response.count || 0,
            next: response.next,
            previous: response.previous,
            current_page: currentPage,
            total_pages: Math.ceil((response.count || 0) / pageSize)
          };
        } else if (Array.isArray(response)) {
          // Direct array response
          accountsData = response;
          paginationData.count = response.length;
        } else {
          // Single object or other format
          accountsData = [response];
          paginationData.count = 1;
        }
      } else if (Array.isArray(response)) {
        accountsData = response;
        paginationData.count = response.length;
      }

      console.log('✅ Processed accounts data:', { 
        count: accountsData.length, 
        pagination: paginationData,
        sampleAccount: accountsData[0]
      });

      setAccounts(accountsData);
      setPagination(paginationData);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('❌ Failed to load accounts:', error);
      setError(error.message || 'Failed to load accounts');
      setAccounts([]);
      setPagination({
        count: 0,
        next: null,
        previous: null,
        current_page: 1,
        total_pages: 1
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const handleStatusFilter = (status) => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (size) => {
    setPageSize(size);
    setCurrentPage(1);
  };

  const handleExport = async () => {
    setIsLoading(true);
    try {
      const response = await staffApiService.exportAccounts('csv');
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `accounts_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export accounts:', error);
      setError(error.message || 'Failed to export accounts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTemplate = async () => {
    // Client-side template generation for Accounts
    const header = ['account_number','tenant_slug','account_type','billing_cycle','billing_day','status','primary_user_email'];
    const csv = header.join(',') + '\n';
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'accounts_import_template.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleCreateAccount = () => {
    setShowCreateModal(true);
  };

  const handleEditAccount = (account) => {
    setSelectedAccount(account);
    setShowEditModal(true);
  };

  const handleViewAccount = (account) => {
    setSelectedAccount(account);
    setShowDetailModal(true);
  };

  const handleDeleteAccount = (account) => {
    setSelectedAccount(account);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedAccount) return;
    
    try {
      await staffApiService.deleteAccount(selectedAccount.id);
      setShowDeleteConfirm(false);
      setSelectedAccount(null);
      loadAccounts(); // Reload the list
    } catch (error) {
      console.error('Failed to delete account:', error);
      setError(error.message || 'Failed to delete account');
    }
  };

  const handleAccountSuccess = () => {
    loadAccounts(); // Reload the list after successful create/update
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedAccount(null);
  };

  const handleSelectAccount = (accountId) => {
    setSelectedAccounts(prev => 
      prev.includes(accountId) 
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    );
  };

  const handleSelectAllAccounts = () => {
    if (selectedAccounts.length === accounts.length) {
      setSelectedAccounts([]);
    } else {
      setSelectedAccounts(accounts.map(account => account.id));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedAccounts.length === 0) return;
    
    try {
      await Promise.all(selectedAccounts.map(id => staffApiService.deleteAccount(id)));
      setSelectedAccounts([]);
      loadAccounts(); // Reload the list
    } catch (error) {
      console.error('Failed to delete accounts:', error);
      setError(error.message || 'Failed to delete selected accounts');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'active': { color: 'green', icon: CheckCircle, label: 'Active' },
      'inactive': { color: 'red', icon: AlertCircle, label: 'Inactive' },
      'suspended': { color: 'yellow', icon: AlertCircle, label: 'Suspended' },
      'pending': { color: 'blue', icon: AlertCircle, label: 'Pending' }
    };

    const statusInfo = statusMap[status] || statusMap['inactive'];
    const Icon = statusInfo.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${statusInfo.color}-100 text-${statusInfo.color}-800`}>
        <Icon className="w-3 h-3 mr-1" />
        {statusInfo.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Intl.DateTimeFormat('en-NZ', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(new Date(dateString));
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return (
      <span className="ml-1">
        {sortOrder === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  const renderPagination = () => {
    const pages = [];
    const maxPagesToShow = 5;
    const startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    const endPage = Math.min(pagination.total_pages, startPage + maxPagesToShow - 1);

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`px-3 py-2 text-sm font-medium rounded-md ${
            i === currentPage
              ? 'bg-indigo-600 text-white'
              : 'text-gray-700 hover:bg-gray-50 border border-gray-300'
          }`}
        >
          {i}
        </button>
      );
    }

    return (
      <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-700">
          <span>
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, pagination.count)} of {pagination.count} results
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={!pagination.previous}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <div className="flex space-x-1">
            {pages}
          </div>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={!pagination.next}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
    
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-6">
            <div className="flex justify-between items-center py-6 space-y-0">
              <div>
                <h1 className="text-left text-xl font-bold text-gray-900">Account Management</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Manage customer accounts and their relationships
                </p>
              </div>
              
              <div className="flex items-center space-x-3">
                <button
                  onClick={loadAccounts}
                  disabled={isLoading}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  title={lastRefresh ? `Last refreshed: ${lastRefresh}` : 'Refresh data'}
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={handleExport}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <Download className="h-3 w-3 mr-1" />
                  Export
                </button>
                <button
                  onClick={handleTemplate}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <Download className="h-3 w-3 mr-1" />
                  Template
                </button>
                <label className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                  <input type="file" accept=".csv" className="hidden" onChange={async (e) => {
                    const file = e.target.files && e.target.files[0];
                    if (!file) return;
                    setIsLoading(true);
                    try {
                      const formData = new FormData();
                      formData.append('file', file);
                      const apiBase = staffApiService.baseURL || '/staff/v1';
                      await import('../services/apiClient').then(async ({ default: apiClient }) => {
                        await apiClient.post(`${apiBase}/accounts/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                      });
                      await loadAccounts();
                    } catch (err) {
                      console.error('Import failed:', err);
                      setError(err.message || 'Import failed');
                    } finally {
                      setIsLoading(false);
                      if (e.target) e.target.value = '';
                    }
                  }} />
                  Import CSV
                </label>
                
                <button
                  onClick={handleCreateAccount}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Account
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {/* Error Alert */}
          {error && (
            <div className="rounded-md bg-red-50 p-4 mx-3 md:mx-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error loading accounts</h3>
                  <div className="mt-1 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={loadAccounts}
                      className="text-sm bg-red-100 text-red-800 rounded-md px-3 py-1 hover:bg-red-200"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filters and Search */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 mt-6 p-4 mx-3 md:mx-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="md:col-span-2">
                <label htmlFor="search" className="block text-left text-sm font-medium text-gray-700 mb-1">
                  <Search className="w-4 h-4 inline mr-1" />
                  Search
                </label>
                <input
                  type="text"
                  id="search"
                  value={searchTerm}
                  onChange={handleSearch}
                  placeholder="Search by account number, email, or name..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                  <Filter className="w-4 h-4 inline mr-1" />
                  Status
                </label>
                <div className="flex space-x-2 mt-2.5">
                  {[
                    { value: 'all', label: 'All' },
                    { value: 'active', label: 'Active' },
                    { value: 'inactive', label: 'Inactive' }
                  ].map(option => (
                    <button
                      key={option.value}
                      onClick={() => handleStatusFilter(option.value)}
                      className={`px-3 py-2 text-xs font-medium rounded-md ${
                        statusFilter === option.value
                          ? 'bg-indigo-100 text-indigo-800'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label htmlFor="sortBy" className="block text-left text-sm font-medium text-gray-700 mb-1">
                  Sort By
                </label>
                <select
                  id="sortBy"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="account_number">Account Number</option>
                  <option value="created_at">Created Date</option>
                  <option value="updated_at">Updated Date</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="pageSize" className="block text-left text-sm font-medium text-gray-700 mb-1">
                  Per Page
                </label>
                <select
                  id="pageSize"
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>
          </div>

          {/* Stats Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mx-3 md:mx-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CreditCard className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Accounts</dt>
                      <dd className="text-lg font-medium text-gray-900">{pagination.count}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Active</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {accounts.filter(a => a.status === 'active').length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Network className="h-6 w-6 text-blue-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">With Connections</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {accounts.filter(a => (a.connections_count || 0) > 0).length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <FileText className="h-6 w-6 text-purple-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Selected</dt>
                      <dd className="text-lg font-medium text-gray-900">{selectedAccounts.length}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Accounts Table */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden mx-3 md:mx-6">
            <div className="px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Accounts ({pagination.count})
                </h3>
                {selectedAccounts.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      {selectedAccounts.length} selected
                </span>
                  <button
                    onClick={handleBulkDelete}
                      className="text-sm text-red-600 hover:text-red-800"
                  >
                    Delete Selected
                  </button>
                </div>
                )}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedAccounts.length === accounts.length && accounts.length > 0}
                        onChange={handleSelectAllAccounts}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('account_number')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Account</span>
                        {getSortIcon('account_number')}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Primary User
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Address
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contracts
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Connections
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('created_at')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Created</span>
                        {getSortIcon('created_at')}
                      </div>
                    </th>
                    <th className="relative px-4 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {accounts.map((account) => (
                    <tr 
                      key={account.id} 
                      id={`account-${account.id}`}
                      className={`hover:bg-gray-50 ${
                        highlightedAccountId === account.id 
                          ? 'bg-blue-50 border-l-4 border-blue-500' 
                          : ''
                      }`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                          <input
                            type="checkbox"
                            checked={selectedAccounts.includes(account.id)}
                            onChange={() => handleSelectAccount(account.id)}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                              <Hash className="h-5 w-5 text-indigo-600" />
                            </div>
                          </div>
                          <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            #{account.account_number || account.id}
                          </div>
                            <div className="text-sm text-left text-gray-500">
                            {account.account_type || 'Standard'}
                            </div>
                          </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
                                {account.primary_user?.first_name && account.primary_user?.last_name ? (
                                <span className="text-sm font-medium text-gray-600">
                                    {account.primary_user.first_name[0]}{account.primary_user.last_name[0]}
                                  </span>
                                ) : (
                                <Users className="h-5 w-5 text-gray-600" />
                                )}
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {account.primary_user?.full_name || 
                                 (account.primary_user?.first_name && account.primary_user?.last_name ? 
                                  `${account.primary_user.first_name} ${account.primary_user.last_name}` : 
                                  account.primary_user?.email?.split('@')[0] || 
                                  'N/A')}
                              </div>
                              <div className="text-sm text-gray-500">
                                {account.primary_user?.email || 'N/A'}
                              </div>
                              {account.primary_user?.phone && (
                                <div className="text-xs text-gray-400">
                                  {account.primary_user.phone}
                                </div>
                              )}
                          </div>
                          </div>
                        </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                          <div className="text-sm text-gray-900">
                            {account.primary_user?.address_line1 || account.primary_user?.street_address ? (
                              <>
                              <div className="font-medium flex items-center">
                                <MapPin className="w-3 h-3 text-gray-400 mr-1" />
                                  {account.primary_user.address_line1 || account.primary_user.street_address}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {account.primary_user.city || account.primary_user.suburb}, {account.primary_user.postal_code}
                                </div>
                              </>
                            ) : (
                              <span className="text-gray-400 text-xs">No address</span>
                            )}
                          </div>
                        </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="flex items-center">
                          <FileText className="w-4 h-4 text-gray-400 mr-1" />
                          <span className="text-sm text-gray-900">{account.contracts_count || 0}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="flex items-center">
                          <Network className="w-4 h-4 text-gray-400 mr-1" />
                          <span className="text-sm text-gray-900">{account.connections_count || 0}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                          {getStatusBadge(account.status)}
                        </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left text-sm text-gray-500">
                            {formatDate(account.created_at)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2 text-left">
                            <button
                              onClick={() => handleViewAccount(account)}
                              className="text-indigo-600 hover:text-indigo-900"
                              title="View account details"
                            >
                            <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleEditAccount(account)}
                              className="text-gray-600 hover:text-gray-900"
                              title="Edit account"
                            >
                            <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteAccount(account)}
                              className="text-red-600 hover:text-red-900"
                              title="Delete account"
                            >
                            <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination.total_pages > 1 && renderPagination()}
                </div>

          {/* Empty State */}
          {accounts.length === 0 && !error && (
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
              <div className="text-center py-12">
                <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-1 text-sm font-medium text-gray-900">No accounts found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || statusFilter !== 'all' 
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Get started by creating your first account.'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && (
                  <div className="mt-6">
                        <button
                      onClick={handleCreateAccount}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Account
                        </button>
                  </div>
                )}
                </div>
              </div>
            )}
        </div>
      </div>

      {/* Modals */}
      <AccountCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleAccountSuccess}
      />

      <AccountEditModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSuccess={handleAccountSuccess}
        account={selectedAccount}
      />

      <AccountDetailModal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        onEdit={handleEditAccount}
        onDelete={handleDeleteAccount}
        accountId={selectedAccount?.id}
      />

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-4 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <Trash2 className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-1">Delete Account</h3>
              <div className="mt-1 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete account #{selectedAccount?.account_number || selectedAccount?.id}? This action cannot be undone.
              </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleConfirmDelete}
                  disabled={isLoading}
                  className="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300 disabled:opacity-50"
                >
                  {isLoading ? 'Deleting...' : 'Delete'}
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setSelectedAccount(null);
                  }}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    
    </div>
  );
};

export default StaffAccounts; 