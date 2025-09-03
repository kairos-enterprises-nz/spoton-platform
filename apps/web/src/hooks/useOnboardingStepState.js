import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * Custom hook to manage state and autosaving for onboarding steps
 * @param {string} stepKey - The key identifying the onboarding step
 * @param {Object} initialData - Initial data for the step
 * @returns {Object} State management methods and current state
 */
export function useOnboardingStepState(stepKey, initialData = {}) {
  // Only manage local state
  const [state, setState] = useState(() => ({
    ...initialData,
    lastModified: initialData.lastModified || new Date().toISOString()
  }));

  const prevInitialDataRef = useRef(initialData);

  // Update state function with memoization
  const updateState = useCallback((updates) => {
    setState(prev => {
      const newState = typeof updates === 'function' ? updates(prev) : { ...prev, ...updates };
      // Only update if there are actual changes
      if (JSON.stringify(prev) === JSON.stringify(newState)) {
        return prev;
      }
      return {
        ...newState,
        lastModified: new Date().toISOString()
      };
    });
  }, []);

  // Update state from initialData if it changes significantly
  useEffect(() => {
    const prevData = prevInitialDataRef.current;
    if (JSON.stringify(prevData) !== JSON.stringify(initialData)) {
      setState(prev => {
        const newState = { ...prev, ...initialData };
        if (JSON.stringify(prev) === JSON.stringify(newState)) {
          return prev;
        }
        return {
          ...newState,
          lastModified: new Date().toISOString()
        };
      });
      prevInitialDataRef.current = initialData;
    }
  }, [initialData]);

  return {
    state,
    updateState
  };
}
