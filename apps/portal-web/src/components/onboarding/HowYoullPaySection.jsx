import { useMemo, useCallback, useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { CreditCard, Building2, Landmark, CheckCircle, Zap, Wifi, Phone } from 'lucide-react';
import { NZ_BANKS } from '../../constants/banks';

const PAYMENT_OPTIONS = [
  {
    id: 'BANK_TRANSFER',
    name: 'Bank Transfer',
    subtitle: 'Manual Payments',
    description: 'Transfer funds directly from your bank account when invoices are due',
    icon: Landmark,
    available: true, // Set this to false to disable this payment method
    features: ['No fees', 'Full control', 'Manual process'],
  },
  {
    id: 'DIRECT_DEBIT',
    name: 'Direct Debit',
    subtitle: 'Automatic Bank Payments',
    description: 'Set and forget - automatic payments directly from your bank account',
    icon: Building2,
    available: true, // Set this to false to disable this payment method
    features: ['Automatic', 'Never miss a payment', 'Bank account'],
  },
  {
    id: 'CREDIT_CARD',
    name: 'Credit Card',
    subtitle: 'Card Payments',
    description: 'Pay securely with your credit or debit card',
    icon: CreditCard,
    available: false, // Set this to true to enable credit card payments
    features: ['Instant processing', 'Secure payments', 'Card rewards'],
    processingFee: '2.5%'
  }
];

const PAYMENT_FREQUENCIES = {
  electricity: { 
    label: 'Electricity', 
    frequency: 'Monthly',
    paymentType: 'Postpaid',
    icon: Zap,
    color: 'green',
    bgColor: 'bg-accent-green/5',
    iconBg: 'bg-accent-green/20',
    textColor: 'text-accent-green',
    badgeColor: 'bg-accent-green/50 text-white',
  },
  broadband: { 
    label: 'Broadband', 
    frequency: 'Monthly',
    paymentType: 'Prepaid',
    icon: Wifi,
    color: 'purple',
    bgColor: 'bg-blue-500/5',
    iconBg: 'bg-accent-purple/20',
    textColor: 'text-accent-purple',
    badgeColor: 'bg-accent-purple/50 text-white',
  },
  mobile: {
    label: 'Mobile',
    frequency: 'Monthly',
    paymentType: 'Prepaid',
    icon: Phone,
    color: 'blue',
    bgColor: 'bg-blue-500/5',
    iconBg: 'bg-blue-500/20',
    textColor: 'text-blue-400',
    badgeColor: 'bg-blue-500/50 text-white',
  }
};

const SERVICE_ORDER = ['electricity', 'broadband', 'mobile'];

const HowYoullPaySection = ({ 
  initialData = {}, 
  selectedServices = { electricity: true, broadband: true },
  onAutosave
}) => {
  // Track if this is the first render
  const isFirstRender = useRef(true);

  // State management using useState (matching Preferences pattern)
  const [selectedMethod, setSelectedMethod] = useState(
    initialData?.paymentMethodType || null
  );

  // Add state for bank account details
  const [bankDetails, setBankDetails] = useState({
    bankName: initialData?.bankName || '',
    accountName: initialData?.accountName || '',
    accountNumber: initialData?.accountNumber || ''
  });

  // Add state for validation errors
  const [validationErrors, setValidationErrors] = useState({
    accountNumber: ''
  });

  // Validate NZ bank account number format
  const validateAccountNumber = useCallback((number) => {
    // Remove any spaces or dashes
    const cleanNumber = number.replace(/[\s-]/g, '');
    
    // Must be exactly 16 digits
    if (cleanNumber.length !== 16) {
      return false;
    }
    
    // Must contain only numbers
    if (!/^\d+$/.test(cleanNumber)) {
      return false;
    }

    // Extract components
    const bankNumber = cleanNumber.substring(0, 2);
    const suffix = cleanNumber.substring(13);

    // Validate bank number exists in our list
    const validBank = NZ_BANKS.some(bank => bank.id === bankNumber);
    if (!validBank) {
      return false;
    }

    // Validate suffix (2 or 3 digits)
    if (suffix.length < 2 || suffix.length > 3) {
      return false;
    }

    return true;
  }, []);

  // Format account number as user types
  const formatAccountNumber = useCallback((number) => {
    // Remove any non-digit characters
    const digits = number.replace(/\D/g, '');
    
    // Format as: BB-bbbb-AAAAAAA-SSS
    let formatted = '';
    if (digits.length > 0) formatted += digits.substring(0, 2);
    if (digits.length > 2) formatted += '-' + digits.substring(2, 6);
    if (digits.length > 6) formatted += '-' + digits.substring(6, 13);
    if (digits.length > 13) formatted += '-' + digits.substring(13, 16);
    
    return formatted;
  }, []);

  // Get active services based on selectedServices prop
  const activeServices = useMemo(() => {
    return SERVICE_ORDER.filter(service => selectedServices[service]);
  }, [selectedServices]);

  // Validate form - check if a payment method is selected and bank details are filled if direct debit
  const validateForm = useCallback(() => {
    if (!selectedMethod) return false;
    
    if (selectedMethod === 'DIRECT_DEBIT') {
      // All bank details are required for direct debit
      if (!bankDetails.bankName || !bankDetails.accountName || !bankDetails.accountNumber) {
        return false;
      }
      
      // Validate account number format
      return validateAccountNumber(bankDetails.accountNumber);
    }
    
    return true;
  }, [selectedMethod, bankDetails, validateAccountNumber]);

  // Handler for payment method selection
  const handlePaymentSelect = useCallback((method) => {
    // Only allow selection if the method is available
    const option = PAYMENT_OPTIONS.find(opt => opt.id === method);
    if (option?.available) {
      // Toggle selection
      const newSelection = selectedMethod === method ? null : method;
      setSelectedMethod(newSelection);
      
      // Clear validation errors when changing payment method
      if (newSelection !== 'DIRECT_DEBIT') {
        setValidationErrors({ accountNumber: '' });
      }
    }
  }, [selectedMethod]);

  // Handler for bank details changes
  const handleBankDetailsChange = useCallback((field, value) => {
    if (field === 'accountNumber') {
      const formattedValue = formatAccountNumber(value);
      setBankDetails(prev => ({
        ...prev,
        [field]: formattedValue
      }));

      // Validate account number format
      if (formattedValue) {
        const isValid = validateAccountNumber(formattedValue);
        setValidationErrors(prev => ({
          ...prev,
          accountNumber: isValid ? '' : 'Account number must be 16 digits'
        }));
      } else {
        setValidationErrors(prev => ({
          ...prev,
          accountNumber: ''
        }));
      }
    } else {
      setBankDetails(prev => ({
        ...prev,
        [field]: value
      }));
    }
  }, [formatAccountNumber, validateAccountNumber]);

  // Auto-save effect when form changes (matches Preferences pattern)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const hasChanged = selectedMethod !== initialData?.paymentMethodType ||
                       bankDetails.bankName !== initialData?.bankName ||
                       bankDetails.accountName !== initialData?.accountName ||
                       bankDetails.accountNumber !== initialData?.accountNumber;

    if (onAutosave && hasChanged) {
      const isValid = validateForm();
      const paymentData = {
        paymentMethodType: selectedMethod,
        selectedServices,
        lastModified: new Date().toISOString(),
        completed: isValid,
        ...(selectedMethod === 'DIRECT_DEBIT' ? bankDetails : {})
      };
      onAutosave(paymentData);
    }
  }, [selectedMethod, selectedServices, bankDetails, validateForm, onAutosave, initialData]);

  return (
    <form className="max-w-3xl mx-auto bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] rounded-2xl border border-white/10 p-4 sm:p-8 shadow-lg backdrop-blur-md space-y-6 sm:space-y-8">
      {/* Service Summary */}
      {activeServices.length > 0 && (
        <section className="space-y-6 p-4 sm:p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
          <h3 className="text-lg text-start font-semibold text-white mb-3">Payment Schedule</h3>
          <div className="grid grid-cols-2 gap-3 w-full">
            {activeServices.map(service => {
              const config = PAYMENT_FREQUENCIES[service];
              if (!config) return null;
              const Icon = config.icon;
              return (
                <div
                  key={service}
                  className={`flex flex-col items-center gap-3 p-3 rounded-xl border-2 ${config.bgColor} border-white/10 bg-gray-800/80`}
                >
                  <div className={`w-10 h-10 rounded-lg ${config.iconBg} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${service === 'electricity' ? 'text-accent-green' : service === 'broadband' ? 'text-accent-purple' : 'text-blue-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0 text-center">
                    <h4 className="font-semibold text-sm text-white mb-1.5 truncate">{config.label}</h4>
                    <div className="flex flex-col sm:flex-row justify-center items-center gap-1.5">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium ${config.badgeColor}`}>{config.frequency}</span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium ${config.paymentType === 'Prepaid' ? 'bg-amber-500/50 text-white' : 'bg-emerald-500/50 text-white'}`}>{config.paymentType}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Payment Options */}
      <section className="space-y-6 p-4 sm:p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-12 w-12 rounded-full bg-slate-500/10 flex items-center justify-center">
            <CreditCard className="h-8 w-8 text-slate-400" />
          </div>
          <div>
            <h3 className="text-lg text-start font-semibold text-white">Payment Method</h3>
            <p className="text-sm text-start text-gray-400">Choose your preferred payment method</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Payment method options">
          {PAYMENT_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isSelected = selectedMethod === option.id;
            
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => handlePaymentSelect(option.id)}
                disabled={!option.available}
                role="radio"
                aria-checked={isSelected}
                aria-disabled={!option.available}
                aria-label={`${option.name} - ${option.subtitle}${!option.available ? ' (not available)' : ''}`}
                className={`
                  p-4 rounded-lg border-1 text-left transition-all duration-200 relative group
                  ${option.available 
                    ? 'hover:border-accent-lightturquoise cursor-pointer' 
                    : 'cursor-not-allowed opacity-60'
                  }
                  ${isSelected && option.available
                    ? 'border-accent-lightturquoise bg-accent-lightturquoise/10' 
                    : 'border-white/10 bg-gray-800/80 hover:bg-gray-700/80'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <div className={`
                    w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0
                    ${isSelected && option.available
                      ? 'bg-accent-lightturquoise text-white' 
                      : option.id === 'BANK_TRANSFER' 
                        ? 'bg-amber-500/20 text-amber-400'
                        : option.id === 'CREDIT_CARD'
                          ? 'bg-purple-500/20 text-purple-400'
                          : 'bg-blue-500/20 text-blue-400'
                    }
                  `}>
                    <Icon className="w-6 h-6" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-base text-white truncate">{option.name}</h4>
                      {isSelected && option.available && (
                        <CheckCircle className="w-5 h-5 text-accent-lightturquoise flex-shrink-0" />
                      )}
                      {option.processingFee && (
                        <span className="text-xs text-amber-400 ml-2">+{option.processingFee} fee</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-400 mb-3">{option.subtitle}</p>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {option.description}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Bank Account Details for Direct Debit */}
        {selectedMethod === 'DIRECT_DEBIT' && (
          <div className="mt-6 p-4 rounded-lg bg-gray-800/50 border border-white/10 space-y-4">
            <h4 className="text-white font-medium mb-4">Bank Account Details <span className="text-red-400">*</span></h4>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="bankName" className="block text-sm font-medium text-gray-300 mb-1">
                  Bank Name <span className="text-red-400">*</span>
                </label>
                <select
                  id="bankName"
                  value={bankDetails.bankName}
                  onChange={(e) => handleBankDetailsChange('bankName', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-accent-lightturquoise focus:border-transparent"
                  required
                >
                  <option value="">Select a bank</option>
                  {NZ_BANKS.map(bank => (
                    <option key={bank.id} value={bank.id}>
                      {bank.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="accountName" className="block text-sm font-medium text-gray-300 mb-1">
                  Account Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  id="accountName"
                  value={bankDetails.accountName}
                  onChange={(e) => handleBankDetailsChange('accountName', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-accent-lightturquoise focus:border-transparent"
                  placeholder="e.g. John Doe"
                  required
                />
              </div>

              <div>
                <label htmlFor="accountNumber" className="block text-sm font-medium text-gray-300 mb-1">
                  Account Number <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  id="accountNumber"
                  value={bankDetails.accountNumber}
                  onChange={(e) => handleBankDetailsChange('accountNumber', e.target.value)}
                  className={`w-full px-3 py-2 bg-gray-700 border ${
                    validationErrors.accountNumber ? 'border-red-500' : 'border-gray-600'
                  } rounded-md text-white focus:outline-none focus:ring-2 focus:ring-accent-lightturquoise focus:border-transparent`}
                  placeholder="e.g. 01-1234-1234567-00"
                  required
                />
                {validationErrors.accountNumber && (
                  <p className="mt-1 text-sm text-red-400">{validationErrors.accountNumber}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Status */}
        <div className="mt-6 text-center">
          {selectedMethod ? (
            <div className={`flex items-center justify-center gap-2 ${
              selectedMethod === 'DIRECT_DEBIT' && !validateForm() 
                ? 'text-amber-400' 
                : 'text-emerald-400'
            }`}>
              {selectedMethod === 'DIRECT_DEBIT' && !validateForm() ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              ) : (
                <CheckCircle className="w-5 h-5" />
              )}
              <span className="text-sm font-medium">
                {selectedMethod === 'DIRECT_DEBIT' && !validateForm() 
                  ? 'Please complete all required bank account details'
                  : 'Payment method selected - Click to change'
                }
              </span>
            </div>
          ) : (
            <span className="text-sm text-gray-400">Select your payment method</span>
          )}
        </div>
      </section>
    </form>
  );
};

HowYoullPaySection.propTypes = {
  initialData: PropTypes.object,
  selectedServices: PropTypes.object,
  onAutosave: PropTypes.func
};

export default HowYoullPaySection;