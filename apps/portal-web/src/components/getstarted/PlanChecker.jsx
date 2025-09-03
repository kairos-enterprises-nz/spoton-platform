import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import PropTypes from "prop-types";
import { Zap, Wifi, ChevronLeft, ChevronRight, Phone, MapPin } from "lucide-react";
import { Switch } from '@headlessui/react';

// Electricity Plan Terms URLs based on type
const ELECTRICITY_PLAN_TERMS_FIXED_URL = "/legal/powerterms/?plan=fixed";
const ELECTRICITY_PLAN_TERMS_TOU_URL = "/legal/powerterms/?plan=tou";
const ELECTRICITY_PLAN_TERMS_SPOT_URL = "/legal/powerterms/?plan=spot";

// Loading Overlay Component
const LoadingOverlay = ({ message }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="absolute inset-0 bg-[#101828] backdrop-blur-sm z-50 flex items-center justify-center"
  >
    <div className="bg-slate-800 p-6 rounded-xl shadow-xl max-w-sm w-full mx-4">
      <div className="flex flex-col items-center gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-turquoise"></div>
        <p className="text-white text-center">{message}</p>
      </div>
    </div>
  </motion.div>
);

LoadingOverlay.propTypes = {
  message: PropTypes.string
};

export default function PlanChecker({ selectedAddress, selectedServices, onContinueToDetails, initialPlans = null, mobilePlans, isLoadingMobilePlans, onPlanSelect, currentPlans, value }) {
  const [error, setError] = useState(null);
  const [selectedElectricityPlan, setSelectedElectricityPlan] = useState(
    initialPlans?.electricity?.pricing_id || initialPlans?.electricity?.id || null
  );
  const [selectedBroadbandPlan, setSelectedBroadbandPlan] = useState(
    initialPlans?.broadband?.pricing_id || initialPlans?.broadband?.id || null
  );
  const [selectedMobilePlan, setSelectedMobilePlan] = useState(
    initialPlans?.mobile?.pricing_id || initialPlans?.mobile?.id || null
  );
  const [visibleServices, setVisibleServices] = useState({
    electricity: false,
    broadband: false,
    mobile: false
  });
  const [showPlansTitle, setShowPlansTitle] = useState(false);
  const [gstInclusive, setGstInclusive] = useState(true);
  const [showPlans, setShowPlans] = useState(false);
  const [userType, setUserType] = useState("standard");
  const [showElectricityRates, setShowElectricityRates] = useState(false);

  // References for slider functionality
  const electricitySliderRef = useRef(null);
  const broadbandSliderRef = useRef(null);
  const mobileSliderRef = useRef(null);
  const electricityTileRefs = useRef({});
  const broadbandTileRefs = useRef({});
  const mobileTileRefs = useRef({});

  // Slider scroll amounts (px) - responsive values
  const scrollAmount = window?.innerWidth < 640 ? 200 : 300;

  // Scroll state for arrow visibility
  const [electricityScrollState, setElectricityScrollState] = useState({
    canScrollLeft: false,
    canScrollRight: true
  });
  const [broadbandScrollState, setBroadbandScrollState] = useState({
    canScrollLeft: false,
    canScrollRight: true
  });
  const [mobileScrollState, setMobileScrollState] = useState({
    canScrollLeft: false,
    canScrollRight: true
  });

  const toggleUserType = () => {
    setUserType(prev => (prev === "standard" ? "lowUser" : "standard"));
  };

  const toggleElectricityRates = () => {
    setShowElectricityRates(prev => !prev);
  };

  // Check if slider can scroll left/right
  const checkSliderScrollPosition = (sliderRef, setScrollState) => {
    if (!sliderRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = sliderRef.current;
    setScrollState({
      canScrollLeft: scrollLeft > 0,
      canScrollRight: scrollLeft < scrollWidth - clientWidth - 5 // Tolerance of 5px
    });
  };

  // Helper to scroll tile into view
  const scrollTileIntoView = (type, planId) => {
    let ref;
    if (type === 'electricity') {
      ref = electricityTileRefs.current[planId];
    } else if (type === 'broadband') {
      ref = broadbandTileRefs.current[planId];
    } else if (type === 'mobile') {
      ref = mobileTileRefs.current[planId];
    }
    if (ref && ref.scrollIntoView) {
      // Use 'nearest' instead of 'center' for better mobile experience
      ref.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    }
  };
  
  // Handle slider scroll for electricity plans
  const handleElectricityScroll = (direction) => {
    if (!electricitySliderRef.current) return;
    const currentScroll = electricitySliderRef.current.scrollLeft;
    const newScroll = direction === 'left' ?
      currentScroll - scrollAmount :
      currentScroll + scrollAmount;
    electricitySliderRef.current.scrollTo({
      left: newScroll,
      behavior: 'smooth'
    });
    setTimeout(() => {
      checkSliderScrollPosition(electricitySliderRef, setElectricityScrollState);
    }, 300);
  };

  // Handle slider scroll for broadband plans
  const handleBroadbandScroll = (direction) => {
    if (!broadbandSliderRef.current) return;
    const currentScroll = broadbandSliderRef.current.scrollLeft;
    const newScroll = direction === 'left' ?
      currentScroll - scrollAmount :
      currentScroll + scrollAmount;
    broadbandSliderRef.current.scrollTo({
      left: newScroll,
      behavior: 'smooth'
    });
    setTimeout(() => {
      checkSliderScrollPosition(broadbandSliderRef, setBroadbandScrollState);
    }, 300);
  };

  // Handle slider scroll for mobile plans
  const handleMobileScroll = (direction) => {
    if (!mobileSliderRef.current) return;
    const currentScroll = mobileSliderRef.current.scrollLeft;
    const newScroll = direction === 'left' ?
      currentScroll - scrollAmount :
      currentScroll + scrollAmount;
    mobileSliderRef.current.scrollTo({
      left: newScroll,
      behavior: 'smooth'
    });
    setTimeout(() => {
      checkSliderScrollPosition(mobileSliderRef, setMobileScrollState);
    }, 300);
  };

  // Initialize scroll state on component mount and when plans change
  useEffect(() => {
    if (electricitySliderRef.current) {
      checkSliderScrollPosition(electricitySliderRef, setElectricityScrollState);
    }
    if (broadbandSliderRef.current) {
      checkSliderScrollPosition(broadbandSliderRef, setBroadbandScrollState);
    }
    if (mobileSliderRef.current) {
      checkSliderScrollPosition(mobileSliderRef, setMobileScrollState);
    }
    const handleResize = () => {
      checkSliderScrollPosition(electricitySliderRef, setElectricityScrollState);
      checkSliderScrollPosition(broadbandSliderRef, setBroadbandScrollState);
      checkSliderScrollPosition(mobileSliderRef, setMobileScrollState);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [selectedAddress, visibleServices]);

  // Update the useEffect for address selection
  useEffect(() => {
    // Reset states first
    setShowPlansTitle(false);
    setShowPlans(false);
    setVisibleServices({ electricity: false, broadband: false, mobile: false });

    if (selectedAddress?.full_address && (selectedServices.electricity || selectedServices.broadband)) {
      setVisibleServices(selectedServices);
      setShowPlansTitle(true);
      setTimeout(() => setShowPlans(true), 1000);
    } else if (selectedServices.mobile && !selectedServices.electricity && !selectedServices.broadband) {
      setVisibleServices(selectedServices);
      setShowPlansTitle(true);
      setTimeout(() => setShowPlans(true), 1000);
    }
  }, [selectedServices, selectedAddress]);

  useEffect(() => {
    if (!selectedElectricityPlan) {
      setShowElectricityRates(false);
    }
  }, [selectedElectricityPlan, selectedBroadbandPlan, selectedMobilePlan]);

  // Update selected plans when initialPlans prop changes
  useEffect(() => {
    const plansToUse = value || initialPlans;
    console.log('PlanChecker: useEffect triggered with plansToUse:', plansToUse);
    if (plansToUse) {
      const mobilePlanId = plansToUse.mobile?.pricing_id || plansToUse.mobile?.id || null;
      console.log('PlanChecker: Setting selectedMobilePlan to:', mobilePlanId);
      console.log('PlanChecker: Mobile plan object:', plansToUse.mobile);
      
      setSelectedElectricityPlan(
        plansToUse.electricity?.pricing_id || 
        plansToUse.electricity?.id || 
        null
      );
      setSelectedBroadbandPlan(
        plansToUse.broadband?.pricing_id || 
        plansToUse.broadband?.id || 
        null
      );
      setSelectedMobilePlan(mobilePlanId);
      // Also update electricity rates view state
      if (!plansToUse.electricity) {
        setShowElectricityRates(false);
      }
    }
  }, [value, initialPlans]);

  // Show plans 1s after GST toggle is visible
  useEffect(() => {
    setShowPlans(false);
    const timer = setTimeout(() => setShowPlans(true), 0);
    return () => clearTimeout(timer);
  }, [selectedAddress, selectedServices]);

  // Helper to compare plans shallowly
  const arePlansEqual = (a, b) => {
    if (!a || !b) return false;
    return (
      (a.electricity?.pricing_id || a.electricity?.id) === (b.electricity?.pricing_id || b.electricity?.id) &&
      (a.broadband?.pricing_id || a.broadband?.id) === (b.broadband?.pricing_id || b.broadband?.id) &&
      (a.mobile?.pricing_id || a.mobile?.id) === (b.mobile?.pricing_id || b.mobile?.id)
    );
  };

  // Only call onPlanSelect if initialPlans exist and are not already set in the parent
  useEffect(() => {
    if (
      initialPlans &&
      onPlanSelect &&
      (!currentPlans || !arePlansEqual(initialPlans, currentPlans))
    ) {
      console.log('PlanChecker: Initializing parent with initialPlans', initialPlans);
      onPlanSelect(initialPlans);
    }
    // Only run on mount
    // eslint-disable-next-line
  }, []);

  const groupPlansByName = (plans) => {
    if (!plans || !Array.isArray(plans)) {
      return {};
    }
    return plans.reduce((acc, plan) => {
      if (!plan) return acc;
      // Always use pricing_id as the key if available
      const key = plan.pricing_id || plan.id || plan.name;
      if (!key) return acc;
      // Ensure the plan object has its pricing_id
      acc[key] = {
        ...plan,
        pricing_id: plan.pricing_id || plan.id // Ensure pricing_id is always set
      };
      return acc;
    }, {});
  };

  const electricityGroup = groupPlansByName(selectedAddress?.electricity?.plans || []);
  const broadbandGroup = groupPlansByName(selectedAddress?.broadband?.plans || []);
  const mobileGroup = groupPlansByName(mobilePlans || []);

  // Ensure selected plans are still active; if not, clear them and show an error
  useEffect(() => {
    // Check if selected electricity plan is still active (only if electricity service is selected)
    if (selectedElectricityPlan && selectedServices.electricity) {
      const electricityPlan = electricityGroup[selectedElectricityPlan];
      // Only consider a plan inactive if it's missing from the group entirely
      if (!electricityPlan) {
        setSelectedElectricityPlan(null);
        setShowElectricityRates(false);
        setError('Your selected electricity plan is no longer available.');
      }
    }
    // Check if selected broadband plan is still active (only if broadband service is selected)
    if (selectedBroadbandPlan && selectedServices.broadband) {
      const broadbandPlan = broadbandGroup[selectedBroadbandPlan];
      // Only consider a plan inactive if it's missing from the group entirely
      if (!broadbandPlan) {
        setSelectedBroadbandPlan(null);
        setError('Your selected broadband plan is no longer available.');
      }
    }
    // Check if selected mobile plan is still active (only if mobile service is selected)
    if (selectedMobilePlan && selectedServices.mobile) {
      // Don't validate mobile plans if they're still loading OR if no mobile plans have been loaded yet
      if (!isLoadingMobilePlans && mobilePlans && mobilePlans.length > 0) {
        const mobilePlan = mobileGroup[selectedMobilePlan];
        // Only consider a plan inactive if it's missing from the group entirely
        if (!mobilePlan) {
          console.log('PlanChecker: Mobile plan not found in group, clearing selection');
          setSelectedMobilePlan(null);
          setError('Your selected mobile plan is no longer available.');
        } else {
          setError(null); // Clear any existing errors
        }
      } else {
        console.log('PlanChecker: Skipping mobile plan validation - loading or no plans loaded yet:', {
          isLoadingMobilePlans,
          mobilePlansLength: mobilePlans?.length || 0,
          selectedMobilePlan
        });
      }
    }
  }, [electricityGroup, broadbandGroup, mobileGroup, selectedElectricityPlan, selectedBroadbandPlan, selectedMobilePlan, selectedServices, isLoadingMobilePlans, mobilePlans]);

  // IMPROVED: Enhanced table responsiveness for mobile devices
  const renderElectricityCharges = (charges, currentUserType, gstInclusive = false) => {
    if (!charges) {
      return <p className="text-sm text-gray-500">Charges not available.</p>;
    }
    const userCharges = charges[currentUserType] || charges.standard;
    return (
      <div className="overflow-x-auto -mx-2 sm:mx-0 max-w-full">
        <table className="w-full text-xs sm:text-sm">
          <thead>
            <tr>
              <th className="text-left px-2 sm:px-4 py-2 font-semibold text-gray-700">Charge Type</th>
              <th className="text-right px-2 sm:px-4 py-2 font-semibold text-gray-700">Rate</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(userCharges || {}).map(([label, val]) => {
              let formattedValue = "";
              const formattedLabel = label.replace(/_/g, " ");
              const amountWithGst = val?.amount * (gstInclusive ? 1.15 : 1);
              if (val?.unit?.toLowerCase().includes("kwh")) {
                const cents = (amountWithGst * 100)?.toFixed(2);
                formattedValue = `<span class="text-gray-600">${cents}</span> cents per kWh`;
              } else if (val?.unit?.toLowerCase().includes("day")) {
                const cents = (amountWithGst * 100)?.toFixed(2);
                formattedValue = `<span class="text-gray-600">${cents}</span> cents per day`;
              } else if (amountWithGst >= 0) {
                const cents = (amountWithGst * 100)?.toFixed(2);
                formattedValue = `<span class="text-gray-600">${cents}</span> cents`;
                if (val?.unit) {
                  formattedValue += ` per ${val.unit}`;
                }
              } else {
                const cents = (amountWithGst * 100)?.toFixed(2);
                formattedValue = `<span class="text-red-600">${cents}</span> cents`;
                if (val?.unit) {
                  formattedValue += ` per ${val.unit}`;
                }
              }
              return (
                <tr key={label} className="border-t border-gray-100">
                  <td className="capitalize text-left px-2 sm:px-4 py-2 text-gray-600">{formattedLabel}</td>
                  <td className="text-right px-2 sm:px-4 py-2 text-gray-600 font-medium" dangerouslySetInnerHTML={{ __html: formattedValue }} />
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  // IMPROVED: Better responsive layout for electricity plan block
  const renderElectricityPlanBlock = (planName, currentUserType, onToggleUserType) => {
    const plan = electricityGroup[planName];
    if (!plan) {
      return null;
    }
    return (
      <motion.div
        className="mt-2 border border-gray-100 bg-gray-50 p-3 sm:p-6 rounded-2xl shadow-sm"
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -15 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex flex-col mb-3 gap-2">
          <div>
            <h5 className="text-base sm:text-lg text-left font-bold text-gray-900">{plan.name}</h5>
            <p className="text-xs sm:text-sm text-gray-600 mt-1">{plan.rate_details}</p>
          </div>
          {/* IMPROVED: Better mobile layout for user type toggle */}
          {plan.charges?.lowUser && (
            <div className="flex items-center mt-2 gap-2 sm:gap-3">
              <span className="text-xs sm:text-sm font-medium text-gray-700 whitespace-nowrap">Standard User</span>
              <Switch
                checked={currentUserType === "lowUser"}
                onChange={onToggleUserType}
                className={`${
                  currentUserType === "lowUser" ? "bg-green-500" : "bg-gray-300"
                } relative inline-flex h-5 sm:h-6 w-9 sm:w-11 items-center rounded-full transition-colors flex-shrink-0`}
              >
                <span
                  className={`${
                    currentUserType === "lowUser" ? "translate-x-5 sm:translate-x-6" : "translate-x-1"
                  } inline-block h-3 sm:h-4 w-3 sm:w-4 transform rounded-full bg-white transition-transform`}
                />
              </Switch>
              <span className="text-xs sm:text-sm font-medium text-gray-700 whitespace-nowrap">Low User</span>
            </div>
          )}
        </div>
        {/* IMPROVED: Better padding and spacing for mobile */}
        <div className="rounded-xl border border-gray-200 bg-white p-2 sm:p-4">
          <h6 className="font-semibold mx-2 text-start text-gray-700 text-sm sm:text-base mb-2">Charges Breakdown</h6>
          {renderElectricityCharges(plan.charges, currentUserType, gstInclusive)}
          <p className="mt-2 text-xs text-end mx-2 text-gray-400 italic">
            {gstInclusive ? "All charges include GST (15%)" : "All charges exclude GST"}
          </p>
        </div>
      </motion.div>
    );
  };

  // Helper to check if a service is available (has plans)
  const isServiceAvailable = (serviceId) => {
    if (serviceId === 'electricity') return Object.keys(electricityGroup).length > 0;
    if (serviceId === 'broadband') return Object.keys(broadbandGroup).length > 0;
    if (serviceId === 'mobile') return Object.keys(mobileGroup).length > 0;
    return false;
  };

  // Coming soon blurb
  const comingSoonBlurb = {
    electricity: 'Electricity plans for your address are coming soon. Check back later!',
    broadband: 'Broadband plans for your address are coming soon. Check back later!',
    mobile: 'Mobile plans are coming soon. Check back later!'
  };

  // Update the renderPlanTile function to handle mobile plans differently
  const renderPlanTile = (planKey, type) => {
    if (type === "mobile" && isLoadingMobilePlans) {
      return (
        <motion.div
          key="mobile-loading"
          className="relative flex-shrink-0 w-48 sm:w-48 md:w-56 lg:w-64 h-auto p-2 sm:p-4 rounded-2xl border border-gray-200 bg-white shadow-sm"
        >
          <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-turquoise"></div>
            <p className="mt-4 text-sm text-gray-500">Loading mobile plans...</p>
            <p className="text-xs text-gray-400 mt-2">This may take a moment</p>
          </div>
        </motion.div>
      );
    }

    const plan =
      type === "electricity" ? electricityGroup[planKey] :
      type === "broadband" ? broadbandGroup[planKey] :
      mobileGroup[planKey];
    
    if (!plan) return null;

    const planId = plan.pricing_id || plan.id || planKey;
    const planName = plan.name;
    
    const isSelected =
      (type === "electricity" && selectedElectricityPlan === planId) ||
      (type === "broadband" && selectedBroadbandPlan === planId) ||
      (type === "mobile" && selectedMobilePlan === planId);

    const refCallback = (el) => {
      if (type === 'electricity') {
        electricityTileRefs.current[planId] = el;
      } else if (type === 'broadband') {
        broadbandTileRefs.current[planId] = el;
      } else if (type === 'mobile') {
        mobileTileRefs.current[planId] = el;
      }
    };
    
    const handleTileClick = () => {
      setError(null);
      
      let newElectricityPlan = selectedElectricityPlan;
      let newBroadbandPlan = selectedBroadbandPlan;
      let newMobilePlan = selectedMobilePlan;
      
      if (type === "electricity") {
        if (selectedElectricityPlan === planId) {
          newElectricityPlan = null;
          setSelectedElectricityPlan(null);
          setShowElectricityRates(false);
        } else {
          newElectricityPlan = planId;
          setSelectedElectricityPlan(planId);
          setShowElectricityRates(false);
          setTimeout(() => scrollTileIntoView('electricity', planId), 20);
        }
      } else if (type === "broadband") {
        if (selectedBroadbandPlan === planId) {
          newBroadbandPlan = null;
          setSelectedBroadbandPlan(null);
        } else {
          newBroadbandPlan = planId;
          setSelectedBroadbandPlan(planId);
          setTimeout(() => scrollTileIntoView('broadband', planId), 20);
        }
      } else if (type === "mobile") {
        console.log('PlanChecker: Mobile plan clicked:', {
          clickedPlanId: planId,
          currentSelectedMobilePlan: selectedMobilePlan,
          isDeselecting: selectedMobilePlan === planId
        });
        if (selectedMobilePlan === planId) {
          console.log('PlanChecker: Deselecting mobile plan');
          newMobilePlan = null;
          setSelectedMobilePlan(null);
        } else {
          console.log('PlanChecker: Selecting mobile plan:', planId);
          newMobilePlan = planId;
          setSelectedMobilePlan(planId);
          setTimeout(() => scrollTileIntoView('mobile', planId), 20);
        }
      }

      // Notify parent component of plan changes immediately
      if (onPlanSelect) {
        const updatedPlans = {
          electricity: selectedServices.electricity && newElectricityPlan ? {
            ...electricityGroup[newElectricityPlan],
            userType,
            gstInclusive,
            pricing_id: newElectricityPlan
          } : null,
          broadband: selectedServices.broadband && newBroadbandPlan ? {
            ...broadbandGroup[newBroadbandPlan],
            gstInclusive,
            pricing_id: newBroadbandPlan
          } : null,
          mobile: selectedServices.mobile && newMobilePlan ? {
            ...mobileGroup[newMobilePlan],
            gstInclusive,
            pricing_id: newMobilePlan
          } : null
        };
        console.log('PlanChecker: Calling onPlanSelect with updated plans:', {
          mobilePlan: updatedPlans.mobile ? {
            name: updatedPlans.mobile.name,
            pricing_id: updatedPlans.mobile.pricing_id,
            plan_id: updatedPlans.mobile.plan_id
          } : null
        });
        onPlanSelect(updatedPlans);
      }
    };

    return (
      <AnimatePresence>
        <motion.div
          key={planId}
          ref={refCallback}
          onClick={handleTileClick}
          className={`relative flex-shrink-0 w-48 sm:w-48 md:w-56 lg:w-64 h-auto p-2 sm:p-4 rounded-2xl border-2 ${
            isSelected ? 'border-accent-green bg-white' : 'border-gray-200 bg-white'
          } shadow-sm cursor-pointer transition-all duration-300 hover:shadow-md`}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {/* Combined checkmark and Plan Selected badge for selected tile */}
          {isSelected && (
            <div className="absolute top-2 right-2 flex items-center  bg-accent-green text-white text-xs font-bold px-2 py-0.5 rounded-full shadow z-10">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Selected
            </div>
          )}
          <div className="flex flex-col gap-2">
            <div className="text-[#40E0D0] mb-1">{type === "electricity" ? <Zap className="w-4 h-4 sm:w-5 sm:h-5" /> :
              type === "broadband" ? <Wifi className="w-4 h-4 sm:w-5 sm:h-5" /> :
              <Phone className="w-4 h-4 sm:w-5 sm:h-5" />}</div>
            <div className="text-sm sm:text-base font-semibold text-gray-800 line-clamp-2">{planName}</div>
            <div className="text-xs uppercase tracking-wider text-gray-400">{type.toUpperCase()}</div>
            <div className="text-sm font-bold text-gray-900">
              {type === "mobile" ? (
                <>
                  <div className="text-sm font-bold">
                    ${gstInclusive ? (plan?.charges?.monthly_charge * 1.15)?.toFixed(2) : plan?.charges?.monthly_charge?.toFixed(2)} / month
                  </div>
                  <div className="text-xs font-light mb-2 text-gray-500">
                    {gstInclusive ? "Incl. GST" : "Excl. GST"}
                  </div>
                  <div className="text-xs text-gray-600">
                    {plan?.charges?.data_allowance} Data
                  </div>
                  <div className="text-xs text-gray-600">
                    {plan?.charges?.minutes} Minutes
                  </div>
                </>
              ) : type === "broadband" ? (
                <>
                  <div className="text-sm font-bold">
                    ${gstInclusive ? (plan?.rate * 1.15)?.toFixed(2) : plan?.rate?.toFixed(2)} / month
                  </div>
                  <div className="text-xs font-light mb-2 text-gray-500">
                    {gstInclusive ? "Incl. GST" : "Excl. GST"}
                  </div>
                </>
              ) : null}
            </div>
            {plan?.term && (
              <span className="inline-block text-xs px-2 py-1 rounded-full font-medium tracking-wide bg-gray-100 text-gray-700">
                {plan.term}
              </span>
            )}
            {plan?.description && (
              <p className="text-xs mt-2 text-gray-600 line-clamp-3">
                {plan.description}
              </p>
            )}
            {renderTermsLinks(type, plan, isSelected, (e) => e.stopPropagation())}
          </div>
        </motion.div>
      </AnimatePresence>
    );
  };

  const handleConfirm = () => {
    // Clear any existing errors
    setError(null);

    // Validate that at least one plan is selected (electricity OR broadband OR mobile)
    const hasAtLeastOnePlan = (
      (selectedServices.electricity && selectedElectricityPlan) ||
      (selectedServices.broadband && selectedBroadbandPlan) ||
      (selectedServices.mobile && selectedMobilePlan)
    );

    if (!hasAtLeastOnePlan) {
      setError('Please select at least one plan (electricity, broadband, or mobile) to continue.');
      return;
    }

    const plans = {
      electricity: selectedServices.electricity && selectedElectricityPlan ? {
        ...electricityGroup[selectedElectricityPlan],
        userType,
        gstInclusive,
        pricing_id: selectedElectricityPlan
      } : null,
      broadband: selectedServices.broadband && selectedBroadbandPlan ? {
        ...broadbandGroup[selectedBroadbandPlan],
        gstInclusive,
        pricing_id: selectedBroadbandPlan
      } : null,
      mobile: selectedServices.mobile && selectedMobilePlan ? {
        ...mobileGroup[selectedMobilePlan],
        gstInclusive,
        pricing_id: selectedMobilePlan
      } : null
    };

    if (typeof onContinueToDetails === 'function') {
      onContinueToDetails(plans);
    }
  };

  // Show error message if it exists
  const renderError = () => {
    if (error) {
      return (
        <div className="text-center p-4 mb-4 rounded-xl border border-amber-400/30 bg-gradient-to-br from-amber-400/20 via-amber-400/10 to-transparent">
          <div className="flex flex-col items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
              <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
              <path d="M12 9v4"></path>
              <path d="M12 17h.01"></path>
            </svg>
            <div>
              <h4 className="text-lg font-semibold text-white mb-1">Plan Selection Required</h4>
              <p className="text-sm text-slate-300">{error}</p>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderTermsLinks = (type, plan, isSelected, onClick) => {
    if (!plan) return null;

    const getElectricityTermsUrl = (plan) => {
      if (plan.name.toLowerCase().includes('spot')) {
        return ELECTRICITY_PLAN_TERMS_SPOT_URL;
      } else if (plan.name.toLowerCase().includes('tou')) {
        return ELECTRICITY_PLAN_TERMS_TOU_URL;
      }
      return ELECTRICITY_PLAN_TERMS_FIXED_URL;
    };

    const ArrowIcon = () => (
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="9 18 15 12 9 6" />
      </svg>
    );

    return (
      <div className="text-xs mt-2 space-y-1">
        <div className="flex items-center justify-center">
          <a
            href={type === 'electricity' ? getElectricityTermsUrl(plan) : type === 'broadband' ? '/legal/broadbandterms' : '/legal/mobileterms'}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClick}
            className="text-gray-600 font-semibold hover:font-bold flex items-center gap-1"
          >
            Plan Terms
            <ArrowIcon />
          </a>
        </div>
        <div className="flex items-center justify-center">
          <a
            href="/legal/generalterms"
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClick}
            className="text-gray-600 font-semibold hover:font-bold flex items-center gap-1"
          >
            General Terms
            <ArrowIcon />
          </a>
        </div>
      </div>
    );
  };

  // Determine which services to show and in what order
  const orderedServices = [
    { id: 'electricity', label: 'Electricity Plans', icon: <Zap className="w-5 h-5" /> },
    { id: 'broadband', label: 'Broadband Plans', icon: <Wifi className="w-5 h-5" /> },
    { id: 'mobile', label: 'Mobile Plans', icon: <Phone className="w-5 h-5" /> }
  ].filter(service => selectedServices[service.id]);

  // Helper to check if continue should be shown - validate that required plans are selected
  const isAnyPlanSelected = (
    (selectedServices.electricity && selectedElectricityPlan) ||
    (selectedServices.broadband && selectedBroadbandPlan) ||
    (selectedServices.mobile && selectedMobilePlan)
  );
  
  // Removed debug logging - validation is working correctly

  return (
    <div className="max-w-4xl mx-auto px-2 sm:px-4 lg:px-6 py-2 relative">
      <AnimatePresence>
        {isLoadingMobilePlans && (
          <LoadingOverlay message="Loading plans..." />
        )}
      </AnimatePresence>
      
      {renderError()}
      
      <AnimatePresence mode="wait">
        {showPlansTitle && (
          <motion.div
            key="title"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="text-center"
          >
            {/* GST toggle */}
            <div className="flex-wrap justify-center items-center gap-2 mt-2 sm:mt-2 mb-4 sm:mb-4">
              <span className="text-sm font-semibold text-slate-300">Prices are shown:</span>
              <div className="flex justify-center items-center pt-2">
                <button
                  onClick={() => setGstInclusive(false)}
                  className={`px-3 py-1 text-xs rounded-l-full transition-colors ${
                    !gstInclusive 
                      ? 'bg-accent-lightturquoise/50 text-white font-bold' 
                      : 'bg-gray-700/50 text-slate-300 hover:bg-gray-700/70'
                  }`}
                >
                  Exclusive of GST
                </button>
                <button
                  onClick={() => setGstInclusive(true)}
                  className={`px-3 py-1 text-xs rounded-r-full transition-colors ${
                    gstInclusive 
                      ? 'bg-accent-lightturquoise/50 text-white font-bold' 
                      : 'bg-gray-700/50 text-slate-300 hover:bg-gray-700/70'
                  }`}
                >
                  Inclusive of GST
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Divider */}
      {showPlansTitle && (
        <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-4 sm:my-6"></div>
      )}

      {showPlans && (
        <AnimatePresence>
          {orderedServices.map((service, index) => (
            <motion.div
              key={`${service.id}-plans-section`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.1 }}
              className="mb-12"
            >
              {index > 0 && (
                <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent my-8"></div>
              )}
              <div className="flex flex-col items-start ml-0 sm:ml-12 mr-0 sm:mr-12 mb-4 sm:mb-6">
                <div className="flex items-center gap-2">
                  {service.icon}
                  <h4 className="text-xl sm:text-2xl font-bold tracking-tight text-white mb-0">
                    {service.label}
                  </h4>
                </div>
                {((service.id === 'electricity' || service.id === 'broadband') && selectedAddress?.full_address) && (
                  <div className="flex items-center gap-2 mt-1 sm:mt-2 bg-slate-800/70 px-2 sm:px-3 py-1 rounded-full text-accent-green text-xs sm:text-sm font-medium shadow-sm">
                    <MapPin className="w-3 sm:w-4 h-3 sm:h-4 text-accent-green" />
                    <span className="truncate max-w-[200px] sm:max-w-xs">{selectedAddress.full_address}</span>
                  </div>
                )}
              </div>
              {!isServiceAvailable(service.id) ? (
                <div className="flex flex-col items-center justify-center min-h-[120px] p-6 bg-slate-800/60 rounded-xl">
                  <h5 className="text-lg font-bold text-white mb-2">Coming Soon</h5>
                  <p className="text-sm text-slate-200">{comingSoonBlurb[service.id]}</p>
                </div>
              ) : (
                <>
                  <div className="relative px-4 sm:px-6 md:px-8 lg:px-12">
                    {service.id === 'electricity' && electricityScrollState.canScrollLeft && (
                      <button
                        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-accent-purple rounded-full shadow-md p-2 hover:bg-primary-turquoise"
                        onClick={() => handleElectricityScroll('left')}
                      >
                        <ChevronLeft className="h-6 w-6 text-white" />
                      </button>
                    )}
                    {service.id === 'broadband' && broadbandScrollState.canScrollLeft && (
                      <button
                        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-accent-purple rounded-full shadow-md p-2 hover:bg-primary-turquoise"
                        onClick={() => handleBroadbandScroll('left')}
                      >
                        <ChevronLeft className="h-6 w-6 text-white" />
                      </button>
                    )}
                    {service.id === 'mobile' && mobileScrollState.canScrollLeft && (
                      <button
                        className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-accent-purple rounded-full shadow-md p-2 hover:bg-primary-turquoise"
                        onClick={() => handleMobileScroll('left')}
                      >
                        <ChevronLeft className="h-6 w-6 text-white" />
                      </button>
                    )}
                    <div
                      ref={
                        service.id === 'electricity' ? electricitySliderRef :
                        service.id === 'broadband' ? broadbandSliderRef :
                        mobileSliderRef
                      }
                      className="flex overflow-x-auto py-6 px-0 space-x-4 scrollbar-hide"
                      style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                      onScroll={() => {
                        if (service.id === 'electricity') {
                          checkSliderScrollPosition(electricitySliderRef, setElectricityScrollState);
                        } else if (service.id === 'broadband') {
                          checkSliderScrollPosition(broadbandSliderRef, setBroadbandScrollState);
                        } else {
                          checkSliderScrollPosition(mobileSliderRef, setMobileScrollState);
                        }
                      }}
                    >
                      {Object.keys(
                        service.id === 'electricity' ? electricityGroup :
                        service.id === 'broadband' ? broadbandGroup :
                        mobileGroup
                      ).map((name) => (
                        <div key={name}>
                          {renderPlanTile(name, service.id)}
                        </div>
                      ))}
                    </div>
                    {service.id === 'electricity' && electricityScrollState.canScrollRight && (
                      <button
                        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-accent-purple rounded-full shadow-md p-2 hover:bg-primary-turquoise"
                        onClick={() => handleElectricityScroll('right')}
                      >
                        <ChevronRight className="h-6 w-6 text-white" />
                      </button>
                    )}
                    {service.id === 'broadband' && broadbandScrollState.canScrollRight && (
                      <button
                        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-accent-purple rounded-full shadow-md p-2 hover:bg-primary-turquoise"
                        onClick={() => handleBroadbandScroll('right')}
                      >
                        <ChevronRight className="h-6 w-6 text-white" />
                      </button>
                    )}
                    {service.id === 'mobile' && mobileScrollState.canScrollRight && (
                      <button
                        className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-accent-purple rounded-full shadow-md p-2 hover:bg-primary-turquoise"
                        onClick={() => handleMobileScroll('right')}
                      >
                        <ChevronRight className="h-6 w-6 text-white" />
                      </button>
                    )}
                  </div>
                  {service.id === 'electricity' && selectedElectricityPlan && (
                    <div className="flex justify-center mt-2">
                      <button
                        onClick={toggleElectricityRates}
                        className="px-2.5 py-1.5 text-xs bg-accent-green text-white rounded-full font-semibold shadow hover:bg-accent-green transition"
                      >
                        {showElectricityRates ? "Hide Rates" : "See Rates"}
                      </button>
                    </div>
                  )}
                  {service.id === 'electricity' && showElectricityRates && selectedElectricityPlan && (
                    <div className="mt-4">
                      {renderElectricityPlanBlock(selectedElectricityPlan, userType, toggleUserType)}
                    </div>
                  )}
                </>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      )}

      {/* Continue Button */}
      {isAnyPlanSelected && (
        <motion.div
          key="continue-button"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="mt-30 flex justify-center"
        >
          <button
            onClick={handleConfirm}
            className="px-8 py-3 bg-accent-green text-white font-bold rounded-full shadow-lg hover:bg-accent-red transition-colors"
          >
            Continue
          </button>
        </motion.div>
      )}

    </div>
  );
}

PlanChecker.propTypes = {
  selectedAddress: PropTypes.object,
  selectedServices: PropTypes.shape({
    electricity: PropTypes.bool,
    broadband: PropTypes.bool,
    mobile: PropTypes.bool,
  }),
  onContinueToDetails: PropTypes.func.isRequired,
  initialPlans: PropTypes.shape({
    electricity: PropTypes.object,
    broadband: PropTypes.object,
    mobile: PropTypes.object,
  }),
  mobilePlans: PropTypes.array,
  isLoadingMobilePlans: PropTypes.bool,
  onPlanSelect: PropTypes.func,
  currentPlans: PropTypes.object,
  value: PropTypes.object,
};