import { useState, useCallback, useEffect, useRef } from 'react';
import { getStepCompletionStatus } from '../utils/onboardingDataUtils';

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
  const calculateStepCompletion = useCallback((data) => {
    if (!data || Object.keys(data).length === 0) {
      return Array(steps.length).fill(false);
    }
    
    try {
      return getStepCompletionStatus(data);
    } catch (error) {
      console.warn('Error calculating step completion:', error);
      return Array(steps.length).fill(false);
    }
  }, [steps.length]);

  // Update step completion when userData changes
  useEffect(() => {
    // Always recalculate step completion when userData changes
    const newCompletion = calculateStepCompletion(userData);
    
    // Only update if completion status actually changed
    if (JSON.stringify(lastCompletionRef.current) !== JSON.stringify(newCompletion)) {

      setStepCompleted(newCompletion);
      lastCompletionRef.current = newCompletion;
    }
    
    lastUserDataRef.current = userData;
  }, [userData, calculateStepCompletion]);

  // Navigate to first incomplete step when completion changes (only if not manually navigated)
  useEffect(() => {
    // Don't auto-navigate if user has manually navigated
    if (manualNavigation) return;
    
    const firstIncompleteStep = stepCompleted.findIndex(completed => !completed);
    const targetStep = firstIncompleteStep === -1 ? stepCompleted.length - 1 : firstIncompleteStep;
    
    // Only update openStep if it's different and we're not on the last step
    // Also only auto-navigate on initial load (when openStep is 0 and no steps are complete)
    const isInitialLoad = openStep === 0 && stepCompleted.every(completed => !completed);
    if (isInitialLoad && openStep !== targetStep && openStep < stepCompleted.length - 1) {
      setOpenStep(targetStep);
    }
  }, [stepCompleted, openStep, stepCompleted.length, manualNavigation]);

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