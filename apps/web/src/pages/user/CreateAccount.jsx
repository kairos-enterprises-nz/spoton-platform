import { useState, useRef, useEffect, useCallback, useContext } from 'react';
import { CheckCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/20/solid';
import { sendOtp, verifyOtp, checkEmailExists } from '../../services/verificationService';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import apiClient from '../../services/apiClient';
import Icon from '../../assets/utilitycopilot-icon.webp';
import Text from '../../assets/spoton-text-reversed.webp';
import AuthContext from '../../context/AuthContext';
import { useAuth } from '../../hooks/useAuth';
import { useLoader } from '../../context/LoaderContext';
import Loader from '../../components/Loader';
import MethodSelection from '../../components/auth/MethodSelection';
import SignupForm from '../../components/auth/SignupForm';

const OTP_LENGTH = 6;
const SHAKE_CLASS = 'animate-shake';

// Re-create the cn function locally
function cn(...args) {
  return args.filter(Boolean).join(' ');
}

export default function UserAccountSetup() {
  const { isAuthenticated, user } = useAuth();
  const { loading, setLoading } = useLoader();
  const navigate = useNavigate();
  const location = useLocation();
  const [loaderMessage, setLoaderMessage] = useState('Loading...');

  // Method selection state
  const [signupMethod, setSignupMethod] = useState(null); // null, 'email', 'social'
  const [socialProvider, setSocialProvider] = useState(null); // 'google', 'facebook', 'apple'
  const [showMethodSelection, setShowMethodSelection] = useState(true);

  // Form state variables
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Validation state
  const [emailError, setEmailError] = useState('');
  const [mobileError, setMobileError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [emailExistsError, setEmailExistsError] = useState('');
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);

  // Password state
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [passwordFieldFocused, setPasswordFieldFocused] = useState(false);

  // OTP state
  const [emailOtp, setEmailOtp] = useState(Array(OTP_LENGTH).fill(''));
  const [mobileOtp, setMobileOtp] = useState(Array(OTP_LENGTH).fill(''));
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [mobileOtpSent, setMobileOtpSent] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [mobileVerified, setMobileVerified] = useState(false);
  const [emailOtpError, setEmailOtpError] = useState('');
  const [mobileOtpError, setMobileOtpError] = useState('');
  const [emailOtpShake, setEmailOtpShake] = useState(false);
  const [mobileOtpShake, setMobileOtpShake] = useState(false);

  // Countdown timers
  const [emailResendCountdown, setEmailResendCountdown] = useState(0);
  const [mobileResendCountdown, setMobileResendCountdown] = useState(0);
  const emailResendTimerRef = useRef(null);
  const mobileResendTimerRef = useRef(null);

  // OTP input refs
  const emailOtpInputRefs = useRef([]);
  const mobileOtpInputRefs = useRef([]);

  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const location_state = useLocation();
  const { refreshUser } = useContext(AuthContext);
  
  // Store session ID for cross-domain transfer (sessionStorage is domain-specific)
  let tempSelectionSessionId = null;

  // Method selection handlers
  const handleMethodSelection = (method) => {
    setSignupMethod(method);
    if (method === 'email') {
      setShowMethodSelection(false);
    } else {
      // Handle social login via Keycloak
      handleSocialSignup(method);
    }
  };

  // Social signup handler via Keycloak
  const handleSocialSignup = async (provider) => {
    try {
      setLoaderMessage(`Checking account status...`);
      setLoading(true);
      setSocialProvider(provider);
      
      // First, we need to get the user's email from their Google account to check existence
      // Since we can't get email before OAuth, we'll modify the flow to check after OAuth
      // but before account creation. For now, proceed with OAuth and handle in callback.
      
      // Save any registration data before redirect
      if (location.state) {
        localStorage.setItem('spoton_registration_data', JSON.stringify(location.state));
        
        // ALSO save to backend if we have service selection data
        const { selectedAddress, selectedServices, selectedPlans } = location.state;
        console.log('🔍 SOCIAL SIGNUP DEBUG: location.state:', location.state);
        console.log('🔍 SOCIAL SIGNUP DEBUG: selectedServices:', selectedServices);
        console.log('🔍 SOCIAL SIGNUP DEBUG: selectedPlans:', selectedPlans);
        console.log('🔍 SOCIAL SIGNUP DEBUG: selectedAddress:', selectedAddress);
        
        if (selectedServices || selectedPlans || selectedAddress) {
          try {
            setLoaderMessage(`Saving your service selection...`);
            console.log('Social signup: Saving service selection to backend:', { selectedAddress, selectedServices, selectedPlans });
            
            // Create a temporary session to save the selection data
            const tempSessionData = {
              selectedAddress,
              selectedServices, 
              selectedPlans,
              timestamp: new Date().toISOString(),
              provider: provider,
              action: 'register'
            };
            
            console.log('🔍 SOCIAL SIGNUP DEBUG: tempSessionData:', tempSessionData);
            
            // Save to a temporary backend storage that can be retrieved after authentication
            const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://uat.spoton.co.nz';
            const fullUrl = `${apiBaseUrl}/api/web/onboarding/save-temp-selection/`;
            console.log('🔍 SOCIAL SIGNUP DEBUG: Making API call to:', fullUrl);
            
            const response = await fetch(fullUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
              },
              body: JSON.stringify(tempSessionData)
            });
            
            console.log('🔍 SOCIAL SIGNUP DEBUG: Response status:', response.status, response.statusText);
            
            if (response.ok) {
              const result = await response.json();
              console.log('🔍 SOCIAL SIGNUP DEBUG: Response data:', result);
              console.log('Service selection saved with session ID:', result.session_id);
              // Store session ID to pass via URL (sessionStorage is domain-specific)
              tempSelectionSessionId = result.session_id;
              console.log('🔍 SOCIAL SIGNUP DEBUG: Session ID will be passed via URL:', result.session_id);
            } else {
              const errorText = await response.text();
              console.warn('🔍 SOCIAL SIGNUP DEBUG: API request failed:', response.status, errorText);
              console.warn('Failed to save service selection to backend, will use localStorage fallback');
            }
          } catch (error) {
            console.warn('Error saving service selection to backend:', error);
            // Continue with localStorage fallback
          }
        } else {
          console.log('🔍 SOCIAL SIGNUP DEBUG: No service selection data to save');
        }
      }
      
      // Store intent to prevent duplicate account creation
      sessionStorage.setItem('social_signup_intent', JSON.stringify({
        provider,
        action: 'register',
        timestamp: Date.now()
      }));
      
      setLoaderMessage(`Redirecting to ${provider} signup...`);
      
      // Store temp session ID in cookie for OAuth flow (survives cross-domain redirects)
      if (tempSelectionSessionId) {
        // Set a short-lived cookie that works across SpotOn subdomains
        document.cookie = `temp_selection_session_id=${tempSelectionSessionId}; path=/; max-age=3600; domain=.spoton.co.nz; SameSite=Lax`;
        console.log('🔍 SOCIAL SIGNUP DEBUG: Stored temp_session_id in cookie for all SpotOn subdomains:', tempSelectionSessionId);
      }
      
      // Redirect to Keycloak with social provider hint for registration
      const baseUrl = window.location.origin;
      const socialRegistrationUrl = `${baseUrl}/api/auth/keycloak/login/?action=register&kc_idp_hint=${provider}`;
      console.log('🔍 SOCIAL SIGNUP DEBUG: Redirecting to OAuth URL:', socialRegistrationUrl);
      window.location.href = socialRegistrationUrl;
      
    } catch (error) {
      console.error('Social signup error:', error);
      setSubmitError(`Failed to initiate ${provider} signup. Please try again.`);
      setLoading(false);
    }
  };

  // Handle post-authentication redirect from Keycloak
  useEffect(() => {
    if (isAuthenticated && user) {
      console.log('User authenticated, saving service selection and redirecting to portal onboarding...');
      setLoading(true);

      const handleRedirectToPortal = async () => {
        try {
          // Save service selection data to backend before cross-domain redirect
          const { selectedAddress, selectedServices, selectedPlans } = location.state || {};
          
          if (selectedServices || selectedPlans || selectedAddress) {
            console.log('Saving service selection to backend:', { selectedAddress, selectedServices, selectedPlans });
            
            // Save initial selection to onboarding progress
            const { saveOnboardingStep } = await import('../../services/onboarding');
            await saveOnboardingStep('initialSelection', {
              selectedAddress,
              selectedServices,
              selectedPlans,
              user: user,
              timestamp: new Date().toISOString()
            }, false);
            
            console.log('Service selection saved successfully');
          }

          // Check if we have other saved registration data
          const savedData = localStorage.getItem('spoton_registration_data');
          if (savedData) {
            try {
              const registrationData = JSON.parse(savedData);
              console.log('Found additional registration data, saving to backend:', registrationData);
              
              // Save additional registration data
              const { saveOnboardingStep } = await import('../../services/onboarding');
              await saveOnboardingStep('registrationData', registrationData, false);
              
              // Clean up saved data
              localStorage.removeItem('spoton_registration_data');
            } catch (error) {
              console.error('Error parsing saved registration data:', error);
            }
          }

          // Redirect to portal onboarding
          const portalUrl = import.meta.env.VITE_PORTAL_URL || 'https://uat.portal.spoton.co.nz';
          const redirectUrl = tempSelectionSessionId 
            ? `${portalUrl}/onboarding?temp_session_id=${tempSelectionSessionId}`
            : `${portalUrl}/onboarding`;
          console.log('🔍 SOCIAL SIGNUP DEBUG: Redirecting to:', redirectUrl);
          window.location.href = redirectUrl;
          
        } catch (error) {
          console.error('Error saving service selection:', error);
          // Still redirect even if save fails
          const portalUrl = import.meta.env.VITE_PORTAL_URL || 'https://uat.portal.spoton.co.nz';
          const redirectUrl = tempSelectionSessionId 
            ? `${portalUrl}/onboarding?temp_session_id=${tempSelectionSessionId}`
            : `${portalUrl}/onboarding`;
          console.log('🔍 SOCIAL SIGNUP DEBUG: Error fallback redirect to:', redirectUrl);
          window.location.href = redirectUrl;
        }
      };

      handleRedirectToPortal();
    }
  }, [isAuthenticated, user, navigate, setLoading, location.state]);

  // Get address, services, plans from navigation state
  const { selectedAddress, selectedServices, selectedPlans } = location.state || {};

  // Focus on first OTP input when OTP is sent
  useEffect(() => {
    if (emailOtpSent && emailOtpInputRefs.current[0]) {
      emailOtpInputRefs.current[0].focus();
    }
  }, [emailOtpSent]);

  useEffect(() => {
    if (mobileOtpSent && mobileOtpInputRefs.current[0]) {
      mobileOtpInputRefs.current[0].focus();
    }
  }, [mobileOtpSent]);

  // Validation functions
  const validateEmail = (e) => {
    const value = e.target.value;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    setEmail(value);
    setEmailError(value && !emailPattern.test(value) ? 'Invalid email address.' : '');
    setEmailExistsError('');
    
    // Clear existing email check error
    if (!value || !emailPattern.test(value)) {
      setEmailExistsError('');
    }
    
    // Trigger debounced email check
    if (value && emailPattern.test(value)) {
      debouncedCheckEmailExists(value);
    }
  };

  const validateMobile = (e) => {
    const value = e.target.value;
    setMobile(value);
    const mobilePattern = /^(02|021|022|027|028|029)\d{7,8}$/;
    setMobileError(value && !mobilePattern.test(value) ? 'Invalid mobile number.' : '');
  };

  const validatePassword = (e) => {
    const value = e.target.value;
    setPassword(value);
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    setPasswordError(
      value && !passwordPattern.test(value)
        ? 'Password must be at least 8 characters with uppercase, lowercase, number, and special character.'
      : ''
    );
    
    // Update password strength
    const { strength } = calculatePasswordStrength(value);
    setPasswordStrength(strength);
    
    // Also re-validate confirm password if password changes
    if (confirmPassword && value !== confirmPassword) {
        setConfirmPasswordError('Passwords do not match.');
    } else if (confirmPassword && value === confirmPassword) {
        setConfirmPasswordError('');
    }
  };

  const validateConfirmPassword = (e) => {
    const value = e.target.value;
    setConfirmPassword(value);
    setConfirmPasswordError(value && value !== password ? 'Passwords do not match.' : '');
  };

  // Helper function to calculate password strength and requirements
  const calculatePasswordStrength = (password) => {
    const requirements = {
      length: password.length >= 8,
      lowercase: /[a-z]/.test(password),
      uppercase: /[A-Z]/.test(password),
      number: /\d/.test(password),
      symbol: /[@$!%*?&]/.test(password)
    };
    
    const strength = Object.values(requirements).filter(Boolean).length;
    return { requirements, strength };
  };

  // Get password requirements status
  const getPasswordRequirements = (password) => {
    const { requirements } = calculatePasswordStrength(password);
    return [
      { label: '8+ characters', met: requirements.length, icon: requirements.length ? '✓' : '○' },
      { label: 'Lowercase letter', met: requirements.lowercase, icon: requirements.lowercase ? '✓' : 'a' },
      { label: 'Uppercase letter', met: requirements.uppercase, icon: requirements.uppercase ? '✓' : 'A' },
      { label: 'Number', met: requirements.number, icon: requirements.number ? '✓' : '1' },
      { label: 'Symbol (@$!%*?&)', met: requirements.symbol, icon: requirements.symbol ? '✓' : '@' }
    ];
  };

  // Helper function to generate strong password
  const generateStrongPassword = () => {
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    const symbols = '@$!%*?&';
    const allChars = lowercase + uppercase + numbers + symbols;
    
    let password = '';
    
    // Ensure at least one character from each category
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += symbols[Math.floor(Math.random() * symbols.length)];
    
    // Fill rest of password (12 characters total)
    for (let i = 4; i < 12; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)];
    }
    
    // Shuffle the password
    return password.split('').sort(() => Math.random() - 0.5).join('');
  };

  // Handle password generation
  const handleGeneratePassword = () => {
    const newPassword = generateStrongPassword();
    setPassword(newPassword);
    const { strength } = calculatePasswordStrength(newPassword);
    setPasswordStrength(strength);
    setPasswordError('');
    
    // Clear confirm password to prompt user to re-confirm
    setConfirmPassword('');
    setConfirmPasswordError('');
  };

  const goToGetStarted = () => {
    navigate('/getstarted');
  };

  // Countdown timer functions
  const startEmailCountdown = () => {
    if (emailResendTimerRef.current) clearInterval(emailResendTimerRef.current);
    setEmailResendCountdown(30);
    emailResendTimerRef.current = setInterval(() => {
      setEmailResendCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(emailResendTimerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const startMobileCountdown = () => {
    if (mobileResendTimerRef.current) clearInterval(mobileResendTimerRef.current);
    setMobileResendCountdown(30);
    mobileResendTimerRef.current = setInterval(() => {
      setMobileResendCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(mobileResendTimerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Check if email exists (debounced)
  const emailCheckTimerRef = useRef(null);
  const debouncedCheckEmailExists = useCallback((currentEmail) => {
    if (emailCheckTimerRef.current) clearTimeout(emailCheckTimerRef.current);

    emailCheckTimerRef.current = setTimeout(async () => {
      if (currentEmail && currentEmail === email) {
        setIsCheckingEmail(true);
        try {
          const exists = await checkEmailExists(currentEmail);
          if (exists && currentEmail === email) {
          setEmailExistsError(
            <span>
              Account found. <a href="/login" className="text-green-600 hover:underline">Please Login</a>.
            </span>
          );
        } else {
          setEmailExistsError('');
        }
        } catch (error) {
          console.error('Email check error:', error);
        } finally {
          setIsCheckingEmail(false);
        }
        }
    }, 500);
  }, [emailError]);

  // Cleanup debounce timer on unmount
  useEffect(() => {
      return () => {
          if (emailCheckTimerRef.current) {
              clearTimeout(emailCheckTimerRef.current);
          }
      };
  }, []);

  // Handle sending OTP
  const handleSendOtp = async (type) => {
    const value = type === 'email' ? email : mobile;

    if (type === 'email') {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(value)) {
        setEmailError('Invalid email address.');
        return;
      }

      // Check if email exists before sending OTP
      setIsCheckingEmail(true);
      try {
        const emailCheckResult = await checkEmailExists(value);
        setIsCheckingEmail(false);
        
        if (emailCheckResult.active) {
          setEmailExistsError(
            <span>
              Account found. <a href="/login" className="text-green-600 hover:underline">Please Login</a>.
            </span>
          );
          return;
        }
      } catch (error) {
        setIsCheckingEmail(false);
      }
    }

    if (type === 'mobile') {
         const mobilePattern = /^(02|021|022|027|028|029)\d{7,8}$/;
         if (!mobilePattern.test(value)) {
           setMobileError('Invalid mobile number.');
           return;
         }
    }

    // Clear errors before sending OTP
    if (type === 'email') setEmailOtpError('');
    if (type === 'mobile') setMobileOtpError('');
    setSubmitError('');

    try {
      const response = await sendOtp(type, value);
      if (response.success) {
        if (type === 'email') {
          setEmailOtpSent(true);
          setEmailOtp(Array(OTP_LENGTH).fill(''));
          startEmailCountdown();
        } else {
          setMobileOtpSent(true);
          setMobileOtp(Array(OTP_LENGTH).fill(''));
          startMobileCountdown();
        }
      } else {
        const errorMessage = response.message || `Failed to send ${type.toUpperCase()} OTP.`;
         if (type === 'email') {
            if (errorMessage.includes('already exists') || errorMessage.includes('found')) {
                 setEmailExistsError(errorMessage);
            } else {
                 setEmailError(errorMessage);
            }
         } else {
             setMobileError(errorMessage);
         }
         setSubmitError(errorMessage);
      }
    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        error.message ||
        `Failed to send ${type.toUpperCase()} OTP.`;
      if (type === 'email') {
        setEmailError(errorMessage);
      } else {
        setMobileError(errorMessage);
      }
       setSubmitError(errorMessage);
    }
  };

  // Handle OTP verification
  const handleOTPVerify = async (
    type,
    otpArray,
    setVerified,
    setShake,
    setOtpArray,
    setOtpSent,
    setError
  ) => {
    const value = type === 'email' ? email : mobile;
    const otpCode = otpArray.join('');
    if (otpCode.length !== OTP_LENGTH) return;

    console.log(`🔍 [OTP Verify] Starting verification for ${type}: ${value} with code: ${otpCode}`);
    
    setError('');
    setSubmitError('');

    try {
      console.log(`🔍 [OTP Verify] Calling verifyOtp API...`);
      const response = await verifyOtp(type, value, otpCode);
      console.log(`🔍 [OTP Verify] API Response:`, response);
      
      if (response.success) {
        console.log(`✅ [OTP Verify] Verification successful for ${type}: ${value}`);
        setVerified(true);
        setOtpSent(false);
        setError('');
        
        // Show success message
        console.log(`✅ [OTP Verify] Setting ${type} as verified`);
      } else {
        console.log(`❌ [OTP Verify] Verification failed:`, response.message);
        setShake(true);
        setError(response.message || `Invalid ${type.toUpperCase()} verification code.`);
        setTimeout(() => {
          setShake(false);
           if (response.message) {
              setOtpArray(Array(OTP_LENGTH).fill(''));
              const refs = type === 'email' ? emailOtpInputRefs : mobileOtpInputRefs;
              if (refs && refs.current && refs.current[0]) {
                  refs.current[0]?.focus();
              }
           }
        }, 500);
      }
    } catch (error) {
      console.error(`❌ [OTP Verify] Exception during verification:`, error);
      const errorMessage =
        error.response?.data?.message ||
        error.message ||
        `Failed to verify ${type.toUpperCase()} OTP.`;
      console.error(`❌ [OTP Verify] Error message:`, errorMessage);
      setError(errorMessage);
      setSubmitError(errorMessage);
    }
  };

  // Handle OTP input change
  const handleOtpChange = (
    type,
    index,
    value
  ) => {
    if (!/^[0-9]?$/.test(value)) return;

    const isEmail = type === 'email';
    const otp = isEmail ? emailOtp : mobileOtp;
    const setOtp = isEmail ? setEmailOtp : setMobileOtp;
    const refs = isEmail ? emailOtpInputRefs : mobileOtpInputRefs;
    const setError = isEmail ? setEmailOtpError : setMobileOtpError;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setError('');

    if (value && index < OTP_LENGTH - 1) {
      if (refs && refs.current && refs.current[index + 1]) {
        refs.current[index + 1]?.focus();
      }
    } else if (!value && index > 0) {
          if (refs && refs.current && refs.current[index - 1]) {
              refs.current[index - 1]?.focus();
          }
    }

    if (newOtp.every((digit) => digit !== '')) {
      const verifyCallback = () => handleOTPVerify(
        type,
        newOtp,
        isEmail ? setEmailVerified : setMobileVerified,
        isEmail ? setEmailOtpShake : setMobileOtpShake,
        setOtp,
        isEmail ? setEmailOtpSent : setMobileOtpSent,
        setError
      );
      verifyCallback();
    }
  };

  // Handle OTP input key down (Backspace)
  const handleOtpKeyDown = (type, index, e) => {
    const isEmail = type === 'email';
    const otp = isEmail ? emailOtp : mobileOtp;
    const setOtp = isEmail ? setEmailOtp : setMobileOtp;
    const refs = isEmail ? emailOtpInputRefs : mobileOtpInputRefs;

        if (e.key === 'Backspace' && index > 0 && !otp[index]) {
            e.preventDefault();
            const newOtp = [...otp];
            newOtp[index] = '';
            setOtp(newOtp);
            if (refs && refs.current && refs.current[index - 1]) {
                refs.current[index - 1]?.focus();
            }
        } else if (e.key === 'ArrowLeft' && index > 0) {
            e.preventDefault();
            if (refs && refs.current && refs.current[index - 1]) {
                refs.current[index - 1]?.focus();
            }
        } else if (e.key === 'ArrowRight' && index < OTP_LENGTH - 1) {
            e.preventDefault();
            if (refs && refs.current && refs.current[index + 1]) {
                refs.current[index + 1]?.focus();
            }
        }
  };

  // Form submission check
  const isSubmitDisabled = !!(
    !firstName ||
    !lastName ||
    !email ||
    !mobile ||
    !password ||
    !confirmPassword ||
    emailError ||
    mobileError ||
    passwordError ||
    confirmPasswordError ||
    emailExistsError ||
    !emailVerified ||
    !mobileVerified ||
    isCheckingEmail
  );

  // Handle account creation via Django backend (which creates Keycloak user)
  const handleCreateAccount = async () => {
      if (isSubmitDisabled) {
        return;
      }

      setIsSubmitting(true);
      setSubmitError('');
      
      try {
        // Prepare account data for Django backend
        const accountData = {
          firstName,
          lastName,
          email,
          mobile,
          password,
          confirmPassword,
          mobileVerified: true,
          emailVerified: true,
          selectedAddress,
          selectedServices,
          selectedPlans
        };

        console.log('🔍 CREATE ACCOUNT DEBUG: Sending account data to backend:', {
          selectedServices,
          selectedPlans,
          mobilePlan: selectedPlans?.mobile ? {
            name: selectedPlans.mobile.name,
            pricing_id: selectedPlans.mobile.pricing_id,
            plan_id: selectedPlans.mobile.plan_id
          } : null
        });

        // Send to Django backend which will create Keycloak user
        const response = await apiClient.post('/auth/keycloak/create-user/', accountData);

        const result = response.data;
        
        if ((response.status === 200 || response.status === 201) && result.success) {
          // Save registration data for onboarding
          if (location.state) {
            localStorage.setItem('spoton_registration_data', JSON.stringify(location.state));
          }
          
          // ALSO save service selection to backend for cross-domain transfer
          if (selectedServices || selectedPlans || selectedAddress) {
            try {
              console.log('🔍 REGULAR SIGNUP DEBUG: Saving service selection to backend:', { selectedAddress, selectedServices, selectedPlans });
              
              // Create a temporary session to save the selection data
              const tempSessionData = {
                selectedAddress,
                selectedServices, 
                selectedPlans,
                timestamp: new Date().toISOString(),
                provider: 'email_mobile',
                action: 'register'
              };
              
              console.log('🔍 REGULAR SIGNUP DEBUG: tempSessionData:', tempSessionData);
              
              // Save to a temporary backend storage that can be retrieved after authentication
              const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://uat.spoton.co.nz';
              const fullUrl = `${apiBaseUrl}/api/web/onboarding/save-temp-selection/`;
              console.log('🔍 REGULAR SIGNUP DEBUG: Making API call to:', fullUrl);
              
              const tempResponse = await fetch(fullUrl, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                },
                body: JSON.stringify(tempSessionData)
              });
              
              console.log('🔍 REGULAR SIGNUP DEBUG: Response status:', tempResponse.status, tempResponse.statusText);
              
              if (tempResponse.ok) {
                const tempResult = await tempResponse.json();
                console.log('🔍 REGULAR SIGNUP DEBUG: Response data:', tempResult);
                console.log('Regular signup: Service selection saved with session ID:', tempResult.session_id);
                // Store session ID to pass via URL (sessionStorage is domain-specific)
                tempSelectionSessionId = tempResult.session_id;
                console.log('🔍 REGULAR SIGNUP DEBUG: Session ID will be passed via URL:', tempResult.session_id);
              } else {
                const errorText = await tempResponse.text();
                console.warn('🔍 REGULAR SIGNUP DEBUG: API request failed:', tempResponse.status, errorText);
                console.warn('Failed to save service selection to backend, will use localStorage fallback');
              }
            } catch (error) {
              console.warn('Error saving service selection to backend:', error);
              // Continue with localStorage fallback
            }
          }
          
          // Show success message with redirect info
          const redirectMessage = result.redirect?.message || 'Redirecting to complete your setup...';
          setSubmitError(''); // Clear any previous errors
          
          // Update UI to show success state
          console.log('Account created successfully:', result.user);
          console.log('Redirect info:', result.redirect);
          
          // Auto-login the user after account creation
          setTimeout(() => {
            const loginUrl = result.loginUrl || '/api/auth/keycloak/login/';
            console.log('Redirecting to login:', loginUrl);
            window.location.href = loginUrl;
          }, 2000);
        } else {
          setSubmitError(result.message || 'Failed to create account. Please try again.');
        }
      } catch (error) {
        console.error('Account creation error:', error);
        
        // Handle different types of errors with specific messaging
        if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
          // Network connectivity issue - check if account was actually created
          console.log('Network error detected, checking if account was created...');
          
          try {
            // Check if the account was created despite the network error
            const checkResponse = await apiClient.get(`/check-email/?email=${encodeURIComponent(email)}`);
            
            if (checkResponse.data.exists) {
              // Account was created successfully despite network error
              console.log('Account was created successfully despite network error');
              setSubmitError('');
              
              // Show success message and redirect
              setTimeout(() => {
                const portalUrl = 'https%3A%2F%2Fuat.portal.spoton.co.nz%2Fonboarding';
                const redirectUrl = tempSelectionSessionId 
                  ? `${portalUrl}%3Ftemp_session_id%3D${tempSelectionSessionId}`
                  : portalUrl;
                const loginUrl = `/auth/keycloak/login/?email=${encodeURIComponent(email)}&auto_login=true&redirect_to=${redirectUrl}`;
                console.log('🔍 REGULAR SIGNUP DEBUG: Redirecting with session ID to:', loginUrl);
                window.location.href = loginUrl;
              }, 2000);
              return;
            }
          } catch (checkError) {
            console.error('Failed to verify account creation:', checkError);
          }
          
          setSubmitError(
            'Network connection issue detected. Your account may have been created successfully. ' +
            'Please check your email or try logging in. If the issue persists, please try again.'
          );
        } else if (error.response?.status >= 400 && error.response?.status < 500) {
          // Client error - show specific message from server
          const errorMessage = error.response?.data?.message || 'Invalid request. Please check your information and try again.';
          setSubmitError(errorMessage);
        } else if (error.response?.status >= 500) {
          // Server error
          setSubmitError('Server temporarily unavailable. Please try again in a few moments.');
        } else {
          // Generic error
          setSubmitError('Failed to create account. Please try again.');
        }
      } finally {
        setIsSubmitting(false);
      }
    };

  // Get CSRF token
  const getCsrfToken = () => {
    const name = 'csrftoken';
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  // Show loader if processing or already authenticated
  if (loading || isAuthenticated) {
    return <Loader fullscreen />;
  }

  // Form data object for SignupForm
  const formData = {
    firstName,
    lastName,
    email,
    mobile,
    password,
    confirmPassword
  };

  // Error object for SignupForm
  const errors = {
    emailError,
    mobileError,
    passwordError,
    confirmPasswordError,
    submitError
  };

  // Input change handler for SignupForm
  const handleInputChange = (field, value) => {
    switch (field) {
      case 'firstName':
        setFirstName(value);
        break;
      case 'lastName':
        setLastName(value);
        break;
      case 'email':
        validateEmail({ target: { value } });
        break;
      case 'mobile':
        validateMobile({ target: { value } });
        break;
      case 'password':
        validatePassword({ target: { value } });
        break;
      case 'confirmPassword':
        validateConfirmPassword({ target: { value } });
        break;
      default:
        break;
    }
  };

  return (
    <div className="flex mx-auto min-h-[60vh] w-[90vw] sm:w-[80vw] max-w-[680px] flex-col items-center justify-center bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] text-white px-4 sm:px-6 rounded-xl shadow-xl my-8">
      {/* Back to Get Started button will be placed at the bottom per request */}
      <div className={`w-full max-w-[120px] sm:max-w-[150px] mx-auto ${showMethodSelection ? 'py-4 sm:py-6' : 'py-6 sm:py-8'}`}>
        <img alt="SpotOn Icon" src={Icon} className={`mx-auto h-16 sm:h-20 w-auto`} />
      </div>
      <div className={`w-full max-w-[180px] sm:max-w-xs mx-auto ${showMethodSelection ? 'pb-2 sm:pb-3' : 'pb-4 sm:pb-2'}`}>
        <div className="mx-auto">
          <img alt="SpotOn Text" src={Text} className={`mx-auto h-8 sm:h-10 w-auto`} />
                </div>
              </div>
      <div className={`${showMethodSelection ? 'mt-6' : 'mt-10'} w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-8`}></div>

      {/* Title */}
      <h2 className={`mb-2 text-center ${showMethodSelection ? 'text-lg sm:text-xl' : 'text-xl sm:text-2xl'} font-semibold text-slate-300 tracking-wide`}>
        Create Your Account
      </h2>
      <p className={`${showMethodSelection ? 'mb-4' : 'mb-6'} text-center text-sm text-slate-400`}>
        {showMethodSelection ? 'Choose how you\'d like to sign up:' : 'Fill in your details below'}
      </p>

      <div className={`w-full ${showMethodSelection ? 'max-w-xs sm:max-w-sm' : 'max-w-xs sm:max-w-sm md:max-w-md'} mx-auto ${showMethodSelection ? 'mt-4 mb-4' : 'mt-6 mb-6'}`}>
        
                  <AnimatePresence mode="wait">
          
          {/* Step 1: Method Selection */}
          {showMethodSelection && (
            <MethodSelection 
              onMethodSelect={handleMethodSelection}
              submitError={submitError}
            />
          )}

          {/* Step 2: Form */}
          {!showMethodSelection && (
            <SignupForm 
              formData={formData}
              onInputChange={handleInputChange}
              onSubmit={handleCreateAccount}
              onBack={() => setShowMethodSelection(true)}
              isSubmitting={isSubmitting}
              isSubmitDisabled={isSubmitDisabled}
              errors={errors}
              showPassword={showPassword}
              showConfirmPassword={showConfirmPassword}
              onTogglePassword={() => setShowPassword(!showPassword)}
              onToggleConfirmPassword={() => setShowConfirmPassword(!showConfirmPassword)}
              // OTP related props
              emailOtpSent={emailOtpSent}
              mobileOtpSent={mobileOtpSent}
              emailVerified={emailVerified}
              mobileVerified={mobileVerified}
              emailOtp={emailOtp}
              mobileOtp={mobileOtp}
              emailOtpError={emailOtpError}
              mobileOtpError={mobileOtpError}
              emailOtpShake={emailOtpShake}
              mobileOtpShake={mobileOtpShake}
              emailResendCountdown={emailResendCountdown}
              mobileResendCountdown={mobileResendCountdown}
              onSendOtp={handleSendOtp}
              onOtpChange={handleOtpChange}
              onOtpKeyDown={handleOtpKeyDown}
              emailOtpInputRefs={emailOtpInputRefs}
              mobileOtpInputRefs={mobileOtpInputRefs}
              // Email checking
              isCheckingEmail={isCheckingEmail}
              emailExistsError={emailExistsError}
              // Password features
              passwordStrength={passwordStrength}
              passwordFieldFocused={passwordFieldFocused}
              onPasswordFocus={() => setPasswordFieldFocused(true)}
              onPasswordBlur={() => setPasswordFieldFocused(false)}
              onGeneratePassword={handleGeneratePassword}
              getPasswordRequirements={getPasswordRequirements}
            />
                      )}

                   </AnimatePresence>
        
              </div>

              {/* Bottom: Back to Get Started */}
              <div className="mt-2">
                <button
                  onClick={goToGetStarted}
                  className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 text-cyan-200 hover:text-white ring-1 ring-white/15 hover:ring-white/25 shadow-sm hover:shadow transition-all duration-200"
                >
                  <svg className="h-4 w-4 -ml-0.5 transition-transform duration-200 group-hover:-translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M15 18l-6-6 6-6" />
                  </svg>
                  <span className="text-[11px] sm:text-xs font-semibold tracking-wide">Back to Get Started</span>
                </button>
              </div>

              <footer className="py-6 sm:py-10 text-center text-xs sm:text-sm text-slate-400">
                &copy; {new Date().getFullYear()} SpotOn. All rights reserved.
              </footer>
    </div>
  );
}

UserAccountSetup.propTypes = {};
