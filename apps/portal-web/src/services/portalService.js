import apiClient from './apiClient';

// Get comprehensive user portal data from onboarding
export async function getUserPortalData() {
  try {
    const response = await apiClient.get('/api/portal-data/');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user portal data:', error);
    return null;
  }
}

// Get user's contracted services based on onboarding choices
export async function getContractedServices() {
  try {
    const portalData = await getUserPortalData();
    if (portalData?.services?.active_services) {
      return portalData.services.active_services;
    }
    return [];
  } catch (error) {
    console.error('Failed to fetch contracted services:', error);
    return [];
  }
}

// Get detailed information for a specific service
export async function getServiceDetails(serviceType) {
  try {
    const response = await apiClient.get(`/api/service/${serviceType}/`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch ${serviceType} service details:`, error);
    return null;
  }
}

