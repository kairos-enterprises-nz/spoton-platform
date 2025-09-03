import React from 'react';
import { motion } from 'framer-motion';
import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

const Button = React.forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  theme = 'default',
  loading = false,
  disabled = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  className = '',
  onClick,
  type = 'button',
  ...props
}, ref) => {
  // Variant styles
  const variants = {
    primary: 'bg-primary-turquoise-500 hover:bg-primary-turquoise-600 text-white border-transparent shadow-sm hover:shadow-md focus:ring-primary-turquoise-500',
    secondary: 'bg-white hover:bg-gray-50 text-secondary-darkgray-700 border-gray-300 shadow-sm hover:shadow focus:ring-primary-turquoise-500',
    outline: 'bg-transparent hover:bg-primary-turquoise-50 text-primary-turquoise-600 border-primary-turquoise-300 hover:border-primary-turquoise-400 focus:ring-primary-turquoise-500',
    ghost: 'bg-transparent hover:bg-gray-100 text-secondary-darkgray-700 border-transparent focus:ring-primary-turquoise-500',
    danger: 'bg-error hover:bg-error-dark text-white border-transparent shadow-sm hover:shadow-md focus:ring-error',
    success: 'bg-success hover:bg-success-dark text-white border-transparent shadow-sm hover:shadow-md focus:ring-success',
    warning: 'bg-warning hover:bg-warning-dark text-white border-transparent shadow-sm hover:shadow-md focus:ring-warning',
  };

  // Size styles
  const sizes = {
    xs: 'px-2.5 py-1.5 text-xs font-medium',
    sm: 'px-3 py-2 text-sm font-medium',
    md: 'px-4 py-2.5 text-sm font-semibold',
    lg: 'px-6 py-3 text-base font-semibold',
    xl: 'px-8 py-4 text-lg font-semibold',
  };

  // Theme-specific overrides
  const themeOverrides = {
    power: variant === 'primary' ? 'bg-service-power hover:bg-primary-turquoise-600' : '',
    broadband: variant === 'primary' ? 'bg-service-broadband hover:bg-purple-600' : '',
    mobile: variant === 'primary' ? 'bg-service-mobile hover:bg-blue-600' : '',
    billing: variant === 'primary' ? 'bg-service-billing hover:bg-red-600' : '',
    support: variant === 'primary' ? 'bg-service-support hover:bg-green-600' : '',
  };

  // Combine classes
  const buttonClasses = [
    // Base styles
    'inline-flex items-center justify-center',
    'border font-medium rounded-lg',
    'transition-all duration-200 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
    
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

  const buttonContent = (
    <>
      {loading && (
        <Loader2 className={`animate-spin ${size === 'xs' ? 'h-3 w-3' : size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'} ${children ? 'mr-2' : ''}`} />
      )}
      {!loading && icon && iconPosition === 'left' && (
        <span className={`${children ? 'mr-2' : ''} ${size === 'xs' ? 'h-3 w-3' : size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'}`}>
          {icon}
        </span>
      )}
      {children && <span>{children}</span>}
      {!loading && icon && iconPosition === 'right' && (
        <span className={`${children ? 'ml-2' : ''} ${size === 'xs' ? 'h-3 w-3' : size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'}`}>
          {icon}
        </span>
      )}
    </>
  );

  return (
    <motion.button
      ref={ref}
      type={type}
      className={buttonClasses}
      disabled={isDisabled}
      onClick={onClick}
      whileHover={!isDisabled ? { scale: 1.02 } : {}}
      whileTap={!isDisabled ? { scale: 0.98 } : {}}
      transition={{ duration: 0.15 }}
      {...props}
    >
      {buttonContent}
    </motion.button>
  );
});

Button.displayName = 'Button';

Button.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['primary', 'secondary', 'outline', 'ghost', 'danger', 'success', 'warning']),
  size: PropTypes.oneOf(['xs', 'sm', 'md', 'lg', 'xl']),
  theme: PropTypes.oneOf(['default', 'power', 'broadband', 'mobile', 'billing', 'support']),
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
  fullWidth: PropTypes.bool,
  icon: PropTypes.element,
  iconPosition: PropTypes.oneOf(['left', 'right']),
  className: PropTypes.string,
  onClick: PropTypes.func,
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
};

export default Button;
