// src/pages/OnboardingPage.jsx
import { useState, useContext, useRef, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';


import PageWrapper from '../../components/PageWrapper';
import Loader from '../../components/Loader';
import SyncStatusIndicator from '../../components/onboarding/SyncStatusIndicator';

import Icon from '../../assets/utilitycopilot-icon.webp';
import Text from '../../assets/spoton-text-reversed.webp';

import {
  CheckIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/solid';
import { LogOut } from 'lucide-react';

import AboutYouSection from '../../components/onboarding/AboutYouSection';
import YourServicesSection from '../../components/onboarding/YourServicesSection';
import ServiceDetailsSection from '../../components/onboarding/ServiceDetailsSection';
import HowYoullPaySection from '../../components/onboarding/HowYoullPaySection';
import PreferencesSection from '../../components/onboarding/PreferencesSection';
import ConfirmationSection from '../../components/onboarding/ConfirmationSection';

import { getOnboardingProgress, saveOnboardingStep, finalizeOnboarding } from '../../services/onboarding';
import { AuthContext } from '../../context/AuthContext';
import { 
  normalizeOnboardingData, 
  getSelectedServices,
  getSelectedPlans
} from '../../utils/onboardingDataUtils';
import { useDataSync } from '../../hooks/useDataSync';
import { useOnboardingStepState } from '../../hooks/useOnboardingStepState';
import { useLocalStepState } from '../../hooks/useLocalStepState';

const steps = [
  { name: 'About You', description: 'Your personal information', key: 'aboutYou' },
  { name: 'Your Services', description: 'Pick your utilities and plans', key: 'yourServices' },
  { name: 'Service Details', description: 'Details about your services', key: 'serviceDetails' },
  { name: 'How You\'ll Pay', description: 'Set up billing details', key: 'howYoullPay' },
  { name: 'Preferences', description: 'Notification settings', key: 'preferences' },
  { name: 'Confirmation', description: 'Final review & submit', key: 'confirmation' },
];

const onboardingInstructions = {
  timeToComplete: "3-7 Minutes",
  requirements: [
    {
      title: "Proof of Identity",
      description: "Keep your New Zealand driver's license and passport handy for credit checking purposes. If you don't have these, please contact us.",
      icon: "identification"
    },
    {
      title: "Bank Account Details",
      description: "If you choose to set up Direct Debit payments, have your bank account details ready. This method helps you avoid credit/debit card fees.",
      icon: "banknotes"
    },
    {
      title: "Important Dates",
      description: "Provide the desired start date for our services. If you're moving, provide your move in date for the new address.",
      icon: "calendar"
    }
  ]
};

// Utility to normalize step keys and flatten serviceDetails
function normalizeStepData(stepKey, data) {
  // Map possible aliases to canonical keys
  const stepKeyMap = {
    aboutYou: 'aboutYou',
    yourServices: 'yourServices',
    serviceDetails: 'serviceDetails',
    howYoullPay: 'howYoullPay',
    preferences: 'preferences',
    confirmation: 'confirmation',
  };
  const canonicalKey = stepKeyMap[stepKey] || stepKey;

  // For serviceDetails, flatten nested yourServices if present
  if (canonicalKey === 'serviceDetails') {
    let flatData = { ...data };
    // If nested yourServices exists, flatten it
    if (data.yourServices) {
      if (data.yourServices.selectedServices) {
        flatData.selectedServices = data.yourServices.selectedServices;
      }
      if (data.yourServices.serviceDetails) {
        flatData.serviceDetails = data.yourServices.serviceDetails;
      }
      // Remove nested yourServices
      delete flatData.yourServices;
    }

    // Normalize service details values
    if (flatData.serviceDetails) {
      const serviceDetails = flatData.serviceDetails;
      
      // Power (pw) normalization
      if (serviceDetails.pw_transferType) {
        if (serviceDetails.pw_transferType === 'MoveIn') {
          serviceDetails.pw_transferType = 'Moving In';
        } else if (serviceDetails.pw_transferType === 'Switch') {
          serviceDetails.pw_transferType = 'Switch Provider';
        } else if (serviceDetails.pw_transferType === 'New' || serviceDetails.pw_transferType === 'Installation') {
          serviceDetails.pw_transferType = 'New Connection';
        }
      }

      // Broadband (bb) normalization
      if (serviceDetails.bb_transferType) {
        if (serviceDetails.bb_transferType === 'MoveIn') {
          serviceDetails.bb_transferType = 'Moving In';
        } else if (serviceDetails.bb_transferType === 'Switch') {
          serviceDetails.bb_transferType = 'Switch Provider';
        } else if (serviceDetails.bb_transferType === 'New' || serviceDetails.bb_transferType === 'Installation') {
          serviceDetails.bb_transferType = 'New Connection';
        }
      }

      // Mobile (mb) normalization
      if (serviceDetails.mb_transferType) {
        if (serviceDetails.mb_transferType === 'Switch') {
          serviceDetails.mb_transferType = 'Switch Provider';
        } else if (serviceDetails.mb_transferType === 'New') {
          serviceDetails.mb_transferType = 'New Number';
        } else if (serviceDetails.mb_transferType === 'Port') {
          serviceDetails.mb_transferType = 'Port Number';
        }
      }

      // Router preference normalization
      if (serviceDetails.bb_routerPreference) {
        if (serviceDetails.bb_routerPreference === 'BYO') {
          serviceDetails.bb_routerPreference = 'Bring Your Own';
        } else if (serviceDetails.bb_routerPreference === 'Purchase') {
          serviceDetails.bb_routerPreference = 'Purchase Router';
        }
      }

      // SIM preference normalization
      if (serviceDetails.mb_simPreference) {
        if (serviceDetails.mb_simPreference === 'Physical') {
          serviceDetails.mb_simPreference = 'Physical SIM';
        } else if (serviceDetails.mb_simPreference === 'eSIM') {
          serviceDetails.mb_simPreference = 'eSIM';
        }
      }

      // Ensure required fields are present based on selections
      if (flatData.selectedServices) {
        // Mobile service validation
        if (flatData.selectedServices.mobile && !serviceDetails.mb_transferType) {
          serviceDetails.mb_transferType = 'New Number'; // Default value
        }
        
        // Clear irrelevant fields
        if (!flatData.selectedServices.mobile) {
          delete serviceDetails.mb_transferType;
          delete serviceDetails.mb_simPreference;
          delete serviceDetails.mb_portingNumber;
          delete serviceDetails.mb_serviceStartDate;
        }
        
        if (!flatData.selectedServices.broadband) {
          delete serviceDetails.bb_transferType;
          delete serviceDetails.bb_routerPreference;
          delete serviceDetails.bb_purchaseDetails;
          delete serviceDetails.bb_serviceStartDate;
        }
        
        if (!flatData.selectedServices.electricity) {
          delete serviceDetails.pw_transferType;
          delete serviceDetails.pw_medicalDependency;
          delete serviceDetails.pw_medicalDependencyDetails;
          delete serviceDetails.pw_serviceStartDate;
        }
      }
    }
    return flatData;
  }
  return data;
}

export default function OnboardingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedAddress, user: navUser } = location.state || {};
  const { user, setUser, isAuthenticated, logout } = useContext(AuthContext);

  // Redirect staff users to staff login page for proper authentication
  useEffect(() => {
    if (user?.is_staff) {
      navigate('/staff/login', { replace: true });
      return;
    }
  }, [user, navigate]);

  // Phone verification is now handled by PrivateRoute - no need for page-level checks

  const { state: userData, updateState: setUserData } = useOnboardingStepState('onboarding', {});
  
  // Use local step state management (separate from data sync)
  const {
    openStep,
    stepCompleted,
    navigateToStep
  } = useLocalStepState(steps, userData);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAutosaving, setIsAutosaving] = useState(false);
  const [syncStatus, setSyncStatus] = useState({
    status: 'idle',
    stepName: '',
    lastSyncTime: null,
    pendingUpdates: 0
  });
  const stepRefs = useRef([]);
  const fetchInProgress = useRef(false);
  const initialFetchDone = useRef(false);
  const authCheckDone = useRef(false);

  // Replace direct dataSyncManager usage with useDataSync hook
  const { queueSync, cleanup, getLocalData, setLocalData, mergeData } = useDataSync({
    onSyncStatusChange: (status) => {
      setSyncStatus(prev => ({
        ...prev,
        ...status,
        stepName: status.stepKey ? 
          (steps.find(s => s.key === status.stepKey)?.name || status.stepKey) : 
          prev.stepName
      }));

      // Step completion is now managed by useLocalStepState hook
      // No need to manually update step completion status
    }
  });

  // Handle auth state changes
  useEffect(() => {
    if (isAuthenticated) {
      authCheckDone.current = true;
      if (!initialFetchDone.current) {
        fetchInitialData();
      }
    } else if (isAuthenticated === false) { // Explicitly check for false
      // If not authenticated, reset fetch flags and stop loading
      console.log('🔍 Auth state changed to false, resetting fetch flags');
      initialFetchDone.current = false;
      fetchInProgress.current = false;
      setIsLoading(false);
      authCheckDone.current = true;
    }
  }, [isAuthenticated]);

  // Update the data fetching effect
  const fetchInitialData = useCallback(async () => {
    let isMounted = true;
    if (fetchInProgress.current || initialFetchDone.current || !authCheckDone.current) return;
    
    // Skip API calls for staff users - they will be redirected
    if (user?.is_staff) {
      setIsLoading(false);
      return;
    }
    
    fetchInProgress.current = true;
    setIsLoading(true);
    
    try {
      const localData = getLocalData();
      // Pass temp_session_id to backend if available (for social login service selection sync)
      const urlParams = new URLSearchParams(window.location.search);
      let tempSessionId = urlParams.get('temp_session_id');
      if (!tempSessionId) {
        tempSessionId = sessionStorage.getItem('temp_selection_session_id');
      }
      if (!tempSessionId) {
        const cookies = document.cookie.split(';');
        const tempCookie = cookies.find(cookie => cookie.trim().startsWith('temp_selection_session_id='));
        if (tempCookie) {
          tempSessionId = tempCookie.split('=')[1];
        }
      }
      
      const backendData = await getOnboardingProgress(tempSessionId) || {};
      
      console.log('🔍 Data loading debug:', {
        hasLocalData: !!localData,
        localDataKeys: localData ? Object.keys(localData) : [],
        hasBackendData: !!backendData,
        backendDataKeys: backendData ? Object.keys(backendData) : [],
        hasAboutYouLocal: !!(localData?.aboutYou),
        hasAboutYouBackend: !!(backendData?.step_data?.aboutYou)
      });
      
      // Check for temporary selection data from cross-domain transfer
      let tempSelectionData = null;
      
      console.log('🔍 TEMP SELECTION DEBUG: Passed temp_session_id to backend:', tempSessionId);
      
      if (tempSessionId) {
        try {
          console.log('🔍 Checking for temporary selection data with session ID:', tempSessionId);
          const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://uat.spoton.co.nz';
          console.log('🔍 Using API base URL:', apiBaseUrl);
          const fullUrl = `${apiBaseUrl}/api/web/onboarding/get-temp-selection/${tempSessionId}/`;
          console.log('🔍 Making request to:', fullUrl);
          
          const response = await fetch(fullUrl);
          console.log('🔍 Response status:', response.status, response.statusText);
          
          if (response.ok) {
            const result = await response.json();
            console.log('🔍 Response data:', result);
            if (result.success) {
              tempSelectionData = result.data;
              console.log('📋 Retrieved temporary selection data:', tempSelectionData);
              // Clean up session storage and URL parameter
              sessionStorage.removeItem('temp_selection_session_id');
              if (urlParams.get('temp_session_id')) {
                const newUrl = new URL(window.location);
                newUrl.searchParams.delete('temp_session_id');
                window.history.replaceState({}, '', newUrl);
                console.log('🔍 Cleaned up URL parameter');
              }
            } else {
              console.warn('🔍 API returned success=false:', result);
            }
          } else {
            const errorText = await response.text();
            console.warn('🔍 API request failed:', response.status, errorText);
          }
        } catch (error) {
          console.warn('Failed to retrieve temporary selection data:', error);
        }
      } else {
        console.log('🔍 TEMP SELECTION DEBUG: No temp_selection_session_id found in sessionStorage');
        console.log('🔍 TEMP SELECTION DEBUG: All sessionStorage keys:', Object.keys(sessionStorage));
      }
      
      if (!isMounted) return;

      let mergedData = mergeData(localData, backendData);
      
      // Check if we have service selections in OnboardingProgress step_data (new approach)
      // Priority: Existing onboarding progress > temp selection data
      const onboardingSelections = backendData?.step_data;
      const hasExistingProgress = onboardingSelections?.selectedServices || onboardingSelections?.selectedPlans || 
                                 onboardingSelections?.yourServices?.selectedServices || onboardingSelections?.yourServices?.selectedPlans;
      
      if (hasExistingProgress) {
        console.log('🔄 Found service selections in OnboardingProgress step_data:', onboardingSelections);
        // PRESERVE all existing data and ONLY add/update service selections
        // DO NOT spread onboardingSelections as it overwrites aboutYou and other step data
        mergedData = {
          ...mergedData,
          // Only merge specific step data that exists, preserving existing data
          ...(onboardingSelections.aboutYou && { aboutYou: { ...mergedData.aboutYou, ...onboardingSelections.aboutYou } }),
          ...(onboardingSelections.yourServices && { yourServices: { ...mergedData.yourServices, ...onboardingSelections.yourServices } }),
          ...(onboardingSelections.serviceDetails && { serviceDetails: { ...mergedData.serviceDetails, ...onboardingSelections.serviceDetails } }),
          ...(onboardingSelections.howYoullPay && { howYoullPay: { ...mergedData.howYoullPay, ...onboardingSelections.howYoullPay } }),
          ...(onboardingSelections.preferences && { preferences: { ...mergedData.preferences, ...onboardingSelections.preferences } }),
          // Ensure service selections are available at top level for compatibility
          selectedAddress: onboardingSelections.selectedAddress || mergedData.selectedAddress,
          selectedServices: onboardingSelections.selectedServices || mergedData.selectedServices,
          selectedPlans: onboardingSelections.selectedPlans || mergedData.selectedPlans,
          // Preserve initialSelection and add service data
          initialSelection: {
            ...mergedData.initialSelection,
            selectedAddress: onboardingSelections.selectedAddress,
            selectedServices: onboardingSelections.selectedServices,
            selectedPlans: onboardingSelections.selectedPlans,
            source: 'onboarding_progress'
          }
        };
        console.log('🔄 Merged data preserving all sections:', {
          hasAboutYou: !!mergedData.aboutYou,
          hasYourServices: !!(mergedData.selectedServices || mergedData.yourServices),
          hasServiceDetails: !!mergedData.serviceDetails,
          allKeys: Object.keys(mergedData),
          aboutYouKeys: mergedData.aboutYou ? Object.keys(mergedData.aboutYou) : []
        });
      }
      // Fallback: If we have temporary selection data and no existing progress, merge it
      else if (tempSelectionData) {
        const userRegistrationMethod = user?.registration_method;
        console.log('🔄 Merging temporary selection data into onboarding state', {
          registrationMethod: userRegistrationMethod,
          tempSelectionData: tempSelectionData,
          hasExistingProgress: false
        });
        
        mergedData = {
          ...mergedData,
          initialSelection: {
            ...mergedData.initialSelection,
            selectedAddress: tempSelectionData.selectedAddress,
            selectedServices: tempSelectionData.selectedServices,
            selectedPlans: tempSelectionData.selectedPlans,
            timestamp: tempSelectionData.timestamp,
            source: 'cross_domain_transfer',
            registrationMethod: userRegistrationMethod
          },
          // Also set at top level for immediate availability
          selectedAddress: tempSelectionData.selectedAddress,
          selectedServices: tempSelectionData.selectedServices,
          selectedPlans: tempSelectionData.selectedPlans
        };
        
        console.log('📋 Applied temporary selection data for user:', {
          registrationMethod: userRegistrationMethod,
          selectedServices: tempSelectionData.selectedServices,
          selectedPlans: tempSelectionData.selectedPlans
        });
      }
      // Debug: Log when neither condition is met
      else {
        console.log('🔍 No service selection data applied:', {
          hasExistingProgress: hasExistingProgress,
          hasTempSelection: !!tempSelectionData,
          registrationMethod: user?.registration_method,
          backendStepData: backendData?.step_data
        });
      }
      
      // Extract and process data...
      
      // Save the merged data locally
      setLocalData(mergedData);
      
      if (!isMounted) return;

      // Update state with memoization to prevent unnecessary rerenders
      setUserData(prev => {
        if (JSON.stringify(prev) === JSON.stringify(mergedData)) {
          return prev;
        }
        return mergedData;
      });
      
      // Step completion is now managed by useLocalStepState hook
      // No need to manually calculate or set step completion
      
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
      const localData = getLocalData();
      if (localData && isMounted) {
        setUserData(localData);
      }
    } finally {
      if (isMounted) {
        setIsLoading(false);
        fetchInProgress.current = false;
        initialFetchDone.current = true;
      }
    }
  }, [user, getLocalData, mergeData, setLocalData, setUserData, cleanup]);


  useEffect(() => {
    // This effect is now just for cleanup
    return () => {
      cleanup();
    };
  }, [cleanup]);

  // Update the autosave function to trigger completion check
  const autosaveStepRef = useRef(
    debounce(async (stepKey, data) => {
      setIsAutosaving(true);
      
      try {
        const normalizedStepData = normalizeStepData(stepKey, data);
        const timestampedData = queueSync(stepKey, normalizedStepData);
        
        setUserData(prev => {
          const newData = { ...prev, [stepKey]: timestampedData };
          // The step completion check will be triggered automatically by DataSyncManager
          return JSON.stringify(prev) === JSON.stringify(newData) ? prev : newData;
        });
      } finally {
        // Reset autosaving state after a delay
        setTimeout(() => setIsAutosaving(false), 1000);
      }
    }, 2000)
  );

  // Immediate autosave function for critical updates (like confirming edits)
  const immediateAutosave = useCallback(async (stepKey, data) => {
    setIsAutosaving(true);
    
    const normalizedStepData = normalizeStepData(stepKey, data);
    const timestampedData = queueSync(stepKey, normalizedStepData);
    
    setUserData(prev => {
      const newData = { ...prev, [stepKey]: timestampedData };
      return JSON.stringify(prev) === JSON.stringify(newData) ? prev : newData;
    });
    
    // Reset autosaving state after a short delay
    setTimeout(() => setIsAutosaving(false), 1000);
  }, [queueSync]);

  const scrollToStep = useCallback((index) => {
    setTimeout(() => {
      const node = stepRefs.current[index];
      if (node) {
        node.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, 150);
  }, [stepRefs]);

  useEffect(() => {
    if (!isLoading) {
      scrollToStep(openStep);
    }
  }, [isLoading, openStep, scrollToStep]);

  // Centralized normalization and fallback
  const normalizedData = normalizeOnboardingData(userData);
  const selectedServices = getSelectedServices(normalizedData);
  const selectedPlans = getSelectedPlans(normalizedData);

  const handleFinalSubmit = async () => {
    const allStepsComplete = stepCompleted.slice(0, steps.length - 1).every(Boolean);
    if (!allStepsComplete || openStep !== steps.length - 1) {
      alert("Please complete all previous steps before submitting. You can navigate to incomplete steps using the step headers above.");
      return;
    }

    setIsSubmitting(true);
    
    try {
      // First save the confirmation step data
      await saveOnboardingStep('confirmation', {
        confirmedAt: new Date().toISOString(),
        userData,
        addressInfo: selectedAddress || userData.serviceDetails?.addressInfo,
        selectedServices: selectedServices || userData.yourServices?.selectedServices,
        selectedPlans: selectedPlans || userData.yourServices?.selectedPlans,
      }, false);

      // Then call finalizeOnboarding with the necessary data
      const finalizationResult = await finalizeOnboarding({
        selectedServices: selectedServices || userData.yourServices?.selectedServices,
        selectedPlans: selectedPlans || userData.yourServices?.selectedPlans,
        addressInfo: selectedAddress || userData.serviceDetails?.addressInfo,
        startDate: userData.yourServices?.startDate,
        preferences: userData.preferences?.preferences
      });
      
      // Update user state to mark onboarding as complete (similar to VerifyPhone pattern)
      if (finalizationResult?.user) {
        setUser(prev => ({
          ...(prev || {}),
          ...finalizationResult.user,
          is_onboarding_complete: true,
          onboarding_complete: true
        }));
      } else {
        // Fallback: update current user state
        setUser(prev => ({
          ...(prev || {}),
          is_onboarding_complete: true,
          onboarding_complete: true
        }));
      }
      
      // Wait for backend to confirm onboarding completion before redirecting
      console.log('🔄 Refreshing user data to confirm onboarding completion...');
      
      try {
        // Force refresh user data from backend to get updated is_onboarding_complete status
        const refreshedUser = await refreshUser();
        
        if (refreshedUser && refreshedUser.is_onboarding_complete) {
          console.log('✅ Onboarding completion confirmed by backend, redirecting to dashboard');
          alert('Your registration has been successfully completed!');
          navigate('/dashboard');
        } else {
          console.warn('⚠️ Backend did not confirm onboarding completion, staying on onboarding page');
          alert('Registration completed but there may be a delay in updating your status. Please refresh the page.');
        }
      } catch (refreshError) {
        console.error('❌ Failed to refresh user data after onboarding completion:', refreshError);
        // Fallback: still redirect but warn user
        alert('Your registration has been completed! If you experience any issues, please refresh the page.');
        navigate('/dashboard');
      }
    } catch (error) {
      alert(`Failed to complete registration: ${error.message}. Please try again. If the problem persists, contact support.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepContent = (index) => {
    if (index !== openStep) return null;
    const stepKey = steps[index]?.key;
    const currentStepData = userData?.[stepKey] || {};
    
    switch (index) {
      case 0: {
        const aboutYouUser = navUser || userData?.initialSelection?.user || user;
        
        // Create more robust initial data for About You section
        const aboutYouInitialData = {
          ...userData.aboutYou,
          // Fallback to user data if aboutYou is empty
          ...((!userData.aboutYou || Object.keys(userData.aboutYou).length === 0) && aboutYouUser ? {
            legalFirstName: aboutYouUser.first_name,
            legalLastName: aboutYouUser.last_name,
            email: aboutYouUser.email,
            mobile: aboutYouUser.mobile || aboutYouUser.phone,
            preferredName: aboutYouUser.preferred_name || aboutYouUser.first_name
          } : {})
        };
        
        console.log('🔍 AboutYou rendering debug:', {
          hasUserDataAboutYou: !!(userData.aboutYou && Object.keys(userData.aboutYou).length > 0),
          hasAboutYouUser: !!aboutYouUser,
          aboutYouInitialDataKeys: Object.keys(aboutYouInitialData),
          aboutYouUser: aboutYouUser ? {
            first_name: aboutYouUser.first_name,
            last_name: aboutYouUser.last_name,
            email: aboutYouUser.email
          } : null
        });
        
        return (
          <AboutYouSection
            initialData={aboutYouInitialData}
            onAutosave={data => autosaveStepRef.current('aboutYou', data)}
            user={aboutYouUser}
          />
        );
      }
      case 1:
        return <YourServicesSection 
          initialData={userData} 
          selectedServices={selectedServices}
          selectedPlans={selectedPlans}
          onAutosave={data => autosaveStepRef.current('yourServices', data)}
          isAutosaving={isAutosaving}
          onNext={(data, shouldAutoAdvance = true) => {
            // Mark the step as confirmed when user proceeds
            const confirmedData = {
              ...data,
              confirmed: true,
              userConfirmed: true,
              confirmedAt: new Date().toISOString()
            };

            // Update local state immediately when services are confirmed
            setUserData(prev => ({
              ...prev,
              yourServices: {
                ...prev.yourServices,
                ...confirmedData
              }
            }));
            
            // Use immediate autosave for critical updates like confirming edits
            immediateAutosave('yourServices', confirmedData);
            
            // Only auto-advance if explicitly requested (e.g., from Continue button)
            if (shouldAutoAdvance) {
              setTimeout(() => {
                const nextStepIndex = 2; // Service Details step
                if (nextStepIndex < steps.length) {
                  navigateToStep(nextStepIndex);
                  scrollToStep(nextStepIndex);
                }
              }, 2000); // Small delay to ensure save completes
            }
          }}
        />;
      case 2:
        return <ServiceDetailsSection
          userData={userData}
          selectedServices={selectedServices}
          selectedPlans={selectedPlans}
          onAutosave={data => autosaveStepRef.current('serviceDetails', data)}
          initialData={currentStepData}
        />;
      case 3:
        return <HowYoullPaySection
          userData={userData}
          selectedServices={selectedServices}
          selectedPlans={selectedPlans}
          onAutosave={data => autosaveStepRef.current('howYoullPay', data)}
          initialData={currentStepData}
        />;
      case 4:
        return <PreferencesSection
          userData={userData}
          selectedServices={selectedServices}
          selectedPlans={selectedPlans}
          onAutosave={data => autosaveStepRef.current('preferences', data)}
          initialData={currentStepData}
        />;
      case 5:
        return (
          <ConfirmationSection
            userData={userData}
            addressInfo={selectedAddress || userData.serviceDetails?.addressInfo || userData.step_data?.initialSelection?.selectedAddress}
            selectedServices={selectedServices}
            selectedPlans={selectedPlans}
            onFinalSubmit={handleFinalSubmit}
            onComplete={() => navigate('/dashboard')}
            isParentSubmitting={isSubmitting}
          />
        );
      default:
        return <div>Error: Unknown Step</div>;
    }
  };

  // Render an error message if essential data is missing initially
  const hasAddress = selectedAddress
    || userData.serviceDetails?.addressInfo
    || userData.step_data?.initialSelection?.selectedAddress
    || userData.yourServices?.addressInfo;
  
  const hasServices = selectedServices
    || userData.yourServices?.selectedServices
    || userData.step_data?.initialSelection?.selectedServices;

  // Allow direct navigation if user has existing onboarding data or if they're authenticated
  const canProceed = hasAddress || hasServices || user || userData.aboutYou || Object.keys(userData).length > 0;

  if (!isLoading && !canProceed) {
    return (
      <PageWrapper>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center text-white">
          <h2 className="text-2xl font-semibold mb-4">Welcome to Onboarding</h2>
          <p className="mb-6">To get the best experience, please start from the Getting Started page where you can select your address and services.</p>
          <button
            onClick={() => navigate('/getstarted')}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Go to Getting Started
          </button>
          <button
            onClick={() => {
              // Allow user to continue anyway
              setIsLoading(false);
              // Set some default data to allow progression
              setUserData(prev => ({
                ...prev,
                aboutYou: prev.aboutYou || {},
                yourServices: prev.yourServices || { selectedServices: {}, selectedPlans: {} }
              }));
            }}
            className="mt-4 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Continue Anyway
          </button>
        </div>
      </PageWrapper>
    );
  }

  if (isLoading) {
    return (
      <PageWrapper>
        <div className="flex justify-center items-center min-h-[80vh]">
          <Loader size="xl" message="Loading onboarding state..." />
        </div>
      </PageWrapper>
    );
  }

  // Check about you data specifically

  // Add the instructions section render function
  const renderInstructions = () => (
    <div className="w-full max-w-3xl px-0.5 mx-auto mb-4">
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700/50 rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 shadow-sm">
        <div className="mb-4">
          <h2 className="text-base text-left font-semibold text-gray-900 dark:text-white mb-4">
            What You Might Need to Complete
          </h2>
          <div className="flex items-center gap-2 px-2 py-1 bg-accent-green/10 rounded-full w-fit">
            <svg className="h-4 w-4 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs font-medium text-accent-green">
              Average Time: {onboardingInstructions.timeToComplete}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          {onboardingInstructions.requirements.map((requirement, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 bg-white dark:bg-gray-800/50 rounded-lg border border-gray-200/50 dark:border-gray-700/50"
            >
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-accent-green/10 flex items-center justify-center">
                {requirement.icon === 'identification' && (
                  <svg className="h-4 w-4 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
                  </svg>
                )}
                {requirement.icon === 'banknotes' && (
                  <svg className="h-4 w-4 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                )}
                {requirement.icon === 'calendar' && (
                  <svg className="h-4 w-4 text-accent-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                )}
              </div>
              <div className="flex-1 text-left">
                <h3 className="text-xs font-semibold text-gray-900 dark:text-white mb-0.5">
                  {requirement.title}
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  {requirement.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <PageWrapper>
      <div className="flex mx-auto md:w-5/6 lg:w-3/4 xl:w-2/3 max-w-4xl min-h-[80vh] flex-col items-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white sm:px-6 rounded-xl shadow-xl pt-12 my-8 py-6">
        <div className="w-full max-w-[120px] sm:max-w-[150px] mx-auto pt-4 pb-2 sm:pt-6 sm:pb-3">
          <div className="mx-auto rounded-md p-2">
            <img alt="SpotOn Icon" src={Icon} className="mx-auto h-16 sm:h-20 w-auto" />
          </div>
        </div>

        <div className="w-full max-w-[180px] sm:max-w-xs mx-auto pb-3 sm:pb-4">
          <div className="mx-auto rounded-md p-1">
            <img alt="SpotOn Text" src={Text} className="mx-auto h-8 sm:h-10 w-auto" />
          </div>
        </div>

        <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-gray-600 to-transparent my-8"></div>
        
        {/* Logout button above the instructions tile */}
        <div className="w-full max-w-3xl px-0.5 mx-auto mb-2 flex justify-end">
          <button
            type="button"
            onClick={logout}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-accent-red to-rose-500 hover:from-rose-600 hover:to-accent-red shadow-sm focus:outline-none focus:ring-2 focus:ring-rose-300 dark:focus:ring-rose-500"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>

        {/* Instructions section */}
        {renderInstructions()}

        <div className="w-full max-w-3xl px-0.5 mx-auto mb-6">
          {steps.map((step, index) => {
            const isCompleted = stepCompleted[index];
            const isOpen = index === openStep;
            const isActuallyEditable = true;
            const headerId = `step-header-${index}`;
            const contentId = `step-content-${index}`;
            const stepNumber = index + 1;

            return (
              <div
                key={step.key}
                ref={(el) => (stepRefs.current[index] = el)}
                className={`mb-5 border border-gray-300 rounded-xl shadow-sm overflow-hidden transition-all duration-300`}
              >
                <button
                  id={headerId}
                  className={`w-full flex items-center justify-between px-5 py-4 text-left transition ${
                    isActuallyEditable
                      ? 'bg-gray-800 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-accent-lightturquoise focus:ring-offset-1 text-white'
                      : 'bg-gray-700 cursor-not-allowed text-white'
                  }`}
                  onClick={() => {
                    if (isActuallyEditable && index !== openStep) {
                      navigateToStep(index);
                    }
                  }}
                  type="button"
                  disabled={!isActuallyEditable}
                  aria-expanded={isOpen}
                  aria-controls={contentId}
                >
                  <div className="flex items-center gap-3 pointer-events-none">
                    {isCompleted ? (
                      <span className="flex-shrink-0 flex items-center justify-center h-8 w-8 rounded-full bg-green-600">
                        <CheckIcon className="h-5 w-5 text-white" aria-hidden="true" />
                      </span>
                    ) : (
                      <span className={`flex-shrink-0 flex items-center justify-center h-8 w-8 rounded-full border-2 text-sm font-bold ${
                        isOpen ? 'border-accent-lightturquoise text-accent-lightturquoise' : 'border-gray-300 text-gray-300'
                      }`}
                      >
                        {stepNumber}
                      </span>
                    )}
                    <div className="text-left px-2">
                      <h3 className={`text-base font-semibold ${isOpen || isCompleted ? 'text-accent-lightturquoise' : 'text-white'}`}> 
                        {step.name}
                      </h3>
                      <p className={`text-sm ${isOpen || isCompleted ? 'text-accent-lightturquoise/90' : 'text-gray-300'}`}> 
                        {step.description}
                      </p>
                    </div>
                  </div>
                  {isActuallyEditable && (
                    <div className="flex items-center">
                      {isOpen ? (
                        <ChevronUpIcon className="h-5 w-5 text-accent-lightturquoise" />
                      ) : (
                        <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                      )}
                    </div>
                  )}
                </button>
                <div
                  id={contentId}
                  role="region"
                  aria-labelledby={headerId}
                  className={`transition-all duration-500 ease-in-out px-0.5 ${isOpen ? (step.key === 'aboutYou' ? 'h-full ' : 'h-full overflow-y-auto') : 'max-h-0'}`}
                >
                  <div className={`border-t border-gray-200 bg-secondary-darkgray text-gray-800 ${isOpen ? 'visible' : 'py-0 invisible h-0'}`}> 
                    {isOpen && renderStepContent(index)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <footer className="pt-4 pb-2 text-center text-xs sm:text-sm text-gray-500">
          &copy; {new Date().getFullYear()} SpotOn. All rights reserved.
        </footer>

        {/* Add the sync status indicator */}
        <SyncStatusIndicator
          syncStatus={syncStatus.status}
          stepName={syncStatus.stepName}
          autoHide={true}
        />
      </div>
    </PageWrapper>
  );
}