import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/20/solid';

const OTP_LENGTH = 6;
const SHAKE_CLASS = 'animate-shake';

// Re-create the cn function locally
function cn(...args) {
  return args.filter(Boolean).join(' ');
}

export default function SignupForm({
  formData,
  onInputChange,
  onSubmit,
  onBack,
  isSubmitting,
  isSubmitDisabled,
  errors,
  showPassword,
  showConfirmPassword,
  onTogglePassword,
  onToggleConfirmPassword,
  emailOtpSent,
  mobileOtpSent,
  emailVerified,
  mobileVerified,
  emailOtp,
  mobileOtp,
  emailOtpError,
  mobileOtpError,
  emailOtpShake,
  mobileOtpShake,
  emailResendCountdown,
  mobileResendCountdown,
  onSendOtp,
  onOtpChange,
  onOtpKeyDown,
  emailOtpInputRefs,
  mobileOtpInputRefs,
  isCheckingEmail,
  emailExistsError,
  passwordStrength,
  passwordFieldFocused,
  onPasswordFocus,
  onPasswordBlur,
  onGeneratePassword,
  getPasswordRequirements
}) {
  return (
    <motion.div
      key="signup-form"
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
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.15, ease: "easeOut" }}
      >
        {/* Back Button */}
        <motion.button
          onClick={onBack}
          className="mb-6 flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          whileHover={{ x: -2 }}
          transition={{ type: "spring", stiffness: 500, damping: 25 }}
        >
          <motion.svg 
            className="h-4 w-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
            whileHover={{ x: -2 }}
            transition={{ type: "spring", stiffness: 500, damping: 25 }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
          </motion.svg>
          <span className="text-sm">Back to options</span>
        </motion.button>

        <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }} className="space-y-6">
          {/* Name Fields */}
          <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <div>
              <label htmlFor="firstName" className="px-1 block text-left text-sm font-medium text-slate-300">
                First Name
              </label>
              <input
                type="text"
                id="firstName"
                placeholder="John"
                value={formData.firstName}
                onChange={(e) => onInputChange('firstName', e.target.value)}
                required
                className={`mt-1 block w-full rounded-md bg-white px-3 py-2 text-base text-gray-900 placeholder-gray-400 outline-1 ${
                  formData.firstName ? 'outline-gray-300 focus:outline-primary-turquoise focus:outline-2' : 'outline-red-300 focus:outline-red-600'
                }`}
              />
            </div>
            <div>
              <label htmlFor="lastName" className="px-1 block text-left text-sm font-medium text-slate-300">
                Last Name
              </label>
              <input
                type="text"
                id="lastName"
                placeholder="Doe"
                value={formData.lastName}
                onChange={(e) => onInputChange('lastName', e.target.value)}
                required
                className={`mt-1 block w-full rounded-md bg-white px-3 py-2 text-base text-gray-900 placeholder-gray-400 outline-1 ${
                  formData.lastName ? 'outline-gray-300 focus:outline-primary-turquoise focus:outline-2' : 'outline-red-300 focus:outline-red-600'
                }`}
              />
            </div>
          </div>

          {/* Email Field and Verification */}
          <div className="space-y-4 mt-6">
            <div>
              <label htmlFor="email" className="px-1 text-start block text-sm font-medium text-slate-300 mb-1">
                Email Address
              </label>

              <div className="flex items-start gap-x-3 sm:gap-x-4 w-full">
                {/* Flexible Input */}
                <div className="flex-grow">
                  <input
                    type="email"
                    id="email"
                    value={formData.email}
                    placeholder="johndoe@email.com"
                    onChange={(e) => onInputChange('email', e.target.value)}
                    disabled={emailVerified || emailOtpSent || isCheckingEmail}
                    className={cn(
                      'w-full h-10 rounded-md bg-white py-2 px-3 text-gray-900 text-base placeholder-gray-400 outline-1 sm:text-sm',
                      emailVerified || emailOtpSent ? 'bg-gray-100 cursor-not-allowed' : '',
                      errors.emailError || emailExistsError ? 'outline-red-300 focus:outline-red-600' : 'outline-gray-300 focus:outline-primary-turquoise focus:outline-2'
                    )}
                  />
                  <AnimatePresence mode="wait">
                    {(errors.emailError || emailExistsError) && (
                      <motion.p
                        key="email-error"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="mt-1 text-sm text-red-600 overflow-hidden"
                      >
                        {errors.emailError || emailExistsError}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
                {/* Right-side Button, Badge, or Loader */}
                <div className="shrink-0 align-top flex items-center h-10">
                  <AnimatePresence mode="wait">
                    {isCheckingEmail ? (
                      <motion.div
                        key="email-checking"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-2 text-gray-500"
                      >
                        <svg
                          className="animate-spin h-5 w-5 text-gray-500"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          ></circle>
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0c-4.42 0-8 3.58-8 8z"
                          ></path>
                        </svg>
                        <span className="text-sm">Checking...</span>
                      </motion.div>
                    ) : emailVerified ? (
                      <motion.div
                        key="email-verified"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-1.5 text-green-500"
                      >
                        <CheckCircleIcon className="w-5 h-5" />
                        <span className="font-medium text-sm">Verified</span>
                      </motion.div>
                    ) : (
                      <motion.button
                        key="email-verify-button"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        type="button"
                        onClick={() => onSendOtp('email')}
                        disabled={!formData.email || !!errors.emailError || isCheckingEmail || !!emailExistsError || emailVerified || emailOtpSent}
                        className={`h-10 px-4 rounded-md text-sm font-semibold text-white focus:outline-none transition-colors ${
                          (!formData.email || !!errors.emailError || isCheckingEmail || !!emailExistsError || emailVerified || emailOtpSent)
                            ? 'bg-gray-300 cursor-not-allowed'
                            : 'bg-accent-purple focus:border-2 focus:border-accent-lightturquoise hover:bg-accent-green'
                        }`}
                      >
                        Verify
                      </motion.button>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Email OTP Panel */}
              <AnimatePresence>
                {emailOtpSent && (
                  <motion.div
                    key="email-otp"
                    initial={{ opacity: 0, height: 0, marginTop: 0 }}
                    animate={{ opacity: 1, height: 'auto', marginTop: '0.5rem' }}
                    exit={{ opacity: 0, height: 0, marginTop: 0 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      'rounded-md border border-gray-200 bg-gray-50 px-4 py-3 shadow-sm w-full overflow-hidden',
                      emailOtpShake && SHAKE_CLASS
                    )}
                  >
                    <label className="block text-sm font-medium text-gray-700 mb-4">
                      Enter Email Verification Code
                    </label>
                    <div className="flex gap-2 sm:gap-3 justify-center">
                      {emailOtp.map((digit, index) => (
                        <motion.input
                          key={index}
                          type="text"
                          maxLength="1"
                          value={digit}
                          onChange={(e) => onOtpChange('email', index, e.target.value)}
                          onKeyDown={(e) => onOtpKeyDown('email', index, e)}
                          ref={(el) => (emailOtpInputRefs.current[index] = el)}
                          whileFocus={{ scale: 1.1 }}
                          className="w-9 h-9 sm:w-11 sm:h-11 text-center text-base sm:text-lg font-semibold border text-gray-900 border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-turquoise"
                        />
                      ))}
                    </div>
                    <AnimatePresence mode="wait">
                      {emailOtpError && (
                        <motion.p
                          key="email-otp-error"
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.2 }}
                          className="mt-2 text-sm text-red-600 overflow-hidden"
                        >
                          {emailOtpError}
                        </motion.p>
                      )}
                    </AnimatePresence>
                    <div className="mt-4 flex items-center justify-center">
                      <button
                        type="button"
                        onClick={() => onSendOtp('email')}
                        disabled={!formData.email || emailResendCountdown > 0 || !!emailExistsError}
                        className="text-sm text-accent-red hover:font-bold disabled:text-gray-400 transition-colors"
                      >
                        {emailResendCountdown > 0
                          ? `Resend in ${emailResendCountdown}s`
                          : 'Resend Code'}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Mobile Field and Verification */}
            <div className="space-y-4">
              <label htmlFor="mobile" className="px-1 text-start block text-sm font-medium text-slate-300 mb-1">
                Mobile Number
              </label>
              <div className="flex items-start gap-x-3 sm:gap-x-4 w-full">
                {/* Flexible Input */}
                <div className="flex-grow">
                  <input
                    type="tel"
                    id="mobile"
                    value={formData.mobile}
                    onChange={(e) => onInputChange('mobile', e.target.value)}
                    disabled={mobileVerified || mobileOtpSent}
                    className={cn(
                      'w-full h-10 rounded-md bg-white py-2 px-3 text-gray-900 text-base placeholder-gray-400 outline-1 sm:text-sm',
                      mobileVerified || mobileOtpSent ? 'bg-gray-100 cursor-not-allowed' : '',
                      errors.mobileError ? 'outline-red-300 focus:outline-red-600' : 'outline-gray-300 focus:outline-primary-turquoise focus:outline-2'
                    )}
                  />
                  <AnimatePresence mode="wait">
                    {errors.mobileError && (
                      <motion.p
                        key="mobile-error"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="mt-1 text-sm text-red-600 overflow-hidden"
                      >
                        {errors.mobileError}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
                {/* Right-side Button or Badge */}
                <div className="shrink-0 align-top flex items-center h-10">
                  <AnimatePresence mode="wait">
                    {mobileVerified ? (
                      <motion.div
                        key="mobile-verified"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex items-center gap-1.5 text-green-500"
                      >
                        <CheckCircleIcon className="w-5 h-5" />
                        <span className="font-medium text-sm">Verified</span>
                      </motion.div>
                    ) : (
                      <motion.button
                        key="mobile-verify-button"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        type="button"
                        onClick={() => onSendOtp('mobile')}
                        disabled={!formData.mobile || !!errors.mobileError || mobileVerified || mobileOtpSent}
                        className={`h-10 px-4 rounded-md text-sm font-semibold text-white focus:outline-none transition-colors ${
                          (!formData.mobile || !!errors.mobileError || mobileVerified || mobileOtpSent)
                            ? 'bg-gray-300 cursor-not-allowed'
                            : 'bg-accent-purple focus:border-2 focus:border-accent-lightturquoise hover:bg-accent-green'
                        }`}
                      >
                        Verify
                      </motion.button>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Mobile OTP Panel */}
              <AnimatePresence>
                {mobileOtpSent && (
                  <motion.div
                    key="mobile-otp"
                    initial={{ opacity: 0, height: 0, marginTop: 0 }}
                    animate={{ opacity: 1, height: 'auto', marginTop: '0.5rem' }}
                    exit={{ opacity: 0, height: 0, marginTop: 0 }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      'rounded-md border border-gray-200 bg-gray-50 px-4 py-3 shadow-sm w-full overflow-hidden',
                      mobileOtpShake && SHAKE_CLASS,
                      'mt-4'
                    )}
                  >
                    <label className="block text-sm font-medium text-gray-700 mb-4">
                      Enter Mobile Verification Code
                    </label>
                    <div className="flex gap-2 sm:gap-3 justify-center">
                      {mobileOtp.map((digit, index) => (
                        <motion.input
                          key={index}
                          type="text"
                          maxLength="1"
                          value={digit}
                          onChange={(e) => onOtpChange('mobile', index, e.target.value)}
                          onKeyDown={(e) => onOtpKeyDown('mobile', index, e)}
                          ref={(el) => (mobileOtpInputRefs.current[index] = el)}
                          whileFocus={{ scale: 1.1 }}
                          className="w-9 h-9 sm:w-11 sm:h-11 text-center text-base sm:text-lg font-semibold border text-gray-900 border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-turquoise"
                        />
                      ))}
                    </div>
                    <AnimatePresence mode="wait">
                      {mobileOtpError && (
                        <motion.p
                          key="mobile-otp-error"
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.2 }}
                          className="mt-2 text-sm text-red-600 overflow-hidden"
                        >
                          {mobileOtpError}
                        </motion.p>
                      )}
                    </AnimatePresence>
                    <div className="mt-4 flex items-center justify-center">
                      <button
                        type="button"
                        onClick={() => onSendOtp('mobile')}
                        disabled={!formData.mobile || mobileResendCountdown > 0}
                        className="text-sm text-accent-red hover:font-bold disabled:text-gray-400 transition-colors"
                      >
                        {mobileResendCountdown > 0
                          ? `Resend in ${mobileResendCountdown}s`
                          : 'Resend Code'}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="px-1 text-left block text-sm font-medium text-slate-300">
                  Create a password
                </label>
                <button
                  type="button"
                  onClick={onGeneratePassword}
                  className="text-xs text-primary-turquoise hover:text-accent-blue transition-colors"
                >
                  Generate Strong Password
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={formData.password}
                  onChange={(e) => onInputChange('password', e.target.value)}
                  onFocus={onPasswordFocus}
                  onBlur={onPasswordBlur}
                  className={cn(
                    'mt-1 block w-full rounded-md px-3 py-2 pr-10 text-base text-gray-900 bg-white placeholder-gray-400 outline-1 sm:text-base',
                    errors.passwordError ? 'outline-red-300 focus:outline-red-600' : 'outline-gray-300 focus:outline-primary-turquoise focus:outline-2'
                  )}
                />
                <button
                  type="button"
                  onClick={onTogglePassword}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              
              {/* Password Strength Indicator */}
              <AnimatePresence mode="wait">
                {formData.password && (passwordFieldFocused || passwordStrength < 5) && (
                  <motion.div
                    key="password-strength"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-2 space-y-2 overflow-hidden"
                  >
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={cn(
                            'h-2 rounded-full transition-all duration-300',
                            passwordStrength <= 1 ? 'bg-red-500' :
                            passwordStrength <= 2 ? 'bg-yellow-500' :
                            passwordStrength <= 3 ? 'bg-blue-500' :
                            passwordStrength <= 4 ? 'bg-green-500' :
                            'bg-green-600'
                          )}
                          style={{ width: `${(passwordStrength / 5) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">
                        {passwordStrength <= 1 ? 'Weak' :
                         passwordStrength <= 2 ? 'Fair' :
                         passwordStrength <= 3 ? 'Good' :
                         passwordStrength <= 4 ? 'Strong' :
                         'Very Strong'}
                      </span>
                    </div>
                    
                    {/* Requirements checklist */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-xs">
                      {getPasswordRequirements(formData.password).map((req, index) => (
                        <div
                          key={index}
                          className={cn(
                            'flex items-center gap-1.5 transition-colors',
                            req.met ? 'text-green-600' : 'text-gray-500'
                          )}
                        >
                          <span className={cn(
                            'w-4 h-4 rounded-full flex items-center justify-center text-xs font-mono',
                            req.met ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                          )}>
                            {req.icon}
                          </span>
                          <span>{req.label}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              
              <AnimatePresence mode="wait">
                {errors.passwordError && (
                  <motion.p
                    key="password-error"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-1 text-sm text-red-600 overflow-hidden"
                  >
                    {errors.passwordError}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="px-1 text-left block text-sm font-medium text-slate-300">
                Confirm your password
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  id="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={(e) => onInputChange('confirmPassword', e.target.value)}
                  className={cn(
                    'mt-1 block w-full rounded-md px-3 py-2 pr-10 text-base text-gray-900 bg-white placeholder-gray-400 outline-1 sm:text-base',
                    errors.confirmPasswordError ? 'outline-red-300 focus:outline-red-600' : 'outline-gray-300 focus:outline-primary-turquoise focus:outline-2'
                  )}
                />
                <button
                  type="button"
                  onClick={onToggleConfirmPassword}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                >
                  {showConfirmPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              
              {/* Passwords Match Indicator */}
              <AnimatePresence mode="wait">
                {formData.confirmPassword && formData.password && formData.confirmPassword === formData.password && !errors.confirmPasswordError && (
                  <motion.div
                    key="passwords-match"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-2 flex items-center gap-2 text-green-600 overflow-hidden"
                  >
                    <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center">
                      <span className="text-xs font-mono">✓</span>
                    </div>
                    <span className="text-sm">Passwords match</span>
                  </motion.div>
                )}
              </AnimatePresence>
              
              <AnimatePresence mode="wait">
                {errors.confirmPasswordError && (
                  <motion.p
                    key="confirm-password-error"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-1 text-sm text-red-600 overflow-hidden"
                  >
                    {errors.confirmPasswordError}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* Submit Error */}
            <AnimatePresence mode="wait">
              {errors.submitError && (
                <motion.p
                  key="submit-error"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="text-red-600 text-sm overflow-hidden"
                >
                  {errors.submitError}
                </motion.p>
              )}
            </AnimatePresence>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitDisabled || isSubmitting}
              className={`w-full flex justify-center rounded-md px-3 py-2 text-sm font-semibold text-white focus:outline-none transition-colors ${
                isSubmitDisabled || isSubmitting
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-accent-purple hover:bg-accent-green'
              }`}
            >
              {isSubmitting ? 'Creating account...' : 'Create Account'}
            </button>

            {/* Link to Login */}
            <div className="text-center text-sm text-gray-500 mt-4">
              Already have an account?{' '}
              <a href="/login" className="font-semibold leading-6 text-primary-turquoise hover:text-accent-green">
                Login
              </a>
            </div>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
} 