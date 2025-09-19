import { useState, useEffect } from 'react';
import { 
  Plus, Search, Filter, Download, Upload, RefreshCw, Edit, Trash2,
  Zap, Wifi, Smartphone, Network, Hash, CreditCard, MapPin, AlertCircle,
  CheckCircle, Clock, Users
} from 'lucide-react';
import ConnectionCreateModal from '../components/staff/ConnectionCreateModal';
import ConnectionPlanModal from '../components/staff/ConnectionPlanModal';
import staffApiService from '../services/staffApi';

const StaffConnections = () => {
  const [connections, setConnections] = useState([]);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [selectedConnections, setSelectedConnections] = useState([]);

  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isPlanModalOpen, setIsPlanModalOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(null);

  // Data for forms
  const [accounts, setAccounts] = useState([]);
  const [plans, setPlans] = useState([]);
  const [contracts, setContracts] = useState([]);

  useEffect(() => {
    loadConnections();
    loadPlansAndAccounts();
  }, [currentPage, pageSize, searchTerm, statusFilter, typeFilter, sortBy, sortOrder]);

  const loadPlansAndAccounts = async () => {
    try {
      console.log('🔄 Loading plans and accounts...');
      const [plansData, accountsData] = await Promise.all([
        staffApiService.getPlans(),
        staffApiService.getAccounts()
      ]);
      
      console.log('📊 Plans response:', plansData);
      console.log('📊 Accounts response:', accountsData);
      
      // Handle response formats
      const processedPlans = Array.isArray(plansData) ? plansData : 
                           (plansData?.results ? plansData.results : []);
      const processedAccounts = Array.isArray(accountsData) ? accountsData : 
                               (accountsData?.results ? accountsData.results : []);
      
      setPlans(processedPlans);
      setAccounts(processedAccounts);
      
      console.log('✅ Processed plans and accounts:', { 
        plans: processedPlans.length, 
        accounts: processedAccounts.length 
      });
    } catch (error) {
      console.error('❌ Failed to load plans and accounts:', error);
      // Fallback to sample data for development
      const samplePlans = [
        { id: '1', service_type: 'electricity', name: 'SpotOn Fixed Electricity', monthly_charge: 150.00 },
        { id: '2', service_type: 'electricity', name: 'SpotOn Green Electricity', monthly_charge: 165.00 },
        { id: '3', service_type: 'broadband', name: 'SpotOn Fibre Basic', monthly_charge: 69.99 },
        { id: '4', service_type: 'broadband', name: 'SpotOn Fibre Pro', monthly_charge: 89.99 },
        { id: '5', service_type: 'mobile', name: 'SpotOn Mobile Essential', monthly_charge: 29.99 },
        { id: '6', service_type: 'mobile', name: 'SpotOn Mobile Plus', monthly_charge: 49.99 }
      ];
      const sampleAccounts = [
        { id: '1', account_number: 'ACC-001-2024', user: { email: 'testuser@email.com' } },
        { id: '2', account_number: 'ACC-002-2024', user: { email: 'admin@spoton.co.nz' } }
      ];
      setPlans(samplePlans);
      setAccounts(sampleAccounts);
    }
  };

  const loadConnections = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('🔄 Loading connections with params:', { 
        page: currentPage, 
        page_size: pageSize, 
        search: searchTerm, 
        status: statusFilter,
        service_type: typeFilter,
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

      if (typeFilter !== 'all') {
        params.service_type = typeFilter;
      }

      const response = await staffApiService.getConnections(params);
      console.log('📊 Connections API response:', response);
      
      // Handle both paginated and direct array responses
      let connectionsData = [];
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
          connectionsData = response.results;
          paginationData = {
            count: response.count || 0,
            next: response.next,
            previous: response.previous,
            current_page: currentPage,
            total_pages: Math.ceil((response.count || 0) / pageSize)
          };
        } else if (Array.isArray(response)) {
          // Direct array response
          connectionsData = response;
          paginationData.count = response.length;
        } else {
          // Single object or other format
          connectionsData = [response];
          paginationData.count = 1;
        }
      } else if (Array.isArray(response)) {
        connectionsData = response;
        paginationData.count = response.length;
      }
      
      console.log('✅ Processed connections data:', { 
        count: connectionsData.length,
        pagination: paginationData,
        sample: connectionsData[0]
      });
      
      setConnections(connectionsData);
      setPagination(paginationData);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('❌ Failed to load connections:', error);
      setError(error.message || 'Failed to load connections');
      setConnections([]);
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

  const handleTypeFilter = (type) => {
    setTypeFilter(type);
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

  const handleRefresh = () => {
    loadConnections();
    loadPlansAndAccounts();
  };

  const handleEditConnection = (connection) => {
    // For now, just show the plan modal as editing functionality
    setSelectedConnection(connection);
    setIsPlanModalOpen(true);
  };

  const handleDeleteConnection = (connection) => {
    setSelectedConnection(connection);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedConnection) return;
    
    try {
      await staffApiService.deleteConnection(selectedConnection.id);
      setShowDeleteConfirm(false);
      setSelectedConnection(null);
      loadConnections(); // Reload the list
    } catch (error) {
      console.error('Failed to delete connection:', error);
      setError(error.message || 'Failed to delete connection');
    }
  };

  const handleConnectionSuccess = () => {
    loadConnections(); // Reload connections when a modal operation succeeds
    setIsCreateModalOpen(false);
    setIsPlanModalOpen(false);
    setSelectedConnection(null);
  };

  const handleSelectConnection = (connectionId) => {
    setSelectedConnections(prev => 
      prev.includes(connectionId) 
        ? prev.filter(id => id !== connectionId)
        : [...prev, connectionId]
    );
  };

  const handleSelectAllConnections = () => {
    if (selectedConnections.length === connections.length) {
      setSelectedConnections([]);
    } else {
      setSelectedConnections(connections.map(connection => connection.id));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedConnections.length === 0) return;
    
    try {
      await Promise.all(selectedConnections.map(id => staffApiService.deleteConnection(id)));
      setSelectedConnections([]);
      loadConnections(); // Reload the list
    } catch (error) {
      console.error('Failed to delete connections:', error);
      setError(error.message || 'Failed to delete selected connections');
    }
  };

  const handleExport = async () => {
    setIsLoading(true);
    try {
      const response = await staffApiService.exportConnections('csv');
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `connections_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export connections:', error);
      setError(error.message || 'Failed to export connections');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTemplate = async () => {
    const header = ['connection_id','service_type','status','account_number','service_identifier','plan_name'];
    const csv = header.join(',') + '\n';
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'connections_import_template.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  // Connection state management functions
  const handleStatusUpdate = (connection) => {
    setSelectedConnection(connection);
    setShowStatusModal(true);
  };

  const handleAssignToContract = (connection) => {
    setSelectedConnection(connection);
    setShowAssignModal(true);
  };

  const handleConfirmStatusUpdate = async (newStatus) => {
    if (!selectedConnection) return;
    
    setIsLoading(true);
    try {
      await staffApiService.updateConnectionStatus(selectedConnection.id, newStatus);
      setShowStatusModal(false);
      setSelectedConnection(null);
      loadConnections(); // Reload to show updated status
    } catch (error) {
      console.error('Failed to update connection status:', error);
      setError(error.message || 'Failed to update connection status');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmContractAssignment = async (contractId) => {
    if (!selectedConnection) return;
    
    setIsLoading(true);
    try {
      if (contractId) {
        await staffApiService.assignConnectionToContract(selectedConnection.id, contractId);
      } else {
        await staffApiService.unassignConnectionFromContract(selectedConnection.id);
      }
      setShowAssignModal(false);
      setSelectedConnection(null);
      loadConnections(); // Reload to show updated assignment
    } catch (error) {
      console.error('Failed to update connection assignment:', error);
      setError(error.message || 'Failed to update connection assignment');
    } finally {
      setIsLoading(false);
    }
  };

  const loadContracts = async () => {
    try {
      const response = await staffApiService.getContracts();
      setContracts(Array.isArray(response) ? response : response?.results || []);
    } catch (error) {
      console.error('Failed to load contracts:', error);
    }
  };

  // Load contracts when assign modal opens
  useEffect(() => {
    if (showAssignModal) {
      loadContracts();
    }
  }, [showAssignModal]);

  const getServiceIcon = (serviceType) => {
    switch (serviceType?.toLowerCase()) {
      case 'electricity':
        return <Zap className="h-4 w-4 text-yellow-500" />;
      case 'broadband':
        return <Wifi className="h-4 w-4 text-blue-500" />;
      case 'mobile':
        return <Smartphone className="h-4 w-4 text-green-500" />;
      default:
        return <Network className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'active': { color: 'green', icon: CheckCircle, label: 'Active' },
      'inactive': { color: 'red', icon: AlertCircle, label: 'Inactive' },
      'suspended': { color: 'yellow', icon: AlertCircle, label: 'Suspended' },
      'pending': { color: 'blue', icon: Clock, label: 'Pending' },
      'disconnected': { color: 'gray', icon: AlertCircle, label: 'Disconnected' }
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
                <h1 className="text-left text-xl font-bold text-gray-900">Connection Management</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Manage customer service connections across all service types
            </p>
          </div>
              
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefresh}
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
                <button onClick={handleTemplate} className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
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
                    await apiClient.post(`${apiBase}/connections/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                  });
                  await loadConnections();
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
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <Plus className="h-3 w-3 mr-1" />
              Add Connection
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
                  <h3 className="text-sm font-medium text-red-800">Error loading connections</h3>
                  <div className="mt-1 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={loadConnections}
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
                  placeholder="Search by connection ID, ICP, or address..."
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
                    { value: 'suspended', label: 'Suspended' }
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
                        onClick={() => handleTypeFilter(option.value)}
                        className={`px-2 py-1 text-xs font-medium rounded-md text-left flex items-center ${
                          typeFilter === option.value
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
                  <option value="connection_id">Connection ID</option>
                  <option value="service_address">Address</option>
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
                    <Network className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Connections</dt>
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
                        {connections.filter(c => c.status === 'active').length}
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
                    {connections.filter(c => c.service_type === 'electricity').length}
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
                    <Users className="h-6 w-6 text-purple-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Selected</dt>
                      <dd className="text-lg font-medium text-gray-900">{selectedConnections.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Connections Table */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden mx-3 md:mx-6">
            <div className="px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Connections ({pagination.count})
                </h3>
                {selectedConnections.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      {selectedConnections.length} selected
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
                        checked={selectedConnections.length === connections.length && connections.length > 0}
                        onChange={handleSelectAllConnections}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('connection_id')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Connection</span>
                        {getSortIcon('connection_id')}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Service
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('service_address')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Address</span>
                        {getSortIcon('service_address')}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Plan
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
                  {connections.map((connection) => (
                    <tr key={connection.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <input
                          type="checkbox"
                          checked={selectedConnections.includes(connection.id)}
                          onChange={() => handleSelectConnection(connection.id)}
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
                              {connection.connection_id || connection.id}
                            </div>
                            <div className="text-sm text-left text-gray-500">
                              {connection.icp_number || connection.service_identifier || 'N/A'}
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
                              #{connection.account?.account_number || connection.account_id || 'N/A'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {connection.account?.primary_user?.email || connection.customer_email || 'N/A'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
                              {getServiceIcon(connection.service_type)}
                            </div>
                          </div>
                          <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                              {connection.service_type || 'Unknown'}
                        </div>
                        <div className="text-sm text-gray-500">
                              {connection.service_details || 'Standard Service'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center">
                              <MapPin className="h-5 w-5 text-gray-600" />
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {connection.service_address || 'N/A'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {connection.address_line_2 || connection.suburb || ''}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="text-sm font-medium text-gray-900">
                          {connection.plan?.name || connection.plan_name || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {connection.plan?.service_type || 'Standard Plan'}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        {getStatusBadge(connection.status)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left text-sm text-gray-500">
                        {formatDate(connection.created_at)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2 text-left">
                        <button
                            onClick={() => handleStatusUpdate(connection)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Update status"
                        >
                            <CheckCircle className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => handleAssignToContract(connection)}
                            className="text-green-600 hover:text-green-900"
                            title="Assign to contract"
                        >
                            <CreditCard className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => handleEditConnection(connection)}
                            className="text-gray-600 hover:text-gray-900"
                            title="Edit connection"
                        >
                            <Edit className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDeleteConnection(connection)}
                          className="text-red-600 hover:text-red-900"
                            title="Delete connection"
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
          {connections.length === 0 && !error && (
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
              <div className="text-center py-12">
                <Network className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-1 text-sm font-medium text-gray-900">No connections found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || statusFilter !== 'all' || typeFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Get started by creating your first connection.'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && typeFilter === 'all' && (
                  <div className="mt-6">
                    <button
                      onClick={() => setIsCreateModalOpen(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Connection
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <ConnectionCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleConnectionSuccess}
        accounts={accounts}
        plans={plans}
      />

      <ConnectionPlanModal
        isOpen={isPlanModalOpen}
        onClose={() => setIsPlanModalOpen(false)}
        connection={selectedConnection}
        plans={plans}
        onSuccess={handleConnectionSuccess}
      />

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-4 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <Trash2 className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-1">Delete Connection</h3>
              <div className="mt-1 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete connection {selectedConnection?.connection_id || selectedConnection?.id}? This action cannot be undone.
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
                    setSelectedConnection(null);
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

      {/* Status Update Modal */}
      {showStatusModal && selectedConnection && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                <CheckCircle className="h-6 w-6 text-blue-600" />
              </div>
              <div className="mt-3 text-center">
                <h3 className="text-lg font-medium text-gray-900">Update Connection Status</h3>
                <div className="mt-2 px-7 py-3">
                  <p className="text-sm text-gray-500">
                    Update status for connection: {selectedConnection.connection_identifier}
                  </p>
                  <div className="mt-4">
                    <select 
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      defaultValue={selectedConnection.status}
                      onChange={(e) => selectedConnection.newStatus = e.target.value}
                    >
                      <option value="pending">Pending</option>
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                      <option value="disconnected">Disconnected</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                </div>
                <div className="items-center px-4 py-3">
                  <button
                    onClick={() => {
                      const select = document.querySelector('select');
                      handleConfirmStatusUpdate(select.value);
                    }}
                    disabled={isLoading}
                    className="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-50"
                  >
                    {isLoading ? 'Updating...' : 'Update'}
                  </button>
                  <button
                    onClick={() => {
                      setShowStatusModal(false);
                      setSelectedConnection(null);
                    }}
                    className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contract Assignment Modal */}
      {showAssignModal && selectedConnection && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <CreditCard className="h-6 w-6 text-green-600" />
              </div>
              <div className="mt-3 text-center">
                <h3 className="text-lg font-medium text-gray-900">Assign to Contract</h3>
                <div className="mt-2 px-7 py-3">
                  <p className="text-sm text-gray-500">
                    Assign connection: {selectedConnection.connection_identifier}
                  </p>
                  <div className="mt-4">
                    <select 
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      defaultValue={selectedConnection.contract_id || ''}
                      onChange={(e) => selectedConnection.newContractId = e.target.value}
                    >
                      <option value="">Unassign from contract</option>
                      {contracts.map(contract => (
                        <option key={contract.id} value={contract.id}>
                          {contract.contract_number} - {contract.account?.account_number}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="items-center px-4 py-3">
                  <button
                    onClick={() => {
                      const select = document.querySelector('select');
                      handleConfirmContractAssignment(select.value || null);
                    }}
                    disabled={isLoading}
                    className="px-4 py-2 bg-green-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300 disabled:opacity-50"
                  >
                    {isLoading ? 'Assigning...' : 'Assign'}
                  </button>
                  <button
                    onClick={() => {
                      setShowAssignModal(false);
                      setSelectedConnection(null);
                    }}
                    className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    
    </div>
  );
};

export default StaffConnections; 