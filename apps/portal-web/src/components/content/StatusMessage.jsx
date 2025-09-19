import React from 'react';
import PropTypes from 'prop-types';
import { 
  CheckCircle, AlertTriangle, Clock, XCircle, 
  Info, Zap, Wifi, Smartphone, Wrench, Truck
} from 'lucide-react';
import Badge from '../ui/Badge';

const StatusMessage = ({ 
  type = 'info', 
  status = 'unknown',
  service = 'general',
  title,
  message,
  actionText,
  onAction,
  showIcon = true,
  className = ''
}) => {
  // Status definitions with user-friendly messaging
  const statusDefinitions = {
    // Power service statuses
    power: {
      active: {
        title: 'Power Connected',
        message: 'Your power service is active and running smoothly.',
        icon: CheckCircle,
        type: 'success'
      },
      switching: {
        title: 'Switching in Progress',
        message: 'We\'re switching your power supply. This usually takes 2-3 business days.',
        icon: Clock,
        type: 'warning',
        actionText: 'Track Progress'
      },
      pending: {
        title: 'Switch Scheduled',
        message: 'Your power switch is scheduled. We\'ll notify you once it\'s complete.',
        icon: Clock,
        type: 'info'
      },
      issue: {
        title: 'Service Issue',
        message: 'There\'s an issue with your power service. Our team is working on it.',
        icon: AlertTriangle,
        type: 'error',
        actionText: 'Get Updates'
      }
    },
    // Broadband service statuses
    broadband: {
      active: {
        title: 'Broadband Connected',
        message: 'Your broadband is active and performing well.',
        icon: CheckCircle,
        type: 'success'
      },
      installing: {
        title: 'Installation Scheduled',
        message: 'Our technician will visit to install your broadband service.',
        icon: Truck,
        type: 'info',
        actionText: 'Reschedule'
      },
      pending: {
        title: 'Installation Pending',
        message: 'We\'re arranging your broadband installation. We\'ll contact you soon.',
        icon: Clock,
        type: 'warning'
      },
      issue: {
        title: 'Connection Issue',
        message: 'There\'s a problem with your broadband connection.',
        icon: XCircle,
        type: 'error',
        actionText: 'Troubleshoot'
      }
    },
    // Mobile service statuses
    mobile: {
      active: {
        title: 'Mobile Service Active',
        message: 'Your mobile service is working perfectly.',
        icon: CheckCircle,
        type: 'success'
      },
      activating: {
        title: 'Activating Service',
        message: 'We\'re activating your mobile service. This may take a few minutes.',
        icon: Clock,
        type: 'info'
      },
      coming_soon: {
        title: 'Coming Soon',
        message: 'Mobile services will be available soon. Get notified when ready.',
        icon: Info,
        type: 'info',
        actionText: 'Get Notified'
      }
    },
    // Billing statuses
    billing: {
      current: {
        title: 'Account Current',
        message: 'All your bills are paid and up to date.',
        icon: CheckCircle,
        type: 'success'
      },
      due: {
        title: 'Payment Due',
        message: 'You have a payment due soon. Pay now to avoid any interruption.',
        icon: AlertTriangle,
        type: 'warning',
        actionText: 'Pay Now'
      },
      overdue: {
        title: 'Payment Overdue',
        message: 'Your payment is overdue. Please pay immediately to avoid service suspension.',
        icon: XCircle,
        type: 'error',
        actionText: 'Pay Now'
      },
      processing: {
        title: 'Payment Processing',
        message: 'Your payment is being processed. This may take 1-2 business days.',
        icon: Clock,
        type: 'info'
      }
    },
    // General statuses
    general: {
      success: {
        title: 'Success',
        message: 'Operation completed successfully.',
        icon: CheckCircle,
        type: 'success'
      },
      error: {
        title: 'Error',
        message: 'Something went wrong. Please try again.',
        icon: XCircle,
        type: 'error',
        actionText: 'Retry'
      },
      loading: {
        title: 'Loading',
        message: 'Please wait while we process your request.',
        icon: Clock,
        type: 'info'
      },
      maintenance: {
        title: 'Maintenance Mode',
        message: 'This service is temporarily unavailable for maintenance.',
        icon: Wrench,
        type: 'warning'
      }
    }
  };

  // Get status definition
  const statusDef = statusDefinitions[service]?.[status] || statusDefinitions.general[status] || statusDefinitions.general.success;

  // Override with custom props if provided
  const finalTitle = title || statusDef.title;
  const finalMessage = message || statusDef.message;
  const finalType = type !== 'info' ? type : statusDef.type;
  const finalActionText = actionText || statusDef.actionText;
  const Icon = statusDef.icon;

  // Type-based styling
  const typeStyles = {
    success: {
      container: 'bg-success-light border-success text-success-dark',
      icon: 'text-success',
      badge: 'success'
    },
    warning: {
      container: 'bg-warning-light border-warning text-warning-dark',
      icon: 'text-warning',
      badge: 'warning'
    },
    error: {
      container: 'bg-error-light border-error text-error-dark',
      icon: 'text-error',
      badge: 'error'
    },
    info: {
      container: 'bg-info-light border-info text-info-dark',
      icon: 'text-info',
      badge: 'info'
    }
  };

  const styles = typeStyles[finalType] || typeStyles.info;

  return (
    <div className={`rounded-lg border-2 p-4 ${styles.container} ${className}`}>
      <div className="flex items-start space-x-3">
        {showIcon && Icon && (
          <div className="flex-shrink-0">
            <Icon className={`h-5 w-5 ${styles.icon}`} />
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold">
              {finalTitle}
            </h3>
            <Badge
              variant="soft"
              theme={styles.badge}
              size="sm"
            >
              {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Badge>
          </div>
          
          <p className="text-sm mb-3">
            {finalMessage}
          </p>
          
          {(finalActionText && onAction) && (
            <button
              onClick={onAction}
              className={`text-sm font-medium underline hover:no-underline transition-all duration-200 ${
                finalType === 'success' ? 'text-success-dark hover:text-success' :
                finalType === 'warning' ? 'text-warning-dark hover:text-warning' :
                finalType === 'error' ? 'text-error-dark hover:text-error' :
                'text-info-dark hover:text-info'
              }`}
            >
              {finalActionText}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

StatusMessage.propTypes = {
  type: PropTypes.oneOf(['success', 'warning', 'error', 'info']),
  status: PropTypes.string.isRequired,
  service: PropTypes.oneOf(['power', 'broadband', 'mobile', 'billing', 'general']),
  title: PropTypes.string,
  message: PropTypes.string,
  actionText: PropTypes.string,
  onAction: PropTypes.func,
  showIcon: PropTypes.bool,
  className: PropTypes.string
};

export default StatusMessage;
