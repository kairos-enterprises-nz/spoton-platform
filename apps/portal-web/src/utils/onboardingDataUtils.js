/**
 * Utility functions for consistent onboarding data structure and synchronization
 */

/**
 * Normalizes onboarding data structure for consistent access across components
 * @param {Object} data - Raw onboarding data from backend or props
 * @returns {Object} Normalized data structure
 */
export function normalizeOnboardingData(data) {
  if (!data) return {};

  const normalized = {
    // About you data
    aboutYou: data.aboutYou || data.step_data?.aboutYou || {},
    
    // Property data
    yourProperty: data.yourProperty || data.step_data?.yourProperty || {},
    
    // Services data
    yourServices: data.yourServices || data.step_data?.yourServices || {},
    
    // Service details data
    serviceDetails: data.serviceDetails || data.step_data?.serviceDetails || {},
    
    // Payment data
    howYoullPay: data.howYoullPay || data.step_data?.howYoullPay || {},
    
    // Preferences data
    preferences: data.preferences || data.step_data?.preferences || {},
    
    // Confirmation data
    confirmation: data.confirmation || data.step_data?.confirmation || {},
    
    // Initial selection data (from create account flow)
    initialSelection: data.initialSelection || data.step_data?.initialSelection || {},
    
    // Include authenticated user data
    authUser: data.user || data.authUser || {},
    
    // Step data wrapper
    step_data: data.step_data || {},
    
    // Include top-level fallbacks for compatibility
    selectedAddress: data.selectedAddress,
    selectedServices: data.selectedServices,
    selectedPlans: data.selectedPlans
  };

  return normalized;
}

/**
 * Extracts selected address from normalized data with fallback chain
 * @param {Object} normalizedData - Normalized onboarding data
 * @returns {Object|null} Selected address object
 */
export function getSelectedAddress(normalizedData) {
  return (
    normalizedData.yourServices?.selectedAddress ||
    normalizedData.yourServices?.addressInfo ||
    normalizedData.yourProperty?.selectedAddress ||
    normalizedData.yourProperty?.addressInfo ||
    normalizedData.userAccount?.selectedAddress ||
    normalizedData.initialSelection?.selectedAddress ||
    null
  );
}

/**
 * Extracts selected services from normalized data with fallback chain
 * @param {Object} normalizedData - Normalized onboarding data
 * @returns {Object} Selected services object
 */
export function getSelectedServices(normalizedData) {
  return (
    normalizedData.yourServices?.selectedServices ||
    normalizedData.yourProperty?.selectedServices ||
    normalizedData.userAccount?.selectedServices ||
    normalizedData.initialSelection?.selectedServices ||
    { electricity: false, broadband: false, mobile: false }
  );
}

/**
 * Extracts selected plans from normalized data with fallback chain
 * @param {Object} normalizedData - Normalized onboarding data
 * @returns {Object|null} Selected plans object
 */
export function getSelectedPlans(normalizedData) {
  const plans = (
    normalizedData.yourServices?.selectedPlans ||
    normalizedData.yourProperty?.selectedPlans ||
    normalizedData.userAccount?.selectedPlans ||
    normalizedData.initialSelection?.selectedPlans ||
    null
  );

  // Validate plans have pricing_id
  if (plans) {
    const validatedPlans = {
      electricity: plans.electricity && plans.electricity.pricing_id ? plans.electricity : null,
      broadband: plans.broadband && plans.broadband.pricing_id ? plans.broadband : null,
      mobile: plans.mobile && (plans.mobile.pricing_id || plans.mobile.plan_id) ? plans.mobile : null
    };

    return validatedPlans;
  }

  return null;
}

/**
 * Extracts user data from normalized data with fallback chain
 * @param {Object} normalizedData - Normalized onboarding data
 * @param {Object} authUser - Authenticated user from context
 * @returns {Object} User data object
 */
export function getEffectiveUser(normalizedData, authUser = {}) {
  return (
    normalizedData.aboutYou?.user ||
    normalizedData.aboutYou?.personalInfo ||
    normalizedData.initialSelection?.user ||
    normalizedData.authUser ||
    authUser ||
    {}
  );
}

/**
 * Validates that required data is present for onboarding steps
 * @param {Object} normalizedData - Normalized onboarding data
 * @returns {Object} Validation result with missing fields
 */
export function validateOnboardingData(normalizedData) {
  const validation = {
    isValid: true,
    missing: [],
    warnings: []
  };

  const address = getSelectedAddress(normalizedData);
  const services = getSelectedServices(normalizedData);
  const plans = getSelectedPlans(normalizedData);

  if (!address) {
    validation.isValid = false;
    validation.missing.push('selectedAddress');
  }

  if (!services || (!services.electricity && !services.broadband && !services.mobile)) {
    validation.isValid = false;
    validation.missing.push('selectedServices');
  }

  if (services) {
    if (services.electricity && (!plans || !plans.electricity)) {
      validation.warnings.push('electricityPlan');
    }
    if (services.broadband && (!plans || !plans.broadband)) {
      validation.warnings.push('broadbandPlan');
    }
    if (services.mobile && (!plans || !plans.mobile)) {
      validation.warnings.push('mobilePlan');
    }
  }

  return validation;
}

/**
 * Creates a consistent data payload for saving onboarding steps
 * @param {string} stepKey - The step being saved
 * @param {Object} stepData - The data for this step
 * @param {Object} contextData - Additional context data (address, services, plans)
 * @returns {Object} Formatted data payload
 */
export function createStepPayload(stepKey, stepData, contextData = {}) {
  const payload = { ...stepData };
  if (stepKey === 'yourServices') {
    if (contextData.selectedServices) {
      payload.selectedServices = contextData.selectedServices;
    }
    if (contextData.selectedPlans) {
      payload.selectedPlans = contextData.selectedPlans;
    }
    if (contextData.selectedAddress) {
      payload.addressInfo = contextData.selectedAddress;
    }
  }
  return payload;
}

/**
 * Ensures consistent field validation across all forms
 * @param {Object} formData - Form data to validate
 * @param {Array} requiredFields - Array of required field names
 * @param {Object} customValidators - Object with custom validation functions
 * @returns {Object} Validation errors object
 */
export function validateFormFields(formData, requiredFields = [], customValidators = {}) {
  const errors = {};

  // Check required fields
  requiredFields.forEach(field => {
    const value = formData[field];
    if (value === undefined || value === null || value === '' || 
        (typeof value === 'string' && !value.trim())) {
      errors[field] = `${field.replace(/([A-Z])/g, ' $1').toLowerCase()} is required.`;
    }
  });

  // Run custom validators
  Object.entries(customValidators).forEach(([field, validator]) => {
    if (formData[field] !== undefined && formData[field] !== null && formData[field] !== '') {
      const validationResult = validator(formData[field], formData);
      if (validationResult !== true && validationResult) {
        errors[field] = validationResult;
      }
    }
  });

  return errors;
}

/**
 * Gets completion status for all onboarding steps
 * @param {Object} normalizedData - Normalized onboarding data
 * @param {number} currentStepIndex - Current step index for smart completion (optional)
 * @returns {Array} Array of boolean values indicating step completion
 */
export function getStepCompletionStatus(normalizedData, currentStepIndex = null) {
  const stepKeys = ['aboutYou', 'yourServices', 'serviceDetails', 'howYoullPay', 'preferences', 'confirmation'];
  const completionStatus = stepKeys.map((stepKey, index) => {
    const isComplete = isStepComplete(normalizedData, stepKey, currentStepIndex);
    console.log(`🔍 Step completion for ${stepKey}:`, isComplete);
    return isComplete;
  });
  console.log('🔍 Final completion status:', completionStatus);
  return completionStatus;
}

/**
 * Checks if a specific onboarding step is complete
 * @param {Object} normalizedData - Normalized onboarding data
 * @param {string} stepKey - The step key to check
 * @param {number} currentStepIndex - Current step index for smart completion (optional)
 * @returns {boolean} Whether the step is complete
 */
export function isStepComplete(normalizedData, stepKey, currentStepIndex = null) {
  if (!normalizedData || !stepKey) return false;

  let stepData = normalizedData[stepKey];
  
  // Special handling for yourServices step - data might be at root level
  if (stepKey === 'yourServices' && (!stepData || Object.keys(stepData).length === 0)) {
    // Check if services/plans data exists at root level
    const hasRootLevelServices = normalizedData.selectedServices && Object.keys(normalizedData.selectedServices).length > 0;
    const hasRootLevelPlans = normalizedData.selectedPlans && Object.keys(normalizedData.selectedPlans).length > 0;
    
    if (hasRootLevelServices || hasRootLevelPlans) {
      // Create a virtual stepData object for yourServices validation
      stepData = {
        selectedServices: normalizedData.selectedServices || {},
        selectedPlans: normalizedData.selectedPlans || {}
      };
      console.log(`🔍 Step ${stepKey}: Using root-level data`, {
        selectedServices: stepData.selectedServices,
        selectedPlans: stepData.selectedPlans
      });
    }
  }
  
  if (!stepData || Object.keys(stepData).length === 0) {
    console.log(`🔍 Step ${stepKey}: No step data found`, {
      stepData,
      normalizedDataKeys: Object.keys(normalizedData)
    });
    return false;
  }

  // For serviceDetails, flatten nested structure if present
  if (stepKey === 'serviceDetails') {
    // Accepts: stepData.serviceDetails, stepData.data?.serviceDetails, or stepData
    stepData = stepData.serviceDetails || stepData.data?.serviceDetails || stepData;
  }

  // Get authenticated user data for context
  const authUser = normalizedData.authUser || {};

  // Step-specific validation logic
  switch (stepKey) {
    case 'aboutYou': {
      // Get user data from multiple possible sources with fallbacks
      const userData = stepData.personalInfo || stepData;
      const initialUserData = normalizedData.initialSelection?.user || {};
      
      // Add debug logging to see the exact field values with fallbacks
      const effectiveEmail = userData.email || authUser.email || initialUserData.email;
      const effectivePhone = userData.phone || authUser.phone || initialUserData.phone;
      const effectiveMobile = userData.mobile || authUser.mobile || initialUserData.mobile;
      const effectiveFirstName = userData.legalFirstName || userData.first_name || initialUserData.first_name;
      const effectiveLastName = userData.legalLastName || userData.last_name || initialUserData.last_name;
      
      // Updated base required fields validation with all fallbacks
      const hasRequiredBaseFields = !!(
        effectiveFirstName && 
        effectiveLastName && 
        (effectiveEmail || effectivePhone || effectiveMobile) && 
        userData.dob &&
        userData.preferredName
      );
      
      console.log('AboutYou Step Validation Debug:', {
        effectiveFirstName,
        effectiveLastName,
        effectiveEmail,
        effectivePhone,
        effectiveMobile,
        dob: userData.dob,
        preferredName: userData.preferredName,
        hasRequiredBaseFields,
        consentCreditCheck: userData.consentCreditCheck,
        idType: userData.idType,
        driverLicenceNumber: userData.driverLicenceNumber,
        driverLicenceVersion: userData.driverLicenceVersion,
        passportNumber: userData.passportNumber
      });
      
      // If basic fields aren't satisfied, return false immediately
      if (!hasRequiredBaseFields) return false;
      
      // Validate ID-related fields
      const hasConsentedToCheck = userData.consentCreditCheck === true;
      
      // If user hasn't consented to credit check, we're done
      if (!hasConsentedToCheck) {
        return false;
      }
      
      // If consent is given, validate ID type and corresponding fields
      if (userData.idType === 'driverLicence') {
        const hasLicenseFields = !!(userData.driverLicenceNumber && userData.driverLicenceVersion);
        return hasLicenseFields;
      } else if (userData.idType === 'passport') {
        const hasPassportField = !!userData.passportNumber;
        return hasPassportField;
      }
      
      // If consent is given but no ID type selected or ID type is invalid
      return false;
    }
    
    case 'yourServices': {
      console.log('YourServices Step Completion Check - START:', {
        stepKey,
        currentStepIndex,
        stepData: Object.keys(stepData),
        normalizedData: Object.keys(normalizedData)
      });

      // Check if services are selected - look in multiple possible locations
      const selectedServices = stepData.selectedServices || 
                              normalizedData.selectedServices || 
                              normalizedData.yourServices?.selectedServices ||
                              normalizedData.initialSelection?.selectedServices || {};
      
      // Check if plans are selected - look in multiple possible locations  
      const selectedPlans = stepData.selectedPlans || 
                           normalizedData.selectedPlans ||
                           normalizedData.yourServices?.selectedPlans ||
                           normalizedData.initialSelection?.selectedPlans || {};
      
      const hasServices = Object.values(selectedServices).some(Boolean);
      const hasAnyPlan = Object.values(selectedPlans).some(plan => plan && (plan.pricing_id || plan.plan_id));
      
      // ALWAYS validate current selections - no smart completion override
      // The step is complete ONLY if user has selected at least one service AND one plan
      const isComplete = hasServices && hasAnyPlan;
      
      console.log('YourServices Step Completion Check:', {
        selectedServices,
        selectedPlans,
        hasServices,
        hasAnyPlan,
        isComplete,
        currentStepIndex
      });
      
      console.log('YourServices: Step completion result:', isComplete);
      return isComplete;
    }

    case 'serviceDetails': {
      const selectedServices = normalizedData.yourServices?.selectedServices || normalizedData.selectedServices || {};
      // Check required fields based on selected services
      if (selectedServices.electricity) {
        if (!stepData.pw_transferType || !stepData.pw_serviceStartDate) return false;
        if (stepData.pw_medicalDependency && !stepData.pw_medicalDependencyDetails) return false;
      }
      if (selectedServices.broadband) {
        if (!stepData.bb_transferType || !stepData.bb_serviceStartDate || !stepData.bb_routerPreference) return false;
        if ((stepData.bb_routerPreference === 'Purchase Router' || stepData.bb_routerPreference === 'Purchase') && !stepData.bb_purchaseDetails?.trim()) return false;
      }
      if (selectedServices.mobile) {
        if (!stepData.mb_transferType) return false;
        if (stepData.mb_transferType === 'Switch Provider') {
          if (!stepData.mb_portingNumber?.trim() || !/^[\d\s-]{7,11}$/.test(stepData.mb_portingNumber.replace(/[\s-]/g, '')) || !stepData.mb_currentProvider?.trim() || !stepData.mb_accountNumber?.trim() || !stepData.mb_portingPin?.trim() || stepData.mb_portingConsent !== true) {
            return false;
          }
        } else if (stepData.mb_transferType === 'New Number') {
          if (!stepData.mb_simPreference) return false;
          if (stepData.mb_simPreference === 'eSIM') {
            if (!stepData.mb_esimEmail?.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(stepData.mb_esimEmail) || !stepData.mb_deviceModel?.trim()) {
              return false;
            }
          } else if (stepData.mb_simPreference === 'Physical SIM') {
            if (!stepData.mb_deliveryAddress?.trim()) {
              return false;
            }
          }
        } else {
          return false;
        }
      }
      return true;
    }
      
    case 'howYoullPay': {
      // Check if payment method is selected
      if (!stepData.paymentMethod && !stepData.paymentMethodType) return false;

      // If Direct Debit, require all bank details
      if (stepData.paymentMethodType === 'DIRECT_DEBIT' || stepData.paymentMethod === 'DIRECT_DEBIT') {
        return !!(
          stepData.bankName &&
          stepData.accountName &&
          stepData.accountNumber
        );
      }

      // For other payment methods, just require the method
      return true;
    }
      
    case 'preferences': {
      if (!stepData || !stepData.preferences) return false;
      
      const { preferences, paymentMethodType } = stepData;
      const hasElectricity = normalizedData.yourServices?.selectedServices?.electricity === true;

      // Check which sections should be visible
      const showDirectDebitReminders = paymentMethodType === 'DIRECT_DEBIT';
      const showBillReminders = paymentMethodType === 'BANK_TRANSFER';
      const showCreditCardReminders = paymentMethodType === 'CREDIT_CARD';
      const showOutageAlerts = hasElectricity;
      
      // If no sections are visible, step is complete
      const hasVisibleSections = showDirectDebitReminders || showOutageAlerts || showBillReminders || showCreditCardReminders;
      if (!hasVisibleSections) return true;

      // Validate each visible section has at least one method selected
      if (showDirectDebitReminders && !preferences.ddRemindersEmail && !preferences.ddRemindersSMS) return false;
      if (showOutageAlerts && !preferences.outageRemindersEmail && !preferences.outageRemindersSMS) return false;
      if (showBillReminders && !preferences.billRemindersEmail && !preferences.billRemindersSMS) return false;
      if (showCreditCardReminders && !preferences.creditCardRemindersEmail && !preferences.creditCardRemindersSMS) return false;

      return true;
    }
    
    case 'confirmation':
      // For confirmation, check if all previous steps are complete
      return getStepCompletionStatus(normalizedData)
        .slice(0, -1) // Exclude confirmation step itself
        .every(Boolean);
    
    default:
      return false;
  }
}

// This function should be updated to properly check the services details
export function isServicesStepComplete(normalizedData) {
  if (!normalizedData || typeof normalizedData !== 'object') {
    return false;
  }
  // Handle nested data structure
  const data = normalizedData.data?.serviceDetails || normalizedData.data || normalizedData;
  // Extract selected services from different possible locations
  const selectedServices = 
    data.selectedServices || 
    data.yourServices?.selectedServices || 
    data.step_data?.yourServices?.selectedServices || 
    {};
  const hasPower = selectedServices.electricity;
  const hasBroadband = selectedServices.broadband;
  const hasMobile = selectedServices.mobile;
  if (!hasPower && !hasBroadband && !hasMobile) {
    return false;
  }
  // Get service details from different possible locations
  const serviceDetails = data.serviceDetails || data;
  let isStepValid = true;
  // Power service validation
  if (hasPower) {
    if (!serviceDetails.pw_transferType || !serviceDetails.pw_serviceStartDate) {
      isStepValid = false;
    }
    if (serviceDetails.pw_medicalDependency === undefined || serviceDetails.pw_medicalDependency === null) {
      isStepValid = false;
    }
    if (serviceDetails.pw_medicalDependency === true && !serviceDetails.pw_medicalDependencyDetails?.trim()) {
      isStepValid = false;
    }
  }
  if (hasBroadband) {
    if (!serviceDetails.bb_transferType || !serviceDetails.bb_serviceStartDate) {
      isStepValid = false;
    }
    if (!serviceDetails.bb_routerPreference) {
      isStepValid = false;
    }
    if ((serviceDetails.bb_routerPreference === 'Purchase Router' || serviceDetails.bb_routerPreference === 'Purchase') && !serviceDetails.bb_purchaseDetails?.trim()) {
      isStepValid = false;
    }
  }
  if (hasMobile) {
    if (!serviceDetails.mb_transferType) {
      isStepValid = false;
    } else {
      if (serviceDetails.mb_transferType === 'Switch Provider') {
        if (!serviceDetails.mb_portingNumber?.trim() || !/^[\d\s-]{7,11}$/.test(serviceDetails.mb_portingNumber.replace(/[\s-]/g, '')) || !serviceDetails.mb_currentProvider?.trim() || !serviceDetails.mb_accountNumber?.trim() || !serviceDetails.mb_portingPin?.trim() || serviceDetails.mb_portingConsent !== true) {
          isStepValid = false;
        }
      } else if (serviceDetails.mb_transferType === 'New Number') {
        if (!serviceDetails.mb_simPreference) {
          isStepValid = false;
        } else {
          if (serviceDetails.mb_simPreference === 'eSIM') {
            if (!serviceDetails.mb_esimEmail?.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(serviceDetails.mb_esimEmail) || !serviceDetails.mb_deviceModel?.trim()) {
              isStepValid = false;
            }
          } else if (serviceDetails.mb_simPreference === 'Physical SIM') {
            if (!serviceDetails.mb_deliveryAddress?.trim()) {
              isStepValid = false;
            }
          }
        }
      } else {
        isStepValid = false;
      }
    }
  }
  if (isStepValid) {
    if (data.completed === false) {
      isStepValid = false;
    }
  }
  return isStepValid;
}

// This function should replace or update the existing step completion check for yourServices
export function checkStepCompletion(stepKey, stepData) {
  if (!stepData) return false;
  
  switch (stepKey) {
    // Existing cases...
    
    case 'yourServices':
      return isServicesStepComplete(stepData);
    
    // Other cases...
    
    default:
      return false;
  }
}

// New property step completion check
export const isPropertyStepComplete = (data) => {
  // Check if address is selected
  if (!data.selectedAddress) return false;

  // Check if at least one service is selected
  const hasSelectedServices = Object.values(data.selectedServices || {}).some(service => service);
  if (!hasSelectedServices) return false;

  // Check if selected services have corresponding plans
  if (data.selectedPlans) {
    const hasElectricityPlan = data.selectedServices.electricity ? data.selectedPlans.electricity : true;
    const hasBroadbandPlan = data.selectedServices.broadband ? data.selectedPlans.broadband : true;
    const hasMobilePlan = data.selectedServices.mobile ? data.selectedPlans.mobile : true;
    
    // At least one plan should be selected for selected services
    return hasElectricityPlan || hasBroadbandPlan || hasMobilePlan;
  }

  return false;
};
