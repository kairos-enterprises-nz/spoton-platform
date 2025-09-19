import React from 'react';
import PropTypes from 'prop-types';
import { AlertCircle, Check, Eye, EyeOff } from 'lucide-react';

const Input = React.forwardRef(({
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  error,
  success,
  helperText,
  required = false,
  disabled = false,
  readOnly = false,
  size = 'md',
  variant = 'default',
  leftIcon,
  rightIcon,
  showPasswordToggle = false,
  className = '',
  containerClassName = '',
  id,
  name,
  autoComplete,
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = React.useState(false);
  const [isFocused, setIsFocused] = React.useState(false);
  
  const inputId = id || name || `input-${Math.random().toString(36).substr(2, 9)}`;
  const actualType = type === 'password' && showPassword ? 'text' : type;

  // Size styles
  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-4 py-3 text-lg',
  };

  // Variant styles
  const variants = {
    default: 'border-gray-300 focus:border-primary-turquoise-500 focus:ring-primary-turquoise-500',
    filled: 'bg-gray-50 border-gray-200 focus:bg-white focus:border-primary-turquoise-500 focus:ring-primary-turquoise-500',
    outlined: 'border-2 border-gray-300 focus:border-primary-turquoise-500 focus:ring-0',
  };

  // State-based styles
  const getStateStyles = () => {
    if (error) {
      return 'border-error focus:border-error focus:ring-error';
    }
    if (success) {
      return 'border-success focus:border-success focus:ring-success';
    }
    return variants[variant];
  };

  // Input classes
  const inputClasses = [
    // Base styles
    'block w-full rounded-lg border',
    'transition-colors duration-200',
    'placeholder-gray-400',
    'focus:outline-none focus:ring-2 focus:ring-opacity-20',
    'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
    'read-only:bg-gray-50 read-only:cursor-default',
    
    // Size
    sizes[size],
    
    // State styles
    getStateStyles(),
    
    // Icon padding adjustments
    leftIcon ? 'pl-10' : '',
    (rightIcon || showPasswordToggle || error || success) ? 'pr-10' : '',
    
    // Custom classes
    className
  ].filter(Boolean).join(' ');

  // Label classes
  const labelClasses = [
    'block text-sm font-medium text-secondary-darkgray-700 mb-2',
    required ? "after:content-['*'] after:ml-1 after:text-error" : '',
  ].filter(Boolean).join(' ');

  // Helper text classes
  const helperClasses = [
    'mt-2 text-sm',
    error ? 'text-error' : success ? 'text-success' : 'text-secondary-darkgray-500'
  ].filter(Boolean).join(' ');

  const handleFocus = (e) => {
    setIsFocused(true);
    onFocus?.(e);
  };

  const handleBlur = (e) => {
    setIsFocused(false);
    onBlur?.(e);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className={`${containerClassName}`}>
      {label && (
        <label htmlFor={inputId} className={labelClasses}>
          {label}
        </label>
      )}
      
      <div className="relative">
        {/* Left Icon */}
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400 h-5 w-5">
              {leftIcon}
            </span>
          </div>
        )}

        {/* Input */}
        <input
          ref={ref}
          id={inputId}
          name={name}
          type={actualType}
          value={value}
          onChange={onChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          readOnly={readOnly}
          autoComplete={autoComplete}
          className={inputClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            (error || success || helperText) ? `${inputId}-description` : undefined
          }
          {...props}
        />

        {/* Right Icons */}
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
          {/* Success/Error Icons */}
          {success && !error && (
            <Check className="h-5 w-5 text-success" />
          )}
          {error && (
            <AlertCircle className="h-5 w-5 text-error" />
          )}
          
          {/* Password Toggle */}
          {showPasswordToggle && type === 'password' && !error && !success && (
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition-colors duration-200"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5" />
              ) : (
                <Eye className="h-5 w-5" />
              )}
            </button>
          )}
          
          {/* Custom Right Icon */}
          {rightIcon && !error && !success && !showPasswordToggle && (
            <span className="text-gray-400 h-5 w-5">
              {rightIcon}
            </span>
          )}
        </div>
      </div>

      {/* Helper Text / Error Message */}
      {(error || success || helperText) && (
        <p id={`${inputId}-description`} className={helperClasses}>
          {error || (success && 'Valid') || helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  label: PropTypes.string,
  type: PropTypes.oneOf(['text', 'email', 'password', 'number', 'tel', 'url', 'search']),
  placeholder: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  onBlur: PropTypes.func,
  onFocus: PropTypes.func,
  error: PropTypes.string,
  success: PropTypes.bool,
  helperText: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  readOnly: PropTypes.bool,
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  variant: PropTypes.oneOf(['default', 'filled', 'outlined']),
  leftIcon: PropTypes.element,
  rightIcon: PropTypes.element,
  showPasswordToggle: PropTypes.bool,
  className: PropTypes.string,
  containerClassName: PropTypes.string,
  id: PropTypes.string,
  name: PropTypes.string,
  autoComplete: PropTypes.string,
};

export default Input;
