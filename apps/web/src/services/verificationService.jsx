import apiClient from './apiClient';

const API_BASE = '';

const handleOtpRequest = async (payload, fallbackMessage) => {
  console.log(`🔍 [VerificationService] Making OTP request:`, payload);
  try {
    const response = await apiClient.post(`/otp/`, payload);
    console.log(`✅ [VerificationService] OTP request successful:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`❌ [VerificationService] OTP request failed:`, error);
    console.error(`❌ [VerificationService] Error response:`, error.response?.data);
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
    const response = await apiClient.get(`/check-email/`, { params: { email } });
    return response.data;
  } catch {
    return { exists: false, active: false, error: true };
  }
};
