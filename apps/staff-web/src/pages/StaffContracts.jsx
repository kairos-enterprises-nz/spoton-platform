import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Search, Filter, Plus, Download, Eye, Edit, FileText, AlertCircle, 
  CheckCircle, Trash2, RefreshCw, Zap, Wifi, Smartphone, Network,
  Hash, CreditCard, Clock, Users, MapPin, DollarSign
} from 'lucide-react';
import staffApiService from '../services/staffApi';
import ContractCreateModal from '../components/staff/ContractCreateModal';
import ContractEditModal from '../components/staff/ContractEditModal';
import ContractDetailModal from '../components/staff/ContractDetailModal';
import { useLoader } from '../context/LoaderContext';
import { useAuth } from '../hooks/useAuth';

const StaffContracts = () => {
  const { setLoading } = useLoader();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [contracts, setContracts] = useState([]);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [serviceFilter, setServiceFilter] = useState('all');
  const [sortBy, setSortBy] = useState('contract_number');
  const [sortOrder, setSortOrder] = useState('asc');
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [contractToDelete, setContractToDelete] = useState(null);
  const [highlightedContractId, setHighlightedContractId] = useState(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);

  // Check for selected contract in URL params
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const selectedId = params.get('selected');
    if (selectedId) {
      setHighlightedContractId(selectedId);
      // Scroll to highlighted contract after data loads
      setTimeout(() => {
        const element = document.getElementById(`contract-${selectedId}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 500);
    }
  }, [location.search]);

  useEffect(() => {
    loadContracts();
  }, [currentPage, pageSize, searchTerm, statusFilter, serviceFilter, sortBy, sortOrder]);

  const loadContracts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('🔄 Loading contracts with params:', { 
        page: currentPage, 
        page_size: pageSize, 
        search: searchTerm, 
        status: statusFilter,
        contract_type: serviceFilter,
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

      if (serviceFilter !== 'all') {
        params.contract_type = serviceFilter;
      }

      const response = await staffApiService.getContracts(params);
      console.log('📊 Contracts API response:', response);

      // Handle both paginated and direct array responses
      let contractsData = [];
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
          contractsData = response.results;
          paginationData = {
            count: response.count || 0,
            next: response.next,
            previous: response.previous,
            current_page: currentPage,
            total_pages: Math.ceil((response.count || 0) / pageSize)
          };
        } else if (Array.isArray(response)) {
          // Direct array response
          contractsData = response;
          paginationData.count = response.length;
        } else {
          // Single object or other format
          contractsData = [response];
          paginationData.count = 1;
        }
      } else if (Array.isArray(response)) {
        contractsData = response;
        paginationData.count = response.length;
      }

      console.log('✅ Processed contracts data:', { 
        count: contractsData.length, 
        pagination: paginationData,
        sampleContract: contractsData[0]
      });

      setContracts(contractsData);
      setPagination(paginationData);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('❌ Failed to load contracts:', error);
      setError(error.message || 'Failed to load contracts');
      setContracts([]);
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

  const handleServiceFilter = (type) => {
    setServiceFilter(type);
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
      const response = await staffApiService.exportContracts('csv');
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `contracts_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export contracts:', error);
      setError(error.message || 'Failed to export contracts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTemplate = async () => {
    const header = ['contract_number','contract_type','service_name','status','start_date','end_date','tenant_slug','account_number','base_charge'];
    const csv = header.join(',') + '\n';
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'contracts_import_template.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleCreateContract = () => {
    setShowCreateModal(true);
  };

  const handleViewContract = (contract) => {
    setSelectedContract(contract);
    setShowDetailModal(true);
  };

  const handleEditContract = (contract) => {
    setSelectedContract(contract);
    setShowEditModal(true);
  };

  const handleDeleteContract = (contract) => {
    setSelectedContract(contract);
    setShowDeleteDialog(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedContract) return;
    
      try {
      await staffApiService.deleteContract(selectedContract.id);
      setShowDeleteDialog(false);
      setSelectedContract(null);
        loadContracts(); // Reload the list
      } catch (error) {
        console.error('Failed to delete contract:', error);
        setError(error.message || 'Failed to delete contract');
    }
  };

  const handleContractSuccess = () => {
    loadContracts(); // Reload contracts when a modal operation succeeds
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedContract(null);
  };

  const handleSelectContract = (contractId) => {
    setSelectedContracts(prev => 
      prev.includes(contractId) 
        ? prev.filter(id => id !== contractId)
        : [...prev, contractId]
    );
  };

  const handleSelectAllContracts = () => {
    if (selectedContracts.length === contracts.length) {
      setSelectedContracts([]);
    } else {
      setSelectedContracts(contracts.map(contract => contract.id));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedContracts.length === 0) return;
    
    try {
      await Promise.all(selectedContracts.map(id => staffApiService.deleteContract(id)));
      setSelectedContracts([]);
      loadContracts(); // Reload the list
    } catch (error) {
      console.error('Failed to delete contracts:', error);
      setError(error.message || 'Failed to delete selected contracts');
    }
  };

  const getServiceIcon = (serviceType) => {
    switch (serviceType?.toLowerCase()) {
      case 'electricity':
        return <Zap className="h-4 w-4 text-yellow-500" />;
      case 'broadband':
        return <Wifi className="h-4 w-4 text-blue-500" />;
      case 'mobile':
        return <Smartphone className="h-4 w-4 text-green-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'active': { color: 'green', icon: CheckCircle, label: 'Active' },
      'inactive': { color: 'red', icon: AlertCircle, label: 'Inactive' },
      'suspended': { color: 'yellow', icon: AlertCircle, label: 'Suspended' },
      'pending': { color: 'blue', icon: Clock, label: 'Pending' },
      'expired': { color: 'gray', icon: AlertCircle, label: 'Expired' }
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

  const formatCurrency = (amount) => {
    if (!amount) return '$0.00';
    return new Intl.NumberFormat('en-NZ', {
      style: 'currency',
      currency: 'NZD'
    }).format(amount);
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
                <h1 className="text-left text-xl font-bold text-gray-900">Contract Management</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Manage service contracts and their relationships
                </p>
              </div>
              
              <div className="flex items-center space-x-3">
                <button
                  onClick={loadContracts}
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
                        await apiClient.post(`${apiBase}/contracts/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                      });
                      await loadContracts();
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
                  onClick={handleCreateContract}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Contract
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
                  <h3 className="text-sm font-medium text-red-800">Error loading contracts</h3>
                  <div className="mt-1 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={loadContracts}
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
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
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
                  placeholder="Search by contract number, account, or customer..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                  <Filter className="w-4 h-4 inline mr-1" />
                  Status
                </label>
                <div className="flex flex-col space-y-1 mt-2">
                  {[
                    { value: 'all', label: 'All' },
                    { value: 'active', label: 'Active' },
                    { value: 'inactive', label: 'Inactive' },
                    { value: 'expired', label: 'Expired' }
                  ].map(option => (
                    <button
                      key={option.value}
                      onClick={() => handleStatusFilter(option.value)}
                      className={`px-2 py-1 text-xs font-medium rounded-md text-left ${
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
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                  Service Type
                </label>
                <div className="flex flex-col space-y-1 mt-2">
                  {[
                    { value: 'all', label: 'All', icon: null },
                    { value: 'electricity', label: 'Electricity', icon: Zap },
                    { value: 'broadband', label: 'Broadband', icon: Wifi },
                    { value: 'mobile', label: 'Mobile', icon: Smartphone }
                  ].map(option => {
                    const Icon = option.icon;
                    return (
                      <button
                        key={option.value}
                        onClick={() => handleServiceFilter(option.value)}
                        className={`px-2 py-1 text-xs font-medium rounded-md text-left flex items-center ${
                          serviceFilter === option.value
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {Icon && <Icon className="w-3 h-3 mr-1" />}
                        {option.label}
                      </button>
                    );
                  })}
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
                  <option value="contract_number">Contract Number</option>
                  <option value="start_date">Start Date</option>
                  <option value="end_date">End Date</option>
                  <option value="created_at">Created Date</option>
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
                    <FileText className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Contracts</dt>
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
                        {contracts.filter(c => c.status === 'active').length}
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
                    <Zap className="h-6 w-6 text-yellow-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Electricity</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {contracts.filter(c => c.service_type === 'electricity').length}
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
                    <Network className="h-6 w-6 text-purple-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Selected</dt>
                      <dd className="text-lg font-medium text-gray-900">{selectedContracts.length}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Contracts Table */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden mx-3 md:mx-6">
            <div className="px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Contracts ({pagination.count})
                </h3>
                {selectedContracts.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      {selectedContracts.length} selected
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
                        checked={selectedContracts.length === contracts.length && contracts.length > 0}
                        onChange={handleSelectAllContracts}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('contract_number')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Contract</span>
                        {getSortIcon('contract_number')}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Service
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Plan
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Value
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('start_date')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Duration</span>
                        {getSortIcon('start_date')}
                      </div>
                    </th>
                    <th className="relative px-4 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {contracts.map((contract) => (
                    <tr 
                      key={contract.id} 
                      id={`contract-${contract.id}`}
                      className={`hover:bg-gray-50 ${
                        highlightedContractId === contract.id 
                          ? 'bg-blue-50 border-l-4 border-blue-500' 
                          : ''
                      }`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <input
                          type="checkbox"
                          checked={selectedContracts.includes(contract.id)}
                          onChange={() => handleSelectContract(contract.id)}
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
                              #{contract.contract_number || contract.id}
                            </div>
                            <div className="text-sm text-left text-gray-500">
                              {contract.contract_type || 'Standard'}
                            </div>
                          </div>
                          </div>
                      </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
                              <CreditCard className="h-5 w-5 text-gray-600" />
                            </div>
                          </div>
                          <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                              #{contract.account?.account_number || contract.account_id || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-500">
                              {contract.account?.primary_user?.email || contract.customer_email || 'N/A'}
                            </div>
                          </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
                              {getServiceIcon(contract.service_type)}
                            </div>
                          </div>
                          <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                              {contract.service_type || 'Unknown'}
                          </div>
                          <div className="text-sm text-gray-500">
                              {contract.connection?.icp_number || contract.icp_number || 'N/A'}
                            </div>
                          </div>
                            </div>
                        </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="text-sm font-medium text-gray-900">
                          {contract.plan_name || contract.plan?.name || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {contract.plan_details || 'Standard Plan'}
                        </div>
                        </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="text-sm font-medium text-gray-900">
                          {formatCurrency(contract.monthly_value || contract.value)}
                                </div>
                        <div className="text-sm text-gray-500">
                          per month
                          </div>
                        </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        {getStatusBadge(contract.status)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="text-sm text-gray-900">
                          {formatDate(contract.start_date)}
                        </div>
                        <div className="text-sm text-gray-500">
                          to {formatDate(contract.end_date)}
                        </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2 text-left">
                            <button
                            onClick={() => handleViewContract(contract)}
                              className="text-indigo-600 hover:text-indigo-900"
                              title="View contract details"
                            >
                            <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleEditContract(contract)}
                              className="text-gray-600 hover:text-gray-900"
                              title="Edit contract"
                            >
                            <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteContract(contract)}
                              className="text-red-600 hover:text-red-900"
                              title="Delete contract"
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
          {contracts.length === 0 && !error && (
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
              <div className="text-center py-12">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-1 text-sm font-medium text-gray-900">No contracts found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || statusFilter !== 'all' || serviceFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Get started by creating your first contract.'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && serviceFilter === 'all' && (
                  <div className="mt-6">
                        <button
                      onClick={handleCreateContract}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Contract
                        </button>
                  </div>
                )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modals */}
        <ContractCreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
        onSuccess={handleContractSuccess}
        />

        <ContractEditModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
        onSuccess={handleContractSuccess}
          contract={selectedContract}
        />

        <ContractDetailModal
          isOpen={showDetailModal}
          onClose={() => setShowDetailModal(false)}
          onEdit={handleEditContract}
          onDelete={handleDeleteContract}
        contractId={selectedContract?.id}
      />

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-4 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <Trash2 className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-1">Delete Contract</h3>
              <div className="mt-1 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete contract #{selectedContract?.contract_number || selectedContract?.id}? This action cannot be undone.
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
                    setShowDeleteDialog(false);
                    setSelectedContract(null);
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

export default StaffContracts; 