import React from 'react';
import { Navigate } from 'react-router-dom';
import Loader from '../Loader';
import { useAuth } from '../../hooks/useAuth';

export default function VerifyPhoneRoute({ children }) {
  const { user, isAuthenticated, loading, initialCheckComplete } = useAuth();

  if (!initialCheckComplete || loading) return <Loader fullscreen />;

  // No session → go to login
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  // Only rely on explicit social markers
  const isSocial = user && (user.registration_method === 'social' || !!user.social_provider);
  const isOnboardingComplete = Boolean(user?.is_onboarding_complete ?? user?.onboarding_complete ?? false);

  // Use normalized mobile_verified field, fallback to legacy phone_verified
  const mobileVerified = user?.mobile_verified !== undefined ? user?.mobile_verified : user?.phone_verified;

  // Non-social users shouldn't be here
  if (!isSocial) return <Navigate to={isOnboardingComplete ? '/' : '/onboarding'} replace />;

  // Already verified → proceed in flow
  if (mobileVerified) return <Navigate to={isOnboardingComplete ? '/' : '/onboarding'} replace />;

  return children;
}

