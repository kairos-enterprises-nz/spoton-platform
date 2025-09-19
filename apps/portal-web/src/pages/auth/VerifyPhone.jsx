import { useState, useContext, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { LogOut } from 'lucide-react';
import { AuthContext } from '../../context/AuthContext';
import PageWrapper from '../../components/PageWrapper';
import Loader from '../../components/Loader';
import Icon from '../../assets/utilitycopilot-icon.webp';
import Text from '../../assets/spoton-text-reversed.webp';
import { validateNZMobileLocalPart, normalizeNZFromLocalPart, normalizeNZPhone } from '../../utils/phoneValidation';

// OTP Configuration
const OTP_LENGTH = 6;
const SHAKE_CLASS = 'animate-pulse';

export default function VerifyPhone() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, setUser, logout } = useContext(AuthContext);
  
  // Debug logging (throttled to prevent spam)
  const currentUserId = user?.id || location.state?.user?.id;
  if (!window._verifyPhoneLoaded || window._verifyPhoneLoaded !== currentUserId) {
    console.log('📱 VerifyPhone component loaded:', {
      pathname: location.pathname,
      user: user ? 'present' : 'null',
      stateUser: location.state?.user ? 'present' : 'null',
      locationState: location.state
    });
    window._verifyPhoneLoaded = currentUserId;
  }
  
  // State from location (passed from OAuth callback)
  const stateUser = location.state?.user;
  const isNewUser = location.state?.isNewUser;
  const provider = location.state?.provider;
  const userEmail = stateUser?.email || user?.email;

  // Form state
  // Store only the local part (without +64 and without leading 0)
  const initialPhone = user?.phone || stateUser?.phone || user?.mobile || stateUser?.mobile || '';
  const [phone, setPhone] = useState(() => {
    // Extract local part if phone exists
    if (initialPhone && initialPhone.startsWith('+64')) {
      return initialPhone.substring(3).replace(/^0/, '');
    }
    return initialPhone.replace(/^\+64/, '').replace(/^0/, '');
  });
  const [phoneError, setPhoneError] = useState('');
  const [phoneTouched, setPhoneTouched] = useState(false);
  const [isPhoneValid, setIsPhoneValid] = useState(Boolean(initialPhone));
  const [step, setStep] = useState(() => {
    // If user has existing phone number, start with OTP step (will auto-send)
    // If no phone number, start with phone input step
    const startStep = initialPhone ? 'otp' : 'phone';
    console.log('📱 VerifyPhone: Initial step determined:', {
      initialPhone: initialPhone,
      startStep: startStep,
      reason: initialPhone ? 'Has existing phone - skip to OTP' : 'No phone - start with input'
    });
    return startStep;
  });
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [error, setError] = useState('');

  // OTP state - using array like traditional flow
  const [otp, setOtp] = useState(Array(OTP_LENGTH).fill(''));
  const [otpSent, setOtpSent] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [otpShake, setOtpShake] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [redirectCountdown, setRedirectCountdown] = useState(5);
  const [postVerifyRedirect, setPostVerifyRedirect] = useState('/onboarding');
  const redirectTimerRef = useRef(null);
  const redirectIntervalRef = useRef(null);
  
  // Refs for OTP inputs
  const otpInputRefs = useRef([]);

  // Resend cooldown effect
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  // Route guards: do not allow anonymous access to verify-phone
  useEffect(() => {
    const isSocial = (u) => {
      if (!u) return false;
      // Check multiple indicators for social/OAuth users
      return (
        u.registration_method === 'social' ||
        !!u.social_provider ||
        provider === 'google' || // From location state (OAuth callback)
        location.state?.from === '/auth/callback' // Coming from OAuth flow
      );
    };
    
    // If there is no user and no state user, push to login
    if (!user && !stateUser) {
      console.log('📱 VerifyPhone: No user data, redirecting to login');
      navigate('/login', { replace: true });
      return;
    }
    
    const effectiveUser = user || stateUser;
    if (!effectiveUser) return;
    
    // Use stable properties to prevent infinite loops
    const userId = effectiveUser.id;
    const registrationMethod = effectiveUser.registration_method;
    const socialProvider = effectiveUser.social_provider;
    // Use normalized mobile_verified field, fallback to legacy phone_verified
    const phoneVerified = effectiveUser.mobile_verified !== undefined ? effectiveUser.mobile_verified : effectiveUser.phone_verified;
    
    // Only log once per user to prevent spam
    if (!window._verifyPhoneChecked || window._verifyPhoneChecked !== userId) {
      console.log('📱 VerifyPhone: Checking user eligibility:', {
        userId,
        isSocial: isSocial(effectiveUser),
        registration_method: registrationMethod,
        social_provider: socialProvider,
        phone_verified: phoneVerified
      });
      window._verifyPhoneChecked = userId;
    }
    
    // Allow access ONLY if:
    // 1. User is social/OAuth user (they need mobile verification), OR
    // 2. User is coming from OAuth callback
    // Traditional users should NOT be here regardless of mobile verification status
    const shouldAllowAccess = isSocial(effectiveUser) || 
                             location.state?.from === '/auth/callback';
    
    if (!shouldAllowAccess) {
      console.log('📱 VerifyPhone: User not eligible for phone verification, redirecting to dashboard');
      navigate('/', { replace: true });
      return;
    }
    
    // If already phone-verified, continue flow (but don't interrupt success UI)
    if (phoneVerified && !verificationSuccess) {
      console.log('📱 VerifyPhone: Phone already verified, redirecting to onboarding');
      navigate('/onboarding', { replace: true });
      return;
    }
    
    console.log('📱 VerifyPhone: All checks passed, staying on verify-phone page');
  }, [user?.id, user?.registration_method, user?.social_provider, user?.phone_verified, user?.mobile_verified, stateUser?.id, stateUser?.registration_method, stateUser?.social_provider, stateUser?.phone_verified, stateUser?.mobile_verified, verificationSuccess, navigate]);

  // Auto-send OTP if phone number exists (for returning users)
  useEffect(() => {
    if (initialPhone && phone && step === 'otp' && isPhoneValid && !sendingOtp && !otpSent) {
      console.log('📱 Auto-sending OTP for existing phone number:', initialPhone);
      handleSendOTP({ preventDefault: () => {} }); // Simulate form submission
    }
  }, [step, initialPhone, phone, isPhoneValid, sendingOtp, otpSent]); // React to step changes
  
  // Cleanup timers when component unmounts or success state resets
  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) clearTimeout(redirectTimerRef.current);
      if (redirectIntervalRef.current) clearInterval(redirectIntervalRef.current);
    };
  }, []);

  // Phone validation function (consistent with traditional flow)
  const validatePhone = (phoneNumber) => {
    const validation = validateNZMobileLocalPart(phoneNumber);
    setPhoneError(validation.error);
    setIsPhoneValid(validation.isValid);
    return validation.isValid;
  };

  // Send OTP using same API as traditional flow
  const handleSendOTP = async (e) => {
    e.preventDefault();
    setPhoneTouched(true);
    if (!validatePhone(phone)) {
      return;
    }

    if (!userEmail) {
      navigate('/login', { replace: true });
      return;
    }

    setSendingOtp(true);
    setError('');
    setPhoneError('');

    try {
      const normalizedPhone = normalizeNZFromLocalPart(phone);
      
      // Use same API endpoint as traditional flow
      const response = await fetch('/api/otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          action: 'send',
          purpose: 'phone_verification',
          mobile: normalizedPhone,
          email: userEmail // For OAuth flow identification
        })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log('📱 OTP sent successfully, switching to OTP step');
        setOtpSent(true);
        if (step !== 'otp') {
          setStep('otp'); // Only switch if not already on OTP step
        }
        setResendCooldown(60);
      } else {
        throw new Error(data.message || 'Failed to send verification code');
      }
      
    } catch (err) {
      setError(err.message || 'Failed to send verification code');
    } finally {
      setSendingOtp(false);
    }
  };

  // Handle OTP input change (exact same logic as traditional flow)
  const handleOtpChange = (index, value) => {
    if (!/^[0-9]?$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setOtpError('');

    // Auto-focus next input
    if (value && index < OTP_LENGTH - 1) {
      if (otpInputRefs.current[index + 1]) {
        otpInputRefs.current[index + 1].focus();
      }
    } else if (!value && index > 0) {
      if (otpInputRefs.current[index - 1]) {
        otpInputRefs.current[index - 1].focus();
      }
    }

    // Auto-verify when all digits filled
    if (newOtp.every((digit) => digit !== '')) {
      handleVerifyOTP(newOtp);
    }
  };

  // Handle OTP key down (backspace navigation)
  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      const newOtp = [...otp];
      if (newOtp[index]) {
        newOtp[index] = '';
        setOtp(newOtp);
      } else if (index > 0) {
        newOtp[index - 1] = '';
        setOtp(newOtp);
        otpInputRefs.current[index - 1]?.focus();
      }
    }
  };

  // Verify OTP using same API as traditional flow
  const handleVerifyOTP = async (otpArray = otp) => {
    const otpCode = otpArray.join('');
    if (otpCode.length !== OTP_LENGTH) return;

    setVerifyingOtp(true);
    setError('');
    setOtpError('');

    try {
      const normalizedPhone = normalizeNZFromLocalPart(phone);
      
      // Use same API endpoint as traditional flow
      const response = await fetch('/api/otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          action: 'verify',
          purpose: 'phone_verification',
          mobile: normalizedPhone,
          otp: otpCode,
          email: userEmail // For OAuth flow identification
        })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log('📱 Phone verification successful!');
        
        // Force fresh user data fetch from /auth/me/ to get updated Keycloak attributes
        console.log('📱 Fetching fresh user data after phone verification...');
        
        try {
          // Use full API URL for /auth/me/ request
          const apiBaseUrl = window.location.hostname.includes('uat.') 
            ? 'https://uat.api.spoton.co.nz' 
            : 'https://api.spoton.co.nz';
            
          const freshUserResponse = await fetch(`${apiBaseUrl}/auth/me/`, {
            method: 'GET',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            }
          });
          
          if (freshUserResponse.ok) {
            const freshUserData = await freshUserResponse.json();
            console.log('✅ Fresh user data after phone verification:', freshUserData);
            
            // Update user with fresh data from backend
            setUser(prev => ({
              ...(prev || {}),
              ...freshUserData,
              phone: normalizedPhone,
              mobile: normalizedPhone,
              phone_verified: true // Ensure this is set
            }));
            
            console.log('✅ User state updated with fresh data after phone verification');
          } else {
            console.warn('⚠️ Failed to fetch fresh user data, using response data');
            // Fallback to response data
            if (data.user) {
              setUser(prev => ({
                ...(prev || {}),
                ...data.user,
                phone: normalizedPhone,
                mobile: normalizedPhone,
                phone_verified: true
              }));
            }
          }
        } catch (fetchError) {
          console.error('❌ Error fetching fresh user data:', fetchError);
          // Fallback to response data
          if (data.user) {
            setUser(prev => ({
              ...(prev || {}),
              ...data.user,
              phone: normalizedPhone,
              mobile: normalizedPhone,
              phone_verified: true
            }));
          }
        }
        
        // Inform other tabs/components
        window.dispatchEvent(new Event('auth-user-updated'));
        window.dispatchEvent(new Event('auth-refresh-request'));

        // Enhanced post-verification routing logic
        const userToCheck = data.user || stateUser;
        
        if (userToCheck) {
          const isOnboardingComplete = Boolean(
            userToCheck.is_onboarding_complete ?? 
            userToCheck.onboarding_complete ?? 
            false
          );

          // Show success UI and delay redirect to allow syncs to complete
          setVerificationSuccess(true);
          const nextPath = !isOnboardingComplete ? '/onboarding' : (userToCheck.is_staff ? (userToCheck.is_superuser ? '/staff/tenants' : '/staff/users') : '/');
          setPostVerifyRedirect(nextPath);

          // 5-second countdown managed by interval; allow early continue
          setRedirectCountdown(5);
          redirectIntervalRef.current = setInterval(() => {
            setRedirectCountdown((prev) => {
              if (prev <= 1) {
                clearInterval(redirectIntervalRef.current);
                redirectIntervalRef.current = null;
                navigate(nextPath, { replace: true });
                return 0;
              }
              return prev - 1;
            });
          }, 1000);
          // Do not navigate immediately; allow countdown/refresh to complete
        } else {
          console.warn('⚠️ Phone verified but no user data available, redirecting to onboarding for safety');
          navigate('/onboarding', { replace: true });
        }
      } else {
        // Handle verification failure with shake animation
        setOtpShake(true);
        setOtpError(data.message || 'Invalid verification code. Please try again.');
        setTimeout(() => {
          setOtpShake(false);
          if (data.message) {
            setOtp(Array(OTP_LENGTH).fill(''));
            if (otpInputRefs.current[0]) {
              otpInputRefs.current[0].focus();
            }
          }
        }, 500);
      }
      
    } catch (err) {
      setOtpError(err.message || 'Verification failed. Please try again.');
    } finally {
      setVerifyingOtp(false);
    }
  };

  // Handle resend OTP
  const handleResendOTP = async () => {
    if (resendCooldown > 0) return;
    
    setSendingOtp(true);
    setError('');
    setOtpError('');

    try {
      const normalizedPhone = normalizeNZPhone(phone);
      
      const response = await fetch('/api/otp/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          action: 'resend',
          purpose: 'phone_verification',
          mobile: normalizedPhone,
          email: userEmail
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setResendCooldown(60);
      } else {
        throw new Error(data.message);
      }
      
    } catch (err) {
      setOtpError(err.message || 'Failed to resend verification code');
    } finally {
      setSendingOtp(false);
    }
  };

  return (
    <PageWrapper>
      
      <div className="flex mx-auto min-h-[70vh] w-[90vw] sm:w-[80vw] max-w-[600px] flex-col items-center justify-center bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] text-white px-5 sm:px-6 rounded-2xl shadow-2xl my-6 pb-10">
        
        {/* Logo Section */}
        <div className="w-full max-w-[120px] sm:max-w-[150px] mx-auto py-8 sm:py-10">
          <img alt="SpotOn Icon" src={Icon} className="mx-auto h-16 sm:h-20 w-auto" />
        </div>
        
        <div className="w-full max-w-[180px] sm:max-w-xs mx-auto pb-6">
          <img alt="SpotOn Text" src={Text} className="mx-auto h-8 sm:h-10 w-auto" />
        </div>

        <div className="mt-8 w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent mb-4"></div>
        
        {/* Logout button */}
        <div className="w-full max-w-[600px] px-0.5 mx-auto mb-4 flex justify-end">
          <button
            type="button"
            onClick={logout}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-red-600 to-rose-500 hover:from-rose-600 hover:to-red-600 shadow-sm focus:outline-none focus:ring-2 focus:ring-rose-300 dark:focus:ring-rose-500 transition-all duration-200"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>

        {/* Welcome message for social login users */}
        {provider && (
          <div className="text-center mb-8">
            <h2 className="text-xl sm:text-2xl font-semibold text-white tracking-wide">
              Welcome to SpotOn!
            </h2>
            <p className="mt-3 max-w-md mx-auto text-slate-300 text-sm">
              Your {provider} account has been connected.
            </p>
            <p className="max-w-md mx-auto text-slate-300 text-sm">
              We'll send you a verification code to confirm your phone number
            </p>
          </div>
        )}

        <div className="w-full max-w-md mx-auto">
          <div className="relative bg-white/10 backdrop-blur-xl px-5 py-7 sm:px-7 sm:py-8 shadow-2xl rounded-2xl border border-white/20">
            
            <AnimatePresence mode="wait">
              {step === 'phone' ? (
                // Phone Number Entry
                <motion.form
                  key="phone-step"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  onSubmit={handleSendOTP}
                  className="space-y-6"
                >
                <div className="text-center mb-8">
                  <h3 className="text-xl font-semibold text-white mb-2">Verify Your Phone</h3>
                  <p className="text-slate-300 leading-relaxed text-xs">
                    We'll send you a verification code to confirm your phone number
                  </p>
                </div>

                <div className="space-y-4">
                  <label htmlFor="phone" className="block text-xs font-medium text-slate-200 mb-2">
                    Mobile Number
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                      <span className="text-slate-400 text-base font-medium">+64</span>
                    </div>
                    <input
                      id="phone"
                      type="tel"
                      placeholder="21 123 4567"
                      value={phone}
                      onChange={(e) => {
                        setPhone(e.target.value);
                        validatePhone(e.target.value);
                      }}
                      onBlur={(e) => { setPhoneTouched(true); validatePhone(e.target.value); }}
                      className={`block w-full rounded-xl bg-white/10 pl-16 pr-4 py-2.5 text-sm text-white placeholder-slate-400 focus:ring-2 focus:ring-cyan-400 focus:bg-white/20 outline-none border-2 transition-all duration-200 ${
                        phoneTouched && !isPhoneValid ? 'border-red-400 focus:ring-red-400' : 'border-white/30 hover:border-white/50'
                      }`}
                      required
                    />
                  </div>
                  <AnimatePresence>
                    {phoneTouched && !isPhoneValid && phoneError && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-red-400 text-xs mt-2"
                      >
                        {phoneError}
                      </motion.p>
                    )}
                  </AnimatePresence>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Enter your New Zealand mobile number (e.g., 021 123 4567)
                  </p>
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-red-500/10 border border-red-400/30 rounded-xl p-4 text-red-400 text-sm text-center"
                  >
                    {error}
                  </motion.div>
                )}

                <button
                  type="submit"
                  disabled={sendingOtp || !isPhoneValid}
                  className={`w-full text-white font-semibold py-3 px-5 rounded-xl shadow-lg transition-all duration-200 transform active:scale-[0.98] text-sm ${
                    sendingOtp || !isPhoneValid
                      ? 'bg-gray-600 cursor-not-allowed opacity-60'
                      : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 hover:scale-[1.01]'
                  }`}
                >
                  {sendingOtp ? (
                    <motion.div 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center justify-center"
                    >
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                      Sending...
                    </motion.div>
                  ) : (
                    'Send Verification Code'
                  )}
                </button>
                </motion.form>
              ) : (
                // OTP Verification
                <motion.div
                  key="otp-step"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="space-y-6"
                >
                <div className="text-center mb-8">
                  <h3 className="text-xl font-semibold text-white mb-2">Enter Verification Code</h3>
                  <p className="text-slate-300 leading-relaxed">
                    We sent a 6-digit code to <br />
                    <span className="font-bold text-cyan-400">{normalizeNZFromLocalPart(phone).replace(/^(\+64)(\d)/, '$1 $2')}</span>
                  </p>
                </div>

                {!verificationSuccess && (
                <div className="space-y-4">
                  <label className="block text-sm font-semibold text-slate-200 mb-4 text-center">
                    Enter Mobile Verification Code
                  </label>
                  
                  {/* OTP Input Boxes - Exact same as traditional flow */}
                  <div className="flex gap-3 justify-center">
                    {otp.map((digit, index) => (
                      <motion.input
                        key={index}
                        type="text"
                        maxLength="1"
                        value={digit}
                        onChange={(e) => handleOtpChange(index, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(index, e)}
                        ref={(el) => (otpInputRefs.current[index] = el)}
                        whileFocus={{ scale: 1.1 }}
                        disabled={verifyingOtp}
                        className={`w-11 h-11 sm:w-12 sm:h-12 text-center text-lg font-semibold border text-white border-white/30 rounded-xl bg-white/10 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all duration-200 ${
                          otpShake ? SHAKE_CLASS : ''
                        } ${verifyingOtp ? 'opacity-60 cursor-not-allowed' : ''}`}
                        autoComplete="one-time-code"
                        inputMode="numeric"
                        pattern="[0-9]*"
                      />
                    ))}
                  </div>
                  
                  {/* Show verification progress */}
                  <AnimatePresence>
                    {verifyingOtp && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex items-center justify-center text-cyan-400 text-sm"
                      >
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-cyan-400 mr-2"></div>
                        Verifying...
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  <AnimatePresence>
                    {otpError && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 text-sm text-red-400 text-center"
                      >
                        {otpError}
                      </motion.p>
                    )}
                  </AnimatePresence>
                  
                  <p className="text-[11px] text-slate-400 text-center">
                    Enter the 6-digit code sent to your phone
                  </p>
                </div>
                )}

                <AnimatePresence>
                  {verificationSuccess && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8, y: 20 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.8, y: -20 }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                      className="text-center space-y-3 py-6"
                    >
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, duration: 0.3, type: "spring", stiffness: 200 }}
                        className="mx-auto w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-400/40"
                      >
                        <motion.svg
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ delay: 0.4, duration: 0.6 }}
                          width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"
                        >
                          <motion.path
                            d="M20 6L9 17L4 12"
                            stroke="#34d399"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </motion.svg>
                      </motion.div>
                      <motion.h4
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6, duration: 0.3 }}
                        className="text-lg font-semibold text-white"
                      >
                        Phone verified
                      </motion.h4>
                      <motion.p
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8, duration: 0.3 }}
                        className="text-xs text-slate-300"
                      >
                        Finishing setup… Redirecting in {redirectCountdown}s
                      </motion.p>
                      <motion.div
                        initial={{ opacity: 0, scaleX: 0 }}
                        animate={{ opacity: 1, scaleX: 1 }}
                        transition={{ delay: 1.0, duration: 0.4 }}
                        className="mx-auto w-40 h-1 bg-white/10 rounded-full overflow-hidden"
                      >
                        <motion.div
                          className="h-full bg-emerald-400"
                          style={{width: `${(5-redirectCountdown+1)*20}%`}}
                          transition={{ duration: 0.3, ease: "easeInOut" }}
                        />
                      </motion.div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-red-500/10 border border-red-400/30 rounded-xl p-3 text-red-400 text-xs text-center"
                  >
                    {error}
                  </motion.div>
                )}

                {/* Resend and Navigation */}
                <div className="flex flex-col space-y-4 pt-6 border-t border-white/20">
                  {/* Resend only when not already verified */}
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    disabled={verificationSuccess || resendCooldown > 0 || sendingOtp}
                    className="text-xs text-cyan-400 hover:text-cyan-300 disabled:text-slate-500 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {resendCooldown > 0 ? (
                      <span className="flex items-center justify-center">
                        <div className="animate-pulse w-2 h-2 bg-slate-500 rounded-full mr-2"></div>
                        Resend code in {resendCooldown}s
                      </span>
                    ) : (
                      'Resend verification code'
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setStep('phone');
                      setOtp(Array(OTP_LENGTH).fill(''));
                      setOtpError('');
                      setError('');
                      setPhoneError('');
                      setOtpSent(false);
                      setVerificationSuccess(false);
                    }}
                    className="text-xs text-slate-400 hover:text-cyan-300 transition-colors font-medium"
                  >
                    ← Change phone number
                  </button>
                </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}