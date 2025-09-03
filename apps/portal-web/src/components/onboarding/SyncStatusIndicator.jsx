import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const SyncStatusIndicator = ({ 
  syncStatus = 'idle', 
  stepName = '',
  autoHide = true 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  // Add debugging
  useEffect(() => {
    // Status changed to syncStatus for stepName
  }, [syncStatus, stepName]);

  useEffect(() => {
    if (syncStatus !== 'idle') {
      setIsVisible(true);
      
      // Auto-hide after successful save
      if (autoHide && (syncStatus === 'saved' || syncStatus === 'saved_locally')) {
        const timer = setTimeout(() => {
          setIsVisible(false);
        }, 3000);
        return () => clearTimeout(timer);
      }
    } else {
      // Hide indicator when status is idle
      setIsVisible(false);
    }
  }, [syncStatus, autoHide, stepName]);

  // Simplified status config - only saving and saved states
  const getStatusConfig = () => {
    switch (syncStatus) {
      case 'saving':
        return {
          icon: ArrowPathIcon,
          text: stepName ? `Saving ${stepName}...` : 'Saving...',
          bgColor: 'bg-blue-500',
          textColor: 'text-blue-100',
          animate: 'animate-spin'
        };
      case 'saved':
      case 'saved_locally':
        return {
          icon: CheckCircleIcon,
          text: stepName ? `${stepName} saved` : 'Saved',
          bgColor: 'bg-green-500',
          textColor: 'text-green-100',
          animate: ''
        };
      default:
        return null;
    }
  };

  const statusConfig = getStatusConfig();

  // Check if we should render the indicator
  if (!isVisible || !statusConfig) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <div 
        className={`${statusConfig.bgColor} ${statusConfig.textColor} px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 min-w-[200px] transition-all duration-300`}
      >
        <statusConfig.icon 
          className={`h-5 w-5 ${statusConfig.animate}`} 
          aria-hidden="true" 
        />
        <span className="text-sm font-medium flex-1">
          {statusConfig.text}
        </span>
      </div>
    </div>
  );
};

SyncStatusIndicator.propTypes = {
  syncStatus: PropTypes.string,
  stepName: PropTypes.string,
  autoHide: PropTypes.bool,
};

export default SyncStatusIndicator;