import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useLoader } from '../context/LoaderContext';
import { initKeycloak, keycloakLogin, keycloakPasswordLogin } from '../services/keycloakService';

const StaffLogin = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, refreshUser } = useAuth();
  const { setLoading } = useLoader();

  // Redirect if already authenticated as staff
  useEffect(() => {
    console.log('👤 StaffLogin: useEffect triggered', {
      isAuthenticated,
      user: user ? { id: user.id, is_staff: user.is_staff, email: user.email } : null,
      pathname: location.pathname,
      fromState: location.state?.from
    });
    
    if (isAuthenticated && user?.is_staff && location.pathname === '/login') {
      // If user came from a specific page, redirect them back there
      // Otherwise, redirect based on user role: super admin -> tenants, staff -> users
      const from = location.state?.from?.pathname || (user?.is_superuser ? '/tenants' : '/users');
      console.log('👤 StaffLogin: Redirecting authenticated staff user to:', from);
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'identifier') setIdentifier(value);
    if (name === 'password') setPassword(value);
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('👤 StaffLogin: Form submitted');
    setError('');
    setIsSubmitting(true);
    setLoading(true);

    try {
      // If password provided, prefer ROPC to keep UI fully in React
      if (password && identifier) {
        const r = await keycloakPasswordLogin(identifier, password);
        console.log('👤 StaffLogin: ROPC login result:', r);
        // Give AuthContext a tick to pick up tokens via Keycloak SDK
        setTimeout(async () => {
          const before = Date.now();
          await refreshUser();
          console.log('👤 StaffLogin: refreshUser completed in', Date.now() - before, 'ms');
          // Use role-based navigation: super admin -> tenants, staff -> users
          const redirectPath = user?.is_superuser ? '/tenants' : '/users';
          window.location.href = redirectPath;
        }, 0);
        return;
      }
      // Fallback: initialize and start auth flow (for SSO session reuse)
      await initKeycloak({ onLoad: 'check-sso' });
      await keycloakLogin({ redirectUri: `${window.location.origin}/` });
      return;
    } catch (error) {
      console.error('👤 StaffLogin: Staff login error:', error);
      setError('Unable to start SSO login. Please try again.');
    } finally {
      setIsSubmitting(false);
      setLoading(false);
      console.log('👤 StaffLogin: Form submission completed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">S</span>
          </div>
          <h2 className="mt-6 text-center text-2xl font-extrabold text-gray-900">
            Staff Portal Login
          </h2>
          <p className="mt-1 text-center text-sm text-gray-600">
            Access the internal staff management system
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="identifier" className="sr-only">Email or Username</label>
              <input
                id="identifier"
                name="identifier"
                type="text"
                autoComplete="username"
                required
                value={identifier}
                onChange={handleChange}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email or username"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={handleChange}
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    {error}
                  </h3>
                </div>
              </div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                <svg className="h-5 w-5 text-indigo-500 group-hover:text-indigo-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
              </span>
              {isSubmitting ? 'Signing in...' : 'Sign in to Staff Portal'}
            </button>
          </div>

        </form>

      </div>
    </div>
    </div>
  );
};

export default StaffLogin; 