import { useState, useEffect, useCallback, useRef, useContext } from 'react';
import PropTypes from 'prop-types';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import '../../styles/datepicker.css';
import AuthContext from '../../context/AuthContext';
import { ESIM_COMPATIBLE_DEVICES } from '../../constants/esimDevices';
import { MOBILE_PROVIDERS } from '../../constants/mobileProviders';

// Add new device lookup components
const DeviceLookup = ({ onSelect, selectedDevice, manufacturer, setManufacturer }) => {
  const selectClass =
    "w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-accent-blue focus:border-accent-blue [&>option]:bg-gray-800 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-gray-700 [&::-webkit-scrollbar-thumb]:bg-accent-blue [&::-webkit-scrollbar-thumb]:rounded-full transition-colors duration-200";

  // Highlight if selected
  const manufacturerSelected = manufacturer && manufacturer !== '';
  const modelSelected = selectedDevice && selectedDevice !== '';

  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Select Manufacturer *</label>
        <select
          value={manufacturer}
          onChange={(e) => setManufacturer(e.target.value)}
          className={`${selectClass} ${manufacturerSelected ? 'border-2 border-accent-blue bg-accent-blue text-white' : ''}`}
        >
          <option value="">Select manufacturer</option>
          {Object.keys(ESIM_COMPATIBLE_DEVICES).map((brand) => (
            <option key={brand} value={brand}>{brand}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Select Model *</label>
        <select
          value={selectedDevice}
          onChange={(e) => onSelect(e.target.value)}
          className={`${selectClass} ${modelSelected ? 'border-2 border-accent-blue bg-accent-blue text-white' : ''}`}
          disabled={!manufacturerSelected}
        >
          <option value="">Select model</option>
          {manufacturerSelected && ESIM_COMPATIBLE_DEVICES[manufacturer].map((model) => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
      </div>
    </div>
  );
};

DeviceLookup.propTypes = {
  onSelect: PropTypes.func.isRequired,
  selectedDevice: PropTypes.string,
  manufacturer: PropTypes.string,
  setManufacturer: PropTypes.func.isRequired
};

export default function ServiceDetailsSection({ 
  initialData = {}, 
  onAutosave, 
  selectedServices = {},
  onStepComplete,
  userData
}) {
  const { user } = useContext(AuthContext);
  const isFirstRender = useRef(true);
  const lastSavedData = useRef(null);
  const [manufacturer, setManufacturer] = useState('');

  // Initialize form state with proper defaults
  const [formState, setFormState] = useState(() => {
    const serviceDetails = initialData?.data?.serviceDetails || initialData?.serviceDetails || {};
    lastSavedData.current = serviceDetails;
    
    return {
      // Power service details
      pw_transferType: serviceDetails.pw_transferType || "",
      pw_serviceStartDate: serviceDetails.pw_serviceStartDate || "asap",
      pw_medicalDependency: serviceDetails.pw_medicalDependency ?? false,
      pw_medicalDependencyDetails: serviceDetails.pw_medicalDependencyDetails || "",

      // Broadband service details
      bb_transferType: serviceDetails.bb_transferType || "",
      bb_serviceStartDate: serviceDetails.bb_serviceStartDate || "asap",
      bb_routerPreference: serviceDetails.bb_routerPreference || "",
      bb_purchaseDetails: serviceDetails.bb_purchaseDetails || "",

      // Enhanced mobile service details
      mb_transferType: serviceDetails.mb_transferType || "",
      mb_serviceStartDate: serviceDetails.mb_serviceStartDate || "asap",
      mb_simPreference: serviceDetails.mb_simPreference || "",
      mb_portingNumber: serviceDetails.mb_portingNumber || "",
      mb_currentProvider: serviceDetails.mb_currentProvider || "",
      mb_accountNumber: serviceDetails.mb_accountNumber || "",
      mb_portingPin: serviceDetails.mb_portingPin || "",
      mb_deviceModel: serviceDetails.mb_deviceModel || "",
      mb_deliveryAddress: serviceDetails.mb_deliveryAddress || "",
      mb_portingConsent: serviceDetails.mb_portingConsent || false,
      mb_esimEmail: serviceDetails.mb_esimEmail || ""
    };
  });

  // Update formState when initialData changes
  useEffect(() => {
    const serviceDetails = initialData?.data?.serviceDetails || initialData?.serviceDetails || {};
    const hasChanged = JSON.stringify(serviceDetails) !== JSON.stringify(lastSavedData.current);
    
    if (hasChanged && !isFirstRender.current) {
      lastSavedData.current = serviceDetails;
      setFormState(prev => ({
        ...prev,
        pw_transferType: serviceDetails.pw_transferType || prev.pw_transferType,
        pw_serviceStartDate: serviceDetails.pw_serviceStartDate || prev.pw_serviceStartDate,
        pw_medicalDependency: serviceDetails.pw_medicalDependency ?? prev.pw_medicalDependency,
        pw_medicalDependencyDetails: serviceDetails.pw_medicalDependencyDetails || prev.pw_medicalDependencyDetails,
        bb_transferType: serviceDetails.bb_transferType || prev.bb_transferType,
        bb_serviceStartDate: serviceDetails.bb_serviceStartDate || prev.bb_serviceStartDate,
        bb_routerPreference: serviceDetails.bb_routerPreference || prev.bb_routerPreference,
        bb_purchaseDetails: serviceDetails.bb_purchaseDetails || prev.bb_purchaseDetails,
        mb_transferType: serviceDetails.mb_transferType || prev.mb_transferType,
        mb_serviceStartDate: serviceDetails.mb_serviceStartDate || prev.mb_serviceStartDate,
        mb_simPreference: serviceDetails.mb_simPreference || prev.mb_simPreference,
        mb_portingNumber: serviceDetails.mb_portingNumber || prev.mb_portingNumber,
        mb_currentProvider: serviceDetails.mb_currentProvider || prev.mb_currentProvider,
        mb_accountNumber: serviceDetails.mb_accountNumber || prev.mb_accountNumber,
        mb_portingPin: serviceDetails.mb_portingPin || prev.mb_portingPin,
        mb_deviceModel: serviceDetails.mb_deviceModel || prev.mb_deviceModel,
        mb_deliveryAddress: serviceDetails.mb_deliveryAddress || prev.mb_deliveryAddress,
        mb_portingConsent: serviceDetails.mb_portingConsent ?? prev.mb_portingConsent,
        mb_esimEmail: serviceDetails.mb_esimEmail || prev.mb_esimEmail
      }));
    }
  }, [initialData]);

  const [errors, setErrors] = useState({});

  // Use the props directly, no normalization needed
  const hasPower = selectedServices.electricity;
  const hasBroadband = selectedServices.broadband;

  // Handle form field changes with validation
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormState(prev => {
      const next = { ...prev };

      // Handle different field types
      if (type === "checkbox") {
        next[name] = checked;
      } else if (name.endsWith("_serviceStartDate")) {
        // Handle date fields
        next[name] = value === "" ? "asap" : value;
      } else {
        next[name] = value;
      }
      
      // Clear dependent fields
      if (name === "pw_medicalDependency" && !checked) {
        next.pw_medicalDependencyDetails = "";
      }
      if (name === "bb_routerPreference" && value !== "Purchase") {
        next.bb_purchaseDetails = "";
      }
      if (name === "mb_transferType" && value !== "Port") {
        next.mb_portingNumber = "";
      }
      
      return next;
    });
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  // Handle toggle switch changes
  const handleToggleChange = useCallback((name, checked) => {
    setFormState(prev => ({
      ...prev,
      [name]: checked
    }));
    
    // Clear any related errors
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  }, [errors]);

  // Handle button selection
  const handleButtonSelect = (field, value) => {
    setFormState(prev => {
      const next = { ...prev, [field]: value };
      
      // Clear dependent fields based on parent field changes
      if (field === "pw_medicalDependency" && !value) {
        next.pw_medicalDependencyDetails = "";
      }
      if (field === "bb_routerPreference" && value !== "Purchase") {
        next.bb_purchaseDetails = "";
      }
      if (field === "mb_transferType" && value !== "Port") {
        next.mb_portingNumber = "";
      }
      
      // Automatically set email for eSIM if selecting eSIM option
      if (field === "mb_simPreference" && value === "eSIM") {
        next.mb_esimEmail = user?.email || "";
      }
      
      return next;
    });
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  // Validate form data
  const validateForm = useCallback(() => {
    const newErrors = {};
    
    // Power service validation
    if (selectedServices.electricity) {
      if (!formState.pw_transferType) {
        newErrors.pw_transferType = "Please select a transfer type";
      }
      if (!formState.pw_serviceStartDate) {
        newErrors.pw_serviceStartDate = "Please select a start date";
      }
    }

    // Broadband service validation
    if (selectedServices.broadband) {
      if (!formState.bb_transferType) {
        newErrors.bb_transferType = "Please select a transfer type";
      }
      if (!formState.bb_serviceStartDate) {
        newErrors.bb_serviceStartDate = "Please select a start date";
      }
      if (!formState.bb_routerPreference) {
        newErrors.bb_routerPreference = "Please select a router preference";
      }
      if (formState.bb_routerPreference === "Purchase Router" && !formState.bb_purchaseDetails) {
        newErrors.bb_purchaseDetails = "Please select a router package";
      }
    }

    // Mobile service validation
    if (selectedServices.mobile) {
      if (!formState.mb_transferType) {
        newErrors.mb_transferType = "Please select a transfer type";
      }

      // Switch Provider validation
      if (formState.mb_transferType === "Switch Provider") {
        if (!formState.mb_portingNumber?.trim()) {
          newErrors.mb_portingNumber = "Please provide your current mobile number";
        } else if (!/^\d{7,11}$/.test(formState.mb_portingNumber.replace(/[\s-]/g, ''))) {
          newErrors.mb_portingNumber = "Please enter a valid mobile number";
        }
        if (!formState.mb_currentProvider?.trim()) {
          newErrors.mb_currentProvider = "Please select your current provider";
        }
        if (!formState.mb_accountNumber?.trim()) {
          newErrors.mb_accountNumber = "Please enter your account number";
        }
        if (!formState.mb_portingPin?.trim()) {
          newErrors.mb_portingPin = "Please enter your porting PIN";
        }
        if (!formState.mb_portingConsent) {
          newErrors.mb_portingConsent = "Please consent to the porting process";
        }
      }

      // New Number validation
      if (formState.mb_transferType === "New Number") {
        if (!formState.mb_simPreference) {
          newErrors.mb_simPreference = "Please select a SIM preference";
        }

        // SIM preference validation
        if (formState.mb_simPreference === "eSIM") {
          if (!formState.mb_esimEmail?.trim()) {
            newErrors.mb_esimEmail = "Please provide an email for eSIM delivery";
          } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formState.mb_esimEmail)) {
            newErrors.mb_esimEmail = "Please enter a valid email address";
          }
          if (!formState.mb_deviceModel?.trim()) {
            newErrors.mb_deviceModel = "Please provide your device model";
          }
        } else if (formState.mb_simPreference === "Physical SIM" && !formState.mb_deliveryAddress?.trim()) {
          newErrors.mb_deliveryAddress = "Please provide a delivery address";
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formState, selectedServices]);

  // Prepare data for autosave with proper structure
  const prepareAutosaveData = useCallback(() => {
    const transformedFormState = { ...formState };
    
    // Ensure all service dates have values
    ["pw", "bb", "mb"].forEach(service => {
      const dateField = `${service}_serviceStartDate`;
      if (!transformedFormState[dateField]) {
        transformedFormState[dateField] = "asap";
      }
    });

    // Ensure medical dependency is boolean
    if (transformedFormState.pw_medicalDependency === null) {
      transformedFormState.pw_medicalDependency = false;
    }

    // Check form validity
    const isValid = validateForm();

    // Match the expected data structure exactly
    return {
      step: "serviceDetails",
      data: {
        serviceDetails: transformedFormState,
        selectedServices,
        completed: isValid,
        lastModified: new Date().toISOString(),
        needsSync: true
      },
      autosave: true
    };
  }, [formState, selectedServices, validateForm]);

  // Autosave effect with proper data structure handling
  useEffect(() => {
    if (!isFirstRender.current && onAutosave) {
      const autosaveData = prepareAutosaveData();
      const currentServiceDetails = autosaveData.data.serviceDetails;
      
      // Only save if data has actually changed
      if (JSON.stringify(currentServiceDetails) !== JSON.stringify(lastSavedData.current)) {
        lastSavedData.current = currentServiceDetails;
        onAutosave(autosaveData);
      }
    } else {
      isFirstRender.current = false;
    }
  }, [formState, onAutosave, prepareAutosaveData]);

  // Add function to check power section completion
  const checkPowerCompletion = useCallback((formData) => {
    if (!selectedServices.electricity) return true;
    return !!(
      formData.pw_transferType &&
      (formData.pw_medicalDependency === false || 
       (formData.pw_medicalDependency === true && formData.pw_medicalDependencyDetails?.trim()))
    );
  }, [selectedServices.electricity]);

  // Add function to check broadband section completion
  const checkBroadbandCompletion = useCallback((formData) => {
    if (!selectedServices.broadband) return true;
    return !!(
      formData.bb_transferType &&
      formData.bb_routerPreference &&
      (formData.bb_routerPreference !== 'Purchase' || formData.bb_purchaseDetails?.trim())
    );
  }, [selectedServices.broadband]);

  // Add function to check mobile section completion
  const checkMobileCompletion = useCallback((formData) => {
    if (!selectedServices.mobile) return true;

    if (formData.mb_transferType === 'Switch Provider') {
      return !!(
        formData.mb_portingNumber?.trim() &&
        formData.mb_currentProvider &&
        formData.mb_accountNumber?.trim() &&
        formData.mb_portingPin?.trim() &&
        formData.mb_portingConsent
      );
    } else if (formData.mb_transferType === 'New Number') {
      if (formData.mb_simPreference === 'eSIM') {
        return !!(
          formData.mb_deviceModel?.trim()
        );
      } else if (formData.mb_simPreference === 'Physical SIM') {
        return !!(
          formData.mb_deliveryAddress?.trim()
        );
      }
    }
    return false;
  }, [selectedServices.mobile]);

  // Update effect to check completion status of all subsections
  useEffect(() => {
    const powerComplete = checkPowerCompletion(formState);
    const broadbandComplete = checkBroadbandCompletion(formState);
    const mobileComplete = checkMobileCompletion(formState);

    // Overall step completion
    const isStepComplete = powerComplete && broadbandComplete && mobileComplete;
    if (onStepComplete) {
      onStepComplete(isStepComplete);
    }
  }, [formState, checkPowerCompletion, checkBroadbandCompletion, checkMobileCompletion, onStepComplete]);

  // Common styles
  const labelClass = "block text-sm font-medium text-slate-300 mb-1";
  const inputClass = "w-full p-2 text-sm text-white bg-white/10 border border-white/20 rounded-lg focus:ring-2 focus:ring-accent-lightturquoise focus:ring-opacity-50 focus:border-accent-lightturquoise transition-colors";
  const errorClass = "mt-1 text-sm text-red-400";
  const sectionHeaderClass = "mb-6 border-b border-white/10 pb-6";

  // Common DatePicker props
  const datePickerProps = {
    dateFormat: "dd/MM/yyyy",
    placeholderText: "DD/MM/YYYY",
    minDate: new Date(),
    maxDate: new Date(new Date().setDate(new Date().getDate() + 90)),
    calendarClassName: "dark:bg-gray-900 dark:text-white border border-white/20",
    dayClassName: () => "dark:text-white dark:hover:bg-gray-700",
    showPopperArrow: false,
    showYearDropdown: true,
    scrollableYearDropdown: true,
    yearDropdownItemNumber: 100,
    showMonthDropdown: true,
    dropdownMode: "select",
    popperPlacement: "bottom-start",
    popperClassName: "datepicker-popper",
    popperModifiers: [
      {
        name: "offset",
        options: {
          offset: [0, -250],
        },
      },
      {
        name: "preventOverflow",
        options: {
          rootBoundary: "document",
          tether: false,
          altAxis: true,
        },
      },
    ],
  };

  const renderToggleSwitch = (label, name, value, onChange, icon) => (
    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-colors duration-200">
      <div className="flex items-center gap-3 flex-1">
        {icon}
        <span className="text-white text-sm">{label}</span>
      </div>
      <div className="flex items-center gap-3">
        <button 
          type="button"
          onClick={() => onChange(true)}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-all duration-200 ${
            value === true ? 'bg-accent-green text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
          }`}
          aria-pressed={value === true}
        >
          Yes
        </button>
        <button
          type="button"
          onClick={() => onChange(false)}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-all duration-200 ${
            value === false ? 'bg-accent-green text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
          }`}
          aria-pressed={value === false}
        >
          No
        </button>
      </div>
    </div>
  );

  // Render mobile service section
  const renderMobileSection = () => {
    if (!selectedServices.mobile) return null;

    const selectClass = "w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-accent-blue focus:border-transparent [&>option]:bg-gray-800 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-gray-700 [&::-webkit-scrollbar-thumb]:bg-accent-blue [&::-webkit-scrollbar-thumb]:rounded-full";

    // Helper function to initialize field with user data
    const getInitialFieldValue = (fieldName, userData) => {
      return formState[fieldName] || userData || '';
    };

  return (
      <section className="space-y-6 p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
        <div className={sectionHeaderClass}>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center">
              <svg className="h-6 w-6 text-accent-blue" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-xl text-left font-semibold text-white">Mobile Service Setup</h3>
              <p className="text-sm text-left text-gray-400">Configure your mobile service details</p>
            </div>
          </div>
        </div>

        <div className="grid text-start gap-6">
          {/* Transfer Type Selection */}
          <div>
            <label className={labelClass}>Transfer Type *</label>
            <div className="flex grid-cols-2 gap-3">
              {[
                { value: 'Switch Provider', label: 'Switch Provider (Port In)' },
                { value: 'New Number', label: 'New Number' }
              ].map(option => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    // If already selected, deselect it and clear related fields
                    if (formState.mb_transferType === option.value) {
                      setFormState(prev => ({
                        ...prev,
                        mb_transferType: '',
                        // Clear related fields
                        mb_portingNumber: '',
                        mb_currentProvider: '',
                        mb_accountNumber: '',
                        mb_portingPin: '',
                        mb_portingConsent: false,
                        // Only clear SIM related fields if deselecting New Number
                        ...(option.value === 'New Number' ? {
                          mb_simPreference: '',
                          mb_esimEmail: '',
                          mb_deviceModel: '',
                          mb_deliveryAddress: ''
                        } : {})
                      }));
                    } else {
                      handleButtonSelect('mb_transferType', option.value);
                      // Clear SIM related fields when switching to Switch Provider
                      if (option.value === 'Switch Provider') {
                        setFormState(prev => ({
                          ...prev,
                          mb_transferType: option.value,
                          mb_simPreference: '',
                          mb_esimEmail: '',
                          mb_deviceModel: '',
                          mb_deliveryAddress: ''
                        }));
                      }
                    }
                  }}
                  className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 ${
                    formState.mb_transferType === option.value
                      ? 'bg-accent-lightturquoise/20 border-accent-blue text-white'
                      : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            {errors.mb_transferType && <p className={errorClass}>{errors.mb_transferType}</p>}
          </div>

          {/* Switch Provider Fields */}
          {formState.mb_transferType === 'Switch Provider' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="mb_portingNumber" className={labelClass}>Current Mobile Number *</label>
                <div className="relative">
                  <input
                    type="tel"
                    id="mb_portingNumber"
                    name="mb_portingNumber"
                    value={getInitialFieldValue('mb_portingNumber', user?.mobile)}
                    onChange={handleChange}
                    placeholder="Enter your current mobile number"
                    className={inputClass}
                  />
                  {user?.mobile && formState.mb_portingNumber !== user.mobile && (
                    <button
                      type="button"
                      onClick={() => {
                        setFormState(prev => ({
                          ...prev,
                          mb_portingNumber: user.mobile
                        }));
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-sm text-accent-blue hover:text-accent-blue/80"
                    >
                      Use account mobile
                    </button>
                  )}
                </div>
                {errors.mb_portingNumber && <p className={errorClass}>{errors.mb_portingNumber}</p>}
              </div>

              <div>
                <label htmlFor="mb_currentProvider" className={labelClass}>Current Provider *</label>
                <select
                  id="mb_currentProvider"
                  name="mb_currentProvider"
                  value={formState.mb_currentProvider}
                  onChange={handleChange}
                  className={selectClass}
                >
                  <option value="">Select provider</option>
                  {MOBILE_PROVIDERS.map(provider => (
                    <option key={provider.id} value={provider.id}>{provider.name}</option>
                  ))}
                </select>
                {errors.mb_currentProvider && <p className={errorClass}>{errors.mb_currentProvider}</p>}
              </div>

              <div>
                <label htmlFor="mb_accountNumber" className={labelClass}>Account Number *</label>
                <input
                  type="text"
                  id="mb_accountNumber"
                  name="mb_accountNumber"
                  value={formState.mb_accountNumber}
                  onChange={handleChange}
                  placeholder="Enter your account number"
                  className={inputClass}
                />
                {errors.mb_accountNumber && <p className={errorClass}>{errors.mb_accountNumber}</p>}
              </div>

              <div>
                <label htmlFor="mb_portingPin" className={labelClass}>Porting PIN *</label>
                <input
                  type="text"
                  id="mb_portingPin"
                  name="mb_portingPin"
                  value={formState.mb_portingPin}
                  onChange={handleChange}
                  placeholder="Enter your porting PIN"
                  className={inputClass}
                />
                {errors.mb_portingPin && <p className={errorClass}>{errors.mb_portingPin}</p>}
              </div>

              <div className="flex items-start gap-2">
                <input
                  type="checkbox"
                  id="mb_portingConsent"
                  name="mb_portingConsent"
                  checked={formState.mb_portingConsent}
                  onChange={handleChange}
                  className="mt-1"
                />
                <label htmlFor="mb_portingConsent" className="text-sm text-gray-300">
                  I authorize the porting of my mobile number and confirm all provided information is correct *
                </label>
              </div>
              {errors.mb_portingConsent && <p className={errorClass}>{errors.mb_portingConsent}</p>}
            </div>
          )}

          {/* SIM Preference - Only show for New Number */}
          {formState.mb_transferType === 'New Number' && (
            <div className={`space-y-4 transition-all duration-300 ${formState.mb_transferType === 'New Number' ? 'opacity-100' : 'opacity-0'}`}>
              <div>
                <label className={labelClass}>SIM Preference *</label>
                <div className="flex grid-cols-2 gap-3">
                  {[
                    { value: 'Physical SIM', label: 'Physical SIM' },
                    { value: 'eSIM', label: 'eSIM' }
                  ].map(option => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => {
                        // If already selected, deselect it and clear related fields
                        if (formState.mb_simPreference === option.value) {
                          setFormState(prev => ({
                            ...prev,
                            mb_simPreference: '',
                            mb_esimEmail: '',
                            mb_deviceModel: '',
                            mb_deliveryAddress: ''
                          }));
                        } else {
                          handleButtonSelect('mb_simPreference', option.value);
                        }
                      }}
                      className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 ${
                        formState.mb_simPreference === option.value
                          ? 'bg-accent-lightturquoise/20 border-accent-blue text-white'
                          : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
                {errors.mb_simPreference && <p className={errorClass}>{errors.mb_simPreference}</p>}
              </div>

              {/* SIM Type Specific Fields */}
              {formState.mb_simPreference && (
                <div className="space-y-4 p-4 rounded-lg bg-white/5">
                  <h4 className="font-medium text-white">
                    {formState.mb_simPreference === 'eSIM' ? 'eSIM Details' : 'Physical SIM Delivery'}
                  </h4>
                  
                  {formState.mb_simPreference === 'eSIM' ? (
                    <>
                      <div>
                        <label htmlFor="mb_esimEmail" className={labelClass}>Email for eSIM Delivery *</label>
                        <div className="relative">
                          <input
                            type="email"
                            id="mb_esimEmail"
                            name="mb_esimEmail"
                            value={getInitialFieldValue('mb_esimEmail', user?.email)}
                            onChange={handleChange}
                            placeholder="Enter email for eSIM delivery"
                            className={inputClass}
                          />
                          {user?.email && formState.mb_esimEmail !== user.email && (
                            <button
                              type="button"
                              onClick={() => {
                                setFormState(prev => ({
                                  ...prev,
                                  mb_esimEmail: user.email
                                }));
                              }}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-sm text-accent-blue hover:text-accent-blue/80"
                            >
                              Use account email
                            </button>
                          )}
                        </div>
                        {errors.mb_esimEmail && <p className={errorClass}>{errors.mb_esimEmail}</p>}
                      </div>

                      <div>
                        <label className={labelClass}>Device Model *</label>
                        <DeviceLookup
                          onSelect={(model) => {
                            setFormState(prev => ({
                              ...prev,
                              mb_deviceModel: model
                            }));
                            if (errors.mb_deviceModel) {
                              setErrors(prev => ({ ...prev, mb_deviceModel: null }));
                            }
                          }}
                          selectedDevice={formState.mb_deviceModel}
                          manufacturer={manufacturer}
                          setManufacturer={(newManufacturer) => {
                            setManufacturer(newManufacturer);
                            setFormState(prev => ({
                              ...prev,
                              mb_deviceModel: '' // Reset model if manufacturer changes
                            }));
                          }}
                        />
                        {manufacturer && formState.mb_deviceModel &&
                          ESIM_COMPATIBLE_DEVICES[manufacturer]?.includes(formState.mb_deviceModel) && (
                            <p className="text-sm mt-1 text-green-500">
                              ✓ Your device supports eSIM
                            </p>
                          )}
                        {errors.mb_deviceModel && <p className={errorClass}>{errors.mb_deviceModel}</p>}
                      </div>
                    </>
                  ) : (
                    <div>
                      <label htmlFor="mb_deliveryAddress" className={labelClass}>Delivery Address *</label>
                      <div className="relative">
                        <textarea
                          id="mb_deliveryAddress"
                          name="mb_deliveryAddress"
                          value={getInitialFieldValue('mb_deliveryAddress', user?.address)}
                          onChange={handleChange}
                          placeholder="Enter delivery address for SIM card"
                          rows={3}
                          className={inputClass}
                        />
                        {user?.address && formState.mb_deliveryAddress !== user.address && (
                          <button
                            type="button"
                            onClick={() => {
                              setFormState(prev => ({
                                ...prev,
                                mb_deliveryAddress: user.address
                              }));
                            }}
                            className="absolute right-2 top-2 text-sm text-accent-blue hover:text-accent-blue/80"
                          >
                            Use account address
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => {
                            // Use the address from yourServices if available
                            const serviceAddress = userData?.yourServices?.addressInfo?.full_address;
                            if (serviceAddress) {
                              setFormState(prev => ({
                                ...prev,
                                mb_deliveryAddress: serviceAddress
                              }));
                            }
                          }}
                          className="absolute right-2 bottom-2 text-sm text-accent-blue hover:text-accent-blue/80"
                        >
                          Use service address
                        </button>
                      </div>
                      {errors.mb_deliveryAddress && <p className={errorClass}>{errors.mb_deliveryAddress}</p>}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    );
  };

  // Set manufacturer if mb_deviceModel is set and manufacturer is not
  useEffect(() => {
    if (formState.mb_deviceModel && !manufacturer) {
      // Find manufacturer for the selected model
      const found = Object.entries(ESIM_COMPATIBLE_DEVICES).find(([, models]) =>
        models.includes(formState.mb_deviceModel)
      );
      if (found) setManufacturer(found[0]);
    }
  }, [formState.mb_deviceModel, manufacturer]);

  return (
    <form className="space-y-8 w-full bg-gray-800 text-gray-100 p-6 rounded-lg">
      {/* Power Section */}
      {hasPower && (
        <section className="space-y-6 p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
          <div className={sectionHeaderClass}>
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center">
                <svg className="h-8 w-8 text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl text-left font-semibold text-white">Power Service Setup</h3>
                <p className="text-sm text-gray-400">Configure your electricity service details</p>
              </div>
            </div>
          </div>

          <div className="grid text-start gap-6">
            <div>
              <label className={labelClass}>Transfer Type *</label>
              <div className="flex grid-cols-3 gap-2">
                {[
                  { value: 'Switch', label: 'Switch Provider' },
                  { value: 'MoveIn', label: 'Moving In' },
                  { value: 'Installation', label: 'New Connection' }
                ].map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleButtonSelect('pw_transferType', option.value)}
                    className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 ${
                      formState.pw_transferType === option.value
                        ? 'bg-accent-lightturquoise/20 border-accent-green text-white'
                        : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              {errors.pw_transferType && <p className={errorClass}>{errors.pw_transferType}</p>}
            </div>
            
            {/* Power Date Section */}
            <div>
              <label className={labelClass}>Service Start Date *</label>
              <div className="flex flex-nowrap gap-2 min-w-0">
                <button
                  type="button"
                  onClick={() => handleButtonSelect('pw_serviceStartDate', 'asap')}
                  className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                    formState.pw_serviceStartDate === 'asap'
                      ? 'bg-accent-lightturquoise/20 border-accent-green text-white' 
                      : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  As soon as possible
                </button>
                <div className="relative datepicker-input-wrapper">
                  <DatePicker
                    {...datePickerProps}
                    selected={formState.pw_serviceStartDate && formState.pw_serviceStartDate !== 'asap' ? new Date(formState.pw_serviceStartDate) : null}
                    onChange={(date) => {
                      handleChange({
                        target: {
                          name: 'pw_serviceStartDate',
                          value: date ? date.toISOString().split('T')[0] : ''
                        }
                      });
                    }}
                    customInput={
                      <button 
                        type="button" 
                        className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap ${
                          formState.pw_serviceStartDate && formState.pw_serviceStartDate !== 'asap'
                            ? 'bg-accent-lightturquoise/20 border-accent-green text-white'
                            : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                        }`}
                      >
                        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" strokeWidth="2"/>
                          <line x1="16" y1="2" x2="16" y2="6" strokeWidth="2"/>
                          <line x1="8" y1="2" x2="8" y2="6" strokeWidth="2"/>
                          <line x1="3" y1="10" x2="21" y2="10" strokeWidth="2"/>
                        </svg>
                        {formState.pw_serviceStartDate && formState.pw_serviceStartDate !== 'asap' 
                          ? new Date(formState.pw_serviceStartDate).toLocaleDateString('en-NZ', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric'
                            })
                          : 'Pick a Date'
                        }
                      </button>
                    }
                  />
                </div>
              </div>
              {errors.pw_serviceStartDate && <p className={errorClass}>{errors.pw_serviceStartDate}</p>}
            </div>

            {renderToggleSwitch(
              "Is anyone in your household medically dependent on power?",
              "pw_medicalDependency",
              formState.pw_medicalDependency,
              (checked) => handleToggleChange("pw_medicalDependency", checked),
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            )}
            
            {formState.pw_medicalDependency && (
              <div className="ml-4 pl-4 border-l border-white/10">
                <textarea 
                  name="pw_medicalDependencyDetails" 
                  value={formState.pw_medicalDependencyDetails} 
                  onChange={handleChange} 
                  placeholder="Please provide details about the medical dependency..." 
                  className={`${inputClass} min-h-[100px] text-white`}
                />
                {errors.pw_medicalDependencyDetails && <p className={errorClass}>{errors.pw_medicalDependencyDetails}</p>}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Broadband Section */}
      {hasBroadband && (
        <section className="space-y-6 p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
          <div className={sectionHeaderClass}>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                <svg className="h-6 w-6 text-accent-purple" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01M7.05 12.705a9 9 0 0110.391 0M3.515 9.705c4.686-4.687 12.284-4.687 17 0" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl text-left font-semibold text-white">Broadband Service Setup</h3>
                <p className="text-sm text-gray-400">Configure your internet service details</p>
              </div>
            </div>
          </div>

          <div className="grid text-start gap-6">
            <div>
              <label className={labelClass}>Transfer Type *</label>
              <div className="flex grid-cols-3 gap-2">
                {[
                  { value: 'Switch', label: 'Switch Provider' },
                  { value: 'MoveIn', label: 'Moving In' },
                  { value: 'Installation', label: 'New Connection' }
                ].map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleButtonSelect('bb_transferType', option.value)}
                    className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 ${
                      formState.bb_transferType === option.value
                        ? 'bg-accent-lightturquoise/20 border-accent-purple text-white'
                        : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              {errors.bb_transferType && <p className={errorClass}>{errors.bb_transferType}</p>}
            </div>
            
            {/* Broadband Date Section */}
            <div>
              <label className={labelClass}>Service Start Date *</label>
              <div className="flex flex-nowrap gap-2 min-w-0">
                <button
                  type="button"
                  onClick={() => handleButtonSelect('bb_serviceStartDate', 'asap')}
                  className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                    formState.bb_serviceStartDate === 'asap'
                      ? 'bg-accent-lightturquoise/20 border-accent-purple text-white' 
                      : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  As soon as possible
                </button>
                <div className="relative datepicker-input-wrapper">
                  <DatePicker
                    {...datePickerProps}
                    selected={formState.bb_serviceStartDate && formState.bb_serviceStartDate !== 'asap' ? new Date(formState.bb_serviceStartDate) : null}
                    onChange={(date) => {
                      handleChange({
                        target: {
                          name: 'bb_serviceStartDate',
                          value: date ? date.toISOString().split('T')[0] : ''
                        }
                      });
                    }}
                    customInput={
                      <button 
                        type="button" 
                        className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap ${
                          formState.bb_serviceStartDate && formState.bb_serviceStartDate !== 'asap'
                            ? 'bg-accent-lightturquoise/20 border-accent-purple text-white'
                            : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                        }`}
                      >
                        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" strokeWidth="2"/>
                          <line x1="16" y1="2" x2="16" y2="6" strokeWidth="2"/>
                          <line x1="8" y1="2" x2="8" y2="6" strokeWidth="2"/>
                          <line x1="3" y1="10" x2="21" y2="10" strokeWidth="2"/>
                        </svg>
                        {formState.bb_serviceStartDate && formState.bb_serviceStartDate !== 'asap' 
                          ? new Date(formState.bb_serviceStartDate).toLocaleDateString('en-NZ', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric'
                            })
                          : 'Pick a Date'
                        }
                      </button>
                    }
                  />
                </div>
              </div>
              {errors.bb_serviceStartDate && <p className={errorClass}>{errors.bb_serviceStartDate}</p>}
            </div>

            <div className="space-y-4">
              <label className={labelClass}>Router Preference *</label>
              <div className="space-y-6">
                <div className="flex grid-cols-2 gap-3">
                  {[
                    { value: 'BYO', label: 'Bring Your Own' },
                    { value: 'Purchase', label: 'Purchase Router' }
                  ].map(option => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => handleButtonSelect('bb_routerPreference', option.value)}
                      className={`py-1.5 px-2.5 rounded-lg border text-sm font-medium transition-all duration-200 ${
                        formState.bb_routerPreference === option.value
                          ? 'bg-accent-lightturquoise/20 border-accent-purple text-white'
                          : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>

                {formState.bb_routerPreference === 'Purchase' && (
                  <div className="pt-6 border-t border-white/10">
                    <div className="grid sm:grid-cols-2 gap-6">
                      <label 
                        onClick={() => handleButtonSelect('bb_purchaseDetails', 'Standard Router - $99')}
                        className={`relative block p-6 rounded-xl border transition-all duration-200 cursor-pointer ${
                        formState.bb_purchaseDetails === "Standard Router - $99"
                          ? 'border-accent-purple bg-gray-800/50 shadow-lg'
                          : 'border-white/10 bg-gray-900/50 hover:bg-gray-800/50 hover:border-accent-purple/50'
                      } backdrop-blur-sm group`}>
                        <div className="absolute top-4 right-4">
                          {formState.bb_purchaseDetails === "Standard Router - $99" && (
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-accent-purple rounded-lg">
                              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span className="text-xs font-medium text-white">Selected</span>
                            </div>
                          )}
                        </div>
                        <div className="space-y-4">
                          <div className="h-12 w-12 rounded-lg bg-accent-purple/20 flex items-center justify-center">
                            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01M7.05 12.705a9 9 0 0110.391 0M3.515 9.705c4.686-4.687 12.284-4.687 17 0" />
                            </svg>
                          </div>
                          <div className="space-y-2">
                            <span className="block text-lg font-medium text-white transition-colors">Standard Router</span>
                            <span className="block text-sm text-gray-400">Perfect for basic internet usage</span>
                            <ul className="mt-4 space-y-2 text-sm text-gray-400">
                              <li className="flex items-center">
                                <svg className="h-4 w-4 mr-2 text-accent-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Up to 100 Mbps speeds
                              </li>
                              <li className="flex items-center">
                                <svg className="h-4 w-4 mr-2 text-accent-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Ideal for apartments
                              </li>
                            </ul>
                          </div>
                          <div className="pt-4 border-t border-white/10">
                            <span className="text-2xl font-semibold text-white">$99</span>
                            <span className="text-gray-400 text-sm ml-2">one-off payment</span>
                            <div className="text-gray-400 text-xs mt-1">(Inclusive of GST)</div>
                          </div>
                        </div>
                      </label>
                      
                      <label
                        onClick={() => handleButtonSelect('bb_purchaseDetails', 'Premium Router - $149')}
                        className={`relative block p-6 rounded-xl border transition-all duration-200 cursor-pointer ${
                        formState.bb_purchaseDetails === "Premium Router - $149"
                          ? 'border-accent-purple bg-gray-800/50 shadow-lg'
                          : 'border-white/10 bg-gray-900/50 hover:bg-gray-800/50 hover:border-accent-purple/50'
                      } backdrop-blur-sm group`}>
                        <div className="absolute top-4 right-4">
                          {formState.bb_purchaseDetails === "Premium Router - $149" && (
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-accent-purple rounded-lg">
                              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span className="text-xs font-medium text-white">Selected</span>
                            </div>
                          )}
                        </div>
                        <div className="space-y-4">
                          <div className="h-12 w-12 rounded-lg bg-accent-purple/20 flex items-center justify-center">
                            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01M7.05 12.705a9 9 0 0110.391 0M3.515 9.705c4.686-4.687 12.284-4.687 17 0" />
                            </svg>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center gap-3">
                              <span className="block text-lg font-medium text-white transition-colors">Premium Router</span>
                              <span className="px-2 py-1 text-xs font-medium border-accent-blue border text-white bg-slate-800 rounded-full">Recommended</span>
                            </div>
                            <span className="block text-sm text-gray-400">Enhanced coverage for larger homes</span>
                            <ul className="mt-4 space-y-2 text-sm text-gray-400">
                              <li className="flex items-center">
                                <svg className="h-4 w-4 mr-2 text-accent-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Up to 1 Gbps speeds
                              </li>
                              <li className="flex items-center">
                                <svg className="h-4 w-4 mr-2 text-accent-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Dual-band Wi-Fi 6
                              </li>
                              <li className="flex items-center">
                                <svg className="h-4 w-4 mr-2 text-accent-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Perfect for large homes
                              </li>
                            </ul>
                          </div>
                          <div className="pt-4 border-t border-white/10">
                            <span className="text-2xl font-semibold text-white">$149</span>
                            <span className="text-gray-400 text-sm ml-2">one-off payment</span>
                            <div className="text-gray-400 text-xs mt-1">(Inclusive of GST)</div>
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>
                )}
              </div>
              {errors.bb_routerPreference && <p className={errorClass}>{errors.bb_routerPreference}</p>}
              {errors.bb_purchaseDetails && <p className={errorClass}>{errors.bb_purchaseDetails}</p>}
            </div>
          </div>
        </section>
      )}

      {renderMobileSection()}
    </form>
  );
}

ServiceDetailsSection.propTypes = {
  initialData: PropTypes.shape({
    data: PropTypes.object,
    serviceDetails: PropTypes.object
  }),
  onAutosave: PropTypes.func.isRequired,
  selectedServices: PropTypes.object,
  onStepComplete: PropTypes.func,
  userData: PropTypes.object
};