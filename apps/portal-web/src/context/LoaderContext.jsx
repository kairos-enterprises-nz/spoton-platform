// src/context/LoaderContext.jsx
import { createContext, useContext, useState, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';

const LoaderContext = createContext();

export const LoaderProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Loading...');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const loadingTimeoutRef = useRef(null);

  // Enhanced loading control with automatic timeout
  const showLoader = useCallback((message = 'Loading...', timeout = 30000) => {
    setLoadingMessage(message);
    setLoadingProgress(0);
    setLoading(true);

    // Clear any existing timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    // Set automatic timeout to prevent stuck loaders
    loadingTimeoutRef.current = setTimeout(() => {
      console.warn('Global loader timeout reached, hiding loader');
      setLoading(false);
      setLoadingProgress(0);
    }, timeout);
  }, []);

  const hideLoader = useCallback(() => {
    setLoading(false);
    setLoadingProgress(0);
    
    // Clear timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }
  }, []);

  const updateProgress = useCallback((progress) => {
    setLoadingProgress(Math.min(100, Math.max(0, progress)));
  }, []);

  const updateMessage = useCallback((message) => {
    setLoadingMessage(message);
  }, []);

  return (
    <LoaderContext.Provider value={{ 
      loading, 
      loadingMessage,
      loadingProgress,
      setLoading, 
      showLoader, 
      hideLoader,
      updateProgress,
      updateMessage
    }}>
      {children}
    </LoaderContext.Provider>
  );
};

LoaderProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export const useLoader = () => {
  const context = useContext(LoaderContext);
  if (!context) {
    throw new Error('useLoader must be used within a LoaderProvider');
  }
  return context;
};

// Custom hook for API loading states
export const useApiLoader = () => {
  const { showLoader, hideLoader, updateProgress, updateMessage } = useLoader();

  const withLoading = useCallback(async (apiCall, message = 'Loading...') => {
    try {
      showLoader(message);
      const result = await apiCall();
      return result;
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    } finally {
      hideLoader();
    }
  }, [showLoader, hideLoader]);

  return { withLoading, showLoader, hideLoader, updateProgress, updateMessage };
};
