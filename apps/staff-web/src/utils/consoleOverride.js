/**
 * Console Override Utility
 * Completely disables console methods in production/live environment
 * Detects environment based on actual domain being accessed
 * Supports debug key (?show=true) for emergency debugging
 */

// Check for debug key in URL
const urlParams = new URLSearchParams(window.location.search);
const debugKeyEnabled = urlParams.get('show') === 'true';

// Detect environment based on current domain
const currentDomain = window.location.hostname;
const isLiveDomain = currentDomain === 'live.spoton.co.nz' || 
                     currentDomain === 'portal.spoton.co.nz' || 
                     currentDomain === 'staff.spoton.co.nz';
const isUATDomain = currentDomain.includes('uat.') || 
                    currentDomain === 'localhost' || 
                    currentDomain.startsWith('192.') || 
                    currentDomain.startsWith('172.');

// Check runtime environment variables as fallback
const runtimeEnvironment = import.meta.env.VITE_ENVIRONMENT;

// Domain detection takes priority over environment variables
const isLiveProduction = isLiveDomain && !isUATDomain;

// Store original console methods
const originalConsole = {
  log: console.log,
  warn: console.warn,
  error: console.error,
  info: console.info,
  debug: console.debug,
  trace: console.trace,
  group: console.group,
  groupEnd: console.groupEnd,
  groupCollapsed: console.groupCollapsed,
  table: console.table,
  time: console.time,
  timeEnd: console.timeEnd
};

// Only log environment detection in UAT or when debug key is enabled
if (!isLiveProduction || debugKeyEnabled) {
  originalConsole.log(`🔧 Environment Detection: domain=${currentDomain}, isLive=${isLiveDomain}, isUAT=${isUATDomain}, runtimeEnv=${runtimeEnvironment}, willDisable=${isLiveProduction}, debugKey=${debugKeyEnabled}`);
}

// Disable console methods in production (unless debug key is used)
if (isLiveProduction && !debugKeyEnabled) {
  console.log = () => {};
  console.warn = () => {};
  console.error = () => {};
  console.info = () => {};
  console.debug = () => {};
  console.trace = () => {};
  console.group = () => {};
  console.groupEnd = () => {};
  console.groupCollapsed = () => {};
  console.table = () => {};
  console.time = () => {};
  console.timeEnd = () => {};
  
  // Do NOT log that console has been disabled in production - stay completely silent
} else if (isLiveProduction && debugKeyEnabled) {
  // Debug key enabled - show console but with warning
  originalConsole.warn('🔑 Debug mode enabled with ?show=true - Console logs visible in production!');
} else {
  // UAT/Development environment - keep console enabled
  originalConsole.log('🔊 Console methods enabled for UAT/development environment');
}

export { originalConsole, isLiveProduction, isLiveDomain, isUATDomain, debugKeyEnabled }; 