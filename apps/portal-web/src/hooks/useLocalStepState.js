import { useState, useCallback, useEffect, useRef } from 'react';
import { getStepCompletionStatus } from '../utils/onboardingDataUtils';

// Debounce utility function
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Local-first step state management hook
 * Separates step state (UI state) from data sync to avoid hierarchy issues
 * Step state is calculated locally based on data, not synced to backend
 * @param {Array} steps - Array of step definitions
 * @param {Object} userData - Current user data
 * @returns {Object} Step state management methods
 */
export function useLocalStepState(steps = [], userData = {}) {
  // Local step state - not synced to backend
  const [openStep, setOpenStep] = useState(0);
  const [stepCompleted, setStepCompleted] = useState(() => Array(steps.length).fill(false));
  const [manualNavigation, setManualNavigation] = useState(false);
  
  // Refs to prevent unnecessary recalculations
  const lastUserDataRef = useRef(userData);
  const lastCompletionRef = useRef([]);

  // Calculate step completion based on current data
  const calculateStepCompletion = useCallback((data, currentStep = null) => {
    if (!data || Object.keys(data).length === 0) {
      return Array(steps.length).fill(false);
    }
    
    try {
      return getStepCompletionStatus(data, currentStep);
    } catch (error) {
      console.warn('Error calculating step completion:', error);
      return Array(steps.length).fill(false);
    }
  }, [steps.length]);

  // Debounced step completion update to reduce excessive calls
  const debouncedStepCompletionUpdate = useCallback(
    debounce((userData, openStep) => {
      const newCompletion = calculateStepCompletion(userData, openStep);
      
      console.log('🔍 Step Completion Debug (Debounced):', {
        openStep,
        userData: Object.keys(userData),
        hasYourServices: !!(userData.yourServices || userData.selectedServices),
        newCompletion,
        previousCompletion: lastCompletionRef.current
      });
      
      // Only update if completion status actually changed
      if (JSON.stringify(lastCompletionRef.current) !== JSON.stringify(newCompletion)) {
        console.log('🔍 Step completion changed, updating:', {
          from: lastCompletionRef.current,
          to: newCompletion
        });
        setStepCompleted(newCompletion);
        lastCompletionRef.current = newCompletion;
      }
      
      lastUserDataRef.current = userData;
    }, 300), // 300ms debounce delay
    [calculateStepCompletion]
  );

  // Update step completion when userData changes (debounced)
  useEffect(() => {
    // Use debounced update to prevent excessive recalculations
    debouncedStepCompletionUpdate(userData, openStep);
  }, [userData, openStep, debouncedStepCompletionUpdate]);

  // Navigate to first incomplete step when completion changes (only if not manually navigated)
  useEffect(() => {
    // If the user has manually navigated, don't automatically change the open step.
    if (manualNavigation) return;

    // Find the first step that is not yet completed.
    const firstIncompleteStep = stepCompleted.findIndex(completed => !completed);
    
    // If all steps are complete, the target is the last step. Otherwise, it's the first incomplete one.
    const targetStep = firstIncompleteStep === -1 ? steps.length - 1 : firstIncompleteStep;

    // Only update the open step if it's not already the target step.
    if (openStep !== targetStep) {
      setOpenStep(targetStep);
    }
  }, [stepCompleted, manualNavigation, openStep, steps.length]);

  // Manual step navigation
  const navigateToStep = useCallback((stepIndex) => {
    if (stepIndex >= 0 && stepIndex < steps.length) {
      setManualNavigation(true);
      setOpenStep(stepIndex);
    }
  }, [steps.length]);

  // Only reset manual navigation flag on significant data structure changes, not minor updates
  useEffect(() => {
    // Only reset manual navigation if this is a completely new user session
    // (e.g., when userData goes from empty to having data for the first time)
    const wasEmpty = !lastUserDataRef.current || Object.keys(lastUserDataRef.current).length === 0;
    const nowHasData = userData && Object.keys(userData).length > 0;
    
    if (wasEmpty && nowHasData) {
      // This is likely initial data load, allow auto-navigation
      setManualNavigation(false);
    }
    // Don't reset manual navigation for regular data updates
  }, [userData]);

  // Check if a specific step is complete
  const isStepComplete = useCallback((stepIndex) => {
    return stepCompleted[stepIndex] || false;
  }, [stepCompleted]);

  // Check if all steps before a given step are complete
  const arePrerequisitesComplete = useCallback((stepIndex) => {
    if (stepIndex === 0) return true;
    return stepCompleted.slice(0, stepIndex).every(Boolean);
  }, [stepCompleted]);

  // Get the next incomplete step
  const getNextIncompleteStep = useCallback(() => {
    const nextIncomplete = stepCompleted.findIndex(completed => !completed);
    return nextIncomplete === -1 ? stepCompleted.length - 1 : nextIncomplete;
  }, [stepCompleted]);

  // Check if ready for final submission
  const isReadyForSubmission = useCallback(() => {
    // All steps except the last one (confirmation) should be complete
    return stepCompleted.slice(0, -1).every(Boolean);
  }, [stepCompleted]);

  return {
    // State
    openStep,
    stepCompleted,
    
    // Actions
    setOpenStep,
    navigateToStep,
    
    // Computed values
    isStepComplete,
    arePrerequisitesComplete,
    getNextIncompleteStep,
    isReadyForSubmission,
    
    // Internal methods (for debugging)
    calculateStepCompletion
  };
} 