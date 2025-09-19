// src/App.js
import React from 'react';
import { Routes, Route, Navigate, useLocation, matchPath } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import PropTypes from 'prop-types';
import './index.css';

// Contexts & Hooks
import { useAuth } from './hooks/useAuth';
import { useLoader } from './context/LoaderContext';

// Components
import Loader from './components/Loader';
import ScrollToTop from './components/ScrollToTop';
import Header from './components/global/Header.jsx';
import Footer from './components/global/Footer.jsx';

// Environment utilities
import { getEnvUrl } from './utils/environment';

// Lazy-loaded Public Pages
const Home = lazy(() => import('./pages/Home.jsx'));
const PowerServicePage = lazy(() => import('./pages/services/Power.jsx'));
const BroadbandServicePage = lazy(() => import('./pages/services/Broadband.jsx'));
const MobileServicePage = lazy(() => import('./pages/services/Mobile.jsx'));
const SupportLandingPage = lazy(() => import('./pages/support/index.jsx'));

// Public Marketing Pages - Customer onboarding flow
const GetStarted = lazy(() => import('./pages/user/GetStarted.jsx'));
const CreateAccount = lazy(() => import('./pages/user/CreateAccount.jsx'));

// Legal Pages - Public
const TermsofService = lazy(() => import('./pages/legal/TermsOfService.jsx'));
const PrivacyPolicy = lazy(() => import('./pages/legal/PrivacyPolicy.jsx'));
const ConsumerCarePolicy = lazy(() => import('./pages/legal/ConsumerCarePolicy.jsx'));
const PowerTerms = lazy(() => import('./pages/legal/PowerTerms.jsx'));
const BroadbandTerms = lazy(() => import('./pages/legal/BroadbandTerms.jsx'));
const MobileTerms = lazy(() => import('./pages/legal/MobileTerms.jsx'));
const ServicePromise = lazy(() => import('./pages/legal/ServicePromise.jsx'));

// Support Pages - Public
const GeneralSupport = lazy(() => import('./pages/support/general/index.jsx'));
const BillingSupport = lazy(() => import('./pages/support/billing/index.jsx'));
const TechnicalSupport = lazy(() => import('./pages/support/technical/index.jsx'));
const ContactSupport = lazy(() => import('./pages/support/contact/index.jsx'));
const MobileSupport = lazy(() => import('./pages/support/mobile/index.jsx'));

// Redirect components for customer portal and staff portal routes
function PortalRedirect({ path = '/' }) {
  React.useEffect(() => {
    window.location.href = `${getEnvUrl('portal')}${path}`;
  }, [path]);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader fullscreen />
      <div className="text-center">Redirecting to customer portal...</div>
    </div>
  );
}

// Login redirect - customers should login via portal
function LoginRedirect() {
  React.useEffect(() => {
    window.location.href = `${getEnvUrl('portal')}/login`;
  }, []);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader fullscreen />
      <div className="text-center">Redirecting to secure login...</div>
    </div>
  );
}

function StaffRedirect({ path = '/' }) {
  React.useEffect(() => {
    window.location.href = `${getEnvUrl('staff')}${path}`;
  }, [path]);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader fullscreen />
      <div className="text-center">Redirecting to staff portal...</div>
    </div>
  );
}

// Component to handle post-login redirects
function PostLoginRedirect() {
  const { isAuthenticated, user, loading } = useAuth();
  
  if (loading) return <Loader fullscreen />;
  
  if (isAuthenticated && user) {
    if (user.is_staff) {
      return <StaffRedirect />;
    } else {
      return <PortalRedirect />;
    }
  }
  
  // If not authenticated, redirect to login
  return <Navigate to="/login" replace />;
}

function App() {
  const location = useLocation();
  const { loading: globalLoading } = useLoader();

  const excludedPatterns = [
    '/getstarted',
    '/createaccount'
  ];

  // Updated check: Use start: true for exact match on base paths,
  // and end: false for paths that might have sub-paths.
  const isExcludedPath = excludedPatterns.some(pattern =>
    matchPath({ path: pattern, end: pattern === '/getstarted' || pattern === '/login' }, location.pathname)
  );

  return (
    <div className="app-container">
      {globalLoading && <Loader fullscreen />}
      <ScrollToTop />
      {/* Conditionally render Header and Footer */}
      {!isExcludedPath && <Header />}

      <main className="main-content">
        <Suspense fallback={<Loader fullscreen />}>
          <Routes>
            {/* Health check route - public */}
            <Route 
              path="/health" 
              element={
                <div style={{ padding: '20px', textAlign: 'center' }}>
                  <h1>SpotOn Website</h1>
                  <p>Service is running</p>
                  <p>Status: OK</p>
                </div>
              } 
            />

            {/* Public Pages */}
            <Route path="/" element={<Home />} />
            <Route path="/power" element={<PowerServicePage />} />
            <Route path="/broadband" element={<BroadbandServicePage />} />
            <Route path="/mobile" element={<MobileServicePage/>} />

            {/* Public Marketing Pages - Customer onboarding flow */}
            <Route path="/getstarted" element={<GetStarted />} />
            <Route path="/createaccount" element={<CreateAccount />} />

            {/* Login redirects - customers login via portal */}
            <Route path="/login" element={<LoginRedirect />} />
            <Route path="/forgotpassword" element={<LoginRedirect />} />
            <Route path="/resetpassword/:uidb64/:token" element={<LoginRedirect />} />

            {/* Legal Pages */}
            <Route path="/legal/termsofservice" element={<TermsofService />} />
            <Route path="/legal/privacypolicy" element={<PrivacyPolicy />} />
            <Route path="/legal/consumercarepolicy" element={<ConsumerCarePolicy />} />
            {/* Power and Mobile terms disabled - services not yet available */}
            {/* <Route path="/legal/powerterms" element={<PowerTerms />} /> */}
            <Route path="/legal/broadbandterms" element={<BroadbandTerms />} />
            {/* <Route path="/legal/mobileterms" element={<MobileTerms />} /> */}
            <Route path="/servicepromise" element={<ServicePromise />} />

            {/* Support Pages */}
            <Route path="/support" element={<SupportLandingPage />} />
            <Route path="/support/general" element={<GeneralSupport />} />
            <Route path="/support/billing" element={<BillingSupport />} />
            <Route path="/support/technical" element={<TechnicalSupport />} />
            <Route path="/support/contact" element={<ContactSupport />} />
            <Route path="/support/mobile" element={<MobileSupport />} />

            {/* Post-login redirect route */}
            <Route path="/redirect" element={<PostLoginRedirect />} />

            {/* Redirect authenticated routes to portal */}
            <Route path="/authenticated" element={<PortalRedirect path="/" />} />
            <Route path="/authenticated/*" element={<PortalRedirect path={location.pathname.replace('/authenticated', '')} />} />
            <Route path="/home" element={<PortalRedirect path="/" />} />
            <Route path="/dashboard" element={<PortalRedirect path="/" />} />
            <Route path="/billing" element={<PortalRedirect path="/billing" />} />
            <Route path="/profile" element={<PortalRedirect path="/profile" />} />
            <Route path="/onboarding" element={<PortalRedirect path="/onboarding" />} />

            {/* Redirect staff routes to staff portal */}
            <Route path="/staff" element={<StaffRedirect path="/" />} />
            <Route path="/staff/*" element={<StaffRedirect path={location.pathname.replace('/staff', '')} />} />

            {/* Catch-all - 404 for unknown routes */}
            <Route path="*" element={
              <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                  <p className="text-gray-600 mb-6">Page not found</p>
                  <a 
                    href="/"
                    className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
                  >
                    Go Home
                  </a>
                </div>
              </div>
            } />
          </Routes>
        </Suspense>
      </main>

      {/* Conditionally render Header and Footer */}
      {!isExcludedPath && <Footer />}
    </div>
  );
}

export default App;