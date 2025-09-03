// src/services/userService.js
import apiClient from './apiClient'; // Uses the apiClient with the token refresh interceptor

const API_BASE = '/users';

// --- Authentication Related ---
export const createUserAccount = async (userData) => {
  try {
    const response = await apiClient.post('/users/', userData);
    return {
      success: true,
      message: response.data.message || "Account created successfully.",
      user: response.data.user,
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.message || error.response?.data?.error || "Failed to create account",
      data: error.response?.data,
    };
  }
};

// Removed cookie-based auth functions - Keycloak only

export const getProfile = async () => {
  // NOTE: 401 errors in browser console are NORMAL for unauthenticated users
  // The browser's Network tab will always show these requests and their status codes
  // This is expected behavior and doesn't indicate a problem with the application
  
  try {
    // If this returns 401, the interceptor in apiClient.js will attempt token refresh.
    // If refresh fails, 'auth-logout-event' is dispatched.
    const response = await apiClient.get('/users/profile/');
    return { success: true, user: response.data };
  } catch (error) {
    // Handle 401 errors silently as they're normal for unauthenticated users
    if (error.response?.status === 401) {
      return {
        success: false,
        message: "User not authenticated",
        data: null,
        status: 401
      };
    }
    
    // Log other errors as they might be actual issues
    console.error('getProfile - Unexpected error:', error);
    return {
      success: false,
      message: error.response?.data?.message || error.response?.data?.error || "Failed to fetch profile",
      data: error.response?.data,
      status: error.response?.status
    };
  }
};

// --- Password Reset ---
export const requestPasswordResetOtp = async (email) => {
  try {
    const response = await apiClient.post(`${API_BASE}/password-reset-request-otp/`, { email });
    return { success: true, ...response.data };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.error || "Failed to request OTP",
      data: error.response?.data,
    };
  }
};

export const verifyPasswordResetOtp = async (email, otp, newPassword) => {
  try {
    const response = await apiClient.post(`${API_BASE}/password-reset-verify-otp/`, {
      email,
      otp,
      new_password: newPassword
    });
    return { success: true, ...response.data };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.error || "Failed to verify OTP",
      data: error.response?.data,
    };
  }
};

// --- Other User CRUD (as an example, you had these as a separate object) ---
// These functions will also benefit from the token refresh interceptor
export const getUserDetails = async () => {
  try {
    const response = await apiClient.get(`${API_BASE}/details/`);
    return { success: true, details: response.data };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.message || "Failed to get user details",
      data: error.response?.data,
    };
  }
};

export const updateUserDetails = async (data) => {
  try {
    const response = await apiClient.put(`${API_BASE}/details/`, data);
    return { success: true, details: response.data };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.message || "Failed to update user details",
      data: error.response?.data,
    };
  }
};

export const getBusinessDetails = async () => {
  try {
    const response = await apiClient.get(`${API_BASE}/business/`);
    return { success: true, businessInfo: response.data };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.message || "Failed to get business details",
      data: error.response?.data,
    };
  }
};

export const updateBusinessDetails = async (data) => {
  try {
    const response = await apiClient.put(`${API_BASE}/business/`, data);
    return { success: true, businessInfo: response.data };
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.message || "Failed to update business details",
      data: error.response?.data,
    };
  }
};

