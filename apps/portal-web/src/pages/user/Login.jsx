import { useState, useEffect } from 'react';
import { useLoader } from '../../context/LoaderContext';
import Loader from '../../components/Loader';
import { ExclamationCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/16/solid'; // Or use /20/solid or /24/solid for different sizes
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import PageWrapper from '../../components/PageWrapper';
import Icon from '../../assets/utilitycopilot-icon.webp';
import Text from '../../assets/spoton-text-reversed.webp';
import { useEmailValidation } from '../../hooks/useEmailValidation';
import { getEnvUrl } from '../../utils/environment';
import { motion, AnimatePresence } from 'framer-motion';

export default function Login() {
  // --- Existing state and hooks ---
  const { login, isAuthenticated, user, loginWithSocial } = useAuth(); // <-- Get the user object here
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { status: emailStatus } = useEmailValidation(email);
  const { loading, setLoading } = useLoader();
  const [loaderMessage, setLoaderMessage] = useState('Loading...');
  
  // Environment badge removed per request
  
  // Method selection state
  const [showMethodSelection, setShowMethodSelection] = useState(true);
  const [selectedMethod, setSelectedMethod] = useState('');

  // Check for account exists message from OAuth callback
  const [accountExistsMessage, setAccountExistsMessage] = useState('');
  
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    const email = urlParams.get('email');
    
    if (message === 'account_exists' && email) {
      setAccountExistsMessage(`An account with email ${email} already exists. Please sign in below.`);
      setEmail(email);
      setShowMethodSelection(false); // Automatically show email form
      setSelectedMethod('email');
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // --- MODIFIED useEffect ---
  useEffect(() => {
    // Check if authenticated AND the user object is available
    // The user object will contain is_onboarding_complete
    if (isAuthenticated && user) {
      // Defer routing decisions to AuthContext/ProtectedRoute to avoid race conditions
      setLoaderMessage('Redirecting...');
      setLoading(false);
    } else if (isAuthenticated === false) {
      // If explicitly not authenticated, make sure loader is off
      setLoading(false);
    }
    // Note: If !isAuthenticated, this useEffect won't trigger the navigation logic.
    // The checkAuthStatus in AuthProvider handles initial load and redirects if needed.
    // Also, the render logic below prevents showing the form if isAuthenticated is true.

  }, [isAuthenticated, user, setLoading]);

  // Redirect authenticated users to dashboard
  if (isAuthenticated && user) {
    return <Navigate to="/" replace />;
  }

  // --- Rest of your component code remains the same ---

  const handleEmailInputChange = (e) => {
    const value = e.target.value;
    setEmail(value);
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    setEmailError(value && !emailPattern.test(value) ? 'Please enter a valid email address.' : '');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailPattern.test(email)) {
      setEmailError('Please enter a valid email address.');
      return;
    }
    if (!password) {
      setPasswordError('Please enter your password.');
      return;
    }
    // You might want to refine this check - maybe allow submission if status is 'checking'
    if (emailError || ['not_found', 'inactive', 'invalid'].includes(emailStatus)) {
      return;
    }

    setLoaderMessage('Signing in...');
    setLoading(true);
    try {
      // The login function updates the AuthContext state (isAuthenticated and user)
      const response = await login({ email, password });

      if (!response?.success) {
        setLoading(false); // Stop loader only on login failure
        setPasswordError(response?.message || 'Invalid email or password.');
      } else if (response.redirect) {
        // Keep loading state during Keycloak redirect
        setLoaderMessage('Redirecting to authentication...');
        // Don't set loading to false - let the redirect happen
      }
      // If login is successful, the useEffect above will be triggered by the change
      // in isAuthenticated and user state, and it will handle the redirection and
      // potentially keeping the loader visible during the transition.

    } catch {
      setLoading(false);
      setPasswordError('Login failed. Please try again.');
    }
  };

  

  const renderEmailStatusMessage = () => {
    switch (emailStatus) {
      case 'not_found':
        return (
          <p className="mt-2 text-sm text-red-500">
            No account found.{' '}
            <Link to="/getstarted" className="text-cyan-400 hover:underline">
              Get Started
            </Link>
          </p>
        );
      case 'inactive':
        return <p className="mt-2 text-sm text-red-500">Account not activated. Please verify your email.</p>;
      case 'invalid':
        return <p className="mt-2 text-sm text-red-500">Error verifying email. Please try again.</p>;
      default:
        return null;
    }
  };

  // Method selection handlers
  const handleMethodSelection = (method) => {
    setSelectedMethod(method);
    if (method === 'email') {
      setShowMethodSelection(false);
    } else if (method === 'google') {
      // Handle social login
      setLoaderMessage('Redirecting to Google...');
      setLoading(true);
      loginWithSocial('google');
    }
  };

  const handleBackToMethodSelection = () => {
    setShowMethodSelection(true);
    setSelectedMethod('');
    setEmail('');
    setPassword('');
    setEmailError('');
    setPasswordError('');
  };

  const redirectToWebsite = () => {
    const websiteUrl = getEnvUrl('web');
    window.location.href = websiteUrl;
  };

  return (
    <PageWrapper>
      {/* Standard Loader will show based on 'loading' state from useLoader */}
      {loading && <Loader fullscreen size="xl" />}

      {/* Only render the form/login UI if NOT currently authenticated */}
      {/* This prevents a brief flash of the login form while waiting for the useEffect redirect */}
      {!isAuthenticated && (
         <AnimatePresence mode="wait">
            <motion.div
              key="login-form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5, ease: 'easeInOut' }}
              className="flex mx-auto min-h-[60vh] w-[90vw] sm:w-[80vw] max-w-[600px] flex-col items-center justify-center bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] text-white px-4 sm:px-6 rounded-xl shadow-xl my-8"
            >
              {/* Icon container */}
              <div className="w-full max-w-[120px] sm:max-w-[150px] mx-auto py-6 sm:py-8">
                <div className="mx-auto">
                  <img alt="SpotOn Icon" src={Icon} className="mx-auto h-16 sm:h-20 w-auto" />
                </div>
              </div>

              {/* Text logo container */}
              <div className="w-full max-w-[180px] sm:max-w-xs mx-auto pb-4 sm:pb-2">
                <div className="mx-auto">
                  <img alt="SpotOn Text" src={Text} className="mx-auto h-8 sm:h-10 w-auto" />
                </div>
              </div>
              <div className="mt-10 w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-8"></div>
              <h2 className="mt-4 text-center text-xl sm:text-2xl font-semibold text-slate-300 tracking-wide">
                {showMethodSelection ? 'Welcome back' : 'Sign in to Your Account'}
              </h2>
              
              {/* Account exists message */}
              {accountExistsMessage && (
                <div className="mt-4 w-full max-w-sm mx-auto">
                  <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3">
                    <div className="flex items-center">
                      <ExclamationCircleIcon className="h-5 w-5 text-orange-400 mr-2 flex-shrink-0" />
                      <p className="text-sm text-orange-200">{accountExistsMessage}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {showMethodSelection && (
                <p className="mt-2 text-center text-sm text-slate-400">Sign in securely with Google or email</p>
              )}

              {!showMethodSelection && (
                <div className="w-full max-w-xs sm:max-w-sm md:max-w-md mx-auto mt-6 mb-6">
                  <div className="relative bg-white/10 backdrop-blur-lg px-4 py-5 sm:px-6 sm:py-6 md:px-8 md:py-8 shadow-xl rounded-xl sm:rounded-2xl border border-white/10 transition-all">
                    <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-6">
                      <div className="relative">
                        <label htmlFor="email" className="sr-only">Email</label>
                        <input
                          id="email"
                          type="email"
                          placeholder="Email"
                          autoComplete="email"
                          value={email}
                          onChange={handleEmailInputChange}
                          className={`block w-full rounded-md bg-white/80 py-2 sm:py-1.5 pr-10 pl-3 text-sm sm:text-base text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-cyan-400 outline-none ${
                            emailError || ['not_found', 'inactive', 'invalid'].includes(emailStatus)
                              ? 'ring-1 ring-red-400 focus:ring-red-500'
                              : 'ring-1 ring-inset ring-gray-300 focus:ring-cyan-400'
                          }`}
                        />
                        {(emailError || ['not_found', 'inactive', 'invalid'].includes(emailStatus)) && (
                          <ExclamationCircleIcon aria-hidden="true" className="absolute right-2 top-1/2 -translate-y-5.5 h-5 w-5 text-red-500" />
                        )}
                        {emailError && <p className="mt-1.5 text-xs sm:text-sm text-red-500">{emailError}</p>}
                        {renderEmailStatusMessage()}
                      </div>

                      <div className="relative">
                        <label htmlFor="password" className="sr-only">Password</label>
                        <input
                          id="password"
                          type={showPassword ? "text" : "password"}
                          autoComplete="current-password"
                          placeholder="Password"
                          value={password}
                          onChange={(e) => {
                            setPassword(e.target.value);
                            setPasswordError('');
                          }}
                          className={`block w-full rounded-md bg-white/80 px-3 py-2 sm:py-1.5 text-sm sm:text-base text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-cyan-400 outline-none ${
                            passwordError ? 'ring-1 ring-red-400 focus:ring-red-500 pr-10' : 'ring-1 ring-inset ring-gray-300 focus:ring-cyan-400 pr-10'
                          }`}
                        />
                        <div className="absolute inset-y-0 right-0 flex items-center">
                          {!passwordError ? (
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className="h-full px-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                            >
                              {showPassword ? (
                                <EyeSlashIcon className="h-4 w-4" />
                              ) : (
                                <EyeIcon className="h-4 w-4" />
                              )}
                            </button>
                          ) : (
                            <div className="h-full px-3 flex items-center">
                              <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
                            </div>
                          )}
                        </div>
                        {passwordError && <p className="mt-1.5 text-xs sm:text-sm text-red-500">{passwordError}</p>}
                      </div>

                      <div className="text-left">
                        <Link
                          to="/forgotpassword"
                          className="text-xs sm:text-sm text-slate-400 hover:text-cyan-300 hover:font-medium"
                        >
                          Forgot Password?
                        </Link>
                      </div>

                      <div>
                        <button
                          type="submit"
                          disabled={
                            Boolean(loading || emailError || passwordError || ['not_found', 'inactive', 'invalid'].includes(emailStatus))
                          }
                          className={`flex w-full justify-center items-center rounded-md px-4 py-2.5 text-sm font-semibold text-white shadow-md transition-all ${
                            loading || emailError || passwordError || ['not_found', 'inactive', 'invalid'].includes(emailStatus)
                              ? 'bg-gray-500 cursor-not-allowed'
                              : 'bg-accent-purple hover:bg-accent-green focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-turquoise'
                          }`}
                        >
                          {loading ? loaderMessage : 'Sign In'}
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}

              {/* Method selection */}
              {showMethodSelection && (
                <div className="w-full max-w-xs sm:max-w-sm md:max-w-md mx-auto mt-4 mb-6">
                  <div className="relative bg-white/10 backdrop-blur-lg px-4 py-5 sm:px-6 sm:py-6 md:px-8 md:py-8 shadow-xl rounded-xl sm:rounded-2xl border border-white/10">
                    <div className="space-y-3">
                      <button
                        type="button"
                        onClick={() => handleMethodSelection('google')}
                        disabled={loading}
                        className={`group relative flex h-11 items-center justify-center gap-3 w-full rounded-lg bg-white text-gray-900 border border-white/10 shadow-sm hover:shadow transition-all ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
                        title="Sign in with Google"
                      >
                        <svg className="h-5 w-5" viewBox="0 0 24 24">
                          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        <span className="text-sm font-semibold">Sign in with Google</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMethodSelection('email')}
                        className="group relative w-full rounded-lg h-11 border border-white/20 text-slate-200 hover:text-white bg-transparent hover:bg-white/5 transition-colors"
                      >
                        <div className="flex items-center justify-center gap-2">
                          <svg className="h-4 w-4 text-slate-300 group-hover:text-slate-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                          </svg>
                          <span className="text-sm font-medium">Sign in with Email</span>
                        </div>
                      </button>
                      <p className="text-[11px] text-center text-slate-300/80">We never see your Google password.</p>
                    </div>
                  </div>
                </div>
              )}

              <footer className="w-full py-4 sm:py-6 text-center">
                <div className="mb-3">
                  <button
                    onClick={showMethodSelection ? redirectToWebsite : handleBackToMethodSelection}
                    className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm text-cyan-200 hover:text-white hover:bg-white/20 ring-1 ring-white/20 hover:ring-white/30 shadow-md hover:shadow-lg transition-all duration-300 transform hover:scale-105 active:scale-95"
                  >
                    <svg className="h-4 w-4 -ml-0.5 transition-transform duration-300 group-hover:-translate-x-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M15 18l-6-6 6-6" />
                    </svg>
                    <span className="text-[11px] sm:text-xs font-semibold tracking-wide">
                      {showMethodSelection ? 'Back to Website' : 'Back to Options'}
                    </span>
                  </button>
                </div>
                <p className="text-[10px] sm:text-xs text-slate-400/90">&copy; {new Date().getFullYear()} SpotOn. All rights reserved.</p>
              </footer>
            </motion.div>
         </AnimatePresence>
      )}
    </PageWrapper>
  );
}