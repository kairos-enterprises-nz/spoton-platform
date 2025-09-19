/**
 * Unified OTP Service for consistent phone verification across all flows
 * Used by both traditional onboarding and OAuth flows
 */

/**
 * Send OTP to phone number
 * @param {string} phoneNumber - Normalized phone number with country code
 * @param {string} purpose - Purpose of OTP ('phone_verification', 'signup', etc.)
 * @returns {Promise<object>} - Response with success status and message
 */
export const sendOTP = async (phoneNumber, purpose = 'phone_verification') => {
  try {
    const response = await fetch('/api/otp/send/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        type: 'mobile',
        identifier: phoneNumber,
        purpose: purpose
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to send verification code');
    }

    return {
      success: true,
      message: data.message || 'Verification code sent successfully',
      data: data
    };
  } catch (error) {
    return {
      success: false,
      message: error.message || 'Failed to send verification code',
      error: error
    };
  }
};

/**
 * Verify OTP code
 * @param {string} phoneNumber - Normalized phone number with country code
 * @param {string} otp - OTP code to verify
 * @param {string} purpose - Purpose of OTP verification
 * @returns {Promise<object>} - Response with verification status and user data
 */
export const verifyOTP = async (phoneNumber, otp, purpose = 'phone_verification') => {
  try {
    const response = await fetch('/api/otp/verify/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        type: 'mobile',
        identifier: phoneNumber,
        otp: otp.trim(),
        purpose: purpose
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Invalid verification code');
    }

    return {
      success: data.success || data.verified || true,
      message: data.message || 'Phone verification successful',
      user: data.user,
      redirect: data.redirect,
      data: data
    };
  } catch (error) {
    return {
      success: false,
      message: error.message || 'Verification failed',
      error: error
    };
  }
};

/**
 * Send OTP for traditional signup flow (backward compatibility)
 * @param {string} type - Type of OTP ('mobile')
 * @param {string} identifier - Phone number
 * @param {string} purpose - Purpose ('signup', 'phone_verification')
 * @returns {Promise<object>} - Response object
 */
export const sendOtp = async (type, identifier, purpose) => {
  return await sendOTP(identifier, purpose);
};

/**
 * Verify OTP for traditional signup flow (backward compatibility)
 * @param {string} type - Type of OTP ('mobile')
 * @param {string} identifier - Phone number
 * @param {string} otp - OTP code
 * @param {string} purpose - Purpose ('signup', 'phone_verification')
 * @returns {Promise<object>} - Response object
 */
export const verifyOtp = async (type, identifier, otp, purpose) => {
  return await verifyOTP(identifier, otp, purpose);
};

export default {
  sendOTP,
  verifyOTP,
  sendOtp,
  verifyOtp
};