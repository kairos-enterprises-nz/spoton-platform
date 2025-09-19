import { useState, useCallback, useEffect } from 'react';

/**
 * Custom hook to manage confirmation step state separately from main onboarding flow
 * This prevents conflicts with the main useOnboardingStepState hook
 * @param {Object} initialTermsLinks - Initial terms links to generate terms state
 * @returns {Object} Confirmation step state management methods
 */
export function useConfirmationStepState(initialTermsLinks = {}) {
  // Terms acceptance state
  const [termsAccepted, setTermsAccepted] = useState(() => 
    Object.keys(initialTermsLinks).reduce((acc, key) => ({
      ...acc,
      [key]: false
    }), {})
  );

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Update terms state when terms links change
  useEffect(() => {
    setTermsAccepted(prev => {
      const newTermsState = Object.keys(initialTermsLinks).reduce((acc, key) => ({
        ...acc,
        [key]: prev[key] || false // Preserve existing state, default to false for new terms
      }), {});
      
      // Only update if there are actual changes
      if (JSON.stringify(prev) === JSON.stringify(newTermsState)) {
        return prev;
      }
      
      return newTermsState;
    });
  }, [initialTermsLinks]);

  // Helper function to handle checkbox changes
  const handleTermsChange = useCallback((term) => {
    setTermsAccepted(prev => ({
      ...prev,
      [term]: !prev[term]
    }));
  }, []);

  // Helper function to accept all terms
  const acceptAllTerms = useCallback(() => {
    setTermsAccepted(prev => 
      Object.keys(prev).reduce((acc, key) => ({
        ...acc,
        [key]: true
      }), {})
    );
  }, []);

  // Helper function to unaccept all terms
  const unacceptAllTerms = useCallback(() => {
    setTermsAccepted(prev => 
      Object.keys(prev).reduce((acc, key) => ({
        ...acc,
        [key]: false
      }), {})
    );
  }, []);

  // Helper function to check if all terms are accepted
  const areAllTermsAccepted = useCallback(() => {
    return Object.values(termsAccepted).every(Boolean);
  }, [termsAccepted]);

  // Reset error when terms change
  useEffect(() => {
    if (error && areAllTermsAccepted()) {
      setError(null);
    }
  }, [termsAccepted, error, areAllTermsAccepted]);

  return {
    // State
    termsAccepted,
    isSubmitting,
    error,
    
    // Actions
    setTermsAccepted,
    setIsSubmitting,
    setError,
    handleTermsChange,
    acceptAllTerms,
    unacceptAllTerms,
    areAllTermsAccepted
  };
} 