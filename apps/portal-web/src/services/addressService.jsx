import apiClient from './apiClient';

export const searchAddress = async (query) => {
  try {
    const response = await apiClient.get('/api/web/address/', { params: { query } });
    const results = response.data?.results ?? [];
    return {
      results,
      success: true,
      isEmpty: results.length === 0,
      error: null
    };
  } catch (error) {
    console.error('Address search failed:', error);
    return {
      results: [],
      success: false,
      isEmpty: false,
      error: error.response?.status >= 500 ? 'service_unavailable' : 'request_failed'
    };
  }
};

export const checkServiceAvailability = async (address, services) => {
  if (!Array.isArray(services) || services.length === 0) {
    throw new Error("No services provided");
  }

  try {
    const response = await apiClient.get('/api/web/address-summary/', {
      params: {
        query: address.full_address,
        services: services.join(','),
      },
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

// New pricing API functions
export const getElectricityPlansByCity = async (city, pricingIds = null) => {
  try {
    const params = { city };
    if (pricingIds) {
      if (Array.isArray(pricingIds)) {
        params.pricing_ids = pricingIds.join(',');
      } else {
        params.pricing_ids = pricingIds;
      }
    }
    
    const response = await apiClient.get('/api/web/pricing/electricity/', { params });
    return response.data?.plans || [];
  } catch (error) {
    return [];
  }
};

export const getBroadbandPlansByCity = async (city, pricingIds = null) => {
  try {
    const params = { city };
    if (pricingIds) {
      if (Array.isArray(pricingIds)) {
        params.pricing_ids = pricingIds.join(',');
      } else {
        params.pricing_ids = pricingIds;
      }
    }
    
    const response = await apiClient.get('/api/web/pricing/broadband/', { params });
    return response.data?.plans || [];
  } catch (error) {
    return [];
  }
};

export const getPlanByPricingId = async (pricingId) => {
  try {
    const response = await apiClient.get(`/api/web/pricing/plan/${pricingId}/`);
    return response.data;
  } catch (error) {
    return null;
  }
};

export const getPlansByPricingIds = async (pricingIds) => {
  try {
    // Validate that we have valid pricing IDs
    if (!pricingIds || !Array.isArray(pricingIds) || pricingIds.length === 0) {
      return [];
    }
    
    // Basic UUID validation
    const isValidUuid = (id) => {
      return id && typeof id === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
    };
    
    // Filter out any falsy values and invalid UUIDs
    const validIds = pricingIds.filter(id => id && isValidUuid(id));
    
    if (validIds.length === 0) {
      return [];
    }
    
    // Join the UUIDs with commas for the API request
    const params = { pricing_ids: validIds.join(',') };
    
    const response = await apiClient.get('/api/web/pricing/plans/bulk/', { params });
    
    // Log the number of plans returned vs. requested
    const returnedPlans = response.data?.plans || [];
    
    return returnedPlans;
  } catch (error) {
    return [];
  }
};

export const getMobilePlansByCity = async (pricingIds = null) => {
  try {
    const params = {};
    if (pricingIds) {
      if (Array.isArray(pricingIds)) {
        params.pricing_ids = pricingIds.join(',');
      } else {
        params.pricing_ids = pricingIds;
      }
    }
    
    const response = await apiClient.get('/api/web/pricing/mobile/', { params });
    return response.data?.plans || [];
  } catch (error) {
    console.error('Error fetching mobile plans:', error);
    return [];
  }
};
