import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import UserCreateModal from '../components/staff/UserCreateModal';
import UserEditModal from '../components/staff/UserEditModal';
import UserDetailModal from '../components/staff/UserDetailModal';
import { useLoader } from '../context/LoaderContext';
import { useAuth } from '../hooks/useAuth';
import staffApiService from '../services/staffApi';
import { 
  Users, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Edit, 
  UserCheck, 
  UserX,
  Building2,
  AlertCircle,
  CheckCircle,
  Shield,
  Trash2,
  RefreshCw,
  Download
} from 'lucide-react';

const StaffUsers = () => {
  const { setLoading } = useLoader();
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tenantFilter, setTenantFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');
  const [sortBy, setSortBy] = useState('email');
  const [sortOrder, setSortOrder] = useState('asc');
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState(null);

  // Check if current user is super admin
  const isSuperAdmin = currentUser?.is_superuser || false;

  // Function definitions (moved before useEffect to avoid hoisting issues)
  const loadTenants = async () => {
    try {
      const response = await staffApiService.getTenants({ page_size: 100 });
      const tenantsList = response.results || [];
      setTenants(tenantsList);
      
      // Auto-select staff's tenant if not super admin
      if (!isSuperAdmin && currentUser && tenantsList.length > 0) {
        // Try different possible tenant field names
        const tenantId = currentUser.tenant_id || currentUser.tenant?.id;
        const tenantName = currentUser.tenant_name || currentUser.tenant?.name;
        
        let userTenant = null;
        if (tenantId) {
          userTenant = tenantsList.find(t => t.id === tenantId);
        } else if (tenantName) {
          userTenant = tenantsList.find(t => t.name === tenantName);
        }
        
        if (userTenant) {
          setTenantFilter(userTenant.id);
        } else if (tenantsList.length === 1) {
          // If only one tenant available, select it for non-super admin
          setTenantFilter(tenantsList[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading tenants:', error);
      setError('Failed to load tenants');
    }
  };

  // Admin access check
  useEffect(() => {
    if (currentUser && !currentUser.is_superuser && !currentUser.isAdmin && !currentUser.groups?.includes('Admin')) {
      navigate('/', { replace: true });
      return;
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    loadTenants();
  }, [currentUser]);

  useEffect(() => {
    loadUsers();
  }, [currentPage, pageSize, searchTerm, statusFilter, tenantFilter, roleFilter, sortBy, sortOrder]);

  // Listen for global refresh events from the sidebar refresh button
  useEffect(() => {
    const onRefresh = () => {
      loadUsers();
    };
    window.addEventListener('staff:refresh', onRefresh);
    return () => window.removeEventListener('staff:refresh', onRefresh);
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setIsLoading(true);
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

      if (tenantFilter !== 'all') {
        params.tenant = tenantFilter;
      }

      if (roleFilter !== 'all') {
        params.is_staff = roleFilter === 'staff';
      }

      const response = await staffApiService.getUsers(params);
      setUsers(response.results || []);
      setPagination({
        count: response.count || 0,
        next: response.next,
        previous: response.previous,
        current_page: currentPage,
        total_pages: Math.ceil((response.count || 0) / pageSize)
      });
    } catch (error) {
      console.error('Failed to load users:', error);
      setError(error.message || 'Failed to load users');
      setUsers([]);
      setPagination({
        count: 0,
        next: null,
        previous: null,
        current_page: 1,
        total_pages: 1
      });
    } finally {
      setLoading(false);
      setIsLoading(false);
    }
  };

  // Don't render anything if user doesn't have admin access
  if (currentUser && !currentUser.is_superuser && !currentUser.isAdmin && !currentUser.groups?.includes('Admin')) {
    return null;
  }



  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const handleStatusFilter = (status) => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleTenantFilter = (tenant) => {
    setTenantFilter(tenant);
    try {
      if (tenant === 'all') {
        localStorage.removeItem('selectedTenantId');
      } else {
        localStorage.setItem('selectedTenantId', tenant);
      }
    } catch (e) {}
    setCurrentPage(1);
  };

  const handleRoleFilter = (role) => {
    setRoleFilter(role);
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

  const handleToggleUserActive = async (userId) => {
    try {
      setLoading(true);
      await staffApiService.toggleUserActive(userId);
      await loadUsers(); // Refresh the list
    } catch (error) {
      console.error('Failed to toggle user status:', error);
      setError(error.message || 'Failed to update user status');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString || dateString === null || dateString === 'null') return 'Never';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Never';
      return new Intl.DateTimeFormat('en-NZ', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    } catch (error) {
      console.error('Failed to format date:', error);
      return 'Never';
    }
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

  const getRoleBadge = (isStaff, isSuperuser) => {
    if (isSuperuser) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          <Shield className="w-3 h-3 mr-1" />
          Super Admin
        </span>
      );
    } else if (isStaff) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <UserCheck className="w-3 h-3 mr-1" />
          Staff
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          <UserX className="w-3 h-3 mr-1" />
          Customer
        </span>
      );
    }
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  };

  const handleSelectUser = (userId) => {
    setSelectedUsers(prev => {
      if (prev.includes(userId)) {
        return prev.filter(id => id !== userId);
      } else {
        return [...prev, userId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedUsers.length === users.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users.map(u => u.id));
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
          className={`px-3 py-2 text-xs font-medium rounded-md ${
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
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center text-xs text-gray-700">
          <span>
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, pagination.count)} of {pagination.count} results
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={!pagination.previous}
            className="px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <div className="flex space-x-1">
            {pages}
          </div>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={!pagination.next}
            className="px-3 py-2 text-xs font-medium text-gray-700 bg-gray-50 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
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
        const response = await staffApiService.exportUsers('csv');
        const url = window.URL.createObjectURL(new Blob([response]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `users_export_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        return;
      } catch (serverErr) {
        console.warn('Server users export failed, falling back to client-side CSV:', serverErr);
      }

      // Fallback: fetch all pages client-side and build CSV with available fields
      const header = ['email','first_name','last_name','is_staff','is_active','last_login','date_joined'];
      let csvRows = [header.join(',')];
      let page = 1;
      const pageSize = 100;
      for (let i = 0; i < 200; i++) {
        const resp = await staffApiService.getUsers({ page, page_size: pageSize, ordering: 'email' });
        const items = resp?.results || [];
        for (const u of items) {
          const row = [
            u.email || '', u.first_name || '', u.last_name || '',
            u.is_staff ? 'true' : 'false', u.is_active ? 'true' : 'false',
            u.last_login || '', u.date_joined || ''
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
      link.setAttribute('download', `users_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export users:', error);
      setError(error.message || 'Failed to export users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = () => {
    setShowCreateModal(true);
  };

  const handleCreateSuccess = (newUser) => {
    console.log('User created successfully:', newUser);
    loadUsers(); // Refresh the list
    setShowCreateModal(false);
  };

  const handleEditUser = (userId) => {
    setSelectedUserId(userId);
    setShowDetailModal(false); // Close view modal when opening edit
    setShowEditModal(true);
  };

  const handleEditSuccess = (updatedUser) => {
    console.log('User updated successfully:', updatedUser);
    loadUsers(); // Refresh the list
    setShowEditModal(false);
    setSelectedUserId(null);
  };

  const handleViewUser = (userId) => {
    setSelectedUserId(userId);
    setShowDetailModal(true);
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      await staffApiService.deleteUser(userId);
      await loadUsers(); // Refresh the list
      setShowDetailModal(false);
      setSelectedUserId(null);
    } catch (error) {
      console.error('Failed to delete user:', error);
      setError(error.message || 'Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkActivate = async () => {
    if (selectedUsers.length === 0) return;
    
    try {
      setLoading(true);
      await staffApiService.bulkUpdateUsers(selectedUsers, { is_active: true });
      await loadUsers();
      setSelectedUsers([]);
    } catch (error) {
      console.error('Failed to activate users:', error);
      setError(error.message || 'Failed to activate users');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDeactivate = async () => {
    if (selectedUsers.length === 0) return;
    
    try {
      setLoading(true);
      await staffApiService.bulkUpdateUsers(selectedUsers, { is_active: false });
      await loadUsers();
      setSelectedUsers([]);
    } catch (error) {
      console.error('Failed to deactivate users:', error);
      setError(error.message || 'Failed to deactivate users');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedUsers.length === 0) return;
    
    if (!window.confirm(`Are you sure you want to delete ${selectedUsers.length} users? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      await staffApiService.bulkDeleteUsers(selectedUsers);
      await loadUsers();
      setSelectedUsers([]);
    } catch (error) {
      console.error('Failed to delete users:', error);
      setError(error.message || 'Failed to delete users');
    } finally {
      setLoading(false);
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
                <h1 className="text-left text-xl font-bold text-gray-900">User Management</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage all user accounts and their permissions
        </p>
      </div>
              
              <div className="flex items-center space-x-3">
                <button
                  onClick={loadUsers}
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
                    // Client-side template generation
                    const header = ['email','first_name','last_name','mobile','user_type','department','job_title','tenant_slug','manager_email','is_staff','is_active'];
                    const csv = header.join(',') + '\n';
                    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', 'users_import_template.csv');
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
                        await apiClient.post(`${apiBase}/users/import/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                      });
                      await loadUsers();
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
                  onClick={handleCreateUser}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add User
                </button>
              </div>
    </div>
  </div>
</div>
        <div className="space-y-4">
          {/* Error Alert */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-3 mx-3 md:mx-6 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-xs font-medium text-red-800">Error loading users</h3>
                  <div className="mt-0.5 text-xs text-red-700">
                    <p>{error}</p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={loadUsers}
                      className="text-xs bg-red-100 text-red-800 rounded-md px-3 py-1 hover:bg-red-200"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* Filters and Search */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 mt-6 mb-4 p-4 mx-3 md:mx-6">
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
                    placeholder="Search by name, email, or phone..."
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
                <label className="block text-left text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={roleFilter}
                    onChange={(e) => handleRoleFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="all">All</option>
                    <option value="staff">Staff</option>
                    <option value="customer">Customer</option>
                  </select>
                </div>
                
                {/* Tenant filter - only show for super admin */}
                {isSuperAdmin && (
                  <div>
                    <label htmlFor="tenantFilter" className="block text-left text-sm font-medium text-gray-700 mb-1">
                      Tenant
                    </label>
                    <select
                      id="tenantFilter"
                      value={tenantFilter}
                      onChange={(e) => handleTenantFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="all">All Tenants</option>
                      {tenants.map(tenant => (
                        <option key={tenant.id} value={tenant.id}>
                          {tenant.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                
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
          </div>

          {/* Stats Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 mx-3 md:mx-6">
            <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
              <div className="p-3">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Users className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">Total Users</dt>
                      <dd className="text-base font-medium text-gray-900">{pagination.count}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
              <div className="p-3">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-5 w-5 text-green-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">Active</dt>
                      <dd className="text-base font-medium text-gray-900">
                        {users.filter(u => u.is_active).length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
              <div className="p-3">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <UserCheck className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">Staff</dt>
                      <dd className="text-base font-medium text-gray-900">
                        {users.filter(u => u.is_staff).length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
              <div className="p-3">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <UserX className="h-5 w-5 text-purple-400" />
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <dl>
                      <dt className="text-xs font-medium text-gray-500 truncate">Selected</dt>
                      <dd className="text-base font-medium text-gray-900">{selectedUsers.length}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Users Table */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden mx-3 md:mx-6">
            <div className="px-3 py-2 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-gray-900">
                  Users ({pagination.count})
                </h3>
                {selectedUsers.length > 0 && (
                  <div className="flex items-center space-x-3">
                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-md">
                      {selectedUsers.length} selected
                    </span>
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={handleBulkActivate}
                        className="text-xs text-green-600 hover:text-green-800 flex items-center bg-green-50 px-2 py-1 rounded-md hover:bg-green-100"
                      >
                        <UserCheck className="w-3 h-3 mr-1" />
                        Activate
                      </button>
                      <button
                        onClick={handleBulkDeactivate}
                        className="text-xs text-orange-600 hover:text-orange-800 flex items-center bg-orange-50 px-2 py-1 rounded-md hover:bg-orange-100"
                      >
                        <UserX className="w-3 h-3 mr-1" />
                        Deactivate
                      </button>
                      <button
                        onClick={handleBulkDelete}
                        className="text-xs text-red-600 hover:text-red-800 flex items-center bg-red-50 px-2 py-1 rounded-md hover:bg-red-100"
                      >
                        <Trash2 className="w-3 h-3 mr-1" />
                        Delete
                      </button>
                    </div>
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
                        checked={selectedUsers.length === users.length && users.length > 0}
                        onChange={handleSelectAll}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('first_name')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>User</span>
                        {getSortIcon('first_name')}
                      </div>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tenant
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('last_login')}
                    >
                      <div className="flex items-center space-x-1">
                        <span>Last Login</span>
                        {getSortIcon('last_login')}
                      </div>
                    </th>
                    <th className="relative px-4 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <input
                          type="checkbox"
                          checked={selectedUsers.includes(user.id)}
                          onChange={() => handleSelectUser(user.id)}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-8 w-8 flex-shrink-0">
                            <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center">
                              <span className="text-gray-600 font-semibold text-xs">
                                {user.first_name?.[0]}{user.last_name?.[0]}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-xs font-medium text-gray-900">
                              {user.first_name} {user.last_name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {user.user_number ? `#${user.user_number}` : `ID: ${user.id}`}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="text-sm text-gray-900">{user.email}</div>
                        {user.phone_number && (
                          <div className="text-sm text-gray-500">{user.phone_number}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        <div className="flex items-center">
                          <Building2 className="w-4 h-4 text-gray-400 mr-1" />
                          <span className="text-sm text-gray-900">{user.tenant_name || 'N/A'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        {getRoleBadge(user.is_staff, user.is_superuser)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left">
                        {getStatusBadge(user.is_active)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-left text-sm text-gray-500">
                          {formatDate(user.last_login)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center space-x-2 text-left">
                          <button
                            onClick={() => handleViewUser(user.id)}
                            className="text-indigo-600 hover:text-indigo-900"
                            title="View user details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleEditUser(user.id)}
                            className="text-gray-600 hover:text-gray-900"
                            title="Edit user"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleToggleUserActive(user.id)}
                            className={`${
                              user.is_active 
                                ? 'text-red-600 hover:text-red-900' 
                                : 'text-green-600 hover:text-green-900'
                            }`}
                            title={user.is_active ? 'Deactivate user' : 'Activate user'}
                          >
                            {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
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
          {users.length === 0 && !error && (
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6 mx-3 md:mx-6">
              <div className="text-center py-12">
                <Users className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-0.5 text-xs font-medium text-gray-900">No users found</h3>
                <p className="mt-0.5 text-xs text-gray-500">
                  {searchTerm || statusFilter !== 'all' || tenantFilter !== 'all' || roleFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Get started by creating your first user.'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && tenantFilter === 'all' && roleFilter === 'all' && (
                  <div className="mt-6">
                    <Link
                      to="/users/create"
                      className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Create User
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Create User Modal */}
          <UserCreateModal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            onSuccess={handleCreateSuccess}
          />

          {/* Edit User Modal */}
          <UserEditModal
            isOpen={showEditModal}
            onClose={() => {
              setShowEditModal(false);
              setSelectedUserId(null);
            }}
            onSuccess={handleEditSuccess}
            userId={selectedUserId}
          />

          {/* User Detail Modal */}
          <UserDetailModal
            isOpen={showDetailModal}
            onClose={() => {
              setShowDetailModal(false);
              setSelectedUserId(null);
            }}
            userId={selectedUserId}
            onEdit={handleEditUser}
            onDelete={handleDeleteUser}
          />
        </div>
    
    </div>
  );
};

export default StaffUsers; 