/**
 * Environment-aware logging utility
 * Console logs are only enabled in UAT and development environments
 * Production (Live) environment has all console logs disabled unless debug key is used
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
const runtimeLoggingEnabled = import.meta.env.VITE_ENABLE_CONSOLE_LOGS;

// Domain-based environment detection takes priority
const isProduction = isLiveDomain && !isUATDomain;
const isUAT = isUATDomain && !isLiveDomain;

const isLoggingEnabled = (!isProduction || debugKeyEnabled) && (
  runtimeLoggingEnabled === 'true' || 
  runtimeLoggingEnabled === true ||
  (typeof __ENABLE_CONSOLE_LOGS__ !== 'undefined' 
    ? __ENABLE_CONSOLE_LOGS__ 
    : process.env.NODE_ENV !== 'production')
);

class Logger {
  constructor() {
    this.environment = isProduction ? 'live' : (isUAT ? 'uat' : 'development');
    this.appType = typeof __APP_TYPE__ !== 'undefined' ? __APP_TYPE__ : 'unknown';
    
    // Log environment detection for debugging (only in non-production or with debug key)
    if ((!isProduction || debugKeyEnabled) && this.environment) {
      console.log(`🔧 Logger initialized: domain=${currentDomain}, env=${this.environment}, logging=${isLoggingEnabled}, isUAT=${isUAT}, isProd=${isProduction}, debugKey=${debugKeyEnabled}`);
    }
  }

  log(...args) {
    if (isLoggingEnabled) {
      console.log(`[${this.appType.toUpperCase()}]`, ...args);
    }
  }

  warn(...args) {
    if (isLoggingEnabled) {
      console.warn(`[${this.appType.toUpperCase()}]`, ...args);
    }
  }

  error(...args) {
    if (isLoggingEnabled) {
      console.error(`[${this.appType.toUpperCase()}]`, ...args);
    }
  }

  info(...args) {
    if (isLoggingEnabled) {
      console.info(`[${this.appType.toUpperCase()}]`, ...args);
    }
  }

  debug(...args) {
    if (isLoggingEnabled) {
      console.debug(`[${this.appType.toUpperCase()}]`, ...args);
    }
  }

  // Special method for UAT-only logging
  uatOnly(...args) {
    if ((isUAT || debugKeyEnabled) && !isProduction) {
      console.log(`[${this.appType.toUpperCase()}-UAT]`, ...args);
    }
  }

  // Environment info
  getEnvironmentInfo() {
    return {
      domain: currentDomain,
      environment: this.environment,
      appType: this.appType,
      loggingEnabled: isLoggingEnabled,
      isUAT,
      isProduction,
      isLiveDomain,
      isUATDomain,
      debugKeyEnabled,
      runtimeEnvironment,
      runtimeLoggingEnabled
    };
  }
}

// Create singleton instance
const logger = new Logger();

// Log environment info on initialization (UAT only or with debug key)
if ((isUAT || debugKeyEnabled) && (!isProduction || debugKeyEnabled)) {
  logger.log('Environment Info:', logger.getEnvironmentInfo());
}

export default logger; 