/**
 * Debug utility to help see localStorage contents
 * Run in browser console: window.debugLocalStorage()
 */

export const debugLocalStorage = () => {
  console.log('🔍 LocalStorage Debug Information');
  console.log('=====================================');
  
  // Show all localStorage keys
  const allKeys = Object.keys(localStorage);
  console.log(`📊 Total localStorage keys: ${allKeys.length}`);
  
  if (allKeys.length === 0) {
    console.log('❌ No localStorage data found');
    return;
  }
  
  // Show SpotOn-related keys
  const spotonKeys = allKeys.filter(key => 
    key.toLowerCase().includes('spoton') || 
    key.toLowerCase().includes('onboarding') ||
    key.toLowerCase().includes('tenant') ||
    key.toLowerCase().includes('selected')
  );
  
  console.log(`🎯 SpotOn-related keys: ${spotonKeys.length}`);
  spotonKeys.forEach(key => {
    const value = localStorage.getItem(key);
    console.log(`🔑 ${key}:`, value);
    
    // Try to parse JSON if possible
    try {
      const parsed = JSON.parse(value);
      console.log(`📋 Parsed ${key}:`, parsed);
    } catch (e) {
      // Not JSON, that's fine
    }
  });
  
  // Show all keys for completeness
  console.log('\n📝 All localStorage keys:');
  allKeys.forEach(key => {
    const value = localStorage.getItem(key);
    const truncated = value && value.length > 100 ? value.substring(0, 100) + '...' : value;
    console.log(`  ${key}: ${truncated}`);
  });
  
  // Check specific onboarding key
  const onboardingData = localStorage.getItem('spoton_onboarding_progress');
  if (onboardingData) {
    console.log('\n🎯 Onboarding Progress Data:');
    try {
      const parsed = JSON.parse(onboardingData);
      console.log(parsed);
      
      // Check for address and plan selections
      if (parsed.yourServices) {
        console.log('📍 Address:', parsed.yourServices.selectedAddress || parsed.yourServices.addressInfo);
        console.log('⚡ Services:', parsed.yourServices.selectedServices);
        console.log('📋 Plans:', parsed.yourServices.selectedPlans);
      }
    } catch (e) {
      console.log('❌ Could not parse onboarding data:', e);
    }
  } else {
    console.log('\n❌ No spoton_onboarding_progress found');
  }
  
  return {
    totalKeys: allKeys.length,
    spotonKeys: spotonKeys,
    onboardingData: onboardingData,
    allKeys: allKeys
  };
};

// Make it available globally for browser console testing
if (typeof window !== 'undefined') {
  window.debugLocalStorage = debugLocalStorage;
}

export default debugLocalStorage; 