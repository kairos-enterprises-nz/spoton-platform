import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Loader from '../Loader';

const ProtectedRoute = () => {
  const { user, loading, initialCheckComplete, isAuthenticated } = useAuth();

  // If the initial auth check is not yet complete, show a loader
  if (loading || !initialCheckComplete) {
    return <Loader />;
  }

  // If not authenticated, redirect to the login page
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Enforce phone verification before onboarding for social users
  if (user) {
    const isSocial = user?.registration_method === 'social' || !!user?.social_provider;
    // Use normalized mobile_verified field, fallback to legacy phone_verified
    const mobileVerified = user?.mobile_verified !== undefined ? user?.mobile_verified : user?.phone_verified;
    
    if (isSocial && !mobileVerified) {
      return <Navigate to="/auth/verify-phone" replace />;
    }

    // If authenticated, but onboarding is not complete, redirect to onboarding
    const isOnboardingComplete = Boolean(
      user?.is_onboarding_complete ?? user?.onboarding_complete ?? false
    );
    if (!isOnboardingComplete) {
      return <Navigate to="/onboarding" replace />;
    }
  }

  // If authenticated and onboarding is complete, render the child routes
  return <Outlet />;
};

export default ProtectedRoute;
