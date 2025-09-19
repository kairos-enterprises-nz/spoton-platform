import apiClient from './apiClient';

const API_BASE = '';

const handleOtpRequest = async (payload, fallbackMessage) => {
  try {
    const response = await apiClient.post(`${API_BASE}/otp/`, payload);
    return response.data;
  } catch (error) {
    return {
      success: false,
      message: error.response?.data?.message || fallbackMessage,
      data: error.response?.data,
    };
  }
};

export const sendOtp = (type, value, purpose = 'signup') =>
  handleOtpRequest({ action: 'send', purpose, [type]: value }, "Failed to send OTP");

export const verifyOtp = (type, value, otp, purpose = 'signup') =>
  handleOtpRequest({ action: 'verify', purpose, otp, [type]: value }, "Failed to verify OTP");

export const resendOtp = (type, value, purpose = 'signup') =>
  handleOtpRequest({ action: 'resend', purpose, [type]: value }, "Failed to resend OTP");

export const checkEmailExists = async (email) => {
  try {
    // Use apiClient.get() which returns axios response
    const response = await apiClient.get(`${API_BASE}/check-email/?email=${encodeURIComponent(email)}`);
    
    // Axios response has .data property, not .json() method
    return response.data;
  } catch (error) {
    console.error('Email check error:', error);
    return { exists: false, active: false, error: true };
  }
};
