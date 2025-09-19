import { useEffect, useState, useContext, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../../context/AuthContext';
import { useLoader } from '../../context/LoaderContext';
import Loader from '../../components/Loader';

export default function OAuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useContext(AuthContext);
  const { setLoading: setGlobalLoading } = useLoader();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const hasHandledRef = useRef(false);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      if (hasHandledRef.current) {
        // Prevent re-entrancy in the same mount/render
        return;
      }
      try {
        console.log('🔄 OAuth Callback URL:', window.location.href);
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');

        console.log('📋 OAuth Callback received:', { 
          code: code ? `${code.substring(0, 20)}...` : null, 
          state: state, 
          error, 
          errorDescription,
          fullURL: window.location.href
        });

        // Handle OAuth errors
        if (error) {
          console.error('OAuth Error:', error, errorDescription);
          setError(`Authentication failed: ${errorDescription || error}`);
          setStatus('error');
          return;
        }

        // Validate required parameters
        if (!code) {
          setError('Missing authorization code');
          setStatus('error');
          return;
        }

        // Validate state parameter (soft check)
        if (state) {
          const storedState = sessionStorage.getItem('oauth_state');
          if (storedState && state !== storedState) {
            console.warn('⚠️ State mismatch. Proceeding due to backend PKCE storage.');
            // Do not block: backend validates state via PKCE cache
          }
          // Single-shot guard across StrictMode double-invocation/remounts
          const guardKey = `oauth_cb:${state}`;
          if (sessionStorage.getItem(guardKey) === '1') {
            console.warn('⏭️ Duplicate OAuth callback suppressed (already handled for this state)');
            return;
          }
          sessionStorage.setItem(guardKey, '1');
          hasHandledRef.current = true;
          // Clean up stored state if present
          sessionStorage.removeItem('oauth_state');
          sessionStorage.removeItem('oauth_nonce');
        }

        setStatus('exchanging');

        // Exchange authorization code for tokens via Django API
        const apiBaseUrl = window.location.hostname.includes('uat.') 
          ? 'https://uat.api.spoton.co.nz' 
          : 'https://api.spoton.co.nz';
        
        // For social login, we need to handle PKCE differently
        // The frontend needs to generate PKCE parameters and store them
        const response = await fetch(`${apiBaseUrl}/auth/keycloak/social-callback/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            code,
            state,
            redirect_uri: window.location.origin + '/auth/callback',
            code_verifier: sessionStorage.getItem('oauth_code_verifier') || null
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          
          // Handle account existence error for social signup
          if (response.status === 409 && errorData.error === 'account_exists') {
            console.log('🚫 Account already exists for social signup');
            setStatus('account_exists');
            setError(`Account with email ${errorData.email} already exists. Redirecting to sign in...`);
            
            // Clear session data
            sessionStorage.removeItem('oauth_code_verifier');
            sessionStorage.removeItem('social_signup_intent');
            
            // Redirect to sign in page after a short delay
            setTimeout(() => {
              window.location.href = '/login?message=account_exists&email=' + encodeURIComponent(errorData.email);
            }, 2000);
            return;
          }
          
          // Allow retry by clearing the single-shot guard for this state
          const state = new URLSearchParams(location.search).get('state');
          if (state) {
            sessionStorage.removeItem(`oauth_cb:${state}`);
          }
          throw new Error(errorData.message || 'Token exchange failed');
        }

        const data = await response.json();
        console.log('Token exchange successful:', { user: !!data.user });

        // Set user in AuthContext from the authoritative backend response
        if (data.user) {
          console.log('✅ OAuth: Authoritative user data received, setting user context:', {
            id: data.user.id,
            email: data.user.email,
            mobile_verified: data.user.mobile_verified,
            is_onboarding_complete: data.user.is_onboarding_complete,
          });
          setUser(data.user);
          
          // Use this authoritative user object for all subsequent logic
          const user = data.user;

          console.log('🔍 Checking user verification status from authoritative source:', {
            email_verified: user.email_verified,
            mobile_verified: user.mobile_verified,
            is_onboarding_complete: user.is_onboarding_complete,
            is_staff: user.is_staff
          });

          const isSocial = (
            user.registration_method === 'social' ||
            !!user.social_provider
          );
          
          const isOnboardingComplete = Boolean(user.is_onboarding_complete);

          // Social users need mobile verification ONLY if mobile is not verified
          // Email verification is handled automatically by Google OAuth
          if (isSocial && !user.mobile_verified) {
            console.log('📱 Social login -> mobile not verified, redirecting to verify-phone', {
              email_verified: user.email_verified,
              mobile_verified: user.mobile_verified,
              mobile_exists: !!user.mobile
            });
            setGlobalLoading(false);
            navigate('/auth/verify-phone', {
              replace: true,
              state: {
                user,
                isNewUser: !user.mobile,  // Simplified: just check if mobile exists
                provider: user.social_provider || 'google',
                from: '/auth/callback'
              }
            });
            return;
          }

          if (!isOnboardingComplete) {
            console.log('📝 Mobile verified but onboarding not complete, redirecting to onboarding');
            setGlobalLoading(false);
            navigate('/onboarding', { 
              replace: true,
              state: { user, from: '/auth/callback' }
            });
            return;
          }

          if (user.is_staff) {
            console.log('👥 Staff user authenticated, redirecting to staff dashboard');
            setGlobalLoading(false);
            navigate(user.is_superuser ? '/staff/tenants' : '/staff/users');
            return;
          }

          console.log('✅ All set, redirecting to dashboard');
          setGlobalLoading(false);
          navigate('/');
        } else {
          console.error('❌ No user data received from OAuth callback');
          setError('Authentication succeeded but no user data received');
          setStatus('error');
          setGlobalLoading(false);
        }

      } catch (err) {
        console.error('OAuth callback error:', err);
        setError(err.message || 'Authentication failed');
        setStatus('error');
        setGlobalLoading(false);
      }
      finally {
        // Cleanup limited session items (state/nonce only)
        sessionStorage.removeItem('oauth_state');
        sessionStorage.removeItem('oauth_nonce');
      }
    };

    handleOAuthCallback();
  }, [location, navigate]);

  if (status === 'processing' || status === 'exchanging') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] flex items-center justify-center">
        <Loader size="xl" fullscreen />
      </div>
    );
  }

  if (status === 'account_exists') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-orange-500/20 rounded-full">
              <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Account Already Exists</h3>
            <p className="text-slate-300 mb-4">{error}</p>
            <p className="text-sm text-slate-400">You will be redirected to the sign in page shortly...</p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-500/20 rounded-full">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Authentication Failed</h2>
            <p className="text-red-300 mb-4">{error}</p>
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}