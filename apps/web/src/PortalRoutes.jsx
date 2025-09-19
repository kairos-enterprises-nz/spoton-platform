import { Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useAuth } from './hooks/useAuth';
import Loader from './components/Loader';

// Lazy-loaded components
const AuthenticatedLayout = lazy(() => import('./pages/authenticated/Home.jsx'));
const DashboardContentPage = lazy(() => import('./pages/authenticated/Dashboard.jsx'));
const PowerContentPage = lazy(() => import('./pages/authenticated/Power.jsx'));
const BroadbandContentPage = lazy(() => import('./pages/authenticated/Broadband.jsx'));
const MobileContentPage = lazy(() => import('./pages/authenticated/Mobile.jsx'));
const BillingContentPage = lazy(() => import('./pages/authenticated/Billing.jsx'));
const ProfileContentPage = lazy(() => import('./pages/authenticated/Profile.jsx'));
const DashboardSupportPage = lazy(() => import('./pages/authenticated/Support.jsx'));

// Private Route wrapper
function PrivateRoute({ children }) {
  const { isAuthenticated, loading, initialCheckComplete } = useAuth();

  if (!initialCheckComplete || loading) return <Loader fullscreen />;
  if (!isAuthenticated) {
    window.location.href = 'https://uat.spoton.co.nz/login';
    return null;
  }
  return children;
}

export default function PortalRoutes() {
  return (
    <Suspense fallback={<Loader fullscreen />}>
      <Routes>
        {/* Portal root - redirect to home */}
        <Route path="/" element={
          <PrivateRoute><Navigate to="/home" replace /></PrivateRoute>
        } />
        
        {/* Portal routes */}
        <Route path="/home" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<DashboardContentPage />} />
        </Route>
        
        <Route path="/power" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<PowerContentPage />} />
        </Route>
        
        <Route path="/broadband" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<BroadbandContentPage />} />
        </Route>
        
        <Route path="/mobile" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<MobileContentPage />} />
        </Route>
        
        <Route path="/billing" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<BillingContentPage />} />
        </Route>
        
        <Route path="/profile" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<ProfileContentPage />} />
        </Route>
        
        <Route path="/support" element={
          <PrivateRoute><AuthenticatedLayout /></PrivateRoute>
        }>
          <Route index element={<DashboardSupportPage />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </Suspense>
  );
}
