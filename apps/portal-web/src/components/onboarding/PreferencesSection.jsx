import { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { BellIcon, EnvelopeIcon, DevicePhoneMobileIcon } from '@heroicons/react/24/outline';
import { Switch } from '@headlessui/react';

export default function PreferencesSection({ onAutosave, userData = {} }) {
  // Extract payment method from all possible paths with improved fallbacks
  const paymentMethod = 
    userData.paymentSetup?.paymentMethodType || 
    userData.howYoullPay?.paymentMethodType ||
    userData.howYoullPay?.paymentSetup?.paymentMethodType ||
    userData.step_data?.howYoullPay?.paymentMethodType ||
    userData.preferences?.paymentMethodType || // Add preferences as last fallback
    undefined;

  // Try to find selectedServices across all data paths
  const selectedServices = 
    userData.yourServices?.selectedServices || 
    userData.selectedServices || 
    userData.services?.selectedServices ||
    userData.howYoullPay?.selectedServices ||
    userData.yourProperty?.selectedServices ||
    userData.initialSelection?.selectedServices ||
    userData.step_data?.yourServices?.selectedServices ||
    {};
  
  // Determine which notification sections to show
  const showDirectDebitReminders = paymentMethod === 'DIRECT_DEBIT';
  const showBillReminders = paymentMethod === 'BANK_TRANSFER';
  const showCreditCardReminders = paymentMethod === 'CREDIT_CARD';

  // Check for electricity service selected
  const hasElectricity = 
    selectedServices.electricity === true ||
    userData.electricity?.selected === true ||
    userData.yourServices?.electricity === true ||
    userData.step_data?.yourServices?.electricity === true;

  const showOutageAlerts = hasElectricity;

  // Track if this is the first render
  const isFirstRender = useRef(true);

  const [form, setForm] = useState(() => {
    // Get preferences with robust fallback chain
    const storedPreferences = 
      userData.preferences?.preferences || 
      userData.step_data?.preferences?.preferences ||
      userData.preferences || // Add direct preferences as fallback
      {};

    return {
      ddRemindersEmail: storedPreferences.ddRemindersEmail ?? false,
      ddRemindersSMS: storedPreferences.ddRemindersSMS ?? false,
      outageRemindersEmail: storedPreferences.outageRemindersEmail ?? false,
      outageRemindersSMS: storedPreferences.outageRemindersSMS ?? false,
      billRemindersEmail: storedPreferences.billRemindersEmail ?? false,
      billRemindersSMS: storedPreferences.billRemindersSMS ?? false,
      creditCardRemindersEmail: storedPreferences.creditCardRemindersEmail ?? false,
      creditCardRemindersSMS: storedPreferences.creditCardRemindersSMS ?? false
    };
  });

  const [errors, setErrors] = useState({});

  // Validate form fields
  const validateForm = useCallback(() => {
    const newErrors = {};
    let isValid = true;

    // Only validate sections that are shown
    if (showDirectDebitReminders && !form.ddRemindersEmail && !form.ddRemindersSMS) {
      newErrors.ddReminders = 'Please select at least one notification method for direct debit reminders.';
      isValid = false;
    }
    if (showOutageAlerts && !form.outageRemindersEmail && !form.outageRemindersSMS) {
      newErrors.outageReminders = 'Please select at least one notification method for outage alerts.';
      isValid = false;
    }
    if (showBillReminders && !form.billRemindersEmail && !form.billRemindersSMS) {
      newErrors.billReminders = 'Please select at least one notification method for bill reminders.';
      isValid = false;
    }
    if (showCreditCardReminders && !form.creditCardRemindersEmail && !form.creditCardRemindersSMS) {
      newErrors.creditCardReminders = 'Please select at least one notification method for credit card reminders.';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  }, [form, showDirectDebitReminders, showOutageAlerts, showBillReminders, showCreditCardReminders]);

  // Handle switch changes and trigger validation
  const handleSwitchChange = useCallback((name, checked) => {
    setForm(prev => {
      return { ...prev, [name]: checked };
    });
  }, []);

  // Replace autosave effect
  useEffect(() => {
    if (isFirstRender.current) {
      // Get preferences with robust fallback chain
      const storedPreferences = 
        userData.preferences?.preferences || 
        userData.step_data?.preferences?.preferences ||
        userData.preferences || // Add direct preferences as fallback
        {};
      setForm({
        ddRemindersEmail: storedPreferences.ddRemindersEmail ?? false,
        ddRemindersSMS: storedPreferences.ddRemindersSMS ?? false,
        outageRemindersEmail: storedPreferences.outageRemindersEmail ?? false,
        outageRemindersSMS: storedPreferences.outageRemindersSMS ?? false,
        billRemindersEmail: storedPreferences.billRemindersEmail ?? false,
        billRemindersSMS: storedPreferences.billRemindersSMS ?? false,
        creditCardRemindersEmail: storedPreferences.creditCardRemindersEmail ?? false,
        creditCardRemindersSMS: storedPreferences.creditCardRemindersSMS ?? false
      });
      isFirstRender.current = false;
    }
    // Do not reset form on every userData change!
  }, []);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const storedPreferences = userData.preferences?.preferences || userData.step_data?.preferences?.preferences || userData.preferences || {};
    const hasChanged = JSON.stringify(form) !== JSON.stringify({
      ddRemindersEmail: storedPreferences.ddRemindersEmail ?? false,
      ddRemindersSMS: storedPreferences.ddRemindersSMS ?? false,
      outageRemindersEmail: storedPreferences.outageRemindersEmail ?? false,
      outageRemindersSMS: storedPreferences.outageRemindersSMS ?? false,
      billRemindersEmail: storedPreferences.billRemindersEmail ?? false,
      billRemindersSMS: storedPreferences.billRemindersSMS ?? false,
      creditCardRemindersEmail: storedPreferences.creditCardRemindersEmail ?? false,
      creditCardRemindersSMS: storedPreferences.creditCardRemindersSMS ?? false
    });

    if (onAutosave && hasChanged) {
      const isValid = validateForm();
      const hasVisibleSections = showDirectDebitReminders || showOutageAlerts || showBillReminders || showCreditCardReminders;
      const preferencesData = {
        preferences: form,
        paymentMethodType: paymentMethod,
        lastModified: new Date().toISOString(),
        completed: hasVisibleSections ? isValid : true
      };
      onAutosave(preferencesData);
    }
  }, [form, validateForm, paymentMethod, showDirectDebitReminders, showOutageAlerts, showBillReminders, showCreditCardReminders, onAutosave, userData]);

  return (
    <form className="max-w-3xl mx-auto">
      <div className="space-y-8">
        <section aria-labelledby="communication-heading" className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-full bg-accent-lightturquoise/10 flex items-center justify-center">
              <BellIcon className="h-6 w-6 text-accent-lightturquoise" />
            </div>
            <div>
              <h3 id="communication-heading" className="text-lg text-start font-semibold text-gray-900 dark:text-white">Notification Preferences</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">Choose how you&apos;d like to receive important updates</p>
            </div>
          </div>

          <div className="space-y-6">
            {/* Direct Debit Reminders */}
            {showDirectDebitReminders && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Direct Debit Reminders</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">Email</span>
                    </div>
                    <Switch
                      checked={form.ddRemindersEmail}
                      onChange={(checked) => handleSwitchChange('ddRemindersEmail', checked)}
                      className={`${form.ddRemindersEmail ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <DevicePhoneMobileIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">SMS</span>
                    </div>
                    <Switch
                      checked={form.ddRemindersSMS}
                      onChange={(checked) => handleSwitchChange('ddRemindersSMS', checked)}
                      className={`${form.ddRemindersSMS ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                </div>
                {errors.ddReminders && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.ddReminders}</p>}
              </div>
            )}

            {/* Outage Alerts */}
            {showOutageAlerts && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Outage Alerts</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">Email</span>
                    </div>
                    <Switch
                      checked={form.outageRemindersEmail}
                      onChange={(checked) => handleSwitchChange('outageRemindersEmail', checked)}
                      className={`${form.outageRemindersEmail ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <DevicePhoneMobileIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">SMS</span>
                    </div>
                    <Switch
                      checked={form.outageRemindersSMS}
                      onChange={(checked) => handleSwitchChange('outageRemindersSMS', checked)}
                      className={`${form.outageRemindersSMS ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                </div>
                {errors.outageReminders && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.outageReminders}</p>}
              </div>
            )}

            {/* Bill Reminders */}
            {showBillReminders && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Bank Transfer Payment Reminders</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">Email</span>
                    </div>
                    <Switch
                      checked={form.billRemindersEmail}
                      onChange={(checked) => handleSwitchChange('billRemindersEmail', checked)}
                      className={`${form.billRemindersEmail ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <DevicePhoneMobileIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">SMS</span>
                    </div>
                    <Switch
                      checked={form.billRemindersSMS}
                      onChange={(checked) => handleSwitchChange('billRemindersSMS', checked)}
                      className={`${form.billRemindersSMS ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                </div>
                {errors.billReminders && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.billReminders}</p>}
              </div>
            )}

            {/* Credit Card Payment Reminders */}
            {showCreditCardReminders && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Credit Card Payment Reminders</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">Email</span>
                    </div>
                    <Switch
                      checked={form.creditCardRemindersEmail}
                      onChange={(checked) => handleSwitchChange('creditCardRemindersEmail', checked)}
                      className={`${form.creditCardRemindersEmail ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between py-2 px-4 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <DevicePhoneMobileIcon className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-700 dark:text-gray-200">SMS</span>
                    </div>
                    <Switch
                      checked={form.creditCardRemindersSMS}
                      onChange={(checked) => handleSwitchChange('creditCardRemindersSMS', checked)}
                      className={`${form.creditCardRemindersSMS ? 'bg-accent-lightturquoise' : 'bg-gray-200 dark:bg-gray-600'}
                        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-lightturquoise`}
                    />
                  </div>
                </div>
                {errors.creditCardReminders && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.creditCardReminders}</p>}
              </div>
            )}
          </div>
        </section>
      </div>
    </form>
  );
}

PreferencesSection.propTypes = {
  onAutosave: PropTypes.func,
  userData: PropTypes.object,
};