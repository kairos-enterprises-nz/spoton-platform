// Staff API service functions
import apiClient from './apiClient';

class StaffApiService {
  constructor() {
    this.baseURL = '/api/staff';
  }

  // Get current tenant filter for multi-tenant operations
  getCurrentTenantFilter() {
    try {
      // For super admin users, allow tenant selection
      // For regular users, use their assigned tenant
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      
      if (user.is_superuser) {
        return localStorage.getItem('selectedTenantId') || null;
      }
      
      // For regular users, return their tenant_id
      return user.tenant_id || null;
    } catch (error) {
      console.error('Error getting tenant filter:', error);
      return null;
    }
  }

  // Helper method to add tenant filter to params
  addTenantFilter(params = {}) {
    const tenantFilter = this.getCurrentTenantFilter();
    if (tenantFilter) {
      params.tenant = tenantFilter;
    }
    return params;
  }

  // Helper method to handle API responses
  async handleResponse(response) {
    if (response.status >= 200 && response.status < 300) {
      return response.data;
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  // Helper method to handle errors with detailed logging
  handleError(error, operation) {
    console.error(`Staff API Error - ${operation}:`, error);
    
    if (error.response) {
      const message = error.response.data?.detail || error.response.data?.error || error.message;
      throw new Error(message);
    } else if (error.request) {
      throw new Error('Network error - please check your connection');
    } else {
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }

  // Validate required parameters
  validateRequired(params, requiredFields, operation) {
    const missing = requiredFields.filter(field => !params[field]);
    if (missing.length > 0) {
      throw new Error(`Missing required fields for ${operation}: ${missing.join(', ')}`);
    }
  }

  // ========================================
  // TENANTS
  // ========================================
  
  async getTenants(params = {}) {
    try {
      // Don't add tenant filter for getTenants - this is used to populate tenant list
      const response = await apiClient.get(`${this.baseURL}/tenants/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get tenants');
    }
  }

  async getTenant(tenantId) {
    try {
      this.validateRequired({ tenantId }, ['tenantId'], 'get tenant');
      const response = await apiClient.get(`${this.baseURL}/tenants/${tenantId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get tenant');
    }
  }

  async createTenant(tenantData) {
    try {
      this.validateRequired(tenantData, ['name', 'slug', 'contact_email'], 'create tenant');
      const response = await apiClient.post(`${this.baseURL}/tenants/`, tenantData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'create tenant');
    }
  }

  async updateTenant(tenantId, tenantData) {
    try {
      this.validateRequired({ tenantId }, ['tenantId'], 'update tenant');
      const response = await apiClient.put(`${this.baseURL}/tenants/${tenantId}/`, tenantData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update tenant');
    }
  }

  async deleteTenant(tenantId) {
    try {
      this.validateRequired({ tenantId }, ['tenantId'], 'delete tenant');
      const response = await apiClient.delete(`${this.baseURL}/tenants/${tenantId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'delete tenant');
    }
  }

  async getTenantStats(tenantId) {
    try {
      this.validateRequired({ tenantId }, ['tenantId'], 'get tenant stats');
      const response = await apiClient.get(`${this.baseURL}/tenants/${tenantId}/stats/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get tenant stats');
    }
  }

  async getTenantUsers(tenantId, params = {}) {
    try {
      this.validateRequired({ tenantId }, ['tenantId'], 'get tenant users');
      const response = await apiClient.get(`${this.baseURL}/tenants/${tenantId}/users/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get tenant users');
    }
  }

  async assignTenantRole(tenantId, userId, roleData) {
    try {
      this.validateRequired({ tenantId, userId }, ['tenantId', 'userId'], 'assign tenant role');
      const response = await apiClient.post(`${this.baseURL}/tenants/${tenantId}/users/${userId}/assign_role/`, roleData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'assign tenant role');
    }
  }

  async removeTenantRole(tenantId, userId) {
    try {
      this.validateRequired({ tenantId, userId }, ['tenantId', 'userId'], 'remove tenant role');
      const response = await apiClient.delete(`${this.baseURL}/tenants/${tenantId}/users/${userId}/remove_role/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'remove tenant role');
    }
  }

  // ========================================
  // USERS
  // ========================================
  
  async getUsers(params = {}) {
    try {
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/users/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get users');
    }
  }

  async getUser(userId) {
    try {
      this.validateRequired({ userId }, ['userId'], 'get user');
      const response = await apiClient.get(`${this.baseURL}/users/${userId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get user');
    }
  }

  async createUser(userData) {
    try {
      this.validateRequired(userData, ['email', 'first_name', 'last_name'], 'create user');
      const response = await apiClient.post(`${this.baseURL}/users/`, userData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'create user');
    }
  }

  async updateUser(userId, userData) {
    try {
      this.validateRequired({ userId }, ['userId'], 'update user');
      const response = await apiClient.put(`${this.baseURL}/users/${userId}/`, userData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update user');
    }
  }

  async deleteUser(userId) {
    try {
      this.validateRequired({ userId }, ['userId'], 'delete user');
      const response = await apiClient.delete(`${this.baseURL}/users/${userId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'delete user');
    }
  }

  async toggleUserActive(userId) {
    try {
      this.validateRequired({ userId }, ['userId'], 'toggle user active');
      const response = await apiClient.post(`${this.baseURL}/users/${userId}/toggle_active/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'toggle user active status');
    }
  }

  async resetUserPassword(userId, passwordData = {}) {
    try {
      this.validateRequired({ userId }, ['userId'], 'reset user password');
      const response = await apiClient.post(`${this.baseURL}/users/${userId}/reset_password/`, passwordData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'reset user password');
    }
  }

  async getUserAccounts(userId, params = {}) {
    try {
      this.validateRequired({ userId }, ['userId'], 'get user accounts');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/users/${userId}/accounts/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get user accounts');
    }
  }

  async getUserContracts(userId, params = {}) {
    try {
      this.validateRequired({ userId }, ['userId'], 'get user contracts');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/users/${userId}/contracts/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get user contracts');
    }
  }

  async getUserConnections(userId, params = {}) {
    try {
      this.validateRequired({ userId }, ['userId'], 'get user connections');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/users/${userId}/connections/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get user connections');
    }
  }

  async getUserPlans(userId, params = {}) {
    try {
      this.validateRequired({ userId }, ['userId'], 'get user plans');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/users/${userId}/plans/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get user plans');
    }
  }

  // ========================================
  // ACCOUNTS
  // ========================================
  
  async getAccounts(params = {}) {
    try {
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/accounts/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get accounts');
    }
  }

  async getAccount(accountId) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'get account');
      const response = await apiClient.get(`${this.baseURL}/accounts/${accountId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get account');
    }
  }

  async createAccount(accountData) {
    try {
      this.validateRequired(accountData, ['account_number', 'tenant'], 'create account');
      const response = await apiClient.post(`${this.baseURL}/accounts/`, accountData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'create account');
    }
  }

  async updateAccount(accountId, accountData) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'update account');
      const response = await apiClient.put(`${this.baseURL}/accounts/${accountId}/`, accountData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update account');
    }
  }

  async deleteAccount(accountId) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'delete account');
      const response = await apiClient.delete(`${this.baseURL}/accounts/${accountId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'delete account');
    }
  }

  async getAccountUsers(accountId, params = {}) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'get account users');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/accounts/${accountId}/users/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get account users');
    }
  }

  async assignAccountUser(accountId, userId, roleData) {
    try {
      this.validateRequired({ accountId, userId }, ['accountId', 'userId'], 'assign account user');
      const response = await apiClient.post(`${this.baseURL}/accounts/${accountId}/users/${userId}/assign/`, roleData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'assign account user');
    }
  }

  async removeAccountUser(accountId, userId) {
    try {
      this.validateRequired({ accountId, userId }, ['accountId', 'userId'], 'remove account user');
      const response = await apiClient.delete(`${this.baseURL}/accounts/${accountId}/users/${userId}/remove/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'remove account user');
    }
  }

  async getAccountContracts(accountId, params = {}) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'get account contracts');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/accounts/${accountId}/contracts/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get account contracts');
    }
  }

  async getAccountAddresses(accountId, params = {}) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'get account addresses');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/accounts/${accountId}/addresses/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get account addresses');
    }
  }

  async addAccountAddress(accountId, addressData) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'add account address');
      const response = await apiClient.post(`${this.baseURL}/accounts/${accountId}/addresses/`, addressData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'add account address');
    }
  }

  async getAccountConnections(accountId, params = {}) {
    try {
      this.validateRequired({ accountId }, ['accountId'], 'get account connections');
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/accounts/${accountId}/connections/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get account connections');
    }
  }

  // ========================================
  // CONTRACTS
  // ========================================
  
  async getContracts(params = {}) {
    try {
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/contracts/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get contracts');
    }
  }

  async getContract(contractId) {
    try {
      this.validateRequired({ contractId }, ['contractId'], 'get contract');
      const response = await apiClient.get(`${this.baseURL}/contracts/${contractId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get contract');
    }
  }

  async createContract(contractData) {
    try {
      this.validateRequired(contractData, ['contract_number', 'tenant'], 'create contract');
      const response = await apiClient.post(`${this.baseURL}/contracts/`, contractData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'create contract');
    }
  }

  async updateContract(contractId, contractData) {
    try {
      this.validateRequired({ contractId }, ['contractId'], 'update contract');
      const response = await apiClient.put(`${this.baseURL}/contracts/${contractId}/`, contractData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update contract');
    }
  }

  async deleteContract(contractId) {
    try {
      this.validateRequired({ contractId }, ['contractId'], 'delete contract');
      const response = await apiClient.delete(`${this.baseURL}/contracts/${contractId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'delete contract');
    }
  }

  async getElectricityContracts(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/contracts/electricity/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get electricity contracts');
    }
  }

  async getBroadbandContracts(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/contracts/broadband/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get broadband contracts');
    }
  }

  async getMobileContracts(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/contracts/mobile/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get mobile contracts');
    }
  }

  async updateContractStatus(contractId, statusData) {
    try {
      this.validateRequired({ contractId }, ['contractId'], 'update contract status');
      this.validateRequired(statusData, ['status'], 'update contract status');
      const response = await apiClient.post(`${this.baseURL}/contracts/${contractId}/update_status/`, statusData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update contract status');
    }
  }

  // ========================================
  // PLANS
  // ========================================
  
  async getPlans(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/plans/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get plans');
    }
  }

  async getPlan(planId) {
    try {
      this.validateRequired({ planId }, ['planId'], 'get plan');
      const response = await apiClient.get(`${this.baseURL}/plans/${planId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get plan');
    }
  }

  async createPlan(planData) {
    try {
      this.validateRequired(planData, ['name', 'plan_type', 'base_rate'], 'create plan');
      const response = await apiClient.post(`${this.baseURL}/plans/`, planData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'create plan');
    }
  }

  async updatePlan(planId, planData) {
    try {
      this.validateRequired({ planId }, ['planId'], 'update plan');
      const response = await apiClient.put(`${this.baseURL}/plans/${planId}/`, planData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update plan');
    }
  }

  async deletePlan(planId) {
    try {
      this.validateRequired({ planId }, ['planId'], 'delete plan');
      const response = await apiClient.delete(`${this.baseURL}/plans/${planId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'delete plan');
    }
  }

  async getElectricityPlans(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/plans/`, { params: { ...params, type: 'electricity' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get electricity plans');
    }
  }

  async getBroadbandPlans(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/plans/`, { params: { ...params, type: 'broadband' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get broadband plans');
    }
  }

  async getMobilePlans(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/plans/`, { params: { ...params, type: 'mobile' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get mobile plans');
    }
  }

  // ========================================
  // CONNECTIONS
  // ========================================
  
  async getConnections(params = {}) {
    try {
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/connections/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get connections');
    }
  }

  async getConnection(connectionId) {
    try {
      this.validateRequired({ connectionId }, ['connectionId'], 'get connection');
      const response = await apiClient.get(`${this.baseURL}/connections/${connectionId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get connection');
    }
  }

  async createConnection(connectionData) {
    try {
      this.validateRequired(connectionData, ['service_identifier', 'tenant'], 'create connection');
      const response = await apiClient.post(`${this.baseURL}/connections/`, connectionData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'create connection');
    }
  }

  async updateConnection(connectionId, connectionData) {
    try {
      this.validateRequired({ connectionId }, ['connectionId'], 'update connection');
      const response = await apiClient.put(`${this.baseURL}/connections/${connectionId}/`, connectionData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update connection');
    }
  }

  async deleteConnection(connectionId) {
    try {
      this.validateRequired({ connectionId }, ['connectionId'], 'delete connection');
      const response = await apiClient.delete(`${this.baseURL}/connections/${connectionId}/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'delete connection');
    }
  }

  async getElectricityConnections(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/connections/`, { params: { ...params, service_type: 'electricity' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get electricity connections');
    }
  }

  async getBroadbandConnections(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/connections/`, { params: { ...params, service_type: 'broadband' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get broadband connections');
    }
  }

  async getMobileConnections(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/connections/`, { params: { ...params, service_type: 'mobile' } });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get mobile connections');
    }
  }

  // ========================================
  // CUSTOMER DATA
  // ========================================
  
  async getCustomerOverview(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/customers/overview/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get customer overview');
    }
  }

  async getCustomerStats() {
    try {
      const response = await apiClient.get(`${this.baseURL}/customers/stats/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get customer stats');
    }
  }

  async getCustomerProfile(customerId) {
    try {
      this.validateRequired({ customerId }, ['customerId'], 'get customer profile');
      const response = await apiClient.get(`${this.baseURL}/customers/${customerId}/profile/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get customer profile');
    }
  }

  // ========================================
  // DASHBOARD
  // ========================================
  
  async getDashboardStats() {
    try {
      const response = await apiClient.get(`${this.baseURL}/dashboard/stats/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get dashboard stats');
    }
  }

  async getRecentActivity(params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/dashboard/activity/`, { params });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get recent activity');
    }
  }

  // ========================================
  // BULK OPERATIONS
  // ========================================
  
  async bulkUpdateUsers(userIds, updateData) {
    try {
      this.validateRequired({ userIds }, ['userIds'], 'bulk update users');
      if (!Array.isArray(userIds) || userIds.length === 0) {
        throw new Error('userIds must be a non-empty array');
      }
      const response = await apiClient.post(`${this.baseURL}/users/bulk_update/`, {
        user_ids: userIds,
        update_data: updateData
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'bulk update users');
    }
  }

  async bulkDeleteUsers(userIds) {
    try {
      this.validateRequired({ userIds }, ['userIds'], 'bulk delete users');
      if (!Array.isArray(userIds) || userIds.length === 0) {
        throw new Error('userIds must be a non-empty array');
      }
      const response = await apiClient.post(`${this.baseURL}/users/bulk_delete/`, {
        user_ids: userIds
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'bulk delete users');
    }
  }

  async bulkUpdateContracts(contractIds, updateData) {
    try {
      this.validateRequired({ contractIds }, ['contractIds'], 'bulk update contracts');
      if (!Array.isArray(contractIds) || contractIds.length === 0) {
        throw new Error('contractIds must be a non-empty array');
      }
      const response = await apiClient.post(`${this.baseURL}/contracts/bulk_update/`, {
        contract_ids: contractIds,
        update_data: updateData
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'bulk update contracts');
    }
  }

  // ========================================
  // SEARCH OPERATIONS
  // ========================================
  
  async searchGlobal(query, params = {}) {
    try {
      this.validateRequired({ query }, ['query'], 'global search');
      const response = await apiClient.get(`${this.baseURL}/search/`, {
        params: { q: query, ...params }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'global search');
    }
  }

  async searchTenants(query, params = {}) {
    try {
      this.validateRequired({ query }, ['query'], 'search tenants');
      const response = await apiClient.get(`${this.baseURL}/tenants/search/`, {
        params: { q: query, ...params }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'search tenants');
    }
  }

  async searchUsers(query, params = {}) {
    try {
      this.validateRequired({ query }, ['query'], 'search users');
      const response = await apiClient.get(`${this.baseURL}/users/search/`, {
        params: { q: query, ...params }
      });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'search users');
    }
  }

  // ========================================
  // EXPORT OPERATIONS
  // ========================================
  
  async exportTenants(format = 'csv', params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/tenants/export/`, {
        params: { format, ...params },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      this.handleError(error, 'export tenants');
    }
  }

  async exportUsers(format = 'csv', params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/users/export/`, {
        params: { format, ...params },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      this.handleError(error, 'export users');
    }
  }

  async exportContracts(format = 'csv', params = {}) {
    try {
      const response = await apiClient.get(`${this.baseURL}/contracts/export/`, {
        params: { format, ...params },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      this.handleError(error, 'export contracts');
    }
  }

  // ========================================
  // VALIDATION RULES
  // ========================================

  async getValidationRules(params = {}) {
    try {
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/validation/rules/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get validation rules');
    }
  }

  async updateValidationRule(ruleId, ruleData) {
    try {
      this.validateRequired({ ruleId }, ['ruleId'], 'update validation rule');
      const response = await apiClient.put(`${this.baseURL}/validation/rules/${ruleId}/`, ruleData);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'update validation rule');
    }
  }

  async getValidationExceptions(params = {}) {
    try {
      const filteredParams = this.addTenantFilter(params);
      const response = await apiClient.get(`${this.baseURL}/validation/exceptions/`, { params: filteredParams });
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'get validation exceptions');
    }
  }

  async overrideValidationException(exceptionId) {
    try {
      this.validateRequired({ exceptionId }, ['exceptionId'], 'override validation exception');
      const response = await apiClient.post(`${this.baseURL}/validation/exceptions/${exceptionId}/override/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'override validation exception');
    }
  }

  // ========================================
  // HEALTH CHECK
  // ========================================
  
  async healthCheck() {
    try {
      const response = await apiClient.get(`${this.baseURL}/health/`);
      return this.handleResponse(response);
    } catch (error) {
      this.handleError(error, 'health check');
    }
  }
}

// Create and export singleton instance
const staffApiService = new StaffApiService();
export default staffApiService; 