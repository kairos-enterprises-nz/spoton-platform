import PropTypes from 'prop-types';

/**
 * FieldSyncIndicator - Shows sync status for a specific form field
 * 
 * @param {Object} props
 * @param {string} props.status - Current sync status: 'synced', 'syncing', 'error', 'unsaved'
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.position - Position style ('right', 'left')
 */
const FieldSyncIndicator = ({ 
  status = 'synced', 
  className = '',
  position = 'right'
}) => {
  // Status configurations
  const statusConfig = {
    synced: {
      icon: (
        <svg className="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M5 13L9 17L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      color: 'text-accent-green',
      tooltip: 'Saved'
    },
    syncing: {
      icon: (
        <svg className="w-full h-full animate-spin" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 6V3M12 21v-3M6.75 12h-3M20.25 12h-3M18.364 18.364l-2.121-2.121M7.757 7.757L5.636 5.636M18.364 5.636l-2.121 2.121M7.757 16.243l-2.121 2.121" 
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      color: 'text-blue-400',
      tooltip: 'Saving...'
    },
    error: {
      icon: (
        <svg className="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      color: 'text-red-500',
      tooltip: 'Error saving'
    },
    unsaved: {
      icon: (
        <svg className="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="2" />
          <circle cx="12" cy="12" r="3" fill="currentColor" />
        </svg>
      ),
      color: 'text-amber-500',
      tooltip: 'Unsaved changes'
    }
  };
  
  // Position configurations
  const positionConfig = {
    'right': 'right-2',
    'left': 'left-2'
  };
  
  // Get current configurations
  const { icon, color, tooltip } = statusConfig[status];
  const positionClass = positionConfig[position];
  
  return (
    <div 
      className={`absolute top-1/2 -translate-y-1/2 ${positionClass} w-4 h-4 ${color} ${className}`}
      title={tooltip}
    >
      {icon}
    </div>
  );
};

FieldSyncIndicator.propTypes = {
  status: PropTypes.oneOf(['synced', 'syncing', 'error', 'unsaved']),
  className: PropTypes.string,
  position: PropTypes.oneOf(['right', 'left']),
};

export default FieldSyncIndicator;
