import React from 'react';
import { motion } from 'framer-motion';
import PropTypes from 'prop-types';
import { ChevronRight, MoreVertical } from 'lucide-react';

const MobileOptimizedCard = ({
  children,
  title,
  subtitle,
  icon: Icon,
  theme = 'default',
  actionable = false,
  onTap,
  onMenuTap,
  className = '',
  ...props
}) => {
  const themeStyles = {
    default: 'bg-white border-gray-200',
    power: 'bg-gradient-to-r from-primary-turquoise-50 to-primary-turquoise-100 border-primary-turquoise-200',
    broadband: 'bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200',
    mobile: 'bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200',
    billing: 'bg-gradient-to-r from-red-50 to-red-100 border-red-200',
    support: 'bg-gradient-to-r from-green-50 to-green-100 border-green-200',
  };

  const iconThemes = {
    default: 'text-gray-600',
    power: 'text-primary-turquoise-600',
    broadband: 'text-purple-600',
    mobile: 'text-blue-600',
    billing: 'text-red-600',
    support: 'text-green-600',
  };

  const cardClasses = [
    'rounded-2xl border shadow-sm backdrop-blur-sm',
    'transition-all duration-300 ease-out',
    actionable ? 'active:scale-95 active:shadow-md' : '',
    themeStyles[theme],
    className
  ].filter(Boolean).join(' ');

  const CardContent = (
    <div className="p-4">
      {/* Header */}
      {(title || subtitle || Icon) && (
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            {Icon && (
              <div className="flex-shrink-0">
                <Icon className={`h-6 w-6 ${iconThemes[theme]}`} />
              </div>
            )}
            {(title || subtitle) && (
              <div className="flex-1 min-w-0">
                {title && (
                  <h3 className="text-base font-semibold text-secondary-darkgray-800 truncate">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="text-sm text-secondary-darkgray-600 truncate">
                    {subtitle}
                  </p>
                )}
              </div>
            )}
          </div>
          
          {/* Action indicators */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            {onMenuTap && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onMenuTap();
                }}
                className="p-2 rounded-full hover:bg-gray-100 active:bg-gray-200 transition-colors touch-manipulation"
                style={{ minWidth: '44px', minHeight: '44px' }}
              >
                <MoreVertical className="h-4 w-4 text-gray-500" />
              </button>
            )}
            {actionable && (
              <ChevronRight className="h-5 w-5 text-gray-400" />
            )}
          </div>
        </div>
      )}

      {/* Content */}
      {children && (
        <div className="space-y-3">
          {children}
        </div>
      )}
    </div>
  );

  if (actionable && onTap) {
    return (
      <motion.button
        className={`w-full text-left ${cardClasses}`}
        onClick={onTap}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.15 }}
        style={{ minHeight: '44px' }}
        {...props}
      >
        {CardContent}
      </motion.button>
    );
  }

  return (
    <motion.div
      className={cardClasses}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      {...props}
    >
      {CardContent}
    </motion.div>
  );
};

MobileOptimizedCard.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  subtitle: PropTypes.string,
  icon: PropTypes.elementType,
  theme: PropTypes.oneOf(['default', 'power', 'broadband', 'mobile', 'billing', 'support']),
  actionable: PropTypes.bool,
  onTap: PropTypes.func,
  onMenuTap: PropTypes.func,
  className: PropTypes.string,
};

export default MobileOptimizedCard;
