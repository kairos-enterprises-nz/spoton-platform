import React from 'react';
import { motion } from 'framer-motion';
import PropTypes from 'prop-types';

const Card = React.forwardRef(({
  children,
  variant = 'default',
  padding = 'md',
  theme = 'default',
  hover = true,
  gradient = false,
  className = '',
  ...props
}, ref) => {
  // Variant styles
  const variants = {
    default: 'bg-white border-gray-200/60 shadow-sm',
    elevated: 'bg-white border-gray-200/60 shadow-md',
    outlined: 'bg-white border-2 border-gray-300 shadow-none',
    filled: 'bg-gray-50 border-gray-200 shadow-none',
    glass: 'bg-white/80 backdrop-blur-sm border-white/20 shadow-lg',
  };

  // Padding styles
  const paddings = {
    none: 'p-0',
    xs: 'p-3',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };

  // Theme-specific styles
  const themeStyles = {
    power: gradient ? 'bg-gradient-to-br from-primary-turquoise-500 to-primary-turquoise-600 text-white border-primary-turquoise-400' : 'border-primary-turquoise-200/50',
    broadband: gradient ? 'bg-gradient-to-br from-service-broadband to-purple-600 text-white border-purple-400' : 'border-purple-200/50',
    mobile: gradient ? 'bg-gradient-to-br from-service-mobile to-blue-600 text-white border-blue-400' : 'border-blue-200/50',
    billing: gradient ? 'bg-gradient-to-br from-service-billing to-red-600 text-white border-red-400' : 'border-red-200/50',
    support: gradient ? 'bg-gradient-to-br from-service-support to-green-600 text-white border-green-400' : 'border-green-200/50',
  };

  // Hover effects
  const hoverEffects = hover ? [
    'transition-all duration-300 ease-out',
    'hover:shadow-lg hover:-translate-y-1',
    theme !== 'default' && !gradient ? `hover:shadow-${theme}` : 'hover:shadow-primary-turquoise/10',
  ].filter(Boolean).join(' ') : '';

  // Combine classes
  const cardClasses = [
    // Base styles
    'rounded-2xl border backdrop-blur-sm',
    
    // Variant styles
    variants[variant],
    
    // Padding
    paddings[padding],
    
    // Theme styles
    theme !== 'default' ? themeStyles[theme] : '',
    
    // Hover effects
    hoverEffects,
    
    // Custom classes
    className
  ].filter(Boolean).join(' ');

  const MotionCard = motion.div;

  return (
    <MotionCard
      ref={ref}
      className={cardClasses}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      {...props}
    >
      {children}
    </MotionCard>
  );
});

Card.displayName = 'Card';

// Card Header Component
const CardHeader = ({ children, className = '', ...props }) => (
  <div className={`mb-6 ${className}`} {...props}>
    {children}
  </div>
);

CardHeader.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

// Card Title Component
const CardTitle = ({ children, size = 'lg', className = '', ...props }) => {
  const sizes = {
    sm: 'text-heading-sm',
    md: 'text-heading-md',
    lg: 'text-heading-lg',
    xl: 'text-heading-xl',
  };

  return (
    <h3 className={`${sizes[size]} text-secondary-darkgray-700 font-semibold ${className}`} {...props}>
      {children}
    </h3>
  );
};

CardTitle.propTypes = {
  children: PropTypes.node.isRequired,
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  className: PropTypes.string,
};

// Card Description Component
const CardDescription = ({ children, className = '', ...props }) => (
  <p className={`text-body-sm text-secondary-darkgray-500 mt-2 ${className}`} {...props}>
    {children}
  </p>
);

CardDescription.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

// Card Content Component
const CardContent = ({ children, className = '', ...props }) => (
  <div className={`${className}`} {...props}>
    {children}
  </div>
);

CardContent.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

// Card Footer Component
const CardFooter = ({ children, className = '', ...props }) => (
  <div className={`mt-6 pt-6 border-t border-gray-200 ${className}`} {...props}>
    {children}
  </div>
);

CardFooter.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['default', 'elevated', 'outlined', 'filled', 'glass']),
  padding: PropTypes.oneOf(['none', 'xs', 'sm', 'md', 'lg', 'xl']),
  theme: PropTypes.oneOf(['default', 'power', 'broadband', 'mobile', 'billing', 'support']),
  hover: PropTypes.bool,
  gradient: PropTypes.bool,
  className: PropTypes.string,
};

// Export components
Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Description = CardDescription;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;
