/**
 * Staff API Testing Utility
 * 
 * This utility can be used in the browser console to test Staff API endpoints.
 * Open browser console and run: testStaffApi.runBasicTests()
 */

import staffApiService from '../services/staffApi';

class StaffApiTester {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      errors: []
    };
  }

  log(message, type = 'info') {
    const colors = {
      info: 'color: #3b82f6',
      success: 'color: #10b981', 
      error: 'color: #ef4444',
      warning: 'color: #f59e0b'
    };
    console.log(`%c[StaffAPI Test] ${message}`, colors[type]);
  }

  async runTest(testName, testFunction) {
    try {
      this.log(`Running: ${testName}`, 'info');
      await testFunction();
      this.results.passed++;
      this.log(`✓ PASSED: ${testName}`, 'success');
      return true;
    } catch (error) {
      this.results.failed++;
      this.results.errors.push({ test: testName, error: error.message });
      this.log(`✗ FAILED: ${testName} - ${error.message}`, 'error');
      return false;
    }
  }

  // Basic connectivity tests
  async testConnectivity() {
    this.log('=== Testing Basic Connectivity ===', 'info');
    
    await this.runTest('Health Check', async () => {
      const result = await staffApiService.healthCheck();
      if (!result) throw new Error('No response from health check');
    });
  }

  // Dashboard tests
  async testDashboard() {
    this.log('=== Testing Dashboard Endpoints ===', 'info');
    
    await this.runTest('Dashboard Stats', async () => {
      const result = await staffApiService.getDashboardStats();
      if (!result) throw new Error('No dashboard stats received');
    });

    await this.runTest('Recent Activity', async () => {
      const result = await staffApiService.getRecentActivity({ limit: 5 });
      if (!result) throw new Error('No activity data received');
    });
  }

  // Tenant tests
  async testTenants() {
    this.log('=== Testing Tenant Endpoints ===', 'info');
    
    await this.runTest('Get Tenants', async () => {
      const result = await staffApiService.getTenants({ page_size: 10 });
      if (!result) throw new Error('No tenants data received');
    });

    await this.runTest('Search Tenants', async () => {
      const result = await staffApiService.searchTenants('test', { limit: 5 });
      if (!result) throw new Error('No tenant search results received');
    });
  }

  // User tests
  async testUsers() {
    this.log('=== Testing User Endpoints ===', 'info');
    
    await this.runTest('Get Users', async () => {
      const result = await staffApiService.getUsers({ page_size: 10 });
      if (!result) throw new Error('No users data received');
    });

    await this.runTest('Search Users', async () => {
      const result = await staffApiService.searchUsers('test', { limit: 5 });
      if (!result) throw new Error('No user search results received');
    });
  }

  // Contract tests
  async testContracts() {
    this.log('=== Testing Contract Endpoints ===', 'info');
    
    await this.runTest('Get Contracts', async () => {
      const result = await staffApiService.getContracts({ page_size: 10 });
      if (!result) throw new Error('No contracts data received');
    });

    await this.runTest('Get Electricity Contracts', async () => {
      const result = await staffApiService.getElectricityContracts({ page_size: 5 });
      if (!result) throw new Error('No electricity contracts received');
    });

    await this.runTest('Get Broadband Contracts', async () => {
      const result = await staffApiService.getBroadbandContracts({ page_size: 5 });
      if (!result) throw new Error('No broadband contracts received');
    });

    await this.runTest('Get Mobile Contracts', async () => {
      const result = await staffApiService.getMobileContracts({ page_size: 5 });
      if (!result) throw new Error('No mobile contracts received');
    });
  }

  // Account tests
  async testAccounts() {
    this.log('=== Testing Account Endpoints ===', 'info');
    
    await this.runTest('Get Accounts', async () => {
      const result = await staffApiService.getAccounts({ page_size: 10 });
      if (!result) throw new Error('No accounts data received');
    });
  }

  // Customer tests
  async testCustomers() {
    this.log('=== Testing Customer Endpoints ===', 'info');
    
    await this.runTest('Customer Overview', async () => {
      const result = await staffApiService.getCustomerOverview();
      if (!result) throw new Error('No customer overview received');
    });

    await this.runTest('Customer Stats', async () => {
      const result = await staffApiService.getCustomerStats();
      if (!result) throw new Error('No customer stats received');
    });
  }

  // Search tests
  async testSearch() {
    this.log('=== Testing Search Endpoints ===', 'info');
    
    await this.runTest('Global Search', async () => {
      const result = await staffApiService.searchGlobal('test');
      if (!result) throw new Error('No global search results received');
    });
  }

  // Run all basic tests
  async runBasicTests() {
    this.log('Starting Staff API Basic Tests', 'info');
    this.results = { passed: 0, failed: 0, errors: [] };
    
    const startTime = Date.now();

    await this.testConnectivity();
    await this.testDashboard();
    await this.testTenants();
    await this.testUsers();
    await this.testContracts();
    await this.testAccounts();
    await this.testCustomers();
    await this.testSearch();

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;

    this.log('=== TEST RESULTS ===', 'info');
    this.log(`Total Tests: ${this.results.passed + this.results.failed}`, 'info');
    this.log(`Passed: ${this.results.passed}`, 'success');
    this.log(`Failed: ${this.results.failed}`, this.results.failed > 0 ? 'error' : 'info');
    this.log(`Duration: ${duration.toFixed(2)}s`, 'info');

    if (this.results.errors.length > 0) {
      this.log('=== FAILED TESTS ===', 'error');
      this.results.errors.forEach(({ test, error }) => {
        this.log(`${test}: ${error}`, 'error');
      });
    }

    return this.results;
  }

  // Test specific endpoint
  async testEndpoint(method, endpoint, data = null) {
    this.log(`Testing ${method} ${endpoint}`, 'info');
    
    try {
      let result;
      switch (method.toUpperCase()) {
        case 'GET':
          result = await staffApiService.apiClient.get(endpoint);
          break;
        case 'POST':
          result = await staffApiService.apiClient.post(endpoint, data);
          break;
        case 'PUT':
          result = await staffApiService.apiClient.put(endpoint, data);
          break;
        case 'DELETE':
          result = await staffApiService.apiClient.delete(endpoint);
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
      
      this.log(`✓ SUCCESS: ${method} ${endpoint} - Status: ${result.status}`, 'success');
      return result.data;
    } catch (error) {
      this.log(`✗ FAILED: ${method} ${endpoint} - ${error.message}`, 'error');
      throw error;
    }
  }

  // Test with sample data
  async testWithSampleData() {
    this.log('=== Testing with Sample Data ===', 'warning');
    this.log('WARNING: This will create test data in your system', 'warning');
    
    const confirm = window.confirm('This will create test data. Continue?');
    if (!confirm) {
      this.log('Test cancelled by user', 'info');
      return;
    }

    // Test tenant creation
    await this.runTest('Create Test Tenant', async () => {
      const testTenant = {
        name: 'Test Energy Company',
        slug: 'test-energy-' + Date.now(),
        contact_email: 'test@example.com',
        business_type: 'electricity'
      };
      
      const result = await staffApiService.createTenant(testTenant);
      if (!result || !result.id) throw new Error('Failed to create tenant');
      
      // Clean up - delete the test tenant
      await staffApiService.deleteTenant(result.id);
      this.log('Test tenant cleaned up', 'info');
    });
  }

  // Performance test
  async performanceTest() {
    this.log('=== Performance Testing ===', 'info');
    
    const tests = [
      () => staffApiService.getDashboardStats(),
      () => staffApiService.getTenants({ page_size: 100 }),
      () => staffApiService.getUsers({ page_size: 100 }),
      () => staffApiService.getContracts({ page_size: 100 })
    ];

    for (let i = 0; i < tests.length; i++) {
      const testName = `Performance Test ${i + 1}`;
      await this.runTest(testName, async () => {
        const startTime = performance.now();
        await tests[i]();
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.log(`Duration: ${duration.toFixed(2)}ms`, 'info');
        
        if (duration > 5000) {
          throw new Error(`Slow response: ${duration.toFixed(2)}ms`);
        }
      });
    }
  }
}

// Create and export instance
const testStaffApi = new StaffApiTester();

// Make it available globally for console testing
if (typeof window !== 'undefined') {
  window.testStaffApi = testStaffApi;
}

export default testStaffApi; 