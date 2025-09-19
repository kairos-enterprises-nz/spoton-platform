import { useRef, useEffect } from 'react';

/**
 * Shared OTP Input Component for consistent 6-digit verification across all flows
 * Used by both traditional onboarding and OAuth flows
 */
export default function OTPInput({ 
  value = '', 
  onChange, 
  onComplete,
  disabled = false,
  error = '',
  length = 6,
  className = '',
  inputClassName = '',
  autoFocus = true
}) {
  const inputRefs = useRef([]);
  const digits = value.padEnd(length, '').split('').slice(0, length);

  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [autoFocus]);

  const handleChange = (index, digit) => {
    // Only allow single digits
    if (!/^[0-9]?$/.test(digit)) return;

    const newDigits = [...digits];
    newDigits[index] = digit;
    const newValue = newDigits.join('').replace(/\s/g, '');
    
    onChange(newValue);

    // Auto-focus next input
    if (digit && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    // Call onComplete when all digits are filled
    if (newValue.length === length && onComplete) {
      onComplete(newValue);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!digits[index] && index > 0) {
        // Move to previous input if current is empty
        inputRefs.current[index - 1]?.focus();
      } else if (digits[index]) {
        // Clear current input
        handleChange(index, '');
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length);
    if (pastedData) {
      onChange(pastedData);
      // Focus the next empty input or the last input
      const nextIndex = Math.min(pastedData.length, length - 1);
      inputRefs.current[nextIndex]?.focus();
    }
  };

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="flex gap-2 sm:gap-3 justify-center">
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(el) => (inputRefs.current[index] = el)}
            type="text"
            maxLength="1"
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onPaste={handlePaste}
            disabled={disabled}
            className={`
              w-9 h-9 sm:w-11 sm:h-11 
              text-center text-base sm:text-lg font-semibold 
              border rounded-md 
              focus:outline-none focus:ring-2 
              transition-all duration-200
              ${error 
                ? 'border-red-400 focus:ring-red-400 focus:border-red-400' 
                : 'border-white/20 focus:ring-cyan-400 focus:border-cyan-400'
              }
              ${disabled 
                ? 'bg-gray-100/10 cursor-not-allowed opacity-50' 
                : 'bg-white/10 text-white hover:bg-white/20'
              }
              ${inputClassName}
            `}
            autoComplete="one-time-code"
            inputMode="numeric"
            pattern="[0-9]*"
          />
        ))}
      </div>
      {error && (
        <p className="text-red-400 text-sm mt-2 text-center">{error}</p>
      )}
    </div>
  );
}