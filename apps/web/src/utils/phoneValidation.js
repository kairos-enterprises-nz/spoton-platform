/**
 * Shared phone validation utilities for consistent validation across all flows
 * Used by both traditional onboarding and OAuth flows
 */

/**
 * Validate New Zealand mobile phone number
 * @param {string} phoneNumber - Phone number to validate (without country code)
 * @returns {object} - {isValid: boolean, error: string}
 */
export const validateNZMobile = (phoneNumber) => {
  if (!phoneNumber) {
    return {
      isValid: false,
      error: 'Phone number is required'
    };
  }

  // Remove spaces and normalize
  const cleanPhone = phoneNumber.trim().replace(/\s/g, '');
  
  // New Zealand mobile pattern (02, 021, 022, 027, 028, 029)
  // Supports both 9 and 10 digit numbers after the prefix
  const mobilePattern = /^(02|021|022|027|028|029)\d{7,8}$/;
  
  if (!mobilePattern.test(cleanPhone)) {
    return {
      isValid: false,
      error: 'Please enter a valid New Zealand mobile number (e.g., 021 123 4567)'
    };
  }

  return {
    isValid: true,
    error: ''
  };
};

/**
 * Normalize phone number to international format
 * @param {string} phoneNumber - Phone number to normalize
 * @returns {string} - Normalized phone number with +64 country code
 */
export const normalizeNZPhone = (phoneNumber) => {
  if (!phoneNumber) return '';
  
  const clean = phoneNumber.trim().replace(/\s/g, '');
  
  // If starts with 0, replace with +64
  if (clean.startsWith('0')) {
    return '+64' + clean.substring(1);
  }
  
  // If doesn't start with +, add it
  if (!clean.startsWith('+')) {
    return '+' + clean;
  }
  
  return clean;
};

/**
 * Format phone number for display (add spaces for readability)
 * @param {string} phoneNumber - Phone number to format
 * @returns {string} - Formatted phone number
 */
export const formatNZPhone = (phoneNumber) => {
  if (!phoneNumber) return '';
  
  const clean = phoneNumber.trim().replace(/\s/g, '');
  
  // Format patterns for different NZ mobile prefixes
  if (clean.match(/^(02\d{8})$/)) {
    // 02 followed by 8 digits: 02 1234 5678
    return clean.replace(/^(02)(\d{4})(\d{4})$/, '$1 $2 $3');
  } else if (clean.match(/^(021|022|027|028|029)(\d{7,8})$/)) {
    // 3-digit prefix: 021 123 4567 or 021 1234 5678
    const match = clean.match(/^(\d{3})(\d{3,4})(\d{4})$/);
    if (match) {
      return `${match[1]} ${match[2]} ${match[3]}`;
    }
  }
  
  return clean;
};

/**
 * Validate phone with country code (backward compatibility)
 * @param {string} phoneNumber - Phone number without country code
 * @returns {boolean} - True if valid
 */
export const validatePhoneNumber = (phoneNumber) => {
  const validation = validateNZMobile(phoneNumber);
  return validation.isValid;
};

/**
 * Get validation error message for phone input
 * @param {string} phoneNumber - Phone number to validate
 * @returns {string} - Error message or empty string if valid
 */
export const getPhoneError = (phoneNumber) => {
  const validation = validateNZMobile(phoneNumber);
  return validation.error;
};

/**
 * Check if phone number is valid
 * @param {string} phoneNumber - Phone number to check
 * @returns {boolean} - True if valid
 */
export const isValidNZPhone = (phoneNumber) => {
  const validation = validateNZMobile(phoneNumber);
  return validation.isValid;
};

// Export patterns for external use if needed
export const NZ_MOBILE_PATTERN = /^(02|021|022|027|028|029)\d{7,8}$/;
export const NZ_COUNTRY_CODE = '+64';