// src/hooks/useNavigationLoader.js
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useLoader } from '../context/LoaderContext';

// Page-specific loading messages
const PAGE_MESSAGES = {
  '/': 'Loading your dashboard...',
  '/power': 'Getting your power usage...',
  '/broadband': 'Checking your connection...',
  '/mobile': 'Loading your mobile services...',
  '/billing': 'Fetching your latest bills...',
  '/profile': 'Loading your profile...',
  '/support': 'Loading support options...',
  '/login': 'Preparing login...',
  '/auth/callback': 'Completing authentication...',
  '/auth/verify-phone': 'Loading verification...'
};

export const useNavigationLoader = () => {
  const location = useLocation();
  const { showLoader, hideLoader, updateMessage } = useLoader();

  useEffect(() => {
    // Get loading message for current route
    const message = PAGE_MESSAGES[location.pathname] || 'Loading page...';
    
    // Show loader briefly during navigation
    showLoader(message, 2000); // 2 second timeout
    
    // Hide loader after a short delay to allow page to render
    const timer = setTimeout(() => {
      hideLoader();
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [location.pathname, showLoader, hideLoader]);

  return { updateMessage };
};

// Hook for manual navigation with loading
export const useNavigateWithLoader = () => {
  const { showLoader, hideLoader } = useLoader();
  
  const navigateWithLoader = (navigate, path, message) => {
    const loadingMessage = message || PAGE_MESSAGES[path] || 'Loading...';
    showLoader(loadingMessage);
    
    // Navigate and hide loader after brief delay
    navigate(path);
    setTimeout(() => hideLoader(), 500);
  };

  return { navigateWithLoader };
};
