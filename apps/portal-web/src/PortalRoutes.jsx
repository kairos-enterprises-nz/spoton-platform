import { Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import Loader from './components/Loader';
import ProtectedRoute from './components/routing/ProtectedRoute'; // Import the new protected route

// Lazy-loaded components
const AuthenticatedLayout = lazy(() => import('./pages/authenticated/Home.jsx'));
const DashboardContentPage = lazy(() => import('./pages/authenticated/Dashboard.jsx'));
const PowerContentPage = lazy(() => import('./pages/authenticated/Power.jsx'));
const BroadbandContentPage = lazy(() => import('./pages/authenticated/Broadband.jsx'));
const MobileContentPage = lazy(() => import('./pages/authenticated/Mobile.jsx'));
const BillingContentPage = lazy(() => import('./pages/authenticated/Billing.jsx'));
const ProfileContentPage = lazy(() => import('./pages/authenticated/Profile.jsx'));
const DashboardSupportPage = lazy(() => import('./pages/authenticated/Support.jsx'));

export default function PortalRoutes() {
  return (
    <Suspense fallback={<Loader fullscreen />}>
      <Routes>
        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<AuthenticatedLayout />}>
            <Route index element={<DashboardContentPage />} />
          </Route>
          <Route path="/power" element={<AuthenticatedLayout />}>
            <Route index element={<PowerContentPage />} />
          </Route>
          <Route path="/broadband" element={<AuthenticatedLayout />}>
            <Route index element={<BroadbandContentPage />} />
          </Route>
          <Route path="/mobile" element={<AuthenticatedLayout />}>
            <Route index element={<MobileContentPage />} />
          </Route>
          <Route path="/billing" element={<AuthenticatedLayout />}>
            <Route index element={<BillingContentPage />} />
          </Route>
          <Route path="/profile" element={<AuthenticatedLayout />}>
            <Route index element={<ProfileContentPage />} />
          </Route>
          <Route path="/support" element={<AuthenticatedLayout />}>
            <Route index element={<DashboardSupportPage />} />
          </Route>
        </Route>

        {/* Catch-all - Redirect to home if authenticated, otherwise handled by ProtectedRoute */}
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </Suspense>
  );
}
