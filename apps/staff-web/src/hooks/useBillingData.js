/**
 * React hooks for billing data management using simple fetch and state.
 */
import { useState, useEffect, useCallback } from 'react';
import { billingApi } from '../services/billingApi';
import { toast } from '../utils/notifications';

// Custom hook for data fetching
const useApiData = (fetchFunction, dependencies = []) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await fetchFunction();
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, isLoading, error, refetch: fetchData };
};

// Custom hook for mutations
const useMutation = (mutationFunction) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const mutate = useCallback(async (variables) => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await mutationFunction(variables);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [mutationFunction]);

  return { mutate, isLoading, error };
};

// Billing Runs Hooks
export const useBillingRuns = (filters = {}) => {
  return useApiData(() => billingApi.getBillingRuns(filters), [JSON.stringify(filters)]);
};

export const useBillingRun = (id) => {
  return useApiData(() => billingApi.getBillingRun(id), [id]);
};

export const useBillingDashboard = () => {
  const result = useApiData(() => billingApi.getBillingDashboard(), []);
  
  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!result.isLoading && !result.error) {
      const interval = setInterval(() => {
        result.refetch();
      }, 30000);
      
      return () => clearInterval(interval);
    }
  }, [result.isLoading, result.error]);
  
  return result;
};

export const useBillingHealthCheck = () => {
  const result = useApiData(() => billingApi.getBillingHealthCheck(), []);
  
  // Auto-refresh every minute
  useEffect(() => {
    if (!result.isLoading && !result.error) {
      const interval = setInterval(() => {
        result.refetch();
      }, 60000);
      
      return () => clearInterval(interval);
    }
  }, [result.isLoading, result.error]);
  
  return result;
};

export const useCreateBillingRun = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.createBillingRun(data);
    toast.success('Billing run created successfully');
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

export const useExecuteBillingRun = (options = {}) => {
  return useMutation(async ({ id, dryRun }) => {
    const result = await billingApi.executeBillingRun(id, dryRun);
    const message = result.dry_run 
      ? 'Dry run completed successfully' 
      : 'Billing run executed successfully';
    toast.success(message);
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

// Bills Hooks
export const useBills = (filters = {}) => {
  return useApiData(() => billingApi.getBills(filters), [JSON.stringify(filters)]);
};

export const useBill = (id) => {
  return useApiData(() => billingApi.getBill(id), [id]);
};

export const useBulkBillAction = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.bulkBillAction(data);
    toast.success(`Bulk action completed: ${data.action}`);
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

// Invoices Hooks
export const useInvoices = (filters = {}) => {
  return useApiData(() => billingApi.getInvoices(filters), [JSON.stringify(filters)]);
};

export const useInvoice = (id) => {
  return useApiData(() => billingApi.getInvoice(id), [id]);
};

export const useInvoiceAnalytics = (filters = {}) => {
  return useApiData(() => billingApi.getInvoiceAnalytics(filters), [JSON.stringify(filters)]);
};

export const useCreateInvoicesFromBills = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.createInvoicesFromBills(data);
    toast.success(`Created ${result.invoices_created} invoices`);
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

export const useBulkInvoiceAction = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.bulkInvoiceAction(data);
    const successMessage = getInvoiceActionSuccessMessage(result);
    toast.success(successMessage);
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

export const useGenerateInvoicePDFs = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.generateInvoicePDFs(data);
    toast.success(`Generated ${result.pdfs_generated} PDFs`);
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

export const useSendInvoiceEmails = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.sendInvoiceEmails(data);
    toast.success(`Sent ${result.emails_sent} emails`);
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

export const useDownloadInvoicePDF = (options = {}) => {
  return useMutation(async (id) => {
    const blob = await billingApi.downloadInvoicePDF(id);
    billingApi.downloadFile(blob, `invoice-${id}.pdf`);
    toast.success('PDF downloaded successfully');
    if (options.onSuccess) {
      options.onSuccess(blob, id);
    }
    return blob;
  });
};

// Service Registry Hooks
export const useServiceRegistry = (filters = {}) => {
  return useApiData(() => billingApi.getServiceRegistry(filters), [JSON.stringify(filters)]);
};

export const useCreateServiceRegistry = (options = {}) => {
  return useMutation(async (data) => {
    const result = await billingApi.createServiceRegistry(data);
    toast.success('Service registry entry created');
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

export const useUpdateServiceRegistry = (options = {}) => {
  return useMutation(async ({ id, data }) => {
    const result = await billingApi.updateServiceRegistry(id, data);
    toast.success('Service registry entry updated');
    if (options.onSuccess) {
      options.onSuccess(result);
    }
    return result;
  });
};

// Billing Cycles Hooks
export const useBillingCycles = (filters = {}) => {
  return useApiData(() => billingApi.getBillingCycles(filters), [JSON.stringify(filters)]);
};

// Payments Hooks
export const usePayments = (filters = {}) => {
  return useApiData(() => billingApi.getPayments(filters), [JSON.stringify(filters)]);
};

// WebSocket Hook for Real-time Updates (simplified)
export const useBillingWebSocket = () => {
  const [updates, setUpdates] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    // For now, simulate connection status
    setConnectionStatus('connected');
    
    // In a real implementation, you would set up WebSocket connection here
    // const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // const wsUrl = `${protocol}//${window.location.host}/ws/billing/`;
    // const ws = new WebSocket(wsUrl);
    
    return () => {
      // Cleanup WebSocket connection
    };
  }, []);

  return { updates, connectionStatus };
};

// Utility functions
function getInvoiceActionSuccessMessage(data) {
  switch (data.action) {
    case 'review':
      return `Reviewed ${data.successful_count} invoices`;
    case 'finalize':
      return `Finalized ${data.successful_count} invoices`;
    case 'generate_pdf':
      return `Generated ${data.successful_count} PDFs`;
    case 'send_email':
      return `Sent ${data.successful_count} emails`;
    default:
      return `Completed ${data.action} for ${data.successful_count} invoices`;
  }
}