// src/App.js
import React from 'react';
import { Routes, Route, Navigate, useLocation, matchPath } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import PropTypes from 'prop-types';
import './index.css';

// Contexts & Hooks
import { useAuth } from './hooks/useAuth';
import { useLoader } from './context/LoaderContext';
import { TenantProvider } from './context/TenantContext';

// Components
import Loader from './components/Loader';
import ScrollToTop from './components/ScrollToTop';
import { AccessibilityProvider } from './components/accessibility/AccessibilityProvider';
import { SkipLinks } from './components/accessibility/SkipLink';
import { ToastProvider } from './components/feedback/Toast';
import ErrorBoundary from './components/content/ErrorBoundary';

// Environment utilities
import { getEnvUrl } from './utils/environment';

// Public Pages - Login and OAuth
const Login = lazy(() => import('./pages/user/Login.jsx'));
const OAuthCallback = lazy(() => import('./pages/auth/OAuthCallback.jsx'));
const VerifyPhone = lazy(() => import('./pages/auth/VerifyPhone.jsx'));

// Lazy-loaded Authenticated Pages - Only authenticated routes
const Home = lazy(() => import('./pages/authenticated/Home.jsx'));
const DashboardContentPage = lazy(() => import('./pages/authenticated/Dashboard.jsx'));
const PowerContentPage = lazy(() => import('./pages/authenticated/Power.jsx'));
const BroadbandContentPage = lazy(() => import('./pages/authenticated/Broadband.jsx'));
const MobileContentPage = lazy(() => import('./pages/authenticated/Mobile.jsx'));
const BillingContentPage = lazy(() => import('./pages/authenticated/Billing.jsx'));
const ProfileContentPage = lazy(() => import('./pages/authenticated/Profile.jsx'));
const DashboardSupportPage = lazy(() => import('./pages/authenticated/Support.jsx'));

// Import the Onboarding Page component
const OnboardingPage = lazy(() => import('./pages/user/Onboarding.jsx'));

// PrivateRoute component - protects authenticated routes and enforces user flow
function PrivateRoute({ children }) {
  const { isAuthenticated, loading, initialCheckComplete, user } = useAuth();
  const location = useLocation();
  
  // Debug logging
  console.log('🔒 PrivateRoute check:', {
    path: location.pathname,
    isAuthenticated,
    loading,
    initialCheckComplete,
    registration_method: user?.registration_method,
    phone_verified: user?.phone_verified,
    mobile_verified: user?.mobile_verified,
    is_onboarding_complete: user?.is_onboarding_complete,
    user_exists: !!user
  });
  
  // Show loader while initial auth check is in progress
  if (!initialCheckComplete || loading) {
    console.log('🔒 PrivateRoute: Showing loader');
    return <Loader fullscreen />;
  }
  
  if (!isAuthenticated) {
    console.log('🔒 PrivateRoute: Not authenticated, redirecting to login');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  // Enforce phone verification ONLY for social users with unverified mobile
  const isSocialUser = user?.registration_method === 'social' || !!user?.social_provider;
  
  // Use normalized mobile_verified field, fallback to legacy phone_verified
  const mobileVerified = user?.mobile_verified !== undefined ? user?.mobile_verified : user?.phone_verified;
  
  // Only social users need phone verification, and only if mobile is not verified
  const needsPhoneVerification = isSocialUser && !mobileVerified;
  
  if (needsPhoneVerification) {
    if (location.pathname !== '/auth/verify-phone') {
      console.log('🔒 PrivateRoute: User needs phone verification, redirecting to verify-phone');
      return <Navigate to="/auth/verify-phone" replace />;
    }
    // If we are on the verify-phone page, allow it
    console.log('🔒 PrivateRoute: On verify-phone page, allowing access.');
    return children;
  }
  
  // If mobile is verified OR user doesn't need phone verification, redirect away from verify-phone
  if ((mobileVerified || !needsPhoneVerification) && location.pathname === '/auth/verify-phone') {
    console.log('🔒 PrivateRoute: Phone already verified or verification not needed, redirecting from verify-phone to onboarding/dashboard');
    return <Navigate to="/onboarding" replace />; // Onboarding will handle redirect to dashboard if complete
  }

  // Enforce onboarding completion (except on onboarding page itself)
  const isOnboardingComplete = user?.is_onboarding_complete ?? user?.onboarding_complete ?? false;
  if (!isOnboardingComplete && location.pathname !== '/onboarding') {
    console.log('🔒 PrivateRoute: Onboarding not complete, redirecting to onboarding');
    return <Navigate to="/onboarding" replace />;
  }
  
  // Redirect away from onboarding if already complete
  if (isOnboardingComplete && location.pathname === '/onboarding') {
    console.log('🔒 PrivateRoute: Onboarding complete, redirecting to dashboard');
    return <Navigate to="/" replace />;
  }
  
  console.log('🔒 PrivateRoute: All checks passed, rendering children');
  return (
    <TenantProvider>
      {children}
    </TenantProvider>
  );
}

PrivateRoute.propTypes = {
  children: PropTypes.node.isRequired,
};

// Phone verification is now handled globally by PrivateRoute
// No need for separate PhoneVerifiedRoute component

function App() {
  const location = useLocation();
  const { loading: globalLoading, loadingMessage, loadingProgress } = useLoader();

  // Debug logging for route changes
  console.log('🌐 App route changed to:', location.pathname, location.state);

  return (
    <ErrorBoundary>
      <AccessibilityProvider>
        <ToastProvider position="top-right">
          <div className="app-container">
            <SkipLinks />
            {globalLoading && (
              <Loader 
                fullscreen 
                message={loadingMessage}
                progress={loadingProgress}
                showProgress={loadingProgress > 0}
              />
            )}
            <ScrollToTop />

            <TenantProvider>
              <main id="main-content" className="main-content">
                <Suspense fallback={<Loader fullscreen />}>
                  <Routes>
            {/* Health check route - public */}
            <Route 
              path="/health" 
              element={
                <div style={{ padding: '20px', textAlign: 'center' }}>
                  <h1>SpotOn Customer Portal</h1>
                  <p>Service is running</p>
                  <p>Status: OK</p>
                </div>
              } 
            />

            {/* Portal Login Route */}
            <Route path="/login" element={<Login />} />
            
            {/* OAuth Callback Routes */}
            <Route path="/auth/callback" element={<OAuthCallback />} />
            <Route path="/auth/verify-phone" element={<VerifyPhone />} />
            
            {/* Root Route - Redirect to login if not authenticated, otherwise to dashboard */}
            <Route 
              path="/" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<DashboardContentPage />} />
            </Route>
            
            <Route 
              path="/power" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<PowerContentPage />} />
            </Route>
            
            <Route 
              path="/broadband" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<BroadbandContentPage />} />
            </Route>
            
            <Route 
              path="/mobile" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<MobileContentPage />} />
            </Route>
            
            <Route 
              path="/billing" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<BillingContentPage />} />
            </Route>
            
            <Route 
              path="/profile" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<ProfileContentPage />} />
            </Route>
            
            <Route 
              path="/support" 
              element={
                <PrivateRoute>
                  <Home />
                </PrivateRoute>
              } 
            >
              <Route index element={<DashboardSupportPage />} />
            </Route>

            {/* Onboarding Route */}
            <Route 
              path="/onboarding" 
              element={
                <PrivateRoute>
                  <OnboardingPage />
                </PrivateRoute>
              } 
            />

            {/* Legacy routes without /authenticated prefix - redirect to new structure */}
            <Route path="/home" element={<Navigate to="/" replace />} />
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
            <Route path="/power" element={<Navigate to="/power" replace />} />
            <Route path="/broadband" element={<Navigate to="/broadband" replace />} />
            <Route path="/mobile" element={<Navigate to="/mobile" replace />} />
            <Route path="/billing" element={<Navigate to="/billing" replace />} />
            <Route path="/profile" element={<Navigate to="/profile" replace />} />
            <Route path="/support" element={<Navigate to="/support" replace />} />
            <Route path="/onboarding" element={<Navigate to="/onboarding" replace />} />

            {/* Redirect any non-authenticated routes to main web app */}
            <Route path="/user/*" element={<Navigate to={`${getEnvUrl('web')}${location.pathname}`} replace />} />
            <Route path="/staff/*" element={<Navigate to={`${getEnvUrl('staff')}${location.pathname}`} replace />} />
            <Route path="/getstarted" element={<Navigate to={`${getEnvUrl('web')}/getstarted`} replace />} />
            <Route path="/createaccount" element={<Navigate to={`${getEnvUrl('web')}/createaccount`} replace />} />
            <Route path="/legal/*" element={<Navigate to={`${getEnvUrl('web')}${location.pathname}`} replace />} />

            {/* Catch-all - redirect to authenticated dashboard or web app */}
            <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </Suspense>
              </main>
            </TenantProvider>
          </div>
        </ToastProvider>
      </AccessibilityProvider>
    </ErrorBoundary>
  );
}

export default App; // Trigger build 2