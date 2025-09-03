import apiClient from './apiClient';

export const checkServiceAvailability = async (address, services) => {
  if (!Array.isArray(services) || services.length === 0) {
    throw new Error("No services provided");
  }

  try {
    const response = await apiClient.get('web/address-summary/', {
      params: {
        query: address.full_address,
        services: services.join(',')
      }
    });

    return response.data;
  } catch (error) {
    throw error;
  }
};
