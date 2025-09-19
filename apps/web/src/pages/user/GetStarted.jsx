import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from 'react-router-dom';
import PageWrapper from '../../components/PageWrapper';
import Loader from '../../components/Loader';
import Icon from '../../assets/utilitycopilot-icon.webp';
import Text from '../../assets/spoton-text-reversed.webp';
import AddressLookup from "../../components/getstarted/AddressLookup";
import ServiceSelector from "../../components/getstarted/ServiceSelector";
import PlanChecker from "../../components/getstarted/PlanChecker";
import { checkServiceAvailability } from "../../services/serviceAvailability";
import { motion, AnimatePresence } from "framer-motion";
import { getMobilePlansByCity } from '../../services/addressService';
import { getEnvUrl } from '../../utils/environment';
// import RegisterInterest from "../../components/getstarted/RegisterInterest";

const GETSTARTED_STORAGE_KEY = 'getstarted';

// Helper functions for localStorage
const saveToLocalStorage = (data) => {
  try {
    const timestampedData = {
      ...data,
      lastModified: new Date().toISOString(),
      page: 'getstarted'
    };
    
    localStorage.setItem(GETSTARTED_STORAGE_KEY, JSON.stringify(timestampedData));
    console.log('💾 GetStarted: Saved to localStorage:', timestampedData);
  } catch (error) {
    console.error('Failed to save GetStarted data to localStorage:', error);
  }
};

const loadFromLocalStorage = () => {
  try {
    const stored = localStorage.getItem(GETSTARTED_STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      console.log('📖 GetStarted: Loaded from localStorage:', data);
      return data;
    }
  } catch (error) {
    console.error('Failed to load GetStarted data from localStorage:', error);
  }
  return null;
};

export default function GettingStarted() {
  const [isLoading, setIsLoading] = useState(false);
  const [loaderMessage, setLoaderMessage] = useState("Loading...");
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [selectedServices, setSelectedServices] = useState({ electricity: false, broadband: false, mobile: false });
  const [selectedPlans, setSelectedPlans] = useState({ electricity: null, broadband: null, mobile: null });
  const [showPlans, setShowPlans] = useState(false);
  const [mobilePlans, setMobilePlans] = useState([]);
  const [hasLoadedMobilePlans, setHasLoadedMobilePlans] = useState(false);
  const [isLoadingMobilePlans, setIsLoadingMobilePlans] = useState(false);
  const [mobilePlansError, setMobilePlansError] = useState(null);
  const [serviceAvailabilityError, setServiceAvailabilityError] = useState(null);
  const navigate = useNavigate();
  const showPlansTimeout = useRef(null);
  const [isBackButtonExpanded, setIsBackButtonExpanded] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const backButtonRef = useRef(null);

  // Detect mobile device
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Handle click outside to collapse back button
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isMobile && isBackButtonExpanded && backButtonRef.current && !backButtonRef.current.contains(event.target)) {
        setIsBackButtonExpanded(false);
      }
    };

    if (isMobile && isBackButtonExpanded) {
      document.addEventListener('touchstart', handleClickOutside);
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('touchstart', handleClickOutside);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isMobile, isBackButtonExpanded]);

  // Load saved data on mount
  useEffect(() => {
    const savedData = loadFromLocalStorage();
    if (savedData) {
      if (savedData.selectedAddress) {
        setSelectedAddress(savedData.selectedAddress);
      }
      if (savedData.selectedServices) {
        setSelectedServices(savedData.selectedServices);
      }
      if (savedData.selectedPlans) {
        setSelectedPlans(savedData.selectedPlans);
      }
      // Show plans if we have services selected
      if (savedData.selectedServices && (savedData.selectedServices.electricity || savedData.selectedServices.broadband || savedData.selectedServices.mobile)) {
        setShowPlans(true);
      }
    }
  }, []);

  // Save to localStorage whenever selections change
  useEffect(() => {
    const dataToSave = {
      selectedAddress,
      selectedServices,
      selectedPlans
    };
    saveToLocalStorage(dataToSave);
  }, [selectedAddress, selectedServices, selectedPlans]);

  // Handle back button click - mobile vs desktop behavior
  const handleBackButtonClick = useCallback(() => {
    if (isMobile) {
      if (isBackButtonExpanded) {
        // Second click - navigate
        const websiteUrl = getEnvUrl('web') || '/';
        window.location.href = websiteUrl;
      } else {
        // First click - expand
        setIsBackButtonExpanded(true);
      }
    } else {
      // Desktop - navigate immediately
      const websiteUrl = getEnvUrl('web') || '/';
      window.location.href = websiteUrl;
    }
  }, [isMobile, isBackButtonExpanded]);

  // When an address is selected, call API, then set address (with plans included)
  const handleAddressSelected = useCallback(async (addressObj) => {
    if (!addressObj) {
      setSelectedAddress(null);
      setSelectedPlans({ electricity: null, broadband: null, mobile: null });
      setShowPlans(false);
      setServiceAvailabilityError(null);
      return;
    }
    
    setServiceAvailabilityError(null);
    
    try {
      // Call API to get electricity/broadband data
      const availability = await checkServiceAvailability(addressObj, ["electricity", "broadband"]);
      setSelectedAddress({
        ...addressObj,
        electricity: availability.electricity,
        broadband: availability.broadband
      });
    } catch (error) {
      console.error('Service availability check failed:', error);
      setSelectedAddress({ ...addressObj });
      setServiceAvailabilityError('Unable to check service availability for this address. Plans may not be available.');
    } finally {
      setIsLoading(false);
      setShowPlans(false);
      setTimeout(() => setShowPlans(true), 1000); // Show plans 1s after GST toggle
    }
  }, []);

  // Handle service selection changes
  const handleServicesSelected = (services) => {
    console.log('[GetStarted] Services selected:', services);
    setSelectedServices(services);
  };

  const handlePlanSelect = (plans) => {
    setSelectedPlans(plans);
  };

  const handleContinueToDetails = (validatedPlans) => {
    console.log('[GetStarted] handleContinueToDetails called with:', validatedPlans);
    console.log('[GetStarted] Current state:', { selectedServices, selectedAddress: !!selectedAddress });
    
    const needsAddress = selectedServices.electricity || selectedServices.broadband;
    console.log('[GetStarted] needsAddress:', needsAddress);
    
    if (needsAddress && (!selectedAddress || !selectedAddress.full_address)) {
      console.log('[GetStarted] BLOCKED: Address required but not provided');
      return;
    }
    if (!selectedServices || typeof selectedServices.electricity !== 'boolean' || 
        typeof selectedServices.broadband !== 'boolean' || 
        typeof selectedServices.mobile !== 'boolean') {
      console.log('[GetStarted] BLOCKED: Invalid selectedServices');
      return;
    }
    // Check that at least one plan is selected (matching PlanChecker logic)
    const hasAtLeastOnePlan = (
      (selectedServices.electricity && validatedPlans?.electricity) ||
      (selectedServices.broadband && validatedPlans?.broadband) ||
      (selectedServices.mobile && validatedPlans?.mobile)
    );
    
    if (!hasAtLeastOnePlan) {
      console.log('[GetStarted] BLOCKED: No plans selected for any service');
      return;
    }
    
    console.log('[GetStarted] All validations passed, proceeding with navigation...');
    setSelectedPlans(validatedPlans);
    setLoaderMessage("Preparing your details...");
    setIsLoading(true);
    const navigationState = {
      selectedAddress: needsAddress ? selectedAddress : null,
      selectedServices,
      selectedPlans: {
        electricity: (selectedServices.electricity && validatedPlans.electricity) ? validatedPlans.electricity : null,
        broadband: (selectedServices.broadband && validatedPlans.broadband) ? validatedPlans.broadband : null,
        mobile: (selectedServices.mobile && validatedPlans.mobile) ? validatedPlans.mobile : null
      }
    };
    console.log('[GetStarted] Navigation state:', navigationState);
    setTimeout(() => {
      navigate('/createaccount', { state: navigationState });
      setIsLoading(false);
    }, 800);
  };

  // Fetch mobile plans when mobile is selected
  useEffect(() => {
    let isMounted = true;
    if (selectedServices.mobile) {
      setIsLoadingMobilePlans(true);
      setMobilePlansError(null);
      getMobilePlansByCity()
        .then((plans) => {
          if (isMounted) {
            setMobilePlans(plans);
            setHasLoadedMobilePlans(true);
          }
        })
        .catch(() => {
          if (isMounted) {
            setMobilePlansError('Failed to load mobile plans. Please try again.');
          }
        })
        .finally(() => {
          if (isMounted) {
            setIsLoadingMobilePlans(false);
          }
        });
    } else {
      setMobilePlans([]);
      setHasLoadedMobilePlans(false);
      setIsLoadingMobilePlans(false);
      setMobilePlansError(null);
      // Clear mobile plan selection when mobile service is unselected
      setSelectedPlans(prevPlans => ({
        ...prevPlans,
        mobile: null
      }));
    }
    return () => { isMounted = false; };
  }, [selectedServices.mobile]);

  // Clear selected plans when electricity/broadband services are unselected
  useEffect(() => {
    setSelectedPlans(prevPlans => ({
      electricity: selectedServices.electricity ? prevPlans.electricity : null,
      broadband: selectedServices.broadband ? prevPlans.broadband : null,
      mobile: prevPlans.mobile // Keep mobile plan as-is, handled by mobile useEffect
    }));
  }, [selectedServices.electricity, selectedServices.broadband]);

  // Determine if address lookup should be shown
  const showAddressLookup = selectedServices.electricity || selectedServices.broadband;
  // Only show address-related info if electricity or broadband is selected
  // Determine if plans should be shown
  const shouldShowPlans = showPlans && (
    (selectedServices.mobile && !selectedServices.electricity && !selectedServices.broadband) ||
    ((selectedServices.electricity || selectedServices.broadband) && selectedAddress)
  );
  
  console.log('[GetStarted] shouldShowPlans:', shouldShowPlans, {
    showPlans,
    selectedServices,
    selectedAddress: !!selectedAddress
  });

  useEffect(() => {
    if (selectedServices.mobile && !selectedServices.electricity && !selectedServices.broadband) {
      setShowPlans(false);
      if (showPlansTimeout.current) clearTimeout(showPlansTimeout.current);
      showPlansTimeout.current = setTimeout(() => setShowPlans(true), 1000);
    } else if (!selectedServices.mobile && !selectedServices.electricity && !selectedServices.broadband) {
      setShowPlans(false);
      if (showPlansTimeout.current) clearTimeout(showPlansTimeout.current);
    } else {
      if (showPlansTimeout.current) clearTimeout(showPlansTimeout.current);
    }
    return () => {
      if (showPlansTimeout.current) clearTimeout(showPlansTimeout.current);
    };
  }, [selectedServices]);

  return (
    <PageWrapper>
      {isLoading && <Loader fullscreen size="xl" message={loaderMessage} />}
      <div className="flex mx-auto w-full sm:w-11/12 md:w-5/6 lg:w-3/4 xl:w-2/3 max-w-4xl min-h-[80vh] flex-col items-center bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] text-white px-4 sm:px-6 rounded-none sm:rounded-xl shadow-xl pt-6 sm:pt-12 my-0 sm:my-8 py-4 sm:py-6">
        {/* Top: Back to Website - Icon transforms to show text on hover (desktop) or click (mobile) */}
        <div className="w-full flex justify-start">
          <button
            ref={backButtonRef}
            onClick={handleBackButtonClick}
            className={`group inline-flex items-center overflow-hidden rounded-full bg-white/10 text-cyan-200 ring-1 ring-white/15 shadow-sm transition-all duration-300 ${
              isMobile 
                ? (isBackButtonExpanded ? 'text-white bg-white/20 ring-white/30' : 'hover:bg-white/15 active:bg-white/20') 
                : 'hover:text-white hover:bg-white/20 hover:ring-white/25 hover:shadow'
            }`}
          >
            {/* Icon - always visible */}
            <div className="flex items-center justify-center w-10 h-10 flex-shrink-0">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </div>
            {/* Text - appears on hover (desktop) or click (mobile) */}
            <span className={`overflow-hidden whitespace-nowrap transition-all duration-300 text-[11px] sm:text-xs font-semibold tracking-wide ${
              isMobile
                ? (isBackButtonExpanded ? 'max-w-xs pr-3' : 'max-w-0')
                : 'max-w-0 group-hover:max-w-xs group-hover:pr-3'
            }`}>
              Back to Website
            </span>
          </button>
        </div>

        {/* Logo and Divider */}
        <div className="w-full max-w-[100px] sm:max-w-[120px] md:max-w-[150px] mx-auto pt-2 pb-1 sm:pt-4 sm:pb-2 md:pt-6 md:pb-3">
          <div className="mx-auto rounded-md p-1">
            <img alt="SpotOn Icon" src={Icon} className="mx-auto h-12 sm:h-16 md:h-20 w-auto" />
          </div>
        </div>
        <div className="w-full max-w-[140px] sm:max-w-[180px] md:max-w-xs mx-auto pb-2 sm:pb-3 md:pb-4">
          <div className="mx-auto rounded-md p-1">
            <img alt="SpotOn Text" src={Text} className="mx-auto h-6 sm:h-8 md:h-10 w-auto" />
          </div>
        </div>
        <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-4 sm:my-6 md:my-8"></div>

        <div className="w-full max-w-3xl mx-auto mb-4 sm:mb-6 space-y-8 sm:space-y-10 md:space-y-12">
          {/* Service Selection - Always visible */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 sm:mb-8"
          >
            <ServiceSelector
              onServicesSelected={handleServicesSelected}
              value={selectedServices}
            />
          </motion.section>
      {/* Divider */}
          <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-3 sm:my-4 md:my-6"></div>
          {/* Address Lookup - Shows when electricity or broadband is selected */}
          <AnimatePresence>
            {showAddressLookup && (
              <motion.section
                key="address"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="mb-6 sm:mb-8"
              >
                <AddressLookup
                  onAddressSelected={handleAddressSelected}
                  value={selectedAddress}
                  selectedServices={selectedServices}
                />
                {serviceAvailabilityError && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-4 bg-red-900/50 border border-red-500/50 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-red-200">Service Availability Issue</p>
                        <p className="text-xs text-red-300 mt-1">{serviceAvailabilityError}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.section>
            )}
          </AnimatePresence>

          {/* Plans - Shows when mobile is selected (mobile-only) or when address is provided for electricity/broadband */}
          <AnimatePresence>
            {shouldShowPlans && (
              <motion.section
                key="plans"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              >
                <PlanChecker
                  selectedAddress={selectedAddress}
                  selectedServices={selectedServices}
                  onPlanSelect={handlePlanSelect}
                  onContinueToDetails={handleContinueToDetails}
                  value={selectedPlans}
                  mobilePlans={mobilePlans.map(plan => ({
                    ...plan,
                    charges: {
                      ...plan.charges.charges,
                      data_allowance: plan.charges.features?.data_allowance,
                      minutes: plan.charges.features?.minutes,
                    },
                  }))}
                  hasLoadedMobilePlans={hasLoadedMobilePlans}
                  isLoadingMobilePlans={isLoadingMobilePlans}
                  mobilePlansError={mobilePlansError}
                />
              </motion.section>
            )}
          </AnimatePresence>
        </div>
        <footer className="pt-12 sm:pt-16 md:pt-24 pb-12 sm:pb-16 md:pb-24 text-center text-xs sm:text-sm text-slate-400">
          &copy; {new Date().getFullYear()} SpotOn. All rights reserved.
        </footer>
      </div>
    </PageWrapper>
  );
}
