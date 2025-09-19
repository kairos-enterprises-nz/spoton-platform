import PropTypes from 'prop-types';

export default function LoadingSpinner({ size = 'md', color = '#40E0D0', text = 'Loading...' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div 
        className={`${sizeClasses[size]} border-4 border-gray-200 border-t-[${color}] rounded-full animate-spin`}
        style={{ borderTopColor: color }}
      ></div>
      {text && (
        <p className="mt-2 text-sm text-gray-600">{text}</p>
      )}
    </div>
  );
}

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  color: PropTypes.string,
  text: PropTypes.string
}; 