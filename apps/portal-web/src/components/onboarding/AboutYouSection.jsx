// src/components/onboarding/AboutYouSection.jsx
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import PropTypes from 'prop-types';
import { InformationCircleIcon } from '@heroicons/react/20/solid';
import { useAuth } from '../../hooks/useAuth';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import '../../styles/datepicker.css';
import '../../styles/tooltip.css';
import '../../styles/dropdown-alignment.css';


// Constants and Helper Functions defined outside the component - these are stable
const NZ_DATE_FORMAT = /^\d{2}\/\d{2}\/\d{4}$/;
const NZ_DL_NUMBER_FORMAT = /^[A-Za-z]{2}\d{6}$/;
const NZ_DL_VERSION_FORMAT = /^\d{0,3}$/;
const BASE_REQUIRED_FIELDS = ['legalFirstName', 'legalLastName', 'preferredName', 'dob', 'consentCreditCheck'];
const MIN_AGE = 16;
// Note: Using a fixed date like this can be problematic if the current date matters for validation over time.
// It's better to use `new Date()` or get the current date dynamically if deployed.
const CURRENT_NZ_DATE = new Date();

const isValidNZDateString = (dateStr) => {
  if (!dateStr || !NZ_DATE_FORMAT.test(dateStr)) return false;
  const [day, month, year] = dateStr.split('/').map(Number);
  const currentYear = CURRENT_NZ_DATE.getFullYear(); // Using the fixed date here too
  if (year < 1900 || year > currentYear || month < 1 || month > 12 || day < 1 || day > 31) return false;
  // Leap year check for February
  const isLeap = (year % 400 === 0 || (year % 100 !== 0 && year % 4 === 0));
  const monthLength = [31, isLeap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day > monthLength[month - 1]) return false;
  const inputDate = new Date(year, month - 1, day); // Month is 0-indexed
  const today = new Date(CURRENT_NZ_DATE); // Using the fixed date here too
  today.setHours(0, 0, 0, 0); // Normalize today's date
  return inputDate <= today; // Ensure date is not in the future relative to CURRENT_NZ_DATE
};

const isOverAgeLimit = (dateStr, limit) => {
  if (!isValidNZDateString(dateStr)) return false; // Ensure it's a valid date format first
  const [day, month, year] = dateStr.split('/').map(Number);
  const birthDate = new Date(year, month - 1, day); // Month is 0-indexed
  const today = new Date(CURRENT_NZ_DATE); // Using the fixed date here too
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) age--; // Adjust age if birthday hasn't occurred yet this year
  return age >= limit;
};


export default function AboutYouSection({ initialData = {}, onNext, onAutosave, user }) {
  // Track if this is the first render
  const isFirstRender = useRef(true);

  // State variables
  const [form, setForm] = useState({
    legalFirstName: '',
    middleName: '',
    legalLastName: '',
    preferredName: '',
    dob: '',
    consentCreditCheck: false,
    idType: '', // Stores 'driverLicence' or 'passport'
    driverLicenceNumber: '',
    driverLicenceVersion: '',
    passportNumber: '',
    email: '',
    mobile: '',
  });
  const [errors, setErrors] = useState({});
  const [showDobTooltip, setShowDobTooltip] = useState(false);
  const [showConsentTooltip, setShowConsentTooltip] = useState(false);

  // Get user from hook
  const { user: authUser } = useAuth();

  // Robustly extract user info from all possible onboarding data shapes
  const userData = useMemo(() => {
    return {
      ...authUser,
      ...(initialData?.user || {}),
      ...(initialData?.personalInfo || {}),
      ...(initialData?.step_data?.initialSelection?.user || {}),
      ...(initialData?.step_data?.aboutYou?.user || {})
    };
  }, [authUser, initialData]);

  // Define utility class string here, before it's used in JSX or useCallback hooks
  const labelClasses = "block text-sm font-medium text-left text-gray-300 mb-1";
  const disabledInputClasses = "block w-full border-gray-600 rounded-md shadow-sm p-2 bg-gray-700 cursor-not-allowed text-gray-400";

  const initialFormStateRef = useRef(null);

  // This single, robust effect handles the initial population of the form.
  // It runs when data sources change, but sets the state and ref only ONCE.
  useEffect(() => {
    // Do not re-initialize if the ref is already set.
    if (initialFormStateRef.current) {
      return;
    }

    const hasInitialData = initialData && Object.keys(initialData).length > 0;
    const hasUserData = userData && Object.keys(userData).length > 0;
    const hasUserProp = user && Object.keys(user).length > 0;

    // Proceed only if we have some data to populate the form with.
    if (hasInitialData || hasUserData || hasUserProp) {
      const populatedForm = {
        legalFirstName: initialData?.legalFirstName || userData?.first_name || user?.first_name || '',
        middleName: initialData?.middleName || userData?.middle_name || '',
        legalLastName: initialData?.legalLastName || userData?.last_name || user?.last_name || '',
        preferredName: initialData?.preferredName || userData?.preferred_name || '',
        dob: initialData?.dob || userData?.dob || '',
        consentCreditCheck: initialData?.consentCreditCheck ?? false,
        idType: initialData?.idType || '',
        driverLicenceNumber: initialData?.driverLicenceNumber || '',
        driverLicenceVersion: initialData?.driverLicenceVersion || '',
        passportNumber: initialData?.passportNumber || '',
        email: initialData?.email || userData?.email || user?.email || '',
        mobile: initialData?.mobile || user?.phone || user?.mobile || userData?.mobile || userData?.phone || userData?.phone_number || '',
      };

      console.log('🔍 AboutYouSection: Initializing form with data:', {
        hasInitialData,
        hasUserData,
        hasUserProp,
        populatedFormKeys: Object.keys(populatedForm).filter(key => populatedForm[key]),
        legalFirstName: populatedForm.legalFirstName,
        email: populatedForm.email
      });

      setForm(populatedForm);
      initialFormStateRef.current = populatedForm; // Set the stable initial state reference.
    }
  }, [initialData, userData, user]); // Depend on all data sources.

  // --- FORM HANDLERS ---
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setForm(prev => {
      const nextForm = { ...prev, [name]: newValue };

      // --- Conditional Logic based on Consent Checkbox ---
      if (name === 'consentCreditCheck') {
        if (newValue && prev.idType === '') { // If consent is checked and no ID type was previously selected, default to Driver Licence
          nextForm.idType = 'driverLicence';
        } else if (!newValue) { // If consent is unchecked, clear ID type and ID fields
          nextForm.idType = '';
          nextForm.driverLicenceNumber = '';
          nextForm.driverLicenceVersion = '';
          nextForm.passportNumber = '';
        }
      }

      return nextForm;
    });

    // Clear error for the field being changed
    setErrors(prev => {
      const nextErrors = { ...prev };
      delete nextErrors[name]; // Clear error for the field that was just changed
      // If consentCreditCheck is unchecked, clear errors for related ID fields too
      if (name === 'consentCreditCheck' && !newValue) {
        delete nextErrors.idType;
        delete nextErrors.driverLicenceNumber;
        delete nextErrors.driverLicenceVersion;
        delete nextErrors.passportNumber;
      }
      return nextErrors;
    });
  };

  // Fix the handleIdTypeChange function to properly autosave
  const handleIdTypeChange = useCallback((isPassport) => {
    setForm(prev => {
      const idType = isPassport ? 'passport' : 'driverLicence';
      const nextForm = { 
        ...prev, 
        idType: idType,
        // Clear fields from the unselected ID type
        ...(isPassport 
          ? { driverLicenceNumber: '', driverLicenceVersion: '' } 
          : { passportNumber: '' })
      };
      
      return nextForm;
    });
    
    // Clear any errors related to ID fields when changing ID type
    setErrors(prev => {
      const nextErrors = { ...prev };
      delete nextErrors.idType;
      delete nextErrors.driverLicenceNumber;
      delete nextErrors.driverLicenceVersion;
      delete nextErrors.passportNumber;
      return nextErrors;
    });
  }, []);

  // --- VALIDATION ---
  // Removed unnecessary dependencies from the useCallback dependency array
  const validate = useCallback((formData) => {
    const newErrors = {};
    const { dob, consentCreditCheck, idType, driverLicenceNumber, driverLicenceVersion, passportNumber, mobile, email } = formData;

    // Validate base required fields
    BASE_REQUIRED_FIELDS.forEach(field => {
      const value = formData[field];
       // Check for empty string after trimming whitespace for text inputs
      if (typeof value === 'string' && !value.trim()) {
           newErrors[field] = 'This field is required.';
      } else if (field === 'consentCreditCheck' && typeof value === 'boolean' && !value) {
           newErrors[field] = 'You must consent to the credit check to proceed.';
       }
       // Handle cases where value might be null/undefined or an empty string for non-string fields like consentCreditCheck if not boolean yet
       else if (value === undefined || value === null || value === '' ) {
            // Re-check based on field type to be explicit
           if (field !== 'dob' && field !== 'consentCreditCheck') {
              newErrors[field] = 'This field is required.';
           } else if (field === 'dob' && !value) {
               newErrors.dob = 'This field is required.';
           }
            // consentCreditCheck is handled by the explicit boolean check above
       }
    });

    // Note: Email and mobile are read-only fields populated from user account
    // No validation needed as they cannot be edited in this form

    // Validate DOB format and age limit if DOB is provided and has no basic required error
    if (dob && !newErrors.dob) {
      if (!isValidNZDateString(dob)) { newErrors.dob = `Please enter a valid past date in DD/MM/YYYY format.`; }
      else if (!isOverAgeLimit(dob, MIN_AGE)) { newErrors.dob = `You must be at least ${MIN_AGE} years old.`; }
    }

    // Validate ID fields if consent is given
    if (consentCreditCheck) {
      if (!idType) { newErrors.idType = 'Please select an ID type for verification.'; }
      else if (idType === 'driverLicence') {
        if (!driverLicenceNumber?.trim()) { newErrors.driverLicenceNumber = 'Driver Licence number is required.'; }
        else if (driverLicenceNumber && !NZ_DL_NUMBER_FORMAT.test(driverLicenceNumber)) { newErrors.driverLicenceNumber = 'Invalid format. Use 2 letters followed by 6 digits (e.g., AA123456).'; } // Check format only if value exists
        // Note: The previous code checked for undefined/null/empty string for version, which is fine.
        // Let's keep that explicit check for version requiredness.
        if (driverLicenceVersion === undefined || driverLicenceVersion === null || driverLicenceVersion === '') {
           newErrors.driverLicenceVersion = 'Driver Licence version is required.';
        }
        else if (driverLicenceVersion && !NZ_DL_VERSION_FORMAT.test(driverLicenceVersion)) { // Check format only if value exists after required check
          newErrors.driverLicenceVersion = 'Invalid format. Use up to 3 digits (e.g., 001).';
        }
      } else if (idType === 'passport') {
        if (!passportNumber?.trim()) { newErrors.passportNumber = 'Passport number is required.'; }
      }
    }

    return newErrors;
  }, []); // Empty dependency array as all external dependencies are constants or module-level

  // Autosave effect - consistent with other sections
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    // Don't autosave if form is empty/uninitialized (prevents saving empty data)
    const formHasData = form.legalFirstName || form.legalLastName || form.email || form.mobile || form.dob;
    if (!formHasData) {
      console.log('🔍 AboutYouSection: Skipping autosave - form is empty/uninitialized');
      return;
    }

    // Use the same change detection pattern as other sections
    const initialFormData = initialFormStateRef.current || {};
    const hasChanged = JSON.stringify(form) !== JSON.stringify(initialFormData);

    if (onAutosave && hasChanged) {
      const validationErrors = validate(form);
      const isValid = Object.keys(validationErrors).length === 0;
      const aboutYouData = {
        ...form,
        lastModified: new Date().toISOString(),
        completed: isValid
      };
      
      console.log('🔍 AboutYouSection: Autosaving data:', {
        hasData: formHasData,
        isValid,
        dataKeys: Object.keys(aboutYouData).filter(key => aboutYouData[key])
      });
      
      onAutosave(aboutYouData);
    }
  }, [form, validate, onAutosave]);

  // --- SUBMIT HANDLER ---
  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    const validationErrors = validate(form);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length === 0) {
      // Create the payload to send to the API
      const payload = { ...form };

      // Remove ID fields that are not relevant based on the selected ID type or consent state
      if (payload.idType === 'driverLicence') {
          delete payload.passportNumber;
      } else if (payload.idType === 'passport') {
          delete payload.driverLicenceNumber;
          delete payload.driverLicenceVersion;
      }
      // If consent is not given, remove all ID related fields regardless of type
      if (!payload.consentCreditCheck) {
          delete payload.idType;
          delete payload.driverLicenceNumber;
          delete payload.driverLicenceVersion;
          delete payload.passportNumber;
      }

              // Add field mappings for backward compatibility
        const enhancedPayload = {
          ...payload,
          // Map fields to what isStepComplete checks for
          first_name: payload.legalFirstName, 
          last_name: payload.legalLastName,
          // Use userData for email/phone since form fields are read-only
          phone_number: userData.phone || userData.mobile || '',
          email: userData.email || '',
          phone: userData.phone || userData.mobile || '',
          mobile: userData.mobile || userData.phone || ''
        };
      
      
      // Use autosave for final save before proceeding to next step
      if (onAutosave) {
        onAutosave(enhancedPayload);
      }
      
      // Proceed to next step
      if (onNext) onNext(enhancedPayload);

    } else {
      // If there are validation errors, find the first field with an error and scroll to/focus it
      const firstErrorFieldKey = Object.keys(validationErrors)[0];
      if (firstErrorFieldKey) {
        // Use requestAnimationFrame to ensure DOM updates (error messages appear) before scrolling/focusing
        requestAnimationFrame(() => {
          let elementToFocus = document.getElementById(firstErrorFieldKey);

          // Handle specific cases for elements without direct input IDs or where scrolling to a container is better
          if (firstErrorFieldKey === 'idType') {
            elementToFocus = document.getElementById('id-type-switch-group'); // Scroll to the switch group container
          } else if (firstErrorFieldKey === 'consentCreditCheck') {
             // Scroll to the checkbox element itself or a container around it
             elementToFocus = document.getElementById('consentCreditCheck'); // Scroll to the checkbox element
          }


          if (elementToFocus) {
             // Use try/catch as focus() can sometimes fail in certain conditions (though rare)
            try {
                elementToFocus.focus({ preventScroll: true }); // Attempt to focus without initial scroll
            } catch {
                // Intentionally ignore focus errors
            }
             // Always scroll into view, regardless of focus success, using smooth behavior
            elementToFocus.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        });
      }
    }
  }, [form, onNext, onAutosave, validate, userData]); // Add userData to dependencies

  // Memoize getError as it's used in render
  const getError = useCallback((fieldName) => errors[fieldName], [errors]); // errors is a dependency

  // Memoize inputClasses as it depends on getError
  const inputClasses = useCallback((fieldName) =>
     `block w-full rounded-md border-0 bg-gray-800 px-3 py-1.5 text-base text-gray-100 shadow-sm ring-1 ring-inset placeholder:text-gray-500 focus:ring-2 focus:ring-inset focus:ring-[#b14eb1] focus:ring-opacity-50 focus:outline-none focus:border-[#40E0D0] sm:text-sm sm:leading-6 transition-all duration-200 ${getError(fieldName) ? 'ring-red-500 focus:ring-red-500' : 'ring-gray-600 hover:ring-gray-500'}`
  , [getError]);

  // Input classes for form fields
  


  return (
    <form onSubmit={handleSubmit} className="space-y-8 w-full bg-gray-800 text-gray-100 p-6 rounded-lg">
      {/* Block 1: Your Details */}
      <section aria-labelledby="your-details-heading" className="space-y-6">
        <h3 id="your-details-heading" className="text-lg text-left font-semibold text-accent-lightturquoise">Your Details</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-5">
          {/* Detail fields */}
          <div>
            <label htmlFor="legalFirstName" className={labelClasses}>Legal First Name *</label>
            {/* Removed required from input as validation handles the message better */}
            <input type="text" id="legalFirstName" name="legalFirstName" value={form.legalFirstName} onChange={handleChange} className={inputClasses('legalFirstName')} aria-required="true" aria-invalid={!!getError('legalFirstName')} aria-describedby={getError('legalFirstName') ? `legalFirstName-error` : undefined} />
            {getError('legalFirstName') && <p id="legalFirstName-error" className="text-sm text-red-600 mt-1 text-left">{getError('legalFirstName')}</p>}
          </div>
          {['middleName', 'legalLastName', 'preferredName'].map((field) => (
            <div key={field}>
              <label htmlFor={field} className={labelClasses}>{field === 'middleName' ? 'Middle Name' : field === 'legalLastName' ? 'Legal Last Name *' : 'Preferred Name *'}</label>
              {/* Removed required from input */}
              <input type="text" id={field} name={field} value={form[field]} onChange={handleChange} required={field !== 'middleName'} className={inputClasses(field)} aria-required={field !== 'middleName'} aria-invalid={!!getError(field)} aria-describedby={getError(field) ? `${field}-error` : undefined} />
              {getError(field) && <p id={`${field}-error`} className="text-sm text-red-600 mt-1 text-left">{getError(field)}</p>}
            </div>
          ))}
          {/* Email and Mobile Phone - Read Only */}
          {['email', 'mobile'].map((field) => (
            <div key={field}>
              <label htmlFor={field} className={labelClasses}>
                {field === 'email' ? 'Email' : 'Mobile Phone'}
              </label>
              <input
                type={field === 'email' ? 'email' : 'tel'}
                id={field}
                name={field}
                value={form[field] || ''}
                disabled
                readOnly
                className={disabledInputClasses}
                aria-label={`${field} (cannot be changed)`}
              />
            </div>
          ))}
          {/* Date of Birth */}
          <div className="sm:col-span-1">
            <div className="flex items-center gap-1 mb-1">
              <label htmlFor="dob" className={labelClasses}>Date of Birth *</label>
              <div
                id="dob-tooltip-trigger"
                className="relative flex-none"
                onMouseEnter={() => setShowDobTooltip(true)}
                onMouseLeave={() => setShowDobTooltip(false)}
                aria-label="Date of birth requirements"
              >
                <InformationCircleIcon className="text-gray-400 h-5 w-5 cursor-help hover:text-gray-300 transition-colors" aria-hidden="true" />
                {showDobTooltip && (
                  <div
                    role="tooltip"
                    id="dob-tooltip"
                    className="datepicker-tooltip absolute z-50 left-0 bottom-full mb-1 w-64 text-xs text-gray-100 px-3 py-2"
                  >
                    Must be 16+ years old.
                  </div>
                )}
              </div>
            </div>
            <div className="relative flex items-center gap-2">
              <div className="datepicker-input-wrapper">
                <DatePicker
                  id="dob"
                  name="dob"
                  selected={form.dob ? new Date(form.dob.split('/').reverse().join('-')) : null}
                  onChange={(date) => {
                    const formattedDate = date ? 
                      `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}` : 
                      '';
                    
                    setForm(prev => {
                      const nextForm = { ...prev, dob: formattedDate };
                      
                      // Ensure we're calling onAutosave with the complete form data
                      if (onAutosave) {
                        setTimeout(() => {
                          onAutosave(nextForm);
                        }, 50);
                      }
                      
                      return nextForm;
                    });
                    
                    setErrors(prev => {
                      const nextErrors = { ...prev };
                      delete nextErrors.dob;
                      return nextErrors;
                    });
                  }}
                  maxDate={new Date(CURRENT_NZ_DATE.getFullYear() - MIN_AGE, CURRENT_NZ_DATE.getMonth(), CURRENT_NZ_DATE.getDate())}
                  minDate={new Date('1900-01-01')}
                  placeholderText="DD/MM/YYYY"
                  dateFormat="dd/MM/yyyy"
                  showMonthDropdown
                  showYearDropdown
                  scrollableYearDropdown
                  yearDropdownItemNumber={100}
                  dropdownMode="scroll"
                  className={`block w-full rounded-md border-0 bg-gray-800 px-3 py-1.5 text-base text-gray-100 shadow-sm ring-1 ring-inset placeholder:text-gray-500 focus:ring-2 focus:ring-inset focus:ring-[#b14eb1] focus:ring-opacity-50 focus:outline-none focus:border-[#40E0D0] sm:text-sm sm:leading-6 transition-all duration-200
                    ${getError('dob') ? 'ring-red-500 focus:ring-red-500' : 'ring-gray-600 hover:ring-gray-500'}`}
                  calendarClassName="dark-theme-calendar"
                  popperClassName="datepicker-popper"
                  popperPlacement="bottom-start"
                  popperModifiers={[
                    {
                      name: 'offset',
                      options: {
                        offset: [0, -200]
                      }
                    },
                    {
                      name: 'preventOverflow',
                      options: {
                        rootBoundary: 'document',
                        tether: false,
                        altAxis: true
                      }
                    }
                  ]}
                  required
                  aria-required="true"
                  aria-invalid={!!getError('dob')}
                  aria-describedby={getError('dob') ? `dob-error dob-tooltip-trigger` : `dob-tooltip-trigger`}
                />
                <div className="datepicker-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              
            </div>
            {getError('dob') && <p id="dob-error" className="text-sm mt-2 text-red-500">{getError('dob')}</p>}
          </div>
        </div>
      </section>

      {/* Block 2: Credit Check */}
      <section aria-labelledby="credit-check-heading" className="border-t border-gray-700 pt-8">
        <div className="flex items-center gap-1 mb-3">
          <h3 id="credit-check-heading" className="text-lg font-semibold text-accent-lightturquoise text-left">Credit Check</h3>
          <div className="relative flex-none" onMouseEnter={() => setShowConsentTooltip(true)} onMouseLeave={() => setShowConsentTooltip(false)} aria-label="Credit check information">
            <span className="text-gray-400 cursor-help">
              <InformationCircleIcon className="w-5 h-5" aria-hidden="true" />
            </span>
            {showConsentTooltip && (
              <div
                role="tooltip"
                id="consent-tooltip"
                className="datepicker-tooltip absolute z-50 left-0 bottom-full mb-1 w-64 text-xs text-gray-100 px-3 py-2"
              >
                We may use your legal name, date of birth, and selected ID details to run a soft credit check. This does not affect your credit score.
              </div>
            )}
          </div>
        </div>
        {/* Consent Checkbox Row */}
        <div className="flex items-start gap-2">
          <div className="flex-shrink-0">
            <input 
              type="checkbox" 
              id="consentCreditCheck" 
              name="consentCreditCheck" 
              checked={form.consentCreditCheck} 
              onChange={handleChange} 
              className={`h-4 w-4 rounded-sm border-gray-600 text-[#b14eb1] focus:ring-[#b14eb1] bg-gray-800 transition-colors duration-200 ${getError('consentCreditCheck') ? 'border-red-500' : ''}`}
              aria-required="true" 
              aria-invalid={!!getError('consentCreditCheck')} 
              aria-describedby={getError('consentCreditCheck') ? `consentCreditCheck-error consentCreditCheck-description` : `consentCreditCheck-description`} 
            />
          </div>
          <div className="text-sm">
            <label htmlFor="consentCreditCheck" className="text-gray-300 text-left font-medium cursor-pointer" id="consentCreditCheck-description">
              I consent to my personal information being used for a credit check.*
            </label>
            {getError('consentCreditCheck') && <p id="consentCreditCheck-error" className="text-sm text-red-600 mt-1 text-left">{getError('consentCreditCheck')}</p>}
          </div>
        </div>

        {/* Conditionally Rendered ID Verification Section */}
        {form.consentCreditCheck && (
          <div className="mt-6 pt-6 border-t border-gray-700" id="id-verification-section">
            <p className="text-sm max-w-2xl text-left text-gray-400 mb-5">
              Providing your Driver Licence or Passport details helps speed up the identity verification process required for the credit check. Please select the type of identification you wish to provide.
            </p>
            {/* ID Type Selector */}
            <div id="id-type-switch-group" className="flex items-center space-x-4 mb-6" role="radiogroup" aria-labelledby="id-type-label">
              <span id="id-type-label" className="sr-only">Select ID type</span>
              <div className="flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => handleIdTypeChange(false)}
                  className={`group flex items-center p-2 rounded-lg transition-all duration-200 min-w-[160px] ${
                    form.idType === 'driverLicence'
                      ? 'bg-gray-800 shadow-md border-2 border-[#b14eb1]'
                      : 'bg-gray-700 hover:bg-gray-800 hover:shadow-sm border-2 border-transparent'
                  }`}
                  aria-pressed={form.idType === 'driverLicence'}
                >
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    form.idType === 'driverLicence'
                      ? 'border-[#b14eb1] bg-[#b14eb1] text-white'
                      : 'border-gray-400 group-hover:border-gray-300'
                  }`}>
                    {form.idType === 'driverLicence' && (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <span className={`ml-2 text-sm ${
                    form.idType === 'driverLicence'
                      ? 'text-gray-100 font-semibold'
                      : 'text-gray-300 group-hover:text-gray-100'
                  }`}>
                    Driver Licence
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => handleIdTypeChange(true)}
                  className={`group flex items-center p-2 rounded-lg transition-all duration-200 min-w-[160px] ${
                    form.idType === 'passport'
                      ? 'bg-gray-800 shadow-md border-2 border-[#b14eb1]'
                      : 'bg-gray-700 hover:bg-gray-800 hover:shadow-sm border-2 border-transparent'
                  }`}
                  aria-pressed={form.idType === 'passport'}
                >
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    form.idType === 'passport'
                      ? 'border-[#b14eb1] bg-[#b14eb1] text-white'
                      : 'border-gray-400 group-hover:border-gray-300'
                  }`}>
                    {form.idType === 'passport' && (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <span className={`ml-2 text-sm ${
                    form.idType === 'passport'
                      ? 'text-gray-100 font-semibold'
                      : 'text-gray-300 group-hover:text-gray-100'
                  }`}>
                    Passport
                  </span>
                </button>
              </div>
              {getError('idType') && <p id="idType-error" className="text-sm text-red-600 ml-2">{getError('idType')}</p>}
            </div>
            {/* Conditional ID Input Fields */}
            {form.idType === 'driverLicence' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-5">
                <div>
                  <label htmlFor="driverLicenceNumber" className={labelClasses}>Driver Licence Number *</label>
                  {/* Removed required from input as validation handles the message better */}
                  <input type="text" id="driverLicenceNumber" name="driverLicenceNumber" value={form.driverLicenceNumber} onChange={handleChange} className={inputClasses('driverLicenceNumber')} maxLength={8} placeholder="e.g., AA123456" aria-required="true" aria-invalid={!!getError('driverLicenceNumber')} aria-describedby={getError('driverLicenceNumber') ? `driverLicenceNumber-error` : undefined} />
                  {getError('driverLicenceNumber') && <p id="driverLicenceNumber-error" className="text-sm text-red-600 mt-1 text-left">{getError('driverLicenceNumber')}</p>}
                </div>
                <div>
                  <label htmlFor="driverLicenceVersion" className={labelClasses}>Driver Licence Version *</label>
                   {/* Removed required from input */}
                  <input type="text" id="driverLicenceVersion" name="driverLicenceVersion" value={form.driverLicenceVersion} onChange={handleChange} className={inputClasses('driverLicenceVersion')} maxLength={3} placeholder="e.g., 001" aria-required="true" aria-invalid={!!getError('driverLicenceVersion')} aria-describedby={getError('driverLicenceVersion') ? `driverLicenceVersion-error` : undefined} />
                  {getError('driverLicenceVersion') && <p id="driverLicenceVersion-error" className="text-sm text-red-600 mt-1 text-left">{getError('driverLicenceVersion')}</p>}
                </div>
              </div>
            )}
            {form.idType === 'passport' && (
              <div>
                <label htmlFor="passportNumber" className={labelClasses}>Passport Number *</label>
                 {/* Removed required from input */}
                <input type="text" id="passportNumber" name="passportNumber" value={form.passportNumber} onChange={handleChange} className={inputClasses('passportNumber')} aria-required="true" aria-invalid={!!getError('passportNumber')} aria-describedby={getError('passportNumber') ? `passportNumber-error` : undefined} />
                {getError('passportNumber') && <p id="passportNumber-error" className="text-sm text-red-600 mt-1 text-left">{getError('passportNumber')}</p>}
              </div>
            )}
          </div>
        )}
      </section>
    </form>
  );
}

AboutYouSection.propTypes = {
  initialData: PropTypes.object,
  onNext: PropTypes.func,
  onAutosave: PropTypes.func,
  user: PropTypes.object
};

// Re-exporting validation helpers if they are used elsewhere, otherwise they can stay internal
// export { isValidNZDateString, isOverAgeLimit, NZ_DATE_FORMAT, MIN_AGE };