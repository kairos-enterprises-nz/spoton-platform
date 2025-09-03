// Add event emitter functionality to DataSyncManager
export class DataSyncManager extends EventTarget {
  constructor() {
    super();
    this.localStorageKey = 'spoton_onboarding_progress';
    this.syncInProgress = false;
    this.pendingUpdates = new Map();
    this.lastSyncTime = null;
    this.currentStatus = 'idle';
    this.syncTimeout = null;
    
    // Define steps to match Onboarding.jsx
    this.steps = [
      { name: 'About You', description: 'Your personal information', key: 'aboutYou' },
      { name: 'Your Services', description: 'Pick your utilities and plans', key: 'yourServices' },
      { name: 'Service Details', description: 'Details about your services', key: 'serviceDetails' },
      { name: 'How You\'ll Pay', description: 'Set up billing details', key: 'howYoullPay' },
      { name: 'Preferences', description: 'Notification settings', key: 'preferences' },
      { name: 'Confirmation', description: 'Final review & submit', key: 'confirmation' }
    ];
  }

  // Emit status updates
  emitStatusUpdate(status, stepKey = null, details = {}) {
    this.currentStatus = status;
    
    this.dispatchEvent(new CustomEvent('statusUpdate', { 
      detail: { 
        status, 
        stepKey, 
        pendingCount: this.pendingUpdates.size,
        lastSyncTime: this.lastSyncTime,
        ...details 
      } 
    }));
  }

  // Get local data with timestamp
  getLocalData() {
    try {
      const stored = localStorage.getItem(this.localStorageKey);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  // Save local data with timestamp
  setLocalData(data) {
    const timestampedData = {
      ...data,
      lastModified: new Date().toISOString(),
      version: (data.version || 0) + 1
    };
    
    try {
      localStorage.setItem(this.localStorageKey, JSON.stringify(timestampedData));
      this.emitStatusUpdate('saved_locally', null, { data: timestampedData });
      
      // Check step completion after setting local data
      this.checkStepCompletion(timestampedData);
      
      return timestampedData;
    } catch (error) {
      this.emitStatusUpdate('error', null, { error: error.message });
      return data;
    }
  }

  // Deep merge helper
  deepMerge(target, source) {
    for (const key in source) {
      if (
        source[key] &&
        typeof source[key] === 'object' &&
        !Array.isArray(source[key])
      ) {
        if (!target[key]) target[key] = {};
        this.deepMerge(target[key], source[key]);
      } else if (
        source[key] !== null &&
        source[key] !== '' &&
        source[key] !== undefined
      ) {
        target[key] = source[key];
      }
    }
    return target;
  }

  // Merge local and backend data intelligently
  mergeData(localData, backendData) {
    if (!localData && !backendData) return {};
    if (!localData) return { ...backendData, source: 'backend' };
    if (!backendData) return { ...localData, source: 'local' };

    const merged = { ...backendData };
    this.steps.forEach(step => {
      const stepKey = step.key;
      const localStep = localData[stepKey];
      const backendStep = backendData[stepKey];
      if (localStep && backendStep) {
        // Deep merge: prefer non-empty local values, otherwise keep backend
        merged[stepKey] = this.deepMerge({ ...backendStep }, localStep);
        merged[stepKey].needsSync = true;
      } else if (localStep) {
        merged[stepKey] = { ...localStep, needsSync: true };
      } else if (backendStep) {
        merged[stepKey] = backendStep;
      }
    });

    // Check step completion after merging
    this.checkStepCompletion(merged);

    return { ...merged, source: 'merged' };
  }

  // Queue updates to prevent conflicts
  queueUpdate(stepKey, data) {
    // Validate step key
    if (!this.steps.some(step => step.key === stepKey)) {
      console.warn(`Invalid step key: ${stepKey}`);
      return;
    }

    this.pendingUpdates.set(stepKey, {
      data,
      timestamp: new Date().toISOString()
    });
    
    // Clear any existing sync timeout
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout);
    }
    
    // Set a new sync timeout
    this.syncTimeout = setTimeout(() => {
      this.processQueuedUpdates();
    }, 1000); // Wait 1 second before syncing
    
    // Change from 'queued' to 'saving' to match UI expectations
    this.emitStatusUpdate('saving', stepKey, { 
      pendingCount: this.pendingUpdates.size 
    });
  }

  // Process queued updates
  async processQueuedUpdates(saveFunction) {
    if (this.syncInProgress || this.pendingUpdates.size === 0) {
      return;
    }

    this.syncInProgress = true;
    this.emitStatusUpdate('saving');
    
    // Define localPendingUpdates in the scope where it's used
    let localPendingUpdates = [];
    
    try {
      localPendingUpdates = Array.from(this.pendingUpdates.entries());
      this.pendingUpdates.clear();
      
      // If multiple steps, process each one individually for better UI feedback
      for (const [stepKey, { data }] of localPendingUpdates) {
        // Validate step key
        if (!this.steps.some(step => step.key === stepKey)) {
          console.warn(`Skipping invalid step key: ${stepKey}`);
          continue;
        }

        this.emitStatusUpdate('saving', stepKey);
        await saveFunction(stepKey, data);
        
        // Emit individual 'saved' events for each step
        this.lastSyncTime = new Date().toISOString();
        this.emitStatusUpdate('saved', stepKey);
        
        // Small delay to ensure UI can show saved status
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      // Only emit a final 'all saved' event if necessary
      if (localPendingUpdates.length > 1) {
        this.lastSyncTime = new Date().toISOString();
        this.emitStatusUpdate('saved');
      }
      
    } catch (error) {
      // Now localPendingUpdates is defined in this scope
      for (const [stepKey, update] of localPendingUpdates) {
        this.queueUpdate(stepKey, update.data);
      }
      
      this.emitStatusUpdate('error', null, { 
        error: error.message,
        willRetry: true 
      });
    } finally {
      this.syncInProgress = false;
    }
  }

  // Get current sync status
  getStatus() {
    return {
      status: this.currentStatus,
      pendingCount: this.pendingUpdates.size,
      lastSyncTime: this.lastSyncTime,
      isOnline: navigator.onLine
    };
  }

  // Clear local data (for testing or reset)
  clearLocalData() {
    localStorage.removeItem(this.localStorageKey);
    this.emitStatusUpdate('cleared');
  }

  // Add method to check step completion
  checkStepCompletion(normalizedData) {
    const completionStatus = this.steps.map(step => {
      const isComplete = this.isStepComplete(normalizedData, step.key);
      return {
        stepKey: step.key,
        isComplete,
        name: step.name
      };
    });

    // Dispatch completion status event
    this.dispatchEvent(new CustomEvent('stepCompletionUpdate', {
      detail: {
        completionStatus,
        timestamp: new Date().toISOString()
      }
    }));

    return completionStatus;
  }

  // Add step completion validation
  isStepComplete(normalizedData, stepKey) {
    if (!normalizedData || !stepKey) return false;

    const stepData = normalizedData[stepKey];
    if (!stepData || Object.keys(stepData).length === 0) return false;

    switch (stepKey) {
      case 'aboutYou': {
        const userData = stepData.personalInfo || stepData;
        const hasRequiredFields = !!(
          userData.legalFirstName && 
          userData.legalLastName && 
          (userData.email || userData.phone || userData.mobile) && 
          userData.dob &&
          userData.preferredName
        );
        
        if (!hasRequiredFields) return false;
        
        const hasConsentedToCheck = userData.consentCreditCheck === true;
        if (!hasConsentedToCheck) return false;
        
        if (userData.idType === 'driverLicence') {
          return !!(userData.driverLicenceNumber && userData.driverLicenceVersion);
        } else if (userData.idType === 'passport') {
          return !!userData.passportNumber;
        }
        return false;
      }
      
      case 'yourServices': {
        const selectedServices = stepData.selectedServices || {};
        const hasServices = Object.values(selectedServices).some(Boolean);
        if (!hasServices) return false;

        const selectedPlans = stepData.selectedPlans || {};
        const hasElectricity = selectedServices.electricity;
        const hasBroadband = selectedServices.broadband;
        const hasMobile = selectedServices.mobile;

        if (hasElectricity && (!selectedPlans.electricity || !selectedPlans.electricity.pricing_id)) return false;
        if (hasBroadband && (!selectedPlans.broadband || !selectedPlans.broadband.pricing_id)) return false;
        if (hasMobile && (!selectedPlans.mobile || !selectedPlans.mobile.pricing_id)) return false;

        return true;
      }

      case 'serviceDetails': {
        const selectedServices = normalizedData.yourServices?.selectedServices || {};
        
        if (selectedServices.electricity) {
          if (!stepData.pw_transferType || !stepData.pw_serviceStartDate) return false;
          if (stepData.pw_medicalDependency && !stepData.pw_medicalDependencyDetails) return false;
        }

        if (selectedServices.broadband) {
          if (!stepData.bb_transferType || !stepData.bb_serviceStartDate || !stepData.bb_routerPreference) return false;
          if (stepData.bb_routerPreference === 'Purchase' && !stepData.bb_purchaseDetails) return false;
        }

        if (selectedServices.mobile) {
          if (!stepData.mb_transferType) return false;
          
          if (stepData.mb_transferType === 'Switch Provider') {
            if (!stepData.mb_portingNumber || !stepData.mb_currentProvider || 
                !stepData.mb_accountNumber || !stepData.mb_portingPin || !stepData.mb_portingConsent) {
              return false;
            }
          } else if (stepData.mb_transferType === 'New Number') {
            if (!stepData.mb_simPreference) return false;
            
            if (stepData.mb_simPreference === 'eSIM') {
              if (!stepData.mb_esimEmail || !stepData.mb_deviceModel) return false;
            } else if (stepData.mb_simPreference === 'Physical SIM') {
              if (!stepData.mb_deliveryAddress) return false;
            }
          }
        }

        return true;
      }
        
      case 'howYoullPay': {
        if (!stepData.paymentMethod && !stepData.paymentMethodType) return false;

        if (stepData.paymentMethodType === 'DIRECT_DEBIT' || stepData.paymentMethod === 'DIRECT_DEBIT') {
          return !!(
            stepData.bankName &&
            stepData.accountName &&
            stepData.accountNumber
          );
        }

        return true;
      }
        
      case 'preferences': {
        if (!stepData || !stepData.preferences) return false;
        
        const { preferences, paymentMethodType } = stepData;
        const hasElectricity = normalizedData.yourServices?.selectedServices?.electricity === true;

        const showDirectDebitReminders = paymentMethodType === 'DIRECT_DEBIT';
        const showBillReminders = paymentMethodType === 'BANK_TRANSFER';
        const showCreditCardReminders = paymentMethodType === 'CREDIT_CARD';
        const showOutageAlerts = hasElectricity;
        
        const hasVisibleSections = showDirectDebitReminders || showOutageAlerts || showBillReminders || showCreditCardReminders;
        if (!hasVisibleSections) return true;

        if (showDirectDebitReminders && !preferences.ddRemindersEmail && !preferences.ddRemindersSMS) return false;
        if (showOutageAlerts && !preferences.outageRemindersEmail && !preferences.outageRemindersSMS) return false;
        if (showBillReminders && !preferences.billRemindersEmail && !preferences.billRemindersSMS) return false;
        if (showCreditCardReminders && !preferences.creditCardRemindersEmail && !preferences.creditCardRemindersSMS) return false;

        return true;
      }
      
      case 'confirmation':
        return this.checkStepCompletion(normalizedData)
          .slice(0, -1)
          .every(status => status.isComplete);
      
      default:
        return false;
    }
  }
}

export const dataSyncManager = new DataSyncManager();