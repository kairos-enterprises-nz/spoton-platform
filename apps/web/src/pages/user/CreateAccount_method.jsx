import { useState, useRef, useEffect, useCallback, useContext } from 'react';
import { CheckCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/20/solid';
import { sendOtp, verifyOtp, checkEmailExists } from '../../services/verificationService';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import Icon from '../../assets/utilitycopilot-icon.webp';
import Text from '../../assets/spoton-text-reversed.webp';
import AuthContext from '../../context/AuthContext';
import { useAuth } from '../../hooks/useAuth';
import { useLoader } from '../../context/LoaderContext';
import Loader from '../../components/Loader';

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
  const [loaderMessage, setLoaderMessage] = useState('Loading...');

  // Method selection state
  const [signupMethod, setSignupMethod] = useState(null); // null, 'email', 'social'
  const [socialProvider, setSocialProvider] = useState(null); // 'google', 'facebook', 'apple'
  const [showMethodSelection, setShowMethodSelection] = useState(true);

  // Form state variables (missing from backup)
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

  const location = useLocation();
  const { refreshUser } = useContext(AuthContext);

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
      setLoading(true);
      setLoaderMessage(`Redirecting to ${provider} signup...`);
      setSocialProvider(provider);
      
      // Save any registration data before redirect
      if (location.state) {
        localStorage.setItem('spoton_registration_data', JSON.stringify(location.state));
      }
      
      // Redirect to Keycloak with social provider hint for registration
      const baseUrl = window.location.origin;
      const socialRegistrationUrl = `${baseUrl}/api/auth/keycloak/login/?action=register&kc_idp_hint=${provider}`;
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
      setLoaderMessage('Account created successfully! Redirecting...');
      setLoading(true);

      // Check if we have saved registration data
      const savedData = localStorage.getItem('spoton_registration_data');
      if (savedData) {
        try {
          const registrationData = JSON.parse(savedData);
          const { selectedAddress, selectedServices, selectedPlans } = registrationData;
          
          localStorage.removeItem('spoton_registration_data');

          setTimeout(() => {
            navigate('/onboarding', {
              state: { selectedAddress, selectedServices, selectedPlans },
              replace: true
            });
          }, 1500);
            } catch (error) {
          console.error('Error parsing saved registration data:', error);
          setTimeout(() => {
            navigate('/onboarding', { replace: true });
          }, 1500);
        }
      } else {
        setTimeout(() => {
          navigate('/onboarding', { replace: true });
        }, 1500);
      }
    }
  }, [isAuthenticated, user, navigate, setLoading]);

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
    
    if (value && !emailPattern.test(value)) {
      setEmailError('Invalid email address.');
    } else {
      setEmailError('');
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
      ? (
        <span className="text-xs text-start">
          Password must be 8+ characters with uppercase, lowercase, numbers, and symbols.
        </span>
        )
      : ''
    );
    
    // Update password strength
    const { strength } = calculatePasswordStrength(value);
    setPasswordStrength(strength);
    
    // Also re-validate confirm password if password changes
    if (confirmPassword && value !== confirmPassword) {
        setConfirmPasswordError('Passwords do not match.');
    } else {
        setConfirmPasswordError('');
    }
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
    return { strength, requirements };
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

  const validateConfirmPassword = (e) => {
    const value = e.target.value;
    setConfirmPassword(value);
    setConfirmPasswordError(value && value !== password ? 'Passwords do not match.' : '');
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
    if (emailCheckTimerRef.current) {
      clearTimeout(emailCheckTimerRef.current);
    }

    if (!currentEmail || emailError) {
        setIsCheckingEmail(false);
        setEmailExistsError('');
        return;
    }

    setIsCheckingEmail(true);
    setEmailExistsError('');

    emailCheckTimerRef.current = setTimeout(async () => {
        try {
        const result = await checkEmailExists(currentEmail);
        setIsCheckingEmail(false);
        if (result.active) {
          setEmailExistsError(
            <span>
              Account found. <a href="/login" className="text-green-600 hover:underline">Please Login</a>.
            </span>
          );
        } else {
          setEmailExistsError('');
        }
        } catch (error) {
          setIsCheckingEmail(false);
          console.error('Email check error:', error);
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

    setError('');
    setSubmitError('');

    try {
      const { success, message } = await verifyOtp(type, value, otpCode);
      if (success) {
        setVerified(true);
        setOtpSent(false);
        setError('');
      } else {
        setShake(true);
        setError(message || `Invalid ${type.toUpperCase()} verification code.`);
        setTimeout(() => {
          setShake(false);
           if (message) {
              setOtpArray(Array(OTP_LENGTH).fill(''));
              const refs = type === 'email' ? emailOtpInputRefs : mobileOtpInputRefs;
              if (refs && refs.current && refs.current[0]) {
                  refs.current[0]?.focus();
              }
           }
        }, 500);
      }
    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        error.message ||
        `Failed to verify ${type.toUpperCase()} OTP.`;
      setError(errorMessage);
      setSubmitError(errorMessage);
    }
  };

  // Handle OTP input change
  const handleOtpChange = (
    index,
    value,
    otp,
    setOtp,
    refs,
    verifyCallback,
    setError
  ) => {
    if (!/^[0-9]?$/.test(value)) return;

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
      verifyCallback(newOtp);
    }
  };

  // Handle OTP input key down (Backspace)
    const handleOtpKeyDown = (index, e, otp, refs, setOtp) => {
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
    !location.state?.selectedAddress ||
    !location.state?.selectedServices ||
    (location.state?.selectedServices?.electricity && !location.state?.selectedPlans?.electricity) ||
    (location.state?.selectedServices?.broadband && !location.state?.selectedPlans?.broadband)
  );

  // Control when verify buttons are disabled
  const isEmailVerifyDisabled =
    !email ||
    !!emailError ||
    isCheckingEmail ||
    !!emailExistsError ||
    emailVerified ||
    emailOtpSent;

  const isMobileVerifyDisabled =
    !mobile ||
    !!mobileError ||
    mobileVerified ||
    mobileOtpSent;

  // Handle account creation via Django backend (which creates Keycloak user)
  const handleCreateAccount = async () => {
      if (isSubmitDisabled) {
        setSubmitError('Please fill in all required fields and verify your contact details.');
        return;
      }

      setIsSubmitting(true);
      setSubmitError('');
      setLoaderMessage('Creating your account...');
      setLoading(true);
      
      try {
        // Prepare account data for Django backend
        const accountData = {
          firstName,
          lastName,
          email,
          mobile,
          password,
          mobileVerified: true,
          emailVerified: true,
          selectedAddress,
          selectedServices,
          selectedPlans
        };

        // Send to Django backend which will create Keycloak user
        const response = await fetch('/api/auth/keycloak/create-user/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
          body: JSON.stringify(accountData),
        });

        const result = await response.json();
        
        if (response.ok && result.success) {
          // Save registration data for onboarding
          if (location.state) {
            localStorage.setItem('spoton_registration_data', JSON.stringify(location.state));
          }
          
          // Auto-login the user after account creation
          setTimeout(() => {
            window.location.href = result.loginUrl || '/api/auth/keycloak/login/';
          }, 2000);
        } else {
          throw new Error(result.message || 'Failed to create account');
        }
      } catch (error) {
        console.error('Account creation error:', error);
        setSubmitError(error.message || 'An unexpected error occurred. Please try again.');
      } finally {
        setIsSubmitting(false);
        setLoading(false);
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

  return (
    <div className="flex mx-auto min-h-[60vh] w-[90vw] sm:w-[80vw] max-w-[680px] flex-col items-center justify-center bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] text-white px-4 sm:px-6 rounded-xl shadow-xl my-8">
      <div className="w-full max-w-[120px] sm:max-w-[150px] mx-auto py-6 sm:py-8">
        <img alt="SpotOn Icon" src={Icon} className="mx-auto h-16 sm:h-20 w-auto" />
      </div>
   <div className="w-full max-w-[180px] sm:max-w-xs mx-auto pb-4 sm:pb-2">
        <div className="cursor-pointer mx-auto">
                   <img alt="SpotOn Text" src={Text} className="mx-auto h-8 sm:h-10 w-auto" />
                </div>
              </div>
                <div className="mt-10 w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-8"></div>           

      {/* Title */}
      <h2 className="mb-2 text-center text-xl sm:text-2xl font-semibold text-slate-300 tracking-wide">
        Create Your Account
      </h2>
      <p className="mb-4 text-center text-sm text-slate-400">
        {showMethodSelection ? 'Choose how you\'d like to sign up:' : 'Fill in your details below'}
      </p>

      <div className="w-full max-w-xs sm:max-w-sm md:max-w-md mx-auto mt-6 mb-6">
        
        <AnimatePresence mode="wait">
          
          {/* Step 1: Method Selection */}
          {showMethodSelection && (
            <motion.div 
              key="method-selection"
              className="relative bg-white/10 backdrop-blur-lg px-6 py-8 shadow-xl rounded-2xl border border-white/10"
              initial={{ opacity: 0, y: 30, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -30, scale: 0.95 }}
              transition={{ 
                duration: 0.4, 
                ease: [0.25, 0.46, 0.45, 0.94],
                opacity: { duration: 0.3 },
                scale: { duration: 0.3 }
              }}
            >
              <motion.div 
                className="space-y-8"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.15, ease: "easeOut" }}
              >
                
                {/* Email Signup Option */}
                <motion.button
                  onClick={() => handleMethodSelection('email')}
                  className="group relative w-full overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600/20 to-cyan-600/20 p-6 border border-blue-500/30 hover:border-blue-400/50"
                  whileHover={{ 
                    scale: 1.02,
                    background: "linear-gradient(to right, rgb(37 99 235 / 0.3), rgb(8 145 178 / 0.3))"
                  }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ 
                    type: "spring", 
                    stiffness: 400, 
                    damping: 25,
                    mass: 0.5
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div className="flex-1 text-left">
                      <h3 className="text-lg font-semibold text-white group-hover:text-blue-100 transition-colors">Using your email</h3>
                      <p className="text-sm text-slate-300/80 group-hover:text-slate-200/90 transition-colors">Create account with email and password</p>
                    </div>
                    <motion.svg 
                      className="h-5 w-5 text-slate-400 group-hover:text-white" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                      whileHover={{ x: 4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </motion.svg>
                  </div>
                </motion.button>

                {/* Divider */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-white/20" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-gradient-to-br from-slate-600 via-slate-600 to-slate-600 px-4 text-sm text-slate-300">Or continue with</span>
                  </div>
                </div>

                {/* Social Login Grid */}
                <div className="grid grid-cols-3 gap-4">
                  {/* Facebook */}
                  <motion.button
                    onClick={() => handleMethodSelection('facebook')}
                    className="group relative flex h-16 items-center justify-center rounded-xl bg-white/5 backdrop-blur-sm border border-white/10"
                    title="Continue with Facebook"
                    whileHover={{ 
                      scale: 1.05,
                      backgroundColor: "rgba(255, 255, 255, 0.1)",
                      borderColor: "rgba(255, 255, 255, 0.2)"
                    }}
                    whileTap={{ scale: 0.95 }}
                    transition={{ 
                      type: "spring", 
                      stiffness: 500, 
                      damping: 30,
                      mass: 0.3
                    }}
                  >
                    <motion.svg 
                      className="h-7 w-7" 
                      viewBox="0 0 24 24" 
                      fill="#1877F2"
                      whileHover={{ scale: 1.1 }}
                      transition={{ 
                        type: "spring", 
                        stiffness: 600, 
                        damping: 25 
                      }}
                    >
                      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                    </motion.svg>
                  </motion.button>

                  {/* Google */}
                  <motion.button
                    onClick={() => handleMethodSelection('google')}
                    className="group relative flex h-16 items-center justify-center rounded-xl bg-white/5 backdrop-blur-sm border border-white/10"
                    title="Continue with Google"
                    whileHover={{ 
                      scale: 1.05,
                      backgroundColor: "rgba(255, 255, 255, 0.1)",
                      borderColor: "rgba(255, 255, 255, 0.2)"
                    }}
                    whileTap={{ scale: 0.95 }}
                    transition={{ 
                      type: "spring", 
                      stiffness: 500, 
                      damping: 30,
                      mass: 0.3
                    }}
                  >
                    <motion.svg 
                      className="h-7 w-7" 
                      viewBox="0 0 24 24"
                      whileHover={{ scale: 1.1 }}
                      transition={{ 
                        type: "spring", 
                        stiffness: 600, 
                        damping: 25 
                      }}
                    >
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </motion.svg>
                  </motion.button>

                  {/* Apple */}
                  <motion.button
                    onClick={() => handleMethodSelection('apple')}
                    className="group relative flex h-16 items-center justify-center rounded-xl bg-white/5 backdrop-blur-sm border border-white/10"
                    title="Continue with Apple"
                    whileHover={{ 
                      scale: 1.05,
                      backgroundColor: "rgba(255, 255, 255, 0.1)",
                      borderColor: "rgba(255, 255, 255, 0.2)"
                    }}
                    whileTap={{ scale: 0.95 }}
                    transition={{ 
                      type: "spring", 
                      stiffness: 500, 
                      damping: 30,
                      mass: 0.3
                    }}
                  >
                    <motion.svg 
                      className="h-7 w-7 text-white" 
                      viewBox="0 0 24 24" 
                      fill="currentColor"
                      whileHover={{ scale: 1.1 }}
                      transition={{ 
                        type: "spring", 
                        stiffness: 600, 
                        damping: 25 
                      }}
                    >
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                    </motion.svg>
                  </motion.button>
                </div>
                
                {/* Error display */}
                {submitError && (
                  <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 backdrop-blur-sm">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/20">
                        <svg className="h-4 w-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </div>
                      <p className="text-sm text-red-300">{submitError}</p>
                    </div>
                  </div>
                )}
              </motion.div>
            </motion.div>
          )}

        </AnimatePresence>
        
      </div>
      
      <footer className="py-6 sm:py-10 text-center text-xs sm:text-sm text-slate-400">
        &copy; {new Date().getFullYear()} SpotOn. All rights reserved.
      </footer>
    </div>
  );
}

UserAccountSetup.propTypes = {};
