import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { User } from 'lucide-react';
import { useDashboard } from '../../../context/DashboardContext';

const UserAvatar = ({ 
  size = 'md', 
  showName = false, 
  showStatus = false,
  className = '',
  onClick 
}) => {
  const { user, getUserDisplayName, getUserInitials } = useDashboard();

  const sizeClasses = {
    sm: 'h-8 w-8 text-sm',
    md: 'h-10 w-10 text-base',
    lg: 'h-12 w-12 text-lg',
    xl: 'h-16 w-16 text-xl'
  };

  const avatarClasses = `
    ${sizeClasses[size]}
    rounded-full bg-gradient-to-br from-primary-turquoise to-secondary-darkgray
    flex items-center justify-center text-white font-semibold
    shadow-md border-2 border-white/20 backdrop-blur-sm
    transition-all duration-300 ease-out
    ${onClick ? 'cursor-pointer hover:scale-105 hover:shadow-lg' : ''}
    ${className}
  `;

  const AvatarContent = () => (
    <div className={avatarClasses}>
      {user ? (
        <span className="font-bold tracking-wide">
          {getUserInitials()}
        </span>
      ) : (
        <User className="h-1/2 w-1/2" />
      )}
    </div>
  );

  const avatar = onClick ? (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className="focus:outline-none focus:ring-2 focus:ring-primary-turquoise/50 rounded-full"
    >
      <AvatarContent />
    </motion.button>
  ) : (
    <AvatarContent />
  );

  if (!showName && !showStatus) {
    return avatar;
  }

  return (
    <div className="flex items-center space-x-3">
      {avatar}
      
      {(showName || showStatus) && (
        <div className="flex flex-col">
          {showName && (
            <span className="text-sm font-medium text-secondary-darkgray">
              {getUserDisplayName()}
            </span>
          )}
          
          {showStatus && user && (
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-accent-green rounded-full animate-pulse" />
              <span className="text-xs text-gray-500">
                {user.is_staff ? 'Staff' : user.user_type || 'User'}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

UserAvatar.propTypes = {
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  showName: PropTypes.bool,
  showStatus: PropTypes.bool,
  className: PropTypes.string,
  onClick: PropTypes.func
};

export default UserAvatar; 