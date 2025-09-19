import { useState, useEffect } from 'react';
import { 
  Plus, Search, Filter, Download, RefreshCw, Eye, Edit, Trash2,
  Zap, Wifi, Smartphone, DollarSign, Hash, AlertCircle,
  Users, FileText, ChevronDown, ChevronRight
} from 'lucide-react';
import staffApiService from '../services/staffApi';

const StaffPlans = () => {
  const [plans, setPlans] = useState([]);
  const [assignedPlans, setAssignedPlans] = useState([]);
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
  const [viewMode, setViewMode] = useState('available'); // 'available' or 'assigned'
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState({});

  // Modal states
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    loadPlans();
    if (viewMode === 'assigned') {
      loadAssignedPlans();
    }
  }, [currentPage, pageSize, searchTerm, statusFilter, typeFilter, sortBy, sortOrder, viewMode]);

  const loadPlans = async () => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('🔄 Loading plans with params:', { 
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
        params.is_active = statusFilter === 'active';
      }

      if (typeFilter !== 'all') {
        params.service_type = typeFilter;
      }

      const response = await staffApiService.getPlans(params);
      console.log('📊 Plans API response:', response);

      // Handle both paginated and direct array responses
      let plansData = [];
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
          plansData = response.results;
          paginationData = {
            count: response.count || 0,
            next: response.next,
            previous: response.previous,
            current_page: currentPage,
            total_pages: Math.ceil((response.count || 0) / pageSize)
          };
        } else if (Array.isArray(response)) {
          // Direct array response
          plansData = response;
          paginationData.count = response.length;
        } else {
          // Single object or other format
          plansData = [response];
          paginationData.count = 1;
        }
      } else if (Array.isArray(response)) {
        plansData = response;
        paginationData.count = response.length;
      }

      console.log('✅ Processed plans data:', { 
        count: plansData.length,
        pagination: paginationData,
        sample: plansData[0]
      });

      setPlans(plansData);
      setPagination(paginationData);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('❌ Failed to load plans:', error);
      setError(error.message || 'Failed to load plans');
      setPlans([]);
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

  const loadAssignedPlans = async () => {
    try {
      // This would typically fetch connections with their assigned plans
      const connectionsResponse = await staffApiService.getConnections({ with_plans: true });
      const connectionsData = Array.isArray(connectionsResponse) ? connectionsResponse : 
                             (connectionsResponse?.results ? connectionsResponse.results : []);
      
      // Group connections by plan
      const planGroups = {};
      connectionsData.forEach(connection => {
        if (connection.plan) {
          const planKey = connection.plan.id;
          if (!planGroups[planKey]) {
            planGroups[planKey] = {
              plan: connection.plan,
              connections: []
            };
          }
          planGroups[planKey].connections.push(connection);
        }
      });

      setAssignedPlans(Object.values(planGroups));
    } catch (error) {
      console.error('❌ Failed to load assigned plans:', error);
      setAssignedPlans([]);
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

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handlePageSizeChange = (size) => {
    setPageSize(size);
    setCurrentPage(1);
  };

  const handleRefresh = () => {
    loadPlans();
    if (viewMode === 'assigned') {
      loadAssignedPlans();
    }
  };

  const handleViewPlan = (plan) => {
    setSelectedPlan(plan);
    // Open plan detail modal or navigate to plan details
  };

  const handleEditPlan = (plan) => {
    setSelectedPlan(plan);
    // Open edit modal
  };

  const handleDeletePlan = (plan) => {
    setSelectedPlan(plan);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    try {
      await staffApiService.deletePlan(selectedPlan.id);
      setShowDeleteConfirm(false);
      setSelectedPlan(null);
      handleRefresh();
    } catch (error) {
      console.error('Failed to delete plan:', error);
    }
  };

  const handlePlanSuccess = () => {
    handleRefresh();
  };

  const handleExport = async () => {
    try {
      const response = await staffApiService.exportPlans();
      const blob = new Blob([response], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `plans_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleTemplate = async () => {
    const header = ['service_type','name','description','monthly_charge','base_rate','setup_fee','term','city','status'];
    const csv = header.join(',') + '\n';
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'plans_import_template.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const toggleGroupExpansion = (groupKey) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupKey]: !prev[groupKey]
    }));
  };

  const getServiceIcon = (serviceType) => {
    switch (serviceType) {
      case 'electricity':
        return <Zap className="h-4 w-4 text-yellow-600" />;
      case 'broadband':
        return <Wifi className="h-4 w-4 text-purple-600" />;
      case 'mobile':
        return <Smartphone className="h-4 w-4 text-blue-600" />;
      default:
        return <FileText className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (status) {
      case 'active':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'inactive':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      case 'pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined || isNaN(amount)) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  const renderPagination = () => {
    if (pagination.total_pages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(pagination.total_pages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`px-3 py-2 text-sm font-medium rounded-md ${
            i === currentPage
              ? 'bg-indigo-600 text-white'
              : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
          }`}
        >
          {i}
        </button>
      );
    }

    return (
    <div className="min-h-screen bg-gray-50 p-8">
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
    </div>
    );
  };

  const totalRevenue = plans.reduce((sum, plan) => sum + (plan.monthly_charge * (plan.active_connections_count || 0)), 0);
  const totalConnections = plans.reduce((sum, plan) => sum + (plan.active_connections_count || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
    
      <div className="px-6 p-4 space-y-4">
        {/* Header */}
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Service Plans</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage pricing plans for electricity, broadband, and mobile services
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
              <button 
                onClick={handleExport}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Download className="h-3 w-3 mr-1" />
                Export
              </button>
              <button 
                onClick={handleTemplate}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
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
                      await apiClient.post(`${apiBase}/plans/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                    });
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
                onClick={() => console.log('Add plan functionality not implemented')}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Plus className="h-3 w-3 mr-1" />
                Add Plan
              </button>
            </div>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => handleViewModeChange('available')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'available'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Available Plans
              </button>
              <button
                onClick={() => handleViewModeChange('assigned')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'assigned'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Assigned Plans
              </button>
            </div>
            {lastRefresh && (
              <span className="text-sm text-gray-500">
                Last updated: {lastRefresh}
              </span>
            )}
          </div>
        </div>

        {/* Filters and Search */}
        <div className="mb-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search plans..."
                value={searchTerm}
                onChange={handleSearch}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            {/* Service Type Filter */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Filter className="h-5 w-5 text-gray-400" />
              </div>
              <select
                value={typeFilter}
                onChange={(e) => handleTypeFilter(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="all">All Services</option>
                <option value="electricity">Electricity</option>
                <option value="broadband">Broadband</option>
                <option value="mobile">Mobile</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => handleStatusFilter(e.target.value)}
                className="block w-full pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DollarSign className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Monthly Revenue</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {formatCurrency(totalRevenue)}
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
                  <Users className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Connections</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {totalConnections.toLocaleString()}
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
                  <FileText className="h-8 w-8 text-indigo-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active Plans</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {plans.filter(p => p.status === 'active').length}
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
                  <Hash className="h-8 w-8 text-yellow-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Avg. Revenue</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {formatCurrency(plans.length > 0 ? totalRevenue / plans.length : 0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:p-4">
            {error ? (
              <div className="text-center py-12">
                <div className="text-red-600 mb-2">
                  <AlertCircle className="mx-auto h-12 w-12" />
                </div>
                <p className="text-sm text-red-600 font-medium">Error loading plans</p>
                <p className="text-sm text-gray-500 mt-1">{error}</p>
                <button 
                  onClick={handleRefresh}
                  className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Try Again
                </button>
              </div>
            ) : isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <p className="mt-1 text-sm text-gray-500">Loading plans...</p>
              </div>
            ) : viewMode === 'available' ? (
              // Available Plans Grid
              plans.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-sm text-gray-500">No plans found matching your criteria.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {plans.map((plan) => (
                    <div key={plan.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-2">
                          {getServiceIcon(plan.service_type)}
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                            plan.service_type === 'electricity' ? 'bg-yellow-100 text-yellow-800' :
                            plan.service_type === 'broadband' ? 'bg-purple-100 text-purple-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {plan.service_type}
                          </span>
                        </div>
                        <span className={getStatusBadge(plan.status)}>
                          {plan.status}
                        </span>
                      </div>

                      <div className="mt-4">
                        <h3 className="text-lg font-medium text-gray-900">{plan.name}</h3>
                        <p className="mt-1 text-sm text-gray-500 line-clamp-2">{plan.description}</p>
                      </div>

                      <div className="mt-4 space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Monthly Rate:</span>
                          <span className="font-medium text-gray-900">{formatCurrency(plan.monthly_charge)}</span>
                        </div>
                        
                        {plan.service_type === 'electricity' && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-500">Unit Rate:</span>
                            <span className="font-medium text-gray-900">{formatCurrency(plan.base_rate)}</span>
                          </div>
                        )}
                        
                        {plan.service_type === 'broadband' && (
                          <>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">Speed:</span>
                              <span className="font-medium text-gray-900">{plan.download_speed} Mbps</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">Data:</span>
                              <span className="font-medium text-gray-900">{plan.data_allowance}</span>
                            </div>
                          </>
                        )}
                        
                        {plan.service_type === 'mobile' && (
                          <>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">Data:</span>
                              <span className="font-medium text-gray-900">{plan.data_allowance}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">Minutes:</span>
                              <span className="font-medium text-gray-900">{plan.call_minutes}</span>
                            </div>
                          </>
                        )}
                      </div>

                      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
                        <span>{plan.active_connections_count || 0} active connections</span>
                        <span>{formatDate(plan.created_at)}</span>
                      </div>

                      <div className="mt-4 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <button 
                            onClick={() => handleViewPlan(plan)}
                            className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
                            title="View Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => handleEditPlan(plan)}
                            className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded-md transition-colors"
                            title="Edit Plan"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => handleDeletePlan(plan)}
                            className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                            title="Delete Plan"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : (
              // Assigned Plans View
              assignedPlans.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-sm text-gray-500">No assigned plans found.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {assignedPlans.map((group) => (
                    <div key={group.plan.id} className="border border-gray-200 rounded-lg">
                      <div 
                        className="p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                        onClick={() => toggleGroupExpansion(group.plan.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            {expandedGroups[group.plan.id] ? (
                              <ChevronDown className="h-5 w-5 text-gray-400" />
                            ) : (
                              <ChevronRight className="h-5 w-5 text-gray-400" />
                            )}
                            {getServiceIcon(group.plan.service_type)}
                            <div>
                              <h3 className="text-lg font-medium text-gray-900">{group.plan.name}</h3>
                              <p className="text-sm text-gray-500">{group.plan.service_type}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            <span className="text-sm text-gray-500">
                              {group.connections.length} connections
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {formatCurrency(group.plan.monthly_charge)}
                            </span>
                            <span className={getStatusBadge(group.plan.status)}>
                              {group.plan.status}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {expandedGroups[group.plan.id] && (
                        <div className="p-4 border-t border-gray-200">
                          <div className="space-y-3">
                            {group.connections.map((connection) => (
                              <div key={connection.id} className="flex items-center justify-between p-3 bg-white border border-gray-100 rounded-md">
                                <div className="flex items-center space-x-3">
                                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                  <div>
                                    <p className="text-sm font-medium text-gray-900">
                                      Connection #{connection.id}
                                    </p>
                                    <p className="text-sm text-gray-500">
                                      {connection.account?.name || 'Unknown Account'}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-4">
                                  <span className="text-sm text-gray-500">
                                    {formatDate(connection.created_at)}
                                  </span>
                                  <span className={getStatusBadge(connection.status)}>
                                    {connection.status}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Confirm Deletion</h2>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to delete plan &quot;{selectedPlan?.name}&quot;? This action cannot be undone.
              </p>
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDelete}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Pagination */}
        {viewMode === 'available' && renderPagination()}
      </div>
    
    </div>
  );
};

export default StaffPlans; 