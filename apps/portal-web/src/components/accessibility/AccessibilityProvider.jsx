import React, { createContext, useContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';

// Accessibility Context
const AccessibilityContext = createContext();

// Accessibility preferences
const defaultPreferences = {
  reduceMotion: false,
  highContrast: false,
  fontSize: 'normal', // small, normal, large, extra-large
  focusVisible: true,
  screenReader: false
};

// Accessibility Provider Component
export const AccessibilityProvider = ({ children }) => {
  const [preferences, setPreferences] = useState(defaultPreferences);
  const [isScreenReaderActive, setIsScreenReaderActive] = useState(false);

  // Detect user preferences from system
  useEffect(() => {
    const detectSystemPreferences = () => {
      const newPreferences = { ...defaultPreferences };

      // Detect reduced motion preference
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        newPreferences.reduceMotion = true;
      }

      // Detect high contrast preference
      if (window.matchMedia('(prefers-contrast: high)').matches) {
        newPreferences.highContrast = true;
      }

      // Detect if screen reader is likely active
      const hasScreenReader = window.navigator.userAgent.includes('NVDA') ||
                             window.navigator.userAgent.includes('JAWS') ||
                             window.speechSynthesis ||
                             window.navigator.userAgent.includes('VoiceOver');
      
      if (hasScreenReader) {
        newPreferences.screenReader = true;
        setIsScreenReaderActive(true);
      }

      setPreferences(newPreferences);
    };

    detectSystemPreferences();

    // Listen for changes in system preferences
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');

    const handleMotionChange = (e) => {
      setPreferences(prev => ({ ...prev, reduceMotion: e.matches }));
    };

    const handleContrastChange = (e) => {
      setPreferences(prev => ({ ...prev, highContrast: e.matches }));
    };

    motionQuery.addListener(handleMotionChange);
    contrastQuery.addListener(handleContrastChange);

    return () => {
      motionQuery.removeListener(handleMotionChange);
      contrastQuery.removeListener(handleContrastChange);
    };
  }, []);

  // Apply accessibility preferences to document
  useEffect(() => {
    const root = document.documentElement;

    // Apply reduced motion
    if (preferences.reduceMotion) {
      root.style.setProperty('--transition-duration', '0.01ms');
      root.style.setProperty('--animation-duration', '0.01ms');
      root.classList.add('reduce-motion');
    } else {
      root.style.removeProperty('--transition-duration');
      root.style.removeProperty('--animation-duration');
      root.classList.remove('reduce-motion');
    }

    // Apply high contrast
    if (preferences.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Apply font size
    root.classList.remove('font-small', 'font-normal', 'font-large', 'font-extra-large');
    root.classList.add(`font-${preferences.fontSize}`);

    // Apply focus visible
    if (preferences.focusVisible) {
      root.classList.add('focus-visible');
    } else {
      root.classList.remove('focus-visible');
    }

  }, [preferences]);

  // Update a specific preference
  const updatePreference = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Reset to defaults
  const resetPreferences = () => {
    setPreferences(defaultPreferences);
  };

  // Announce to screen readers
  const announce = (message, priority = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.setAttribute('class', 'sr-only');
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };

  const contextValue = {
    preferences,
    updatePreference,
    resetPreferences,
    isScreenReaderActive,
    announce
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
};

// Hook to use accessibility context
export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  
  return context;
};

// Accessibility Settings Component
export const AccessibilitySettings = ({ className = '' }) => {
  const { preferences, updatePreference, resetPreferences } = useAccessibility();

  const fontSizeOptions = [
    { value: 'small', label: 'Small' },
    { value: 'normal', label: 'Normal' },
    { value: 'large', label: 'Large' },
    { value: 'extra-large', label: 'Extra Large' }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-semibold text-secondary-darkgray-800 mb-4">
          Accessibility Settings
        </h3>
        
        {/* Reduce Motion */}
        <div className="flex items-center justify-between py-3 border-b border-gray-200">
          <div>
            <label htmlFor="reduce-motion" className="text-sm font-medium text-secondary-darkgray-700">
              Reduce Motion
            </label>
            <p className="text-xs text-secondary-darkgray-500 mt-1">
              Minimize animations and transitions
            </p>
          </div>
          <input
            id="reduce-motion"
            type="checkbox"
            checked={preferences.reduceMotion}
            onChange={(e) => updatePreference('reduceMotion', e.target.checked)}
            className="h-4 w-4 text-primary-turquoise-600 focus:ring-primary-turquoise-500 border-gray-300 rounded"
          />
        </div>

        {/* High Contrast */}
        <div className="flex items-center justify-between py-3 border-b border-gray-200">
          <div>
            <label htmlFor="high-contrast" className="text-sm font-medium text-secondary-darkgray-700">
              High Contrast
            </label>
            <p className="text-xs text-secondary-darkgray-500 mt-1">
              Increase color contrast for better visibility
            </p>
          </div>
          <input
            id="high-contrast"
            type="checkbox"
            checked={preferences.highContrast}
            onChange={(e) => updatePreference('highContrast', e.target.checked)}
            className="h-4 w-4 text-primary-turquoise-600 focus:ring-primary-turquoise-500 border-gray-300 rounded"
          />
        </div>

        {/* Font Size */}
        <div className="py-3 border-b border-gray-200">
          <label htmlFor="font-size" className="text-sm font-medium text-secondary-darkgray-700 block mb-2">
            Font Size
          </label>
          <select
            id="font-size"
            value={preferences.fontSize}
            onChange={(e) => updatePreference('fontSize', e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-turquoise-500 focus:border-primary-turquoise-500 rounded-md"
          >
            {fontSizeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Focus Visible */}
        <div className="flex items-center justify-between py-3 border-b border-gray-200">
          <div>
            <label htmlFor="focus-visible" className="text-sm font-medium text-secondary-darkgray-700">
              Enhanced Focus Indicators
            </label>
            <p className="text-xs text-secondary-darkgray-500 mt-1">
              Show clear focus outlines for keyboard navigation
            </p>
          </div>
          <input
            id="focus-visible"
            type="checkbox"
            checked={preferences.focusVisible}
            onChange={(e) => updatePreference('focusVisible', e.target.checked)}
            className="h-4 w-4 text-primary-turquoise-600 focus:ring-primary-turquoise-500 border-gray-300 rounded"
          />
        </div>

        {/* Reset Button */}
        <div className="pt-4">
          <button
            onClick={resetPreferences}
            className="px-4 py-2 text-sm font-medium text-secondary-darkgray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-turquoise-500"
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
};

// Keyboard navigation helper component
export const KeyboardNavigation = ({ children, className = '' }) => {
  useEffect(() => {
    let isUsingKeyboard = false;

    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        isUsingKeyboard = true;
        document.body.classList.add('using-keyboard');
      }
    };

    const handleMouseDown = () => {
      isUsingKeyboard = false;
      document.body.classList.remove('using-keyboard');
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  return <div className={className}>{children}</div>;
};

AccessibilityProvider.propTypes = {
  children: PropTypes.node.isRequired
};

AccessibilitySettings.propTypes = {
  className: PropTypes.string
};

KeyboardNavigation.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string
};

export default AccessibilityProvider;
