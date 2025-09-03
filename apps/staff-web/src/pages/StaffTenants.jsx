import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import TenantCreateModal from '../components/staff/TenantCreateModal';
import TenantEditModal from '../components/staff/TenantEditModal';
import TenantViewModal from '../components/staff/TenantViewModal';
import { useLoader } from '../context/LoaderContext';
import staffApiService from '../services/staffApi';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Edit, 
  Users, 
  FileText, 
  AlertCircle,
  CheckCircle,
  Download,
  Trash2,
  RefreshCw
} from 'lucide-react';

const StaffTenants = () => {
  const { setLoading } = useLoader();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tenants, setTenants] = useState([]);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [selectedTenants, setSelectedTenants] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [tenantToDelete, setTenantToDelete] = useState(null);
  const [tenantToEdit, setTenantToEdit] = useState(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [tenantToView, setTenantToView] = useState(null);

  // Admin access check
  useEffect(() => {
    if (user && !user.is_superuser && !user.isAdmin && !user.groups?.includes('Admin')) {
      navigate('/users', { replace: true });
      return;
    }
  }, [user, navigate]);

  useEffect(() => {
    loadTenants();
  }, [currentPage, pageSize, searchTerm, statusFilter, sortBy, sortOrder]);

  // Don't render anything if user doesn't have admin access
  if (user && !user.is_superuser && !user.isAdmin && !user.groups?.includes('Admin')) {
    return null;
  }

  const loadTenants = async () => {
    setLoading(true);
    setError(null);
    try {
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

      const response = await staffApiService.getTenants(params);
      setTenants(response.results || []);
      setPagination({
        count: response.count || 0,
        next: response.next,
        previous: response.previous,
        current_page: currentPage,
        total_pages: Math.ceil((response.count || 0) / pageSize)
      });
    } catch (error) {
      console.error('Failed to load tenants:', error);
      setError(error.message || 'Failed to load tenants');
      // Fallback to empty state
      setTenants([]);
      setPagination({
        count: 0,
        next: null,
        previous: null,
        current_page: 1,
        total_pages: 1
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1); // Reset to first page on search
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Intl.DateTimeFormat('en-NZ', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(new Date(dateString));
  };

  const getStatusBadge = (isActive) => {
    if (isActive) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Active
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <AlertCircle className="w-3 h-3 mr-1" />
          Inactive
        </span>
      );
    }
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  };

  const handleSelectTenant = (tenantId) => {
    setSelectedTenants(prev => {
      if (prev.includes(tenantId)) {
        return prev.filter(id => id !== tenantId);
      } else {
        return [...prev, tenantId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedTenants.length === tenants.length) {
      setSelectedTenants([]);
    } else {
      setSelectedTenants(tenants.map(t => t.id));
    }
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
              : 'text-gray-700 hover:bg-white border border-gray-300'
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
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <div className="flex space-x-1">
            {pages}
          </div>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={!pagination.next}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  const handleExport = async () => {
    setIsLoading(true);
    try {
      // Try server export first
      try {
        const response = await staffApiService.exportTenants('csv');
        const url = window.URL.createObjectURL(new Blob([response]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `tenants_export_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        return;
      } catch (serverErr) {
        console.warn('Server export failed, falling back to client-side CSV:', serverErr);
      }

      // Fallback: fetch all pages client-side and build CSV
      const header = ['name','slug','business_number','tax_number','contact_email','contact_phone','address','timezone','currency','is_active'];
      let csvRows = [header.join(',')];
      let page = 1;
      const pageSize = 100;
      // Limit to avoid runaway loops
      for (let i = 0; i < 200; i++) {
        const resp = await staffApiService.getTenants({ page, page_size: pageSize, ordering: 'name' });
        const items = resp?.results || [];
        for (const t of items) {
          const row = [
            t.name || '', t.slug || '', t.business_number || '', t.tax_number || '',
            t.contact_email || '', t.contact_phone || '', (t.address || '').toString().replace(/\n|\r/g, ' '),
            t.timezone || 'Pacific/Auckland', t.currency || 'NZD', (t.is_active ? 'true' : 'false')
          ].map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',');
          csvRows.push(row);
        }
        if (!resp?.next || items.length === 0) break;
        page += 1;
      }
      const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tenants_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export tenants:', error);
      setError(error.message || 'Failed to export tenants');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditTenant = (tenant) => {
    setTenantToEdit(tenant);
    setShowEditModal(true);
  };

  const handleEditSuccess = (updatedTenant) => {
    console.log('Tenant updated successfully:', updatedTenant);
    loadTenants(); // Refresh the list
    setShowEditModal(false);
    setTenantToEdit(null);
  };

  const handleViewTenant = (tenant) => {
    setTenantToView(tenant);
    setShowViewModal(true);
  };

  const handleCreateTenant = () => {
    setShowCreateModal(true);
  };

  const handleCreateSuccess = (newTenant) => {
    console.log('Tenant created successfully:', newTenant);
    loadTenants(); // Refresh the list
    setShowCreateModal(false);
  };

  const handleDeleteTenant = async (tenant) => {
    setTenantToDelete(tenant);
    setShowDeleteDialog(true);
  };

  const confirmDeleteTenant = async () => {
    if (!tenantToDelete) return;
    
    setIsLoading(true);
    try {
      await staffApiService.deleteTenant(tenantToDelete.id);
      await loadTenants(); // Refresh the list
      setShowDeleteDialog(false);
      setTenantToDelete(null);
    } catch (error) {
      console.error('Failed to delete tenant:', error);
      setError(error.message || 'Failed to delete tenant');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkDeleteSelected = async () => {
    if (!selectedTenants || selectedTenants.length === 0) return;
    const confirmed = window.confirm(`Delete ${selectedTenants.length} selected tenant(s)? This cannot be undone.`);
    if (!confirmed) return;

    setIsLoading(true);
    try {
      const deletions = selectedTenants.map((tenantId) => staffApiService.deleteTenant(tenantId));
      await Promise.allSettled(deletions);
      setSelectedTenants([]);
      await loadTenants();
    } catch (err) {
      console.error('Bulk delete failed:', err);
      setError(err.message || 'Failed to delete selected tenants');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
    
      <div className="min-h-screen bg-white">
        {/* Header */}
        <div className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-6">
            <div className="flex justify-between items-center py-6 space-y-0">
              <div>
                <h1 className="text-left text-xl font-bold text-gray-900">Tenant Management</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Manage all tenant organizations and their settings
                </p>
              </div>
              
              <div className="flex items-center space-x-3">
                <button
                  onClick={loadTenants}
                  disabled={isLoading}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={handleExport}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <Download className="h-3 w-3 mr-1" />
                  Export
                </button>
                <button
                  onClick={async () => {
                    // Client-side template generation (no API dependency)
                    const header = ['name','slug','business_number','tax_number','contact_email','contact_phone','address','timezone','currency','is_active'];
                    const csv = header.join(',') + '\n';
                    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', 'tenants_import_template.csv');
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    window.URL.revokeObjectURL(url);
                  }}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <Download className="h-3 w-3 mr-1" />
                  Template
                </button>
                <label className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-white cursor-pointer">
                  <input type="file" accept=".csv" className="hidden" onChange={async (e) => {
                    const file = e.target.files && e.target.files[0];
                    if (!file) return;
                    setIsLoading(true);
                    try {
                      const formData = new FormData();
                      formData.append('file', file);
                      // Use same axios client as staffApiService to include auth automatically
                      const apiBase = staffApiService.baseURL || '/staff/v1';
                      await import('../services/apiClient').then(async ({ default: apiClient }) => {
                        await apiClient.post(`${apiBase}/tenants/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                      });
                      await loadTenants();
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
                  onClick={handleCreateTenant}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Tenant
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {/* Error Alert */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error loading tenants</h3>
                  <div className="mt-1 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={loadTenants}
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
                  placeholder="Search by name, slug, or email..."
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
                  <option value="name">Name</option>
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
                    <Building2 className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Tenants</dt>
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
                        {tenants.filter(t => t.is_active).length}
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
                    <Users className="h-6 w-6 text-blue-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Users</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {tenants.reduce((sum, t) => sum + (t.users_count || 0), 0)}
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
                      <dd className="text-lg font-medium text-gray-900">{selectedTenants.length}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tenants Table */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden mx-3 md:mx-6">
            <div className="px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  Tenants ({pagination.count})
                </h3>
                {selectedTenants.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      {selectedTenants.length} selected
                    </span>
                    <button onClick={handleBulkDeleteSelected} className="text-sm text-red-600 hover:text-red-800">
                      Delete Selected
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-white">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedTenants.length === tenants.length && tenants.length > 0}
                        onChange={handleSelectAll}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Tenant</span>
                        {getSortIcon('name')}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Users
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
                  {tenants.map((tenant) => (
                    <tr key={tenant.id} className="hover:bg-white">
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <input
                          type="checkbox"
                          checked={selectedTenants.includes(tenant.id)}
                          onChange={() => handleSelectTenant(tenant.id)}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                              <span className="text-indigo-600 font-semibold text-sm">
                                {tenant.name?.split(' ').map(word => word[0]).join('').slice(0, 2) || 'T'}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {tenant.name}
                            </div>
                            <div className="text-sm text-left text-gray-500">
                              {tenant.slug}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="text-sm text-gray-900">{tenant.contact_email}</div>
                        <div className="text-sm text-gray-500">{tenant.contact_phone}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 text-gray-400 mr-1" />
                          <span className="text-sm text-gray-900">{tenant.users_count || 0}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        {getStatusBadge(tenant.is_active)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left text-sm text-gray-500">
                        {formatDate(tenant.created_at)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2 text-left">
                          <button
                            onClick={() => handleViewTenant(tenant)}
                            className="text-indigo-600 hover:text-indigo-900"
                            title="View tenant details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleEditTenant(tenant)}
                            className="text-gray-600 hover:text-gray-900"
                            title="Edit tenant"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteTenant(tenant)}
                            className="text-red-600 hover:text-red-900"
                            title="Delete tenant"
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
          {tenants.length === 0 && !error && (
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
              <div className="text-center py-12">
                <Building2 className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-1 text-sm font-medium text-gray-900">No tenants found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || statusFilter !== 'all' 
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Get started by creating your first tenant.'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && (
                  <div className="mt-6">
                    <button
                      onClick={handleCreateTenant}
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create Tenant
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Create Tenant Modal */}
        <TenantCreateModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />

        {/* Edit Tenant Modal */}
        {showEditModal && (
          <TenantEditModal
            isOpen={showEditModal}
            onClose={() => {
              setShowEditModal(false);
              setTenantToEdit(null);
            }}
            onSuccess={handleEditSuccess}
            tenantId={tenantToEdit?.id}
          />
        )}

        {/* View Tenant Modal */}
        <TenantViewModal
          isOpen={showViewModal}
          onClose={() => {
            setShowViewModal(false);
            setTenantToView(null);
          }}
          tenantId={tenantToView?.id}
        />

        {/* Delete Confirmation Dialog */}
        {showDeleteDialog && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-4 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3 text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <Trash2 className="h-6 w-6 text-red-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mt-1">Delete Tenant</h3>
                <div className="mt-1 px-7 py-3">
                  <p className="text-sm text-gray-500">
                    Are you sure you want to delete &quot;{tenantToDelete?.name}&quot;? This action cannot be undone.
                  </p>
                </div>
                <div className="items-center px-4 py-3">
                  <button
                    onClick={confirmDeleteTenant}
                    disabled={isLoading}
                    className="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300 disabled:opacity-50"
                  >
                    {isLoading ? 'Deleting...' : 'Delete'}
                  </button>
                  <button
                    onClick={() => {
                      setShowDeleteDialog(false);
                      setTenantToDelete(null);
                    }}
                    className="px-4 py-2 bg-white text-gray-700 border border-gray-300 text-base font-medium rounded-md w-24 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    
    </div>
  );
};

export default StaffTenants; 