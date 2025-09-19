import apiClient from './apiClient';

// Get user's current service interests
export async function getServiceInterests() {
  try {
    const response = await apiClient.get('/api/service-interest/');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch service interests:', error);
    return null;
  }
}

// Update user's interest in a specific service
export async function updateServiceInterest(serviceType, interested = true) {
  try {
    const response = await apiClient.post('/api/service-interest/', {
      service_type: serviceType,
      interested: interested
    });
    return response.data;
  } catch (error) {
    console.error(`Failed to update ${serviceType} service interest:`, error);
    throw error;
  }
}
