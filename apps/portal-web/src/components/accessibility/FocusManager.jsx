import React, { useRef, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

// Hook for managing focus
export const useFocusManagement = () => {
  const focusableElementsSelector = `
    a[href]:not([disabled]),
    button:not([disabled]),
    textarea:not([disabled]),
    input[type="text"]:not([disabled]),
    input[type="radio"]:not([disabled]),
    input[type="checkbox"]:not([disabled]),
    select:not([disabled]),
    [tabindex]:not([tabindex="-1"]):not([disabled])
  `;

  const getFocusableElements = useCallback((container) => {
    if (!container) return [];
    return Array.from(container.querySelectorAll(focusableElementsSelector));
  }, [focusableElementsSelector]);

  const trapFocus = useCallback((container) => {
    if (!container) return () => {};

    const focusableElements = getFocusableElements(container);
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    // Focus the first element initially
    firstElement?.focus();

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [getFocusableElements]);

  const restoreFocus = useCallback((previousElement) => {
    if (previousElement && typeof previousElement.focus === 'function') {
      // Use setTimeout to ensure the focus happens after any DOM updates
      setTimeout(() => {
        previousElement.focus();
      }, 0);
    }
  }, []);

  return {
    getFocusableElements,
    trapFocus,
    restoreFocus
  };
};

// Focus trap component for modals and dialogs
const FocusTrap = ({ 
  children, 
  active = true,
  restoreFocus = true,
  className = '',
  ...props 
}) => {
  const containerRef = useRef(null);
  const previousActiveElementRef = useRef(null);
  const { trapFocus, restoreFocus: restorePreviousFocus } = useFocusManagement();

  useEffect(() => {
    if (!active) return;

    // Store the currently focused element
    previousActiveElementRef.current = document.activeElement;

    // Set up focus trap
    const cleanup = trapFocus(containerRef.current);

    return () => {
      cleanup();
      
      // Restore focus to previous element if requested
      if (restoreFocus && previousActiveElementRef.current) {
        restorePreviousFocus(previousActiveElementRef.current);
      }
    };
  }, [active, trapFocus, restoreFocus, restorePreviousFocus]);

  return (
    <div
      ref={containerRef}
      className={className}
      {...props}
    >
      {children}
    </div>
  );
};

// Component for managing focus announcements
const FocusAnnouncement = ({ 
  message, 
  priority = 'polite',
  className = ''
}) => {
  const announcementRef = useRef(null);

  useEffect(() => {
    if (message && announcementRef.current) {
      // Clear and set the message to ensure screen readers announce it
      announcementRef.current.textContent = '';
      setTimeout(() => {
        if (announcementRef.current) {
          announcementRef.current.textContent = message;
        }
      }, 100);
    }
  }, [message]);

  return (
    <div
      ref={announcementRef}
      className={`sr-only ${className}`}
      aria-live={priority}
      aria-atomic="true"
      role="status"
    />
  );
};

// Hook for managing announcements
export const useAnnouncement = () => {
  const [announcement, setAnnouncement] = React.useState('');
  const [priority, setPriority] = React.useState('polite');

  const announce = useCallback((message, announcementPriority = 'polite') => {
    setPriority(announcementPriority);
    setAnnouncement(message);
    
    // Clear the announcement after a delay to allow for re-announcements
    setTimeout(() => {
      setAnnouncement('');
    }, 1000);
  }, []);

  const AnnouncementComponent = () => (
    <FocusAnnouncement message={announcement} priority={priority} />
  );

  return {
    announce,
    AnnouncementComponent
  };
};

// Component for managing page titles and announcements
const PageAnnouncement = ({ 
  title, 
  description,
  announceOnMount = true 
}) => {
  const { announce } = useAnnouncement();

  useEffect(() => {
    if (announceOnMount && title) {
      const message = description ? `${title}. ${description}` : title;
      announce(message, 'assertive');
    }
  }, [title, description, announceOnMount, announce]);

  return null;
};

// Roving tabindex for managing focus in lists/grids
export const useRovingTabindex = (items = []) => {
  const [focusedIndex, setFocusedIndex] = React.useState(0);

  const handleKeyDown = useCallback((e, index) => {
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex((prev) => (prev + 1) % items.length);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex((prev) => (prev - 1 + items.length) % items.length);
        break;
      case 'Home':
        e.preventDefault();
        setFocusedIndex(0);
        break;
      case 'End':
        e.preventDefault();
        setFocusedIndex(items.length - 1);
        break;
    }
  }, [items.length]);

  const getTabIndex = useCallback((index) => {
    return index === focusedIndex ? 0 : -1;
  }, [focusedIndex]);

  const focusItem = useCallback((index) => {
    setFocusedIndex(index);
  }, []);

  return {
    focusedIndex,
    handleKeyDown,
    getTabIndex,
    focusItem
  };
};

FocusTrap.propTypes = {
  children: PropTypes.node.isRequired,
  active: PropTypes.bool,
  restoreFocus: PropTypes.bool,
  className: PropTypes.string
};

FocusAnnouncement.propTypes = {
  message: PropTypes.string.isRequired,
  priority: PropTypes.oneOf(['polite', 'assertive']),
  className: PropTypes.string
};

PageAnnouncement.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
  announceOnMount: PropTypes.bool
};

export { FocusTrap, FocusAnnouncement, PageAnnouncement };
export default FocusTrap;
