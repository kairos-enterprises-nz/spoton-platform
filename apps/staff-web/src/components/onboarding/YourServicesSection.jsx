import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AddressLookup from "../getstarted/AddressLookup";
import ServiceSelector from "../getstarted/ServiceSelector";
import PlanChecker from "../getstarted/PlanChecker";
import { PencilIcon } from "@heroicons/react/20/solid";
import { Wifi, Zap, Eye, EyeOff, Phone } from "lucide-react";
import PropTypes from "prop-types";
import apiClient from '../../services/apiClient';
import { checkServiceAvailability } from "../../services/serviceAvailability";
import { 
  normalizeOnboardingData, 
  getSelectedAddress, 
  getSelectedServices, 
  getSelectedPlans
} from '../../utils/onboardingDataUtils';
import { getMobilePlansByCity } from '../../services/addressService';

const YourServicesSection = ({ 
  initialData = {}, 
  onNext,
  onAutosave = () => {},
  isAutosaving = false
}) => {
  // Normalize data using utility functions
  const normalizedData = useMemo(() => normalizeOnboardingData(initialData), [initialData]);
  
  // Get standardized data using utility functions
  const selectedAddress = useMemo(() => {
    // First try to get from yourServices step data
    const stepDataAddress = getSelectedAddress(normalizedData);
    if (stepDataAddress) {
      return stepDataAddress;
    }
    // Fallback to initialSelection if no step data
    return normalizedData?.initialSelection?.address || null;
  }, [normalizedData]);

  const selectedServices = useMemo(() => {
    // Always use normalization utility and fallback
    const stepDataServices = getSelectedServices(normalizedData);
    if (stepDataServices && Object.values(stepDataServices).some(v => v === true)) {
      return stepDataServices;
    }
    // Fallback to initialSelection if no step data
    return normalizedData?.initialSelection?.services || { electricity: false, broadband: false, mobile: false };
  }, [normalizedData]);

  const selectedPlans = useMemo(() => {
    // Always use normalization utility and fallback
    let plans = getSelectedPlans(normalizedData);
    const isPlanObject = p => p && typeof p === 'object' && ('pricing_id' in p || 'plan_id' in p);
    if (!plans || Object.values(plans).every(p => !p || typeof p === 'boolean')) {
      if (normalizedData?.initialSelection?.plans && Object.values(normalizedData.initialSelection.plans).some(isPlanObject)) {
        plans = normalizedData.initialSelection.plans;
      }
    }
    // Ensure mobile is included if present in initialSelection.plans
    if (
      (!plans || !plans.mobile || typeof plans.mobile !== 'object' || plans.mobile === null) &&
      normalizedData?.initialSelection?.plans?.mobile
    ) {
      plans = { ...plans, mobile: normalizedData.initialSelection.plans.mobile };
    }
    return plans;
  }, [normalizedData]);
  
  // State declarations
  const [isEditing, setIsEditing] = useState(() => !selectedAddress);
  const [tempAddress, setTempAddress] = useState(selectedAddress);
  const [tempServices, setTempServices] = useState(selectedServices);
  const [tempPlans, setTempPlans] = useState(selectedPlans);
  const [showElectricityRates, setShowElectricityRates] = useState(false);
  const [gstInclusive, setShowGstInclusive] = useState(true);
  const [currentUserType, setUserType] = useState("standard");
  const [isValidating, setIsValidating] = useState(false);
  const [validatedPlans, setValidatedPlans] = useState(null);
  const [lastValidatedIds, setLastValidatedIds] = useState('');
  
  // Track when user is actively making plan selections to prevent validation interference
  const isUserSelectingRef = useRef(false);
  // Track when autosave is in progress to prevent state resets
  const isAutosavingRef = useRef(false);
  
  // Sync parent autosave state with local ref
  useEffect(() => {
    isAutosavingRef.current = isAutosaving;
  }, [isAutosaving]);
  
  // Derive services from plans for display purposes (now includes mobile)
  const servicesFromPlans = useMemo(() => {
    const currentPlansToCheck = isEditing ? tempPlans : selectedPlans;
    return {
      electricity: !!(currentPlansToCheck?.electricity?.pricing_id),
      broadband: !!(currentPlansToCheck?.broadband?.pricing_id),
      mobile: !!(currentPlansToCheck?.mobile?.pricing_id)
    };
  }, [isEditing, tempPlans, selectedPlans]);

  const toggleGstInclusive = useCallback(() => {
    setShowGstInclusive(prev => !prev);
  }, []);

  // Update temp states when initialData changes - but only if user is not actively editing
  useEffect(() => {
    if (isEditing || isUserSelectingRef.current || isAutosavingRef.current) {
      return;
    }
    setTempAddress(selectedAddress);
    setTempServices(selectedServices);
    setTempPlans(selectedPlans);
    if (selectedPlans?.electricity?.userType) {
      setUserType(selectedPlans.electricity.userType);
    }
  }, [selectedAddress, selectedServices, selectedPlans, isEditing]);



  // Force re-validation when selectedPlans changes
  useEffect(() => {
    if (selectedPlans) {
      setValidatedPlans(null);
      setLastValidatedIds('');
    }
  }, [selectedPlans]);

  // Refresh tempAddress with active plans when entering edit mode
  useEffect(() => {
    const refreshPlansForEdit = async () => {
      if (isEditing && selectedAddress && selectedAddress.full_address) {
        try {
          const availability = await checkServiceAvailability(selectedAddress, ["electricity", "broadband", "mobile"]);
          const addressWithActivePlans = {
            ...selectedAddress,
            electricity: availability.electricity,
            broadband: availability.broadband,
            mobile: availability.mobile,
          };
          setTempAddress(addressWithActivePlans);
        } catch {
          // Keep the existing address if refresh fails
        }
      }
    };
    refreshPlansForEdit();
  }, [isEditing, selectedAddress]);

  // Plan validation effect (now includes mobile)
  useEffect(() => {
    if (isValidating || isUserSelectingRef.current || isEditing || !selectedPlans || !selectedAddress) {
      return;
    }
    const currentIds = [
      selectedPlans.electricity?.pricing_id,
      selectedPlans.broadband?.pricing_id,
      selectedPlans.mobile?.pricing_id
    ].filter(Boolean).sort().join(',');
    if (!currentIds || currentIds === lastValidatedIds) {
      return;
    }
    const timeoutId = setTimeout(async () => {
      if (isValidating || isUserSelectingRef.current || isEditing || !selectedPlans || !selectedAddress) {
        return;
      }
      setIsValidating(true);
      const abortController = new AbortController();
      try {
        const plansToValidate = [];
        if (selectedPlans.electricity?.pricing_id) plansToValidate.push(selectedPlans.electricity.pricing_id);
        if (selectedPlans.broadband?.pricing_id) plansToValidate.push(selectedPlans.broadband.pricing_id);
        if (selectedPlans.mobile?.pricing_id) plansToValidate.push(selectedPlans.mobile.pricing_id);
        if (plansToValidate.length > 0) {
          const response = await apiClient.get('pricing/plans/bulk/', {
            params: { pricing_ids: plansToValidate.join(',') },
            signal: abortController.signal
          });
          const { plans: activePlans = [] } = response.data || {};
          const activePlanMap = activePlans.reduce((acc, plan) => {
            acc[plan.pricing_id] = plan;
            return acc;
          }, {});
          const validatedPlansResult = {
            electricity: selectedPlans.electricity?.pricing_id && activePlanMap[selectedPlans.electricity.pricing_id]
              ? { ...selectedPlans.electricity, ...activePlanMap[selectedPlans.electricity.pricing_id] }
              : null,
            broadband: selectedPlans.broadband?.pricing_id && activePlanMap[selectedPlans.broadband.pricing_id]
              ? { ...selectedPlans.broadband, ...activePlanMap[selectedPlans.broadband.pricing_id] }
              : null,
            mobile: selectedPlans.mobile?.pricing_id && activePlanMap[selectedPlans.mobile.pricing_id]
              ? { ...selectedPlans.mobile, ...activePlanMap[selectedPlans.mobile.pricing_id] }
              : null
          };
          setValidatedPlans(validatedPlansResult);
          setLastValidatedIds(currentIds);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          setValidatedPlans(null);
          setLastValidatedIds('');
        }
      } finally {
        setIsValidating(false);
      }
    }, 5000);
    return () => clearTimeout(timeoutId);
  }, [selectedPlans, selectedAddress, isEditing, isValidating, lastValidatedIds]);

  // Address selection
  const handleAddressSelected = useCallback(async (address) => {
    if (!address) {
      setTempServices({ electricity: false, broadband: false, mobile: false });
      setTempAddress(null);
      // Do not autosave here in edit mode
      return;
    }
    try {
      const availability = await checkServiceAvailability(address, ["electricity", "broadband", "mobile"]);
      const addressWithPlans = {
        ...address,
        electricity: availability.electricity,
        broadband: availability.broadband,
        mobile: availability.mobile,
      };
      setTempAddress(addressWithPlans);
      // Do not autosave here in edit mode
    } catch {
      setTempAddress(address);
      // Do not autosave here in edit mode
    }
  }, [tempServices, tempAddress]);

  // Services selection
  const handleServicesSelected = useCallback((services) => {
    const servicesChanged = JSON.stringify(services) !== JSON.stringify(tempServices);
    setTempServices(services);
    if (servicesChanged) {
      setTempPlans(prevPlans => {
        const updatedPlans = { ...prevPlans };
        if (!services.electricity && tempServices.electricity) updatedPlans.electricity = null;
        if (!services.broadband && tempServices.broadband) updatedPlans.broadband = null;
        if (!services.mobile && tempServices.mobile) updatedPlans.mobile = null;
        return updatedPlans;
      });
      // Do not autosave here in edit mode
    }
  }, [tempAddress, tempServices]);

  // Plan selection
  const handlePlanSelected = useCallback((plans) => {
    isUserSelectingRef.current = true;
    const updatedPlans = {
      electricity: plans?.electricity ? { ...plans.electricity } : null,
      broadband: plans?.broadband ? { ...plans.broadband } : null,
      mobile: plans?.mobile ? { ...plans.mobile } : null
    };

    setTempPlans(updatedPlans);
    setValidatedPlans(null);
    setLastValidatedIds('');
    const flagTimeout = setTimeout(() => {
      isUserSelectingRef.current = false;
    }, 1000);
    return () => {
      clearTimeout(flagTimeout);
    };
  }, []);

  // Confirm changes
  const handleConfirmChanges = useCallback(async (plansFromContinue = null) => {
    // Use the latest tempPlans or the plans passed from PlanChecker
    const finalPlans = plansFromContinue || tempPlans;

    const filteredPlans = finalPlans ? {
      electricity: tempServices.electricity ? finalPlans.electricity : null,
      broadband: tempServices.broadband ? finalPlans.broadband : null,
      mobile: tempServices.mobile ? finalPlans.mobile : null
    } : null;
    setTempPlans(filteredPlans);
    setIsEditing(false);
    setValidatedPlans(null);
    setLastValidatedIds('');
    isUserSelectingRef.current = false;

    // Save the selected plans for the user and force backend sync
    const dataToSave = {
      yourServices: {
        addressInfo: tempAddress,
        selectedAddress: tempAddress,
        selectedServices: tempServices,
        selectedPlans: filteredPlans,
        lastModified: new Date().toISOString(),
        completed: true,
        hasPower: tempServices.electricity,
        hasBroadband: tempServices.broadband,
        hasMobile: tempServices.mobile
      },
      // Also include at top level for compatibility
      selectedAddress: tempAddress,
      selectedServices: tempServices,
      selectedPlans: filteredPlans
    };

    try {
      // Prepare the data structure for both autosave and next step
      const nextStepData = {
        yourServices: {
          ...dataToSave.yourServices,
          selectedServices: tempServices,
          selectedPlans: filteredPlans,
          addressInfo: tempAddress,
          selectedAddress: tempAddress,
          hasPower: tempServices.electricity,
          hasBroadband: tempServices.broadband,
          hasMobile: tempServices.mobile,
          completed: true,
          lastModified: new Date().toISOString()
        },
        // Also include at top level for compatibility
        selectedAddress: tempAddress,
        selectedServices: tempServices,
        selectedPlans: filteredPlans
      };
      


      // First trigger autosave with the complete data structure
      if (onAutosave) {
        await onAutosave(nextStepData);
      }
      
      // Then proceed to next step with the same data structure
      if (onNext) {
        onNext(nextStepData);
      }
    } catch (error) {
      console.error('Failed to save services data:', error);
      // Re-enable editing if save fails
      setIsEditing(true);
    }
  }, [tempAddress, tempServices, tempPlans, onNext, onAutosave]);

  // Cancel editing
  const handleCancelEdit = useCallback(() => {
    setTempAddress(selectedAddress);
    setTempServices(selectedServices);
    setTempPlans(selectedPlans);
    setIsEditing(false);
  }, [selectedAddress, selectedServices, selectedPlans]);

  // Use validatedPlans or selectedPlans based on validation state
  const currentPlans = useMemo(() => {
    if (isEditing) {
      return tempPlans;
    }
    if (validatedPlans && selectedPlans) {
      const currentIds = [
        selectedPlans.electricity?.pricing_id,
        selectedPlans.broadband?.pricing_id,
        selectedPlans.mobile?.pricing_id
      ].filter(Boolean).sort().join(',');
      if (currentIds === lastValidatedIds) {
        return validatedPlans;
      }
    }
    return selectedPlans;
  }, [isEditing, tempPlans, validatedPlans, selectedPlans, lastValidatedIds]);

  // --- Mobile plans state ---
  const [mobilePlans, setMobilePlans] = useState([]);
  const [hasLoadedMobilePlans, setHasLoadedMobilePlans] = useState(false);
  const [isLoadingMobilePlans, setIsLoadingMobilePlans] = useState(false);
  const [mobilePlansError, setMobilePlansError] = useState(null);

  // Fetch mobile plans when mobile is selected
  useEffect(() => {
    let isMounted = true;
    if (tempServices?.mobile) {
      setIsLoadingMobilePlans(true);
      setMobilePlansError(null);
      getMobilePlansByCity()
        .then((plans) => {
          if (isMounted) {
            // Transform mobile plans to match the structure used in GetStarted.jsx
            const transformedPlans = plans.map(plan => ({
              ...plan,
              charges: {
                // Spread the nested charges if they exist, otherwise use the plan charges directly
                ...(plan.charges?.charges || plan.charges || {}),
                // Add features data at the top level
                data_allowance: plan.charges?.features?.data_allowance || plan.charges?.data_allowance,
                minutes: plan.charges?.features?.minutes || plan.charges?.minutes,
              },
            }));

            setMobilePlans(transformedPlans);
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
    }
    return () => { isMounted = false; };
  }, [tempServices?.mobile]);

  // --- UI Logic for edit mode ---
  const showAddressLookup = tempServices?.electricity || tempServices?.broadband;
  const showPlans = (
    (tempServices?.mobile && !tempServices?.electricity && !tempServices?.broadband) ||
    ((tempServices?.electricity || tempServices?.broadband) && tempAddress)
  );

  // Render plan card (now includes mobile)
  const renderRateCard = (plan, type, address = null) => {
    if (!plan || !plan.pricing_id) {
      console.log(`renderRateCard: No plan or pricing_id for ${type}:`, plan);
      return null;
    }
    
    // Debug mobile plan structure (temporary) - removed excessive logging
    

    let icon = null;
    let colorClass = "";
    if (type === 'electricity') {
      icon = <Zap className="w-6 h-6 text-white" />;
      colorClass = "from-accent-green/20 via-accent-green/10 to-transparent border-2 border-accent-green/30";
    } else if (type === 'broadband') {
      icon = <Wifi className="w-6 h-6 text-white" />;
      colorClass = "from-purple-400/20 via-purple-400/10 to-transparent border-2 border-purple-400/30";
    } else if (type === 'mobile') {
      icon = <Phone className="w-6 h-6 text-white" />;
      colorClass = "from-blue-400/20 via-blue-400/10 to-transparent border-2 border-blue-400/30";
    }
    return (
      <motion.div 
        className="space-y-4"
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -15 }}
        transition={{ duration: 0.3 }}
      >
        <div className={`relative w-full p-6 rounded-2xl transition-all duration-300 bg-gradient-to-br ${colorClass}`}>
          <div className="flex flex-col h-full">
            <div className="flex flex-col items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-accent-green to-accent-green/70">
                {icon}
              </div>
              <div className="text-center">
                <h4 className="text-xl font-semibold text-white">{plan.name}</h4>
                <p className="text-sm text-slate-300">{plan.term}</p>
              </div>
            </div>
            {/* Address for electricity/broadband */}
            {address && (
              <div className="mb-3">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-white/10 border border-white/10">
                  <span className="text-xs text-slate-300">{type === 'electricity' ? 'Electricity Address:' : 'Broadband Address:'}</span>
                  <span className="text-xs font-medium text-white">{address}</span>
                </div>
              </div>
            )}
            {/* Rate Display for Broadband and Mobile */}
            {(type === 'broadband' || type === 'mobile') && (
              <div className="mb-4 pb-4 border-b border-white/10 text-center">
                <div className="text-2xl font-bold text-white">
                  ${(() => {
                    let rate = 0;
                    if (type === 'mobile') {
                      // Handle multiple possible data structures for mobile plans
                      rate = plan.charges?.monthly_charge || 
                             plan.charges?.charges?.monthly_charge ||
                             plan.monthly_price || 
                             plan.rate || 0;
                    } else {
                      rate = plan.rate || 0;
                    }
                    return (rate * (gstInclusive ? 1.15 : 1)).toFixed(2);
                  })()}
                  <span className="text-base font-medium text-slate-300"> / month</span>
                </div>
                <div className="text-sm text-slate-300">
                  {gstInclusive ? "Incl. GST" : "Excl. GST"}
                </div>
                {/* Mobile plan details */}
                {type === 'mobile' && (
                  <div className="mt-2 space-y-1">
                    {(plan.charges?.data_allowance || plan.charges?.charges?.data_allowance) && (
                      <div className="text-xs text-slate-300">
                        {plan.charges?.data_allowance || plan.charges?.charges?.data_allowance} Data
                      </div>
                    )}
                    {(plan.charges?.minutes || plan.charges?.charges?.minutes) && (
                      <div className="text-xs text-slate-300">
                        {plan.charges?.minutes || plan.charges?.charges?.minutes} Minutes
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            <p className="text-sm text-slate-300 leading-relaxed mb-6 text-center">{plan.description}</p>
            <div className="flex flex-row items-center justify-center gap-4 w-full">
              <a 
                href={type === 'electricity' ? 
                  `/legal/powerterms/?plan=${plan.name.toLowerCase().includes('fixed') ? 'fixed' : plan.name.toLowerCase().includes('tou') ? 'tou' : 'spot'}` : 
                  type === 'broadband' ?
                  `/legal/broadbandterms/?plan=${plan.name.toLowerCase().includes('fibre') ? 'fibre' : plan.name.toLowerCase().includes('wireless') ? 'wireless' : 'rural'}` :
                  `/legal/mobileterms/?plan=${plan.name.toLowerCase()}`
                } 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xs font-medium text-slate-300 hover:text-white hover:font-bold"
              >
                View Plan Terms →
              </a>
              <a 
                href={type === 'electricity' ? "/legal/powerterms?section=general" : type === 'broadband' ? "/legal/broadbandterms?section=general" : "/legal/mobileterms?section=general"}
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xs font-medium text-slate-300 hover:text-white hover:font-bold"
              >
                General Terms →
              </a>
            </div>
          </div>
        </div>
        {/* Electricity Rates Section */}
        {type === 'electricity' && (
          <div className="flex flex-col gap-4">
            <div className="flex justify-center">
              <button
                onClick={() => setShowElectricityRates(prev => !prev)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                  showElectricityRates
                    ? "bg-accent-green/20 text-white"
                    : "bg-white/5 text-white hover:bg-white/10"
                }`}
              >
                {showElectricityRates ? (
                  <>
                    <EyeOff className="h-3 w-3" />
                    <span>Hide Rates</span>
                  </>
                ) : (
                  <>
                    <Eye className="h-3 w-3" />
                    <span>See Rates</span>
                  </>
                )}
              </button>
            </div>
            <AnimatePresence>
              {showElectricityRates && plan.charges && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="p-6 bg-gradient-to-br from-accent-green/10 via-accent-green/5 to-transparent rounded-xl border border-accent-green/20">
                    <div className="mb-4 space-y-2 pb-4 border-b border-white/10">
                      <div className="flex flex-col">
                        <div className="space-y-2">
                          <span className="text-base font-semibold text-white block">
                            {plan.userType === "lowUser" ? "Low User" : "Standard User"} Plan
                          </span>
                          <span className="text-sm text-slate-300 block leading-relaxed">
                            {plan.userType === "lowUser" 
                              ? "Suitable for households using less than 8,000 kWh per year" 
                              : "Suitable for households using more than 8,000 kWh per year"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <table className="w-full text-sm">
                      <thead>
                        <tr>
                          <th className="text-left px-4 py-3 font-semibold text-white">Charge Type</th>
                          <th className="text-right px-4 py-3 font-semibold text-white">Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(plan.charges[currentUserType || "standard"] || {}).map(([label, val]) => {
                          let formattedValue = "";
                          const formattedLabel = label.replace(/_/g, " ");
                          if (val?.amount && val?.unit) {
                            const amountWithGst = val.amount * (gstInclusive ? 1.15 : 1);
                            if (val.unit.toLowerCase().includes("kwh")) {
                              const cents = (amountWithGst * 100)?.toFixed(2);
                              formattedValue = `<span class="text-slate-300 font-medium">${cents} cents per kWh</span>`;
                            } else if (val.unit.toLowerCase().includes("day")) {
                              formattedValue = `<span class="text-slate-300 font-medium">$${amountWithGst.toFixed(2)} per day</span>`;
                            } else if (val.unit.toLowerCase().includes("month")) {
                              formattedValue = `<span class="text-slate-300 font-medium">$${amountWithGst.toFixed(2)} per month</span>`;
                            } else {
                              formattedValue = `<span class="text-slate-300 font-medium">$${amountWithGst.toFixed(2)}${val.unit ? ` ${val.unit}` : ''}</span>`;
                            }
                          }
                          return (
                            <tr key={label} className="border-t border-white/5">
                              <td className="capitalize text-left px-4 py-3 text-slate-300">{formattedLabel}</td>
                              <td 
                                className="text-right px-4 py-3" 
                                dangerouslySetInnerHTML={{ __html: formattedValue }} 
                              />
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    <p className="mt-2 text-xs text-right text-slate-400 italic">
                      {gstInclusive ? "All charges include GST (15%)" : "All charges exclude GST"}
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </motion.div>
    );
  };

  // --- RENDER ---
  return (
    <div className="max-w-3xl mx-auto bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155] rounded-2xl border border-white/10 p-8 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-end">
        {selectedAddress && !isEditing && (
          <button
            onClick={() => {
              setTempServices(selectedServices);
              setTempPlans(selectedPlans); // Preserve current plans in edit mode
              setIsEditing(true);
            }}
            className="flex items-center gap-1.5 text-sm font-medium text-slate-300 hover:text-accent-lightturquoise"
          >
            <PencilIcon className="h-4 w-4" />
            <span>Edit</span>
          </button>
        )}
      </div>
      {isEditing ? (
        <div className="space-y-6">
          {/* Service selection comes first */}
          <ServiceSelector
            selectedAddress={tempAddress}
            onServicesSelected={handleServicesSelected}
            value={tempServices}
          />
          {/* Address lookup only if electricity or broadband is selected */}
          {showAddressLookup && (
            <AddressLookup
              onAddressSelected={handleAddressSelected}
              initialAddress={tempAddress}
            />
          )}
          {/* Show plans if mobile-only or if address is provided for electricity/broadband */}
          {showPlans && (
            <PlanChecker
              key={`plans-${tempAddress?.full_address || 'mobileonly'}-${JSON.stringify(tempServices)}`}
              selectedAddress={tempAddress}
              selectedServices={tempServices}
              onPlanSelect={handlePlanSelected}
              onContinueToDetails={handleConfirmChanges}
              initialPlans={tempPlans}
              currentPlans={tempPlans}
              mobilePlans={mobilePlans}
              hasLoadedMobilePlans={hasLoadedMobilePlans}
              isLoadingMobilePlans={isLoadingMobilePlans}
              mobilePlansError={mobilePlansError}
            />
          )}
          <div className="flex flex-col sm:flex-row justify-end items-stretch sm:items-center gap-3 mt-6 pt-6 border-t border-white/10">
            <button
              onClick={handleCancelEdit}
              className="px-4 py-2 text-slate-300 bg-[#1e293b] border border-white/20 rounded-md hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white/10 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : selectedAddress ? (
        <div className="space-y-6">
          {/* --- SELECTED SERVICES FIRST --- */}
          {(servicesFromPlans.electricity || servicesFromPlans.broadband || servicesFromPlans.mobile) && (
            <div className="text-center">
              <h3 className="text-sm font-bold text-slate-300 mb-2">Selected Services</h3>
              <div className="inline-flex items-center gap-3 px-4 py-2 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                {servicesFromPlans.electricity && (
                  <span className="inline-flex items-center gap-1.5 text-accent-green">
                    <Zap className="h-4 w-4" />
                    <span className="text-base font-medium">Electricity</span>
                  </span>
                )}
                {servicesFromPlans.electricity && (servicesFromPlans.broadband || servicesFromPlans.mobile) && (
                  <span className="text-slate-400">•</span>
                )}
                {servicesFromPlans.broadband && (
                  <span className="inline-flex items-center gap-1.5 text-purple-400">
                    <Wifi className="h-4 w-4" />
                    <span className="text-base font-medium">Broadband</span>
                  </span>
                )}
                {servicesFromPlans.broadband && servicesFromPlans.mobile && (
                  <span className="text-slate-400">•</span>
                )}
                {servicesFromPlans.mobile && (
                  <span className="inline-flex items-center gap-1.5 text-blue-400">
                    <Phone className="h-4 w-4" />
                    <span className="text-base font-medium">Mobile</span>
                  </span>
                )}
              </div>
            </div>
          )}
          {/* --- SELECTED PLANS --- */}
          {selectedPlans && (
            <div className="mt-8 pt-6 border-t border-white/10">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Selected Plans</h3>
              {/* GST Toggle */}
              <div className="flex items-center justify-center gap-3 mb-4">
                <div className="flex items-center gap-2 px-3 py-1.5">
                  <span className="text-xs text-slate-300">Prices:</span>
                  <button
                    onClick={toggleGstInclusive}
                    className="relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus:outline-none"
                    style={{
                      backgroundColor: gstInclusive ? 'rgba(174, 238, 238, 0.2)' : 'rgba(255, 255, 255, 0.05)'
                    }}
                  >
                    <span
                      className={`inline-block h-3 w-3 transform rounded-full bg-white shadow-lg transition-transform duration-200 ease-in-out ${
                        gstInclusive ? 'translate-x-5' : 'translate-x-1'
                      }`}
                    />
                    <span className="sr-only">Toggle GST</span>
                  </button>
                  <span className={`text-xs font-medium transition-colors duration-200 ${
                    gstInclusive ? 'text-accent-lightturquoise' : 'text-slate-400'
                  }`}>
                    {gstInclusive ? 'Including GST' : 'Excluding GST'}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Electricity Plan Section */}
                {servicesFromPlans.electricity && (isEditing ? tempPlans?.electricity?.pricing_id : currentPlans?.electricity?.pricing_id) && (
                  <div className="mt-8">
                    <h4 className="text-lg font-bold text-accent-green mt-2 mb-2 text-center">Electricity Plan</h4>
                    {selectedAddress?.full_address && (
                      <div className="flex items-center justify-center gap-2 mb-2 text-xs text-slate-300">
                        <svg className="w-4 h-4 text-primary-turquoise" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.828 0l-4.243-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        <span>{selectedAddress.full_address}</span>
                      </div>
                    )}
                    <div className="max-w-md mx-auto">
                      {renderRateCard(isEditing ? tempPlans.electricity : currentPlans.electricity, 'electricity')}
                    </div>
                  </div>
                )}
                {/* Broadband Plan Section */}
                {servicesFromPlans.broadband && (isEditing ? tempPlans?.broadband?.pricing_id : currentPlans?.broadband?.pricing_id) && (
                  <div className="mt-8">
                    <h4 className="text-lg font-bold text-purple-400 mt-2 mb-2 text-center">Broadband Plan</h4>
                    {selectedAddress?.full_address && (
                      <div className="flex items-center justify-center gap-2 mb-2 text-xs text-slate-300">
                        <svg className="w-4 h-4 text-primary-turquoise" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.828 0l-4.243-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        <span>{selectedAddress.full_address}</span>
                      </div>
                    )}
                    <div className="max-w-md mx-auto">
                      {renderRateCard(isEditing ? tempPlans.broadband : currentPlans.broadband, 'broadband')}
                    </div>
                  </div>
                )}
                {/* Mobile Plan Section */}
                {servicesFromPlans.mobile && (isEditing ? tempPlans?.mobile?.pricing_id : currentPlans?.mobile?.pricing_id) && (
                  <div className="mt-8">
                    <h4 className="text-lg font-bold text-blue-400 mt-2 mb-2 text-center">Mobile Plan</h4>
                    <div className="max-w-md mx-auto">
                      {renderRateCard(isEditing ? tempPlans.mobile : currentPlans.mobile, 'mobile')}
                    </div>
                  </div>
                )}
                {/* Show message if services are selected but no active plans exist */}
                {isValidating ? (
                  <div className="col-span-2 text-center p-6">
                    <p className="text-sm text-slate-400">Validating plans...</p>
                  </div>
                ) : (() => {
                  const plansToCheck = isEditing ? tempPlans : currentPlans;
                  const hasActiveElectricityPlan = plansToCheck?.electricity && plansToCheck.electricity?.pricing_id;
                  const hasActiveBroadbandPlan = plansToCheck?.broadband && plansToCheck.broadband?.pricing_id;
                  const hasActiveMobilePlan = plansToCheck?.mobile && plansToCheck.mobile?.pricing_id;
                  const hasAtLeastOnePlan = hasActiveElectricityPlan || hasActiveBroadbandPlan || hasActiveMobilePlan;
                  return !hasAtLeastOnePlan;
                })() ? (
                  <div className="col-span-2 text-center p-6 rounded-xl border border-amber-400/30 bg-gradient-to-br from-amber-400/20 via-amber-400/10 to-transparent">
                    <div className="flex flex-col items-center gap-3">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                        <path d="M12 9v4"></path>
                        <path d="M12 17h.01"></path>
                      </svg>
                      <div>
                        <h4 className="text-lg font-semibold text-white mb-1">Plan Selection Required</h4>
                        <p className="text-sm text-slate-300">
                          {(() => {
                            const plansToCheck = isEditing ? tempPlans : currentPlans;
                            const hasActiveElectricityPlan = plansToCheck?.electricity && plansToCheck.electricity?.pricing_id;
                            const hasActiveBroadbandPlan = plansToCheck?.broadband && plansToCheck.broadband?.pricing_id;
                            const hasActiveMobilePlan = plansToCheck?.mobile && plansToCheck.mobile?.pricing_id;
                            if (!hasActiveElectricityPlan && !hasActiveBroadbandPlan && !hasActiveMobilePlan) {
                              return "Please select at least one plan (electricity, broadband, or mobile) to continue.";
                            } else {
                              return "Please select a valid plan to continue.";
                            }
                          })()} Please edit your selection to choose a plan.
                        </p>
                      </div>
                      <button
                        onClick={() => setIsEditing(true)}
                        className="mt-2 px-4 py-2 bg-amber-400/20 text-amber-400 rounded-md hover:bg-amber-400/30 transition-colors"
                      >
                        Edit Selection
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-slate-300">Please select your property to continue.</p>
        </div>
      )}
    </div>
  );
};

YourServicesSection.propTypes = {
  initialData: PropTypes.object,
  onNext: PropTypes.func,
  onAutosave: PropTypes.func,
  isAutosaving: PropTypes.bool,
};

export default YourServicesSection;