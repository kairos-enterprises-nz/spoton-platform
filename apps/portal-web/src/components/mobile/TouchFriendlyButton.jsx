import React from 'react';
import { motion } from 'framer-motion';
import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

const TouchFriendlyButton = ({
  children,
  variant = 'primary',
  size = 'lg', // Default to large for mobile
  theme = 'default',
  loading = false,
  disabled = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  className = '',
  onClick,
  type = 'button',
  hapticFeedback = true,
  ...props
}) => {
  // Ensure minimum touch target size (44px)
  const sizes = {
    sm: 'px-4 py-3 text-sm font-medium min-h-[44px]',
    md: 'px-6 py-4 text-base font-semibold min-h-[48px]',
    lg: 'px-8 py-5 text-lg font-semibold min-h-[52px]',
    xl: 'px-10 py-6 text-xl font-bold min-h-[56px]',
  };

  // Enhanced variants for mobile
  const variants = {
    primary: 'bg-primary-turquoise-500 hover:bg-primary-turquoise-600 active:bg-primary-turquoise-700 text-white border-transparent shadow-lg active:shadow-xl',
    secondary: 'bg-white hover:bg-gray-50 active:bg-gray-100 text-secondary-darkgray-700 border-gray-300 shadow-md active:shadow-lg',
    outline: 'bg-transparent hover:bg-primary-turquoise-50 active:bg-primary-turquoise-100 text-primary-turquoise-600 border-2 border-primary-turquoise-300 hover:border-primary-turquoise-400 active:border-primary-turquoise-500',
    ghost: 'bg-transparent hover:bg-gray-100 active:bg-gray-200 text-secondary-darkgray-700 border-transparent',
    danger: 'bg-error hover:bg-error-dark active:bg-red-700 text-white border-transparent shadow-lg active:shadow-xl',
    success: 'bg-success hover:bg-success-dark active:bg-green-700 text-white border-transparent shadow-lg active:shadow-xl',
  };

  // Theme overrides for mobile
  const themeOverrides = {
    power: variant === 'primary' ? 'bg-service-power hover:bg-primary-turquoise-600 active:bg-primary-turquoise-700' : '',
    broadband: variant === 'primary' ? 'bg-service-broadband hover:bg-purple-600 active:bg-purple-700' : '',
    mobile: variant === 'primary' ? 'bg-service-mobile hover:bg-blue-600 active:bg-blue-700' : '',
    billing: variant === 'primary' ? 'bg-service-billing hover:bg-red-600 active:bg-red-700' : '',
    support: variant === 'primary' ? 'bg-service-support hover:bg-green-600 active:bg-green-700' : '',
  };

  const buttonClasses = [
    // Base styles
    'inline-flex items-center justify-center',
    'border font-medium rounded-xl',
    'transition-all duration-200 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-turquoise-500',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
    'touch-manipulation', // Optimize for touch
    'select-none', // Prevent text selection on touch
    
    // Variant styles
    variants[variant],
    
    // Size styles
    sizes[size],
    
    // Theme overrides
    theme !== 'default' ? themeOverrides[theme] : '',
    
    // Full width
    fullWidth ? 'w-full' : '',
    
    // Custom classes
    className
  ].filter(Boolean).join(' ');

  const isDisabled = disabled || loading;

  const handleClick = (e) => {
    // Add haptic feedback on supported devices
    if (hapticFeedback && navigator.vibrate) {
      navigator.vibrate(10); // Short vibration
    }
    
    if (onClick && !isDisabled) {
      onClick(e);
    }
  };

  const buttonContent = (
    <>
      {loading && (
        <Loader2 className={`animate-spin ${
          size === 'sm' ? 'h-4 w-4' : 
          size === 'md' ? 'h-5 w-5' : 
          size === 'lg' ? 'h-6 w-6' : 
          'h-7 w-7'
        } ${children ? 'mr-3' : ''}`} />
      )}
      {!loading && icon && iconPosition === 'left' && (
        <span className={`${children ? 'mr-3' : ''} ${
          size === 'sm' ? 'h-4 w-4' : 
          size === 'md' ? 'h-5 w-5' : 
          size === 'lg' ? 'h-6 w-6' : 
          'h-7 w-7'
        }`}>
          {icon}
        </span>
      )}
      {children && <span className="truncate">{children}</span>}
      {!loading && icon && iconPosition === 'right' && (
        <span className={`${children ? 'ml-3' : ''} ${
          size === 'sm' ? 'h-4 w-4' : 
          size === 'md' ? 'h-5 w-5' : 
          size === 'lg' ? 'h-6 w-6' : 
          'h-7 w-7'
        }`}>
          {icon}
        </span>
      )}
    </>
  );

  return (
    <motion.button
      type={type}
      className={buttonClasses}
      disabled={isDisabled}
      onClick={handleClick}
      whileTap={!isDisabled ? { scale: 0.95 } : {}}
      transition={{ duration: 0.1 }}
      {...props}
    >
      {buttonContent}
    </motion.button>
  );
};

TouchFriendlyButton.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['primary', 'secondary', 'outline', 'ghost', 'danger', 'success']),
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  theme: PropTypes.oneOf(['default', 'power', 'broadband', 'mobile', 'billing', 'support']),
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
  icon: PropTypes.element,
  iconPosition: PropTypes.oneOf(['left', 'right']),
  className: PropTypes.string,
  onClick: PropTypes.func,
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  hapticFeedback: PropTypes.bool,
};

export default TouchFriendlyButton;
