import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PropTypes from 'prop-types';
import { 
  CheckCircle, AlertTriangle, AlertCircle, Info, X 
} from 'lucide-react';

// Toast Context
const ToastContext = createContext();

// Toast types and their configurations
const toastTypes = {
  success: {
    icon: CheckCircle,
    className: 'bg-success-light border-success text-success-dark',
    iconClassName: 'text-success'
  },
  error: {
    icon: AlertCircle,
    className: 'bg-error-light border-error text-error-dark',
    iconClassName: 'text-error'
  },
  warning: {
    icon: AlertTriangle,
    className: 'bg-warning-light border-warning text-warning-dark',
    iconClassName: 'text-warning'
  },
  info: {
    icon: Info,
    className: 'bg-info-light border-info text-info-dark',
    iconClassName: 'text-info'
  }
};

// Individual Toast Component
const Toast = ({ 
  id,
  type = 'info',
  title,
  message,
  duration = 5000,
  dismissible = true,
  onDismiss,
  actions = []
}) => {
  const config = toastTypes[type] || toastTypes.info;
  const Icon = config.icon;

  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, onDismiss]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -50, scale: 0.9 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={`
        relative max-w-sm w-full rounded-xl border-2 p-4 shadow-lg backdrop-blur-sm
        ${config.className}
      `}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className="flex-shrink-0">
          <Icon className={`h-5 w-5 ${config.iconClassName}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className="text-sm font-semibold mb-1 truncate">
              {title}
            </h4>
          )}
          {message && (
            <p className="text-sm leading-relaxed">
              {message}
            </p>
          )}

          {/* Actions */}
          {actions.length > 0 && (
            <div className="flex space-x-2 mt-3">
              {actions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => {
                    action.onClick();
                    if (action.dismissOnClick !== false) {
                      onDismiss(id);
                    }
                  }}
                  className="text-xs font-medium underline hover:no-underline transition-all duration-200"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Dismiss Button */}
        {dismissible && (
          <button
            onClick={() => onDismiss(id)}
            className={`flex-shrink-0 p-1 rounded-md hover:bg-black/10 transition-colors ${config.iconClassName}`}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Progress bar for timed toasts */}
      {duration > 0 && (
        <motion.div
          className="absolute bottom-0 left-0 h-1 bg-current opacity-30 rounded-b-xl"
          initial={{ width: '100%' }}
          animate={{ width: '0%' }}
          transition={{ duration: duration / 1000, ease: 'linear' }}
        />
      )}
    </motion.div>
  );
};

// Toast Container
const ToastContainer = ({ toasts, onDismiss, position = 'top-right' }) => {
  const positions = {
    'top-left': 'top-4 left-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2',
    'bottom-right': 'bottom-4 right-4'
  };

  return (
    <div className={`fixed ${positions[position]} z-50 space-y-2`}>
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            {...toast}
            onDismiss={onDismiss}
          />
        ))}
      </AnimatePresence>
    </div>
  );
};

// Toast Provider
export const ToastProvider = ({ children, position = 'top-right', maxToasts = 5 }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    const newToast = { id, ...toast };
    
    setToasts((prev) => {
      const updated = [newToast, ...prev];
      return updated.slice(0, maxToasts);
    });
    
    return id;
  }, [maxToasts]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const removeAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const contextValue = {
    addToast,
    removeToast,
    removeAllToasts,
    toasts
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer 
        toasts={toasts} 
        onDismiss={removeToast} 
        position={position}
      />
    </ToastContext.Provider>
  );
};

// Hook to use toasts
export const useToast = () => {
  const context = useContext(ToastContext);
  
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }

  const { addToast, removeToast, removeAllToasts } = context;

  // Convenience methods
  const success = useCallback((title, message, options = {}) => {
    return addToast({ type: 'success', title, message, ...options });
  }, [addToast]);

  const error = useCallback((title, message, options = {}) => {
    return addToast({ type: 'error', title, message, duration: 0, ...options });
  }, [addToast]);

  const warning = useCallback((title, message, options = {}) => {
    return addToast({ type: 'warning', title, message, ...options });
  }, [addToast]);

  const info = useCallback((title, message, options = {}) => {
    return addToast({ type: 'info', title, message, ...options });
  }, [addToast]);

  const promise = useCallback(async (
    promiseFunction,
    {
      loading: loadingMessage = 'Loading...',
      success: successMessage = 'Success!',
      error: errorMessage = 'Something went wrong'
    } = {}
  ) => {
    const loadingId = addToast({
      type: 'info',
      title: loadingMessage,
      duration: 0,
      dismissible: false
    });

    try {
      const result = await promiseFunction();
      removeToast(loadingId);
      success(successMessage);
      return result;
    } catch (err) {
      removeToast(loadingId);
      error(errorMessage, err.message);
      throw err;
    }
  }, [addToast, removeToast, success, error]);

  return {
    success,
    error,
    warning,
    info,
    promise,
    dismiss: removeToast,
    dismissAll: removeAllToasts
  };
};

Toast.propTypes = {
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  type: PropTypes.oneOf(['success', 'error', 'warning', 'info']),
  title: PropTypes.string,
  message: PropTypes.string,
  duration: PropTypes.number,
  dismissible: PropTypes.bool,
  onDismiss: PropTypes.func.isRequired,
  actions: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
    dismissOnClick: PropTypes.bool
  }))
};

ToastContainer.propTypes = {
  toasts: PropTypes.array.isRequired,
  onDismiss: PropTypes.func.isRequired,
  position: PropTypes.oneOf([
    'top-left', 'top-center', 'top-right',
    'bottom-left', 'bottom-center', 'bottom-right'
  ])
};

ToastProvider.propTypes = {
  children: PropTypes.node.isRequired,
  position: PropTypes.oneOf([
    'top-left', 'top-center', 'top-right',
    'bottom-left', 'bottom-center', 'bottom-right'
  ]),
  maxToasts: PropTypes.number
};

export default Toast;
