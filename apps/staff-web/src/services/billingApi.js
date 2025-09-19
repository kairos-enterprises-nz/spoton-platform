/**
 * Billing API service client with comprehensive error handling and caching.
 */
import apiClient from './apiClient';

class BillingApiService {
  constructor() {
    this.baseURL = '/api/finance';
    this.client = apiClient; // Use the shared API client that handles domain and auth
  }

  // setupInterceptors() removed - using shared apiClient that already handles auth and errors

  formatError(error) {
    if (error.response) {
      // Server responded with error status
      return {
        message: error.response.data?.error || error.response.data?.message || 'Server error',
        status: error.response.status,
        data: error.response.data,
      };
    } else if (error.request) {
      // Network error
      return {
        message: 'Network error - please check your connection',
        status: 0,
        data: null,
      };
    } else {
      // Other error
      return {
        message: error.message || 'Unknown error occurred',
        status: -1,
        data: null,
      };
    }
  }

  // Billing Runs API
  async getBillingRuns(params = {}) {
    const response = await this.client.get(`${this.baseURL}/billing/runs/`, { params });
    return response.data;
  }

  async getBillingRun(id) {
    const response = await this.client.get(`/billing/runs/${id}/`);
    return response.data;
  }

  async createBillingRun(data) {
    const response = await this.client.post(`${this.baseURL}/billing/runs/create_run/`, data);
    return response.data;
  }

  async executeBillingRun(id, dryRun = false) {
    const response = await this.client.post(`/billing/runs/${id}/execute/`, {
      dry_run: dryRun,
    });
    return response.data;
  }

  async getBillingDashboard() {
    const response = await this.client.get(`${this.baseURL}/billing/runs/dashboard/`);
    return response.data;
  }

  async getBillingHealthCheck() {
    const response = await this.client.get(`${this.baseURL}/billing/runs/health_check/`);
    return response.data;
  }

  // Bills API
  async getBills(params = {}) {
    const response = await this.client.get(`${this.baseURL}/billing/bills/`, { params });
    return response.data;
  }

  async getBill(id) {
    const response = await this.client.get(`${this.baseURL}/billing/bills/${id}/`);
    return response.data;
  }

  async bulkBillAction(data) {
    const response = await this.client.post(`${this.baseURL}/billing/bills/bulk_action/`, data);
    return response.data;
  }

  // Invoices API
  async getInvoices(params = {}) {
    const response = await this.client.get(`${this.baseURL}/invoices/`, { params });
    return response.data;
  }

  async getInvoice(id) {
    const response = await this.client.get(`${this.baseURL}/invoices/${id}/`);
    return response.data;
  }

  async createInvoicesFromBills(data) {
    const response = await this.client.post(`${this.baseURL}/invoices/create_from_bills/`, data);
    return response.data;
  }

  async bulkInvoiceAction(data) {
    const response = await this.client.post(`${this.baseURL}/invoices/bulk_action/`, data);
    return response.data;
  }

  async generateInvoicePDFs(data) {
    const response = await this.client.post(`${this.baseURL}/invoices/generate_pdfs/`, data);
    return response.data;
  }

  async sendInvoiceEmails(data) {
    const response = await this.client.post(`${this.baseURL}/invoices/send_emails/`, data);
    return response.data;
  }

  async downloadInvoicePDF(id) {
    const response = await this.client.get(`/invoices/${id}/download_pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async getInvoiceAnalytics(params = {}) {
    const response = await this.client.get(`${this.baseURL}/invoices/analytics/`, { params });
    return response.data;
  }

  // Service Registry API
  async getServiceRegistry(params = {}) {
    const response = await this.client.get(`${this.baseURL}/billing/registry/`, { params });
    return response.data;
  }

  async createServiceRegistry(data) {
    const response = await this.client.post(`${this.baseURL}/billing/registry/`, data);
    return response.data;
  }

  async updateServiceRegistry(id, data) {
    const response = await this.client.put(`/billing/registry/${id}/`, data);
    return response.data;
  }

  async deleteServiceRegistry(id) {
    const response = await this.client.delete(`/billing/registry/${id}/`);
    return response.data;
  }

  // Billing Cycles API
  async getBillingCycles(params = {}) {
    const response = await this.client.get(`${this.baseURL}/billing/cycles/`, { params });
    return response.data;
  }

  async createBillingCycle(data) {
    const response = await this.client.post(`${this.baseURL}/billing/cycles/`, data);
    return response.data;
  }

  async updateBillingCycle(id, data) {
    const response = await this.client.put(`/billing/cycles/${id}/`, data);
    return response.data;
  }

  async deleteBillingCycle(id) {
    const response = await this.client.delete(`/billing/cycles/${id}/`);
    return response.data;
  }

  // Payments API
  async getPayments(params = {}) {
    const response = await this.client.get(`${this.baseURL}/billing/payments/`, { params });
    return response.data;
  }

  async getPayment(id) {
    const response = await this.client.get(`/billing/payments/${id}/`);
    return response.data;
  }

  // Utility methods
  downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  formatCurrency(amount, currency = 'NZD') {
    return new Intl.NumberFormat('en-NZ', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  }

  formatDate(date, options = {}) {
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    };
    return new Intl.DateTimeFormat('en-NZ', { ...defaultOptions, ...options }).format(
      new Date(date)
    );
  }
}

// Create singleton instance
export const billingApi = new BillingApiService();

// Export class for testing
export { BillingApiService };
