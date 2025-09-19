import React from 'react';
import PropTypes from 'prop-types';

const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  theme = 'default',
  icon,
  iconPosition = 'left',
  className = '',
  ...props
}) => {
  // Variant styles
  const variants = {
    default: 'bg-gray-100 text-gray-800 border-gray-200',
    solid: 'text-white',
    outline: 'bg-transparent border-2',
    soft: 'border-transparent',
  };

  // Size styles
  const sizes = {
    sm: 'px-2 py-0.5 text-xs font-medium',
    md: 'px-2.5 py-1 text-sm font-medium',
    lg: 'px-3 py-1.5 text-sm font-semibold',
  };

  // Theme-specific styles
  const getThemeStyles = () => {
    const themes = {
      default: {
        solid: 'bg-gray-600',
        outline: 'text-gray-600 border-gray-600',
        soft: 'bg-gray-100 text-gray-800',
      },
      power: {
        solid: 'bg-primary-turquoise-500',
        outline: 'text-primary-turquoise-600 border-primary-turquoise-600',
        soft: 'bg-primary-turquoise-100 text-primary-turquoise-800',
      },
      broadband: {
        solid: 'bg-service-broadband',
        outline: 'text-purple-600 border-purple-600',
        soft: 'bg-purple-100 text-purple-800',
      },
      mobile: {
        solid: 'bg-service-mobile',
        outline: 'text-blue-600 border-blue-600',
        soft: 'bg-blue-100 text-blue-800',
      },
      billing: {
        solid: 'bg-service-billing',
        outline: 'text-red-600 border-red-600',
        soft: 'bg-red-100 text-red-800',
      },
      support: {
        solid: 'bg-service-support',
        outline: 'text-green-600 border-green-600',
        soft: 'bg-green-100 text-green-800',
      },
      success: {
        solid: 'bg-success',
        outline: 'text-success-dark border-success-dark',
        soft: 'bg-success-light text-success-dark',
      },
      warning: {
        solid: 'bg-warning',
        outline: 'text-warning-dark border-warning-dark',
        soft: 'bg-warning-light text-warning-dark',
      },
      error: {
        solid: 'bg-error',
        outline: 'text-error-dark border-error-dark',
        soft: 'bg-error-light text-error-dark',
      },
      info: {
        solid: 'bg-info',
        outline: 'text-info-dark border-info-dark',
        soft: 'bg-info-light text-info-dark',
      },
    };

    return themes[theme]?.[variant] || themes.default[variant];
  };

  // Combine classes
  const badgeClasses = [
    // Base styles
    'inline-flex items-center rounded-full border font-medium',
    'transition-colors duration-200',
    
    // Variant base styles
    variants[variant],
    
    // Size styles
    sizes[size],
    
    // Theme styles
    getThemeStyles(),
    
    // Custom classes
    className
  ].filter(Boolean).join(' ');

  const iconSize = size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-4 w-4' : 'h-3.5 w-3.5';

  return (
    <span className={badgeClasses} {...props}>
      {icon && iconPosition === 'left' && (
        <span className={`${children ? 'mr-1' : ''} ${iconSize}`}>
          {icon}
        </span>
      )}
      {children}
      {icon && iconPosition === 'right' && (
        <span className={`${children ? 'ml-1' : ''} ${iconSize}`}>
          {icon}
        </span>
      )}
    </span>
  );
};

Badge.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['default', 'solid', 'outline', 'soft']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  theme: PropTypes.oneOf([
    'default', 'power', 'broadband', 'mobile', 'billing', 'support',
    'success', 'warning', 'error', 'info'
  ]),
  icon: PropTypes.element,
  iconPosition: PropTypes.oneOf(['left', 'right']),
  className: PropTypes.string,
};

export default Badge;
