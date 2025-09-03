import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import loaderIcon from '../assets/utilitycopilot-icon.webp';

export default function Loader({ 
  size = 'lg', 
  fullscreen = false, 
  icon = loaderIcon, 
  message = 'Getting things SpotOn...',
  progress = 0,
  showProgress = false
}) {
  const sizeClasses = {
    sm: 'h-12 w-12',
    md: 'h-16 w-16',
    lg: 'h-32 w-32',
    xl: 'h-40 w-40',
  };

  return (
    <div
      className={`${
        fullscreen
          ? 'fixed inset-0 z-50 bg-black/80 flex items-center justify-center w-screen h-screen'
          : 'relative min-h-[120px] flex items-center justify-center'
      }`}
      aria-busy="true"
      role="status"
    >
      {/* === Inline Keyframes for SpotOn Animation === */}
      <style>
        {`
          @keyframes spoton-spin {
            0% {
              transform: rotate(0deg) scale(1);
              filter: drop-shadow(0 0 0 rgba(127, 90, 240, 0.2));
            }
            50% {
              transform: rotate(180deg) scale(1.10);
              filter: drop-shadow(0 0 4px rgba(127, 90, 240, 0.4));
            }
            100% {
              transform: rotate(360deg) scale(1);
              filter: drop-shadow(0 0 0 rgba(127, 90, 240, 0.2));
            }
          }
        `}
      </style>

      <div className="flex flex-col items-center justify-center px-6 py-6 max-w-xs w-full mx-4">
        <motion.img
          src={icon}
          alt="Loading"
          className={`${sizeClasses[size]}`}
          style={{
            animation: 'spoton-spin 1.6s ease-in-out infinite',
          }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        />
        
        <motion.p 
          className="mt-4 text-sm text-center text-white font-medium tracking-wide"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          {message}
        </motion.p>
        
        {showProgress && (
          <motion.div 
            className="mt-4 w-full max-w-xs"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <div className="w-full bg-gray-700 rounded-full h-2">
              <motion.div 
                className="bg-primary-turquoise h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <p className="text-xs text-gray-300 mt-2 text-center">
              {Math.round(progress)}%
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}

Loader.propTypes = {
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  fullscreen: PropTypes.bool,
  icon: PropTypes.string,
  message: PropTypes.string,
  progress: PropTypes.number,
  showProgress: PropTypes.bool,
};
