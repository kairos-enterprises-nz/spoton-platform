import React from 'react';
import { Routes, Route, Navigate, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { TenantProvider } from './context/TenantContext';
import StaffLayout from './components/staff/StaffLayout';
import { getEnvUrl } from './utils/environment';
// Staff pages
import StaffLogin from './pages/StaffLogin';
import StaffUsers from './pages/StaffUsers';
import StaffTenants from './pages/StaffTenants';
import StaffAccounts from './pages/StaffAccounts';
import StaffConnections from './pages/StaffConnections';
import StaffContracts from './pages/StaffContracts';
import StaffPlans from './pages/StaffPlans';
import StaffEnergyData from './pages/StaffEnergyData';
import StaffEnergyAnalytics from './pages/StaffEnergyAnalytics';
import StaffReports from './pages/StaffReports';
import StaffValidationRules from './pages/StaffValidationRules';
import StaffValidationExceptions from './pages/StaffValidationExceptions';
import StaffSystem from './pages/StaffSystem';
import StaffAirflow from './pages/StaffAirflow';
import StaffBilling from './pages/StaffBilling';

const StaffDashboard = () => {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const goToStaff = () => navigate('/');
  const goToLogin = () => navigate('/login');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">SpotOn Staff Dashboard</h1>
            </div>
            <div>
              {isAuthenticated && user?.is_staff ? (
                <button onClick={goToStaff} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                  Open Staff Portal
                </button>
              ) : (
                <button onClick={goToLogin} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                  Staff Login
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Welcome to Staff Dashboard</h2>
              <p className="text-gray-600 mb-4">
                The staff dashboard is currently being updated with new features.
              </p>
              {!isAuthenticated && (
                <div className="mb-6">
                  <button onClick={goToLogin} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                    Login to manage staff tools
                  </button>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium text-blue-900">System Status</h3>
                  <p className="text-blue-700 text-sm">All systems operational</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium text-green-900">Services</h3>
                  <p className="text-green-700 text-sm">Management tools available</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-medium text-purple-900">Analytics</h3>
                  <p className="text-purple-700 text-sm">Performance monitoring</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Redirect customers attempting to login here to the customer portal
function LoginRedirect() {
  React.useEffect(() => {
    // On staff domain, /login is the staff login route
    window.location.href = '/login';
  }, []);
  return null;
}

// Staff-only route guard
function PrivateRoute({ children }) {
  const { isAuthenticated, user, loading, initialCheckComplete } = useAuth();
  if (!initialCheckComplete || loading) return null;
  if (!isAuthenticated || !user?.is_staff) return <Navigate to="/login" replace />;
  return children;
}

// Role-based default redirect
function RoleBasedRedirect() {
  const { user } = useAuth();
  
  // Debug logging
  console.log('🔧 RoleBasedRedirect: User data:', {
    user: user,
    is_superuser: user?.is_superuser,
    isAdmin: user?.isAdmin,
    groups: user?.groups,
    roles: user?.roles
  });
  
  // Super admin goes to tenants page, regular staff goes to users page
  if (user?.is_superuser || user?.isAdmin) {
    console.log('🔧 RoleBasedRedirect: Redirecting to /tenants');
    return <Navigate to="/tenants" replace />;
  } else {
    console.log('🔧 RoleBasedRedirect: Redirecting to /users');
    return <Navigate to="/users" replace />;
  }
}

function App() {
  return (
    <Routes>
      {/* Health check */}
      <Route
        path="/health"
        element={
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <h1>SpotOn Staff Web</h1>
            <p>Service is running</p>
            <p>Status: OK</p>
          </div>
        }
      />

      {/* Staff login */}
      <Route path="/login" element={<StaffLogin />} />

      {/* Staff portal protected area (root) */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <TenantProvider>
              <StaffLayout>
                <Outlet />
              </StaffLayout>
            </TenantProvider>
          </PrivateRoute>
        }
      >
        <Route index element={<RoleBasedRedirect />} />
        <Route path="users" element={<StaffUsers />} />
        <Route path="tenants" element={<StaffTenants />} />
        <Route path="tenant" element={<Navigate to="/tenants" replace />} />
        <Route path="accounts" element={<StaffAccounts />} />
        <Route path="connections" element={<StaffConnections />} />
        <Route path="contracts" element={<StaffContracts />} />
        <Route path="plans" element={<StaffPlans />} />
        <Route path="energy" element={<StaffEnergyData />} />
        <Route path="energy/analytics" element={<StaffEnergyAnalytics />} />
        <Route path="reports" element={<StaffReports />} />
        <Route path="validation-rules" element={<StaffValidationRules />} />
        <Route path="validation-exceptions" element={<StaffValidationExceptions />} />
        <Route path="system" element={<StaffSystem />} />
        <Route path="airflow" element={<StaffAirflow />} />
        <Route path="billing" element={<StaffBilling />} />
      </Route>

      {/* Landing catch-all - temporarily disabled for debugging */}
      {/* <Route path="*" element={<StaffDashboard />} /> */}
    </Routes>
  );
}

export default App; // Trigger build 3
