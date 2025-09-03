import PropTypes from 'prop-types';
import { 
  UserIcon,
  HomeIcon,
  BoltIcon,
  WifiIcon,
  DevicePhoneMobileIcon,
  CreditCardIcon,
  BellIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { finalizeOnboarding } from '../../services/onboarding';
import { NZ_BANKS } from '../../constants/banks';
import { MOBILE_PROVIDERS } from '../../constants/mobileProviders';
import { useConfirmationStepState } from '../../hooks/useConfirmationStepState';

const ConfirmationSection = ({ 
  userData, 
  addressInfo, 
  selectedServices, 
  selectedPlans,
  onComplete = () => {},
  onFinalSubmit = null,
  isParentSubmitting = false,
  isGstInclusive = true
}) => {
  // Helper function to get terms links based on selected services and plans
  const getTermsLinks = () => {
    const links = {
      generalTerms: {
        url: '/terms/general',
        label: 'General Terms of Service'
      },
      paymentTerms: {
        url: '/terms/payment',
        label: 'Payment Terms'
      }
    };

    // Add combined service and plan terms if selected
    if (selectedServices?.electricity) {
      links.electricityTerms = {
        serviceUrl: '/terms/electricity',
        serviceLabel: 'Electricity General Terms',
        planUrl: selectedPlans?.electricity?.id ? `/terms/plans/electricity/${selectedPlans.electricity.id}` : null,
        planLabel: selectedPlans?.electricity?.name ? `${selectedPlans.electricity.name} Plan Terms` : 'Selected Plan Terms'
      };
    }
    if (selectedServices?.broadband) {
      links.broadbandTerms = {
        serviceUrl: '/terms/broadband',
        serviceLabel: 'Broadband General Terms',
        planUrl: selectedPlans?.broadband?.id ? `/terms/plans/broadband/${selectedPlans.broadband.id}` : null,
        planLabel: selectedPlans?.broadband?.name ? `${selectedPlans.broadband.name} Plan Terms` : 'Selected Plan Terms'
      };
    }
    if (selectedServices?.mobile) {
      const planId = selectedPlans?.mobile?.id || selectedPlans?.mobile?.pricing_id;
      links.mobileTerms = {
        serviceUrl: '/terms/mobile',
        serviceLabel: 'Mobile General Terms',
        planUrl: planId ? `/terms/plans/mobile/${planId}` : null,
        planLabel: selectedPlans?.mobile?.name ? `${selectedPlans.mobile.name} Plan Terms` : 'Selected Plan Terms'
      };
    }

    return links;
  };

  // Get terms links
  const termsLinks = getTermsLinks();

  // Use the confirmation step state hook
  const {
    termsAccepted,
    isSubmitting,
    error,
    setIsSubmitting,
    setError,
    handleTermsChange,
    acceptAllTerms,
    unacceptAllTerms,
    areAllTermsAccepted
  } = useConfirmationStepState(termsLinks);

  // Function to handle direct submission using the API
  const handleSubmit = async () => {
    if (!areAllTermsAccepted()) {
      setError('Please accept all terms and conditions to proceed.');
      return;
    }

    // If parent provides onFinalSubmit, use it (it handles user state updates)
    if (onFinalSubmit) {
      try {
        setError(null);
        await onFinalSubmit();
      } catch (error) {
        console.error('Onboarding submission error:', error);
        const errorMessage = error.response?.data?.error || 
                            error.response?.data?.message || 
                            error.message || 
                            'Failed to complete your service signup. Please try again.';
        setError(errorMessage);
      }
      return;
    }

    // Fallback: use internal submission logic (legacy)
    try {
      setIsSubmitting(true);
      setError(null);

      // Validate required data before submission
      if (!selectedServices || Object.keys(selectedServices).length === 0) {
        throw new Error('No services selected. Please go back and select at least one service.');
      }

      if (!selectedPlans || Object.keys(selectedPlans).length === 0) {
        throw new Error('No plans selected. Please go back and select plans for your chosen services.');
      }

      // Format service start dates
      const formatServiceStartDate = (dateStr) => {
        if (!dateStr || dateStr === 'asap') {
          // Set to tomorrow's date if ASAP
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          return tomorrow.toISOString().split('T')[0];
        }
        return dateStr;
      };

      // Get service details from multiple possible locations
      const serviceDetails = userData?.yourServices?.serviceDetails || 
                            userData?.serviceDetails?.data?.serviceDetails || 
                            userData?.step_data?.serviceDetails?.data?.serviceDetails ||
                            userData?.serviceDetails || 
                            {};

      // Prepare the data for submission
      const submissionData = {
        selectedServices: selectedServices || {},
        selectedPlans: selectedPlans || {},
        addressInfo: addressInfo || {},
        preferences: userData?.preferences?.preferences || {},
        termsAccepted: { ...termsAccepted },
        yourServices: {
          serviceDetails: {
            pw_transferType: serviceDetails?.pw_transferType,
            pw_serviceStartDate: serviceDetails?.pw_serviceStartDate,
            pw_medicalDependency: serviceDetails?.pw_medicalDependency,
            pw_medicalDependencyDetails: serviceDetails?.pw_medicalDependencyDetails,
            bb_transferType: serviceDetails?.bb_transferType,
            bb_serviceStartDate: serviceDetails?.bb_serviceStartDate,
            bb_routerPreference: serviceDetails?.bb_routerPreference,
            bb_purchaseDetails: serviceDetails?.bb_purchaseDetails,
            mb_transferType: serviceDetails?.mb_transferType,
            mb_serviceStartDate: serviceDetails?.mb_serviceStartDate,
            mb_simPreference: serviceDetails?.mb_simPreference,
            mb_portingNumber: serviceDetails?.mb_portingNumber,
            mb_currentProvider: serviceDetails?.mb_currentProvider,
            mb_accountNumber: serviceDetails?.mb_accountNumber,
            mb_portingPin: serviceDetails?.mb_portingPin,
            mb_deviceModel: serviceDetails?.mb_deviceModel,
            mb_deliveryAddress: serviceDetails?.mb_deliveryAddress,
            mb_portingConsent: serviceDetails?.mb_portingConsent,
            mb_esimEmail: serviceDetails?.mb_esimEmail
          }
        },
        contracts: {
          electricity: selectedServices?.electricity ? {
            service_type: 'electricity',
            plan_id: selectedPlans?.electricity?.id || selectedPlans?.electricity?.pricing_id,
            proposed_start_date: formatServiceStartDate(serviceDetails?.pw_serviceStartDate),
            transfer_type: serviceDetails?.pw_transferType,
            medical_dependency: serviceDetails?.pw_medicalDependency,
            medical_dependency_details: serviceDetails?.pw_medicalDependencyDetails
          } : null,
          broadband: selectedServices?.broadband ? {
            service_type: 'broadband',
            plan_id: selectedPlans?.broadband?.id || selectedPlans?.broadband?.pricing_id,
            proposed_start_date: formatServiceStartDate(serviceDetails?.bb_serviceStartDate),
            transfer_type: serviceDetails?.bb_transferType,
            router_preference: serviceDetails?.bb_routerPreference,
            purchase_details: serviceDetails?.bb_purchaseDetails
          } : null,
          mobile: selectedServices?.mobile ? {
            service_type: 'mobile',
            plan_id: selectedPlans?.mobile?.id || selectedPlans?.mobile?.pricing_id || selectedPlans?.mobile?.plan_id,
            proposed_start_date: formatServiceStartDate(serviceDetails?.mb_serviceStartDate),
            transfer_type: serviceDetails?.mb_transferType,
            sim_preference: serviceDetails?.mb_simPreference,
            porting_number: serviceDetails?.mb_portingNumber,
            current_provider: serviceDetails?.mb_currentProvider,
            account_number: serviceDetails?.mb_accountNumber,
            porting_pin: serviceDetails?.mb_portingPin,
            device_model: serviceDetails?.mb_deviceModel,
            delivery_address: serviceDetails?.mb_deliveryAddress,
            porting_consent: serviceDetails?.mb_portingConsent,
            esim_email: serviceDetails?.mb_esimEmail
          } : null
        }
      };

      // Log submission data for debugging (remove in production)
      console.log('Submitting onboarding data:', {
        selectedServices,
        selectedPlans,
        addressInfo,
        serviceDetails,
        submissionData
      });

      // Call the API with the prepared data
      await finalizeOnboarding(submissionData);
      onComplete();
    } catch (error) {
      console.error('Onboarding submission error:', error);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to complete your service signup. Please try again.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };



  // Helper function to format date strings
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not specified';
    if (dateStr === 'asap') return 'As soon as possible';
    try {
      // Handle DD/MM/YYYY format
      if (dateStr.includes('/')) {
        const [day, month, year] = dateStr.split('/');
        return new Date(year, month - 1, day).toLocaleDateString('en-NZ', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      }
      // Handle ISO date format
      if (dateStr.includes('-')) {
        return new Date(dateStr).toLocaleDateString('en-NZ', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      }
      return dateStr;
    } catch {
      return dateStr;
    }
  };

  // Helper function to format boolean values
  const formatBoolean = (value) => {
    if (value === true) return 'Yes';
    if (value === false) return 'No';
    return 'Not specified';
  };

  // Helper function to format notification preferences
  const formatNotifications = (emailKey, smsKey, preferencesData) => {
    const email = preferencesData?.[emailKey];
    const sms = preferencesData?.[smsKey];
    
    if (email && sms) return 'Email & SMS';
    if (email) return 'Email';
    if (sms) return 'SMS';
    return 'None selected';
  };

  // Helper function to format price with GST
  const formatPrice = (amount, unit) => {
    if (!amount) return '-';
    
    const numericAmount = parseFloat(amount);
    
    // Format based on unit type
    if (unit === 'kWh') {
      // For kWh rates, input is in cents per kWh
      const price = isGstInclusive ? numericAmount : (numericAmount / 1.15);
      return `${price.toFixed(2)} cents per kWh`;
    }
    
    // For dollar amounts (daily charge, monthly charge)
    const price = isGstInclusive ? numericAmount : (numericAmount / 1.15);
    
    // Format according to the unit
    if (unit === 'day') {
      return `$${price.toFixed(2)} per day`;
    }
    
    // For monthly charges (broadband)
    return `$${price.toFixed(2)}/month`;
  };

  // Extract data from nested structures
  const aboutYouData = userData?.aboutYou || {};
  const serviceDetails = userData?.yourServices?.serviceDetails || 
                        userData?.serviceDetails?.data?.serviceDetails || 
                        userData?.step_data?.serviceDetails?.data?.serviceDetails ||
                        userData?.serviceDetails || 
                        {};
  const paymentData = userData?.howYoullPay || {};
  const preferencesData = userData?.preferences?.preferences || {};
  const propertyData = userData?.yourProperty || {};

  const sections = [
    {
      title: 'Personal Details',
      icon: UserIcon,
      content: [
        { 
          label: 'Legal Name', 
          value: `${aboutYouData.legalFirstName || ''} ${aboutYouData.middleName ? aboutYouData.middleName + ' ' : ''}${aboutYouData.legalLastName || ''}`.trim() || 'Not specified'
        },
        { label: 'Preferred Name', value: aboutYouData.preferredName || 'Not specified' },
        { label: 'Date of Birth', value: formatDate(aboutYouData.dob) },
        { label: 'Email', value: userData?.initialSelection?.user?.email || userData?.aboutYou?.user?.email || 'Not specified' },
        { label: 'Mobile', value: userData?.initialSelection?.user?.mobile || userData?.aboutYou?.user?.mobile || 'Not specified' },
        { 
          label: 'Credit Check Consent', 
          value: formatBoolean(aboutYouData.consentCreditCheck) 
        },
        ...(aboutYouData.consentCreditCheck && aboutYouData.idType ? [{
          label: 'ID Verification Type', 
          value: aboutYouData.idType === 'driverLicence' ? 'NZ Driver Licence' : aboutYouData.idType === 'passport' ? 'Passport' : 'Not specified'
        }] : []),
        ...(aboutYouData.consentCreditCheck && aboutYouData.idType === 'driverLicence' && aboutYouData.driverLicenceNumber ? [{
          label: 'Driver Licence Number', 
          value: aboutYouData.driverLicenceNumber
        }] : []),
        ...(aboutYouData.consentCreditCheck && aboutYouData.idType === 'driverLicence' && aboutYouData.driverLicenceVersion ? [{
          label: 'Driver Licence Version', 
          value: aboutYouData.driverLicenceVersion
        }] : []),
        ...(aboutYouData.consentCreditCheck && aboutYouData.idType === 'passport' && aboutYouData.passportNumber ? [{
          label: 'Passport Number', 
          value: aboutYouData.passportNumber
        }] : [])
      ].filter(item => item.value && item.value !== 'Not specified')
    },
    {
      title: 'Your Services',
      icon: HomeIcon,
      content: [
        {
          label: 'Selected Services',
          value: (
            <div className="flex-wrap gap-2">
              {selectedServices?.electricity && (
                <div className="inline-flex items-center gap-1.5 bg-gray-700/40 px-3 py-1 rounded-full">
                  <BoltIcon className="h-5 w-5 text-accent-green" />
                  <span className="text-base">Electricity</span>
                </div>
              )}
              {selectedServices?.broadband && (
                <div className="inline-flex items-center gap-1.5 bg-gray-700/40 px-3 py-1 rounded-full">
                  <WifiIcon className="h-5 w-5 text-purple-400" />
                  <span className="text-base">Broadband</span>
                </div>
              )}
              {selectedServices?.mobile && (
                <div className="inline-flex items-center gap-1.5 bg-gray-700/40 px-3 py-1 rounded-full">
                  <DevicePhoneMobileIcon className="h-5 w-5 text-blue-400" />
                  <span className="text-base">Mobile</span>
                </div>
              )}
            </div>
          )
        },
        {
          label: 'Your Address',
          value: addressInfo?.full_address || propertyData?.selectedAddress?.full_address
        },
        ...(selectedPlans?.electricity ? [{
          label: 'Power Plan',
          details: [
            { label: 'Plan Name', value: selectedPlans.electricity.name },
            { label: 'Term', value: selectedPlans.electricity.term },
            { 
              label: 'Daily Charge', 
              value: formatPrice(
                selectedPlans.electricity.charges[selectedPlans.electricity.userType || 'standard'].daily_charge.amount,
                'day'
              )
            },
            ...(selectedPlans.electricity.charges[selectedPlans.electricity.userType || 'standard'].peak_charge ? [
              { 
                label: 'Peak Rate', 
                value: formatPrice(
                  selectedPlans.electricity.charges[selectedPlans.electricity.userType || 'standard'].peak_charge.amount,
                  'kWh'
                )
              },
              { 
                label: 'Off-Peak Rate', 
                value: formatPrice(
                  selectedPlans.electricity.charges[selectedPlans.electricity.userType || 'standard'].off_peak_charge.amount,
                  'kWh'
                )
              }
            ] : [
              { 
                label: 'Variable Rate', 
                value: formatPrice(
                  selectedPlans.electricity.charges[selectedPlans.electricity.userType || 'standard'].variable_charge?.amount,
                  'kWh'
                )
              }
            ]),
          ]
        }] : []),
        ...(selectedPlans?.broadband ? [{
          label: 'Broadband Plan',
          details: [
            { label: 'Plan Name', value: selectedPlans.broadband.name },
            { 
              label: 'Monthly Price', 
              value: formatPrice(selectedPlans.broadband.charges.monthly_charge, 'month', 'rate')
            },
            { label: 'Term', value: selectedPlans.broadband.term },
            { label: 'Download Speed', value: selectedPlans.broadband.download_speed },
            { label: 'Upload Speed', value: selectedPlans.broadband.upload_speed },
            { label: 'Data Allowance', value: selectedPlans.broadband.data_allowance },
          ]
        }] : []),
        ...(selectedPlans?.mobile ? [{
          label: 'Mobile Plan',
          details: [
            { label: 'Plan Name', value: selectedPlans.mobile.name },
            { 
              label: 'Monthly Price', 
              value: formatPrice(selectedPlans.mobile.charges?.monthly_charge || selectedPlans.mobile.monthly_price, 'month')
            },
            { label: 'Term', value: selectedPlans.mobile.term },
            { label: 'Data Allowance', value: selectedPlans.mobile.data_allowance || selectedPlans.mobile.data },
            { label: 'Call Minutes', value: selectedPlans.mobile.call_minutes || selectedPlans.mobile.calls || 'Unlimited' },
            { label: 'Text Messages', value: selectedPlans.mobile.text_messages || selectedPlans.mobile.texts || 'Unlimited' },
          ]
        }] : []),
        <div key="gst-footer" className="mt-2 text-sm text-gray-400">All prices shown {isGstInclusive ? 'include' : 'exclude'} GST</div>
      ],
    },
    // Consolidated Service Details Section
    ...((selectedServices?.electricity || selectedServices?.broadband || selectedServices?.mobile) ? [{
      title: 'Service Details',
      icon: CheckIcon,
      content: [
        // Power Service Details
        ...(selectedServices?.electricity ? [
          {
            label: 'Power Service',
            details: [
              { 
                label: 'Transfer Type', 
                value: serviceDetails.pw_transferType === 'Switch' ? 'Switch Provider' :
                       serviceDetails.pw_transferType === 'MoveIn' ? 'Moving In' :
                       serviceDetails.pw_transferType === 'Installation' ? 'New Connection' :
                       serviceDetails.pw_transferType || 'Not specified' 
              },
              { label: 'Service Start Date', value: formatDate(serviceDetails.pw_serviceStartDate) },
              { label: 'Medical Dependency', value: formatBoolean(serviceDetails.pw_medicalDependency) },
              ...(serviceDetails.pw_medicalDependency && serviceDetails.pw_medicalDependencyDetails ? [{
                label: 'Medical Dependency Details', 
                value: serviceDetails.pw_medicalDependencyDetails
              }] : [])
            ]
          }
        ] : []),
        // Broadband Service Details
        ...(selectedServices?.broadband ? [
          {
            label: 'Broadband Service',
            details: [
              { 
                label: 'Transfer Type', 
                value: serviceDetails.bb_transferType === 'Switch' ? 'Switch Provider' :
                       serviceDetails.bb_transferType === 'MoveIn' ? 'Moving In' :
                       serviceDetails.bb_transferType === 'Installation' ? 'New Connection' :
                       serviceDetails.bb_transferType || 'Not specified' 
              },
              { label: 'Service Start Date', value: formatDate(serviceDetails.bb_serviceStartDate) },
              { 
                label: 'Router Preference', 
                value: serviceDetails.bb_routerPreference === 'BYO' ? 'Bring Your Own' :
                       serviceDetails.bb_routerPreference === 'Purchase' ? 'Purchase Router' :
                       serviceDetails.bb_routerPreference || 'Not specified' 
              },
              ...(serviceDetails.bb_routerPreference === 'Purchase' && serviceDetails.bb_purchaseDetails ? [{
                label: 'Router Purchase Details', 
                value: serviceDetails.bb_purchaseDetails
              }] : [])
            ]
          }
        ] : []),
        // Mobile Service Details
        ...(selectedServices?.mobile ? [
          {
            label: 'Mobile Service',
            details: [
              { 
                label: 'Transfer Type', 
                value: serviceDetails.mb_transferType === 'Switch Provider' ? 'Switch Provider (Port In)' :
                       serviceDetails.mb_transferType === 'New Number' ? 'New Number' :
                       serviceDetails.mb_transferType || 'Not specified' 
              },
              { label: 'Service Start Date', value: formatDate(serviceDetails.mb_serviceStartDate) },
              ...(serviceDetails.mb_transferType === 'Switch Provider' ? [
                { label: 'Porting Number', value: serviceDetails.mb_portingNumber || 'Not specified' },
                { 
                  label: 'Current Provider', 
                  value: MOBILE_PROVIDERS.find(provider => provider.id === serviceDetails.mb_currentProvider)?.name || serviceDetails.mb_currentProvider || 'Not specified'
                },
                { label: 'Account Number', value: serviceDetails.mb_accountNumber || 'Not specified' },
                { label: 'Porting PIN', value: serviceDetails.mb_portingPin ? '****' : 'Not specified' },
                { label: 'Porting Consent', value: formatBoolean(serviceDetails.mb_portingConsent) }
              ] : []),
              ...(serviceDetails.mb_transferType === 'New Number' ? [
                { 
                  label: 'SIM Preference', 
                  value: serviceDetails.mb_simPreference === 'Physical SIM' ? 'Physical SIM' :
                         serviceDetails.mb_simPreference === 'eSIM' ? 'eSIM' :
                         serviceDetails.mb_simPreference || 'Not specified' 
                },
                ...(serviceDetails.mb_simPreference === 'eSIM' ? [
                  { label: 'eSIM Email', value: serviceDetails.mb_esimEmail || 'Not specified' },
                  { label: 'Device Model', value: serviceDetails.mb_deviceModel || 'Not specified' }
                ] : []),
                ...(serviceDetails.mb_simPreference === 'Physical SIM' ? [
                  { label: 'Delivery Address', value: serviceDetails.mb_deliveryAddress || 'Not specified' }
                ] : [])
              ] : [])
            ]
          }
        ] : [])
      ]
    }] : []),
    {
      title: 'Payment Method',
      icon: CreditCardIcon,
      content: [
        { 
          label: 'Payment Method Type', 
          value: paymentData.paymentMethodType === 'DIRECT_DEBIT' ? 'Direct Debit' : 
                 paymentData.paymentMethodType === 'CREDIT_CARD' ? 'Credit Card' : 
                 paymentData.paymentMethodType === 'BANK_TRANSFER' ? 'Bank Transfer' : 
                 'Not specified' 
        },
        ...(paymentData.paymentMethodType === 'DIRECT_DEBIT' ? [
          {
            label: 'Bank Details',
            details: [
              { 
                label: 'Bank', 
                value: NZ_BANKS.find(bank => bank.id === paymentData.bankName)?.name || paymentData.bankName || 'Not specified'
              },
              { label: 'Account Name', value: paymentData.accountName || 'Not specified' },
              { label: 'Account Number', value: paymentData.accountNumber || 'Not specified' }
            ]
          }
        ] : [])
      ]
    },
    {
      title: 'Notification Preferences',
      icon: BellIcon,
      content: [
        ...(paymentData.paymentMethodType === 'DIRECT_DEBIT' ? [{
          label: 'Direct Debit Reminders', 
          value: formatNotifications('ddRemindersEmail', 'ddRemindersSMS', preferencesData)
        }] : []),
        ...(selectedServices?.electricity ? [{
          label: 'Outage Alerts', 
          value: formatNotifications('outageRemindersEmail', 'outageRemindersSMS', preferencesData)
        }] : []),
        ...(paymentData.paymentMethodType === 'BANK_TRANSFER' ? [{
          label: 'Bill Payment Reminders', 
          value: formatNotifications('billRemindersEmail', 'billRemindersSMS', preferencesData)
        }] : []),
        ...(paymentData.paymentMethodType === 'CREDIT_CARD' ? [{
          label: 'Credit Card Payment Reminders', 
          value: formatNotifications('creditCardRemindersEmail', 'creditCardRemindersSMS', preferencesData)
        }] : [])
      ].filter(item => item.value && item.value !== 'None selected')
    }
  ].filter(section => section.content.length > 0); // Only show sections that have content

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <header className="text-left mb-8">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-accent-green/10 rounded-full mb-3">
              <CheckIcon className="w-6 h-6 text-accent-green" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Review Your Details
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 max-w-2xl">
            Please carefully review all information below before completing your service signup. 
            Once submitted, your account will be activated and services will be processed.
          </p>
        </header>

        {/* Content Sections */}
        <div className="space-y-8 mb-12">
          {sections.map((section) => (
            <section
              key={section.title}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              {/* Section Header */}
              <div className="bg-gray-50 dark:bg-gray-700/50 px-3 py-1.5 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-accent-lightturquoise/10 flex items-center justify-center">
                    <section.icon className="h-3.5 w-3.5 text-accent-lightturquoise" aria-hidden="true" />
                  </div>
                  <h2 className="text-base font-semibold text-gray-900 dark:text-white">
                    {section.title}
                  </h2>
                </div>
              </div>

              {/* Section Content */}
              <div className="px-4 py-3">
                <div className="space-y-2">
                  {section.content.map((item, itemIndex) => (
                    <div key={itemIndex} className="border-b border-gray-100 dark:border-gray-700 last:border-b-0 pb-2 last:pb-0">
                      <div className="flex flex-col md:flex-row md:items-start">
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 md:w-1/4 md:min-w-[140px] text-left">
                          {item.label}
                        </dt>
                        <dd className="text-sm text-gray-900 dark:text-white md:w-3/4">
                          <div className="font-medium text-left">
                            {item.value}
                          </div>
                          {item.details && (
                            <div className="mt-1.5 bg-gray-50 dark:bg-gray-700/30 rounded-md px-3 py-2">
                              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {item.details.map((detail, detailIndex) => (
                                  <li key={detailIndex} className="flex flex-col text-sm leading-snug">
                                    <span className="font-medium text-gray-500 dark:text-gray-400 mb-1 text-left">{detail.label}</span>
                                    <span className="text-gray-800 dark:text-gray-200 break-words text-left">{detail.value}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </dd>
                      </div>
                    </div>
                  ))}
                </div>
                {/* GST Footer for Your Services section only */}
                {section.title === 'Your Services' && (
                  <div className="mt-2 text-sm text-gray-400 text-left">
                    All prices shown {isGstInclusive ? 'include' : 'exclude'} GST
                  </div>
                )}
              </div>
            </section>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-8 px-2 rounded-t-xl shadow-lg">
          <div className="w-full mx-auto">
            {/* Terms and Conditions Checkboxes - Compact with Original Design */}
            <div className="space-y-4 mb-6">
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700/50 rounded-xl p-3 sm:p-4 border border-gray-200/50 dark:border-gray-700/50 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-3">
                  <div className="flex items-center gap-2">
                    <div className="h-7 w-7 rounded-full bg-accent-green/10 flex items-center justify-center">
                      <svg className="h-4 w-4 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">Legal Acceptance</span>
                  </div>
                  <button
                    type="button"
                    onClick={areAllTermsAccepted() ? unacceptAllTerms : acceptAllTerms}
                    className="px-3 py-1.5 text-xs font-medium text-white bg-accent-green/60 rounded-full hover:bg-accent-green/80 transition-colors duration-200 flex items-center gap-1 self-start sm:self-center"
                  >
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={areAllTermsAccepted() ? "M6 18L18 6M6 6l12 12" : "M5 13l4 4L19 7"} />
                    </svg>
                    {areAllTermsAccepted() ? 'Unaccept All' : 'Accept All'}
                  </button>
                </div>

                <div className="space-y-3 max-h-80 sm:max-h-none overflow-y-auto sm:overflow-visible">
                  {/* 1. General Terms */}
                  <div className="relative">
                    <div className="absolute -left-1 top-1/2 -translate-y-1/2 h-6 w-1 bg-accent-green rounded-full"></div>
                    <label className="relative flex items-start group cursor-pointer pl-4 py-2 transition-all select-none">
                      <span className="flex items-center justify-center h-6 w-6 rounded-full bg-accent-green/10 mr-3 mt-0.5 flex-shrink-0">
                        <svg className="h-3.5 w-3.5 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 15c2.5 0 4.847.655 6.879 1.804M15 11a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </span>
                      <span className="relative inline-flex items-center mr-3 mt-0.5 flex-shrink-0">
                        <input
                          type="checkbox"
                          checked={termsAccepted.generalTerms}
                          onChange={() => handleTermsChange('generalTerms')}
                          className="peer appearance-none h-5 w-5 rounded-lg border-2 border-gray-300 checked:border-accent-green checked:bg-accent-green/80 transition-colors duration-200 focus:outline-none"
                        />
                        <span className="absolute left-0 top-0 h-5 w-5 flex items-center justify-center pointer-events-none">
                          {termsAccepted.generalTerms && (
                            <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                          )}
                        </span>
                      </span>
                      <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed text-left flex-1">
                        I accept the{' '}
                        <a
                          href={termsLinks.generalTerms.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80 break-words"
                        >
                          {termsLinks.generalTerms.label}
                        </a>
                      </span>
                    </label>
                  </div>

                  {/* 2. Electricity Terms */}
                  {selectedServices?.electricity && termsLinks.electricityTerms && (
                    <div className="relative">
                      <div className="absolute -left-1 top-1/2 -translate-y-1/2 h-5 w-1 bg-yellow-500/50 rounded-full"></div>
                      <label className="relative flex items-start group cursor-pointer pl-4 py-2 transition-all select-none">
                        <span className="flex items-center justify-center h-6 w-6 rounded-full bg-yellow-500/10 mr-3 mt-0.5 flex-shrink-0">
                          <BoltIcon className="h-3.5 w-3.5 text-yellow-500" />
                        </span>
                        <span className="relative inline-flex items-center mr-3 mt-0.5 flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={termsAccepted.electricityTerms}
                            onChange={() => handleTermsChange('electricityTerms')}
                            className="peer appearance-none h-5 w-5 rounded-lg border-2 border-gray-300 checked:border-yellow-500 checked:bg-yellow-500/80 transition-colors duration-200 focus:outline-none"
                          />
                          <span className="absolute left-0 top-0 h-5 w-5 flex items-center justify-center pointer-events-none">
                            {termsAccepted.electricityTerms && (
                              <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                            )}
                          </span>
                        </span>
                        <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed text-left flex-1">
                          I accept the{' '}
                          <a
                            href={termsLinks.electricityTerms.serviceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                          >
                            {termsLinks.electricityTerms.serviceLabel}
                          </a>
                          {termsLinks.electricityTerms.planUrl && (
                            <>
                              {' and '}
                              <a
                                href={termsLinks.electricityTerms.planUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                              >
                                {termsLinks.electricityTerms.planLabel}
                              </a>
                            </>
                          )}
                        </span>
                      </label>
                    </div>
                  )}

                  {/* 3. Broadband Terms */}
                  {selectedServices?.broadband && termsLinks.broadbandTerms && (
                    <div className="relative">
                      <div className="absolute -left-1 top-1/2 -translate-y-1/2 h-5 w-1 bg-purple-500/50 rounded-full"></div>
                      <label className="relative flex items-start group cursor-pointer pl-4 py-2 transition-all select-none">
                        <span className="flex items-center justify-center h-6 w-6 rounded-full bg-purple-500/10 mr-3 mt-0.5 flex-shrink-0">
                          <WifiIcon className="h-3.5 w-3.5 text-purple-500" />
                        </span>
                        <span className="relative inline-flex items-center mr-3 mt-0.5 flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={termsAccepted.broadbandTerms}
                            onChange={() => handleTermsChange('broadbandTerms')}
                            className="peer appearance-none h-5 w-5 rounded-lg border-2 border-gray-300 checked:border-purple-500 checked:bg-purple-500/80 transition-colors duration-200 focus:outline-none"
                          />
                          <span className="absolute left-0 top-0 h-5 w-5 flex items-center justify-center pointer-events-none">
                            {termsAccepted.broadbandTerms && (
                              <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                            )}
                          </span>
                        </span>
                        <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed text-left flex-1">
                          I accept the{' '}
                          <a
                            href={termsLinks.broadbandTerms.serviceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                          >
                            {termsLinks.broadbandTerms.serviceLabel}
                          </a>
                          {termsLinks.broadbandTerms.planUrl && (
                            <>
                              {' and '}
                              <a
                                href={termsLinks.broadbandTerms.planUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                              >
                                {termsLinks.broadbandTerms.planLabel}
                              </a>
                            </>
                          )}
                        </span>
                      </label>
                    </div>
                  )}

                  {/* 4. Mobile Terms */}
                  {selectedServices?.mobile && termsLinks.mobileTerms && (
                    <div className="relative">
                      <div className="absolute -left-1 top-1/2 -translate-y-1/2 h-5 w-1 bg-pink-500/50 rounded-full"></div>
                      <label className="relative flex items-start group cursor-pointer pl-4 py-2 transition-all select-none">
                        <span className="flex items-center justify-center h-6 w-6 rounded-full bg-pink-500/10 mr-3 mt-0.5 flex-shrink-0">
                          <DevicePhoneMobileIcon className="h-3.5 w-3.5 text-pink-500" />
                        </span>
                        <span className="relative inline-flex items-center mr-3 mt-0.5 flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={termsAccepted.mobileTerms}
                            onChange={() => handleTermsChange('mobileTerms')}
                            className="peer appearance-none h-5 w-5 rounded-lg border-2 border-gray-300 checked:border-pink-500 checked:bg-pink-500/80 transition-colors duration-200 focus:outline-none"
                          />
                          <span className="absolute left-0 top-0 h-5 w-5 flex items-center justify-center pointer-events-none">
                            {termsAccepted.mobileTerms && (
                              <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                            )}
                          </span>
                        </span>
                        <span className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed text-left flex-1">
                          I accept the{' '}
                          <a
                            href={termsLinks.mobileTerms.serviceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                          >
                            {termsLinks.mobileTerms.serviceLabel}
                          </a>
                          {termsLinks.mobileTerms.planUrl && (
                            <>
                              {' and '}
                              <a
                                href={termsLinks.mobileTerms.planUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                              >
                                {termsLinks.mobileTerms.planLabel}
                              </a>
                            </>
                          )}
                        </span>
                      </label>
                    </div>
                  )}

                  {/* 5. Payment Terms */}
                  <div className="relative">
                    <div className="absolute -left-1 top-1/2 -translate-y-1/2 h-6 w-1 bg-accent-green rounded-full"></div>
                    <label className="relative flex items-start group cursor-pointer pl-4 py-2 transition-all select-none">
                      <span className="flex items-center justify-center h-6 w-6 rounded-full bg-accent-green/10 mr-3 mt-0.5 flex-shrink-0">
                        <svg className="h-3.5 w-3.5 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </span>
                      <span className="relative inline-flex items-center mr-3 mt-0.5 flex-shrink-0">
                        <input
                          type="checkbox"
                          checked={termsAccepted.paymentTerms}
                          onChange={() => handleTermsChange('paymentTerms')}
                          className="peer appearance-none h-5 w-5 rounded-lg border-2 border-gray-300 checked:border-accent-green checked:bg-accent-green/80 transition-colors duration-200 focus:outline-none"
                        />
                        <span className="absolute left-0 top-0 h-5 w-5 flex items-center justify-center pointer-events-none">
                          {termsAccepted.paymentTerms && (
                            <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                          )}
                        </span>
                      </span>
                      <span className="ml-3 text-xs text-gray-700 dark:text-gray-300">
                        I accept the{' '}
                        <a
                          href={termsLinks.paymentTerms.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline decoration-2 underline-offset-2 transition-colors duration-200 hover:opacity-80"
                        >
                          {termsLinks.paymentTerms.label}
                        </a>
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-left px-2 mb-6">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                By clicking &ldquo;Confirm &amp; Submit&rdquo;, you confirm that all information provided is accurate.
              </p>
            </div>

            {error && (
              <div className="rounded-xl bg-red-50 dark:bg-red-900/30 p-4 mb-4 border border-red-100 dark:border-red-800/50">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800 dark:text-red-200">{error}</h3>
                  </div>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={handleSubmit}
              disabled={(onFinalSubmit ? isParentSubmitting : isSubmitting) || !Object.values(termsAccepted).every(accepted => accepted)}
              className="w-full  inline-flex items-center justify-center px-8 py-4 text-base font-medium text-white bg-gradient-to-r from-accent-green to-accent-green/90 rounded-xl hover:from-accent-green/90 hover:to-accent-green/80 focus:outline-none focus:ring-4 focus:ring-accent-green/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              {(onFinalSubmit ? isParentSubmitting : isSubmitting) ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing Your Service Signup...
                </>
              ) : (
                <>
                  <CheckIcon className="h-6 w-6 mr-3" />
                  Complete Service Signup
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

ConfirmationSection.propTypes = {
  userData: PropTypes.object,
  addressInfo: PropTypes.object,
  selectedServices: PropTypes.object,
  selectedPlans: PropTypes.object,
  onComplete: PropTypes.func.isRequired,
  isSubmitting: PropTypes.bool,
  isGstInclusive: PropTypes.bool
};

export default ConfirmationSection;
