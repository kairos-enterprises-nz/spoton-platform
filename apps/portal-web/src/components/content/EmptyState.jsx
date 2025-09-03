import React from 'react';
import PropTypes from 'prop-types';
import { 
  Inbox, Search, Wifi, Zap, Smartphone, CreditCard, 
  HelpCircle, FileText, Settings, AlertCircle
} from 'lucide-react';
import Button from '../ui/Button';

const EmptyState = ({
  type = 'general',
  title,
  description,
  actionText,
  onAction,
  secondaryActionText,
  onSecondaryAction,
  illustration,
  className = ''
}) => {
  // Predefined empty states with contextual messaging
  const emptyStates = {
    // Service-specific empty states
    no_services: {
      icon: Inbox,
      title: 'No Active Services',
      description: 'You don\'t have any active services yet. Get started by choosing a service that fits your needs.',
      actionText: 'Browse Services',
      secondaryActionText: 'Contact Sales'
    },
    no_power: {
      icon: Zap,
      title: 'Power Service Not Connected',
      description: 'Switch to SpotOn for transparent pricing and clean energy options.',
      actionText: 'Get Power',
      secondaryActionText: 'Learn More'
    },
    no_broadband: {
      icon: Wifi,
      title: 'No Broadband Service',
      description: 'Get ultra-fast fiber internet with no data caps and reliable speeds.',
      actionText: 'Get Broadband',
      secondaryActionText: 'Check Availability'
    },
    no_mobile: {
      icon: Smartphone,
      title: 'Mobile Service Coming Soon',
      description: 'Our mobile service will be available soon with simple plans and no surprises.',
      actionText: 'Get Notified',
      secondaryActionText: 'Learn More'
    },
    
    // Billing and transactions
    no_bills: {
      icon: FileText,
      title: 'No Bills Available',
      description: 'Your bills will appear here once your services are active and billing begins.',
      actionText: 'View Services',
      secondaryActionText: 'Contact Support'
    },
    no_transactions: {
      icon: CreditCard,
      title: 'No Payment History',
      description: 'Your payment history will be shown here once you make your first payment.',
      actionText: 'Make Payment',
      secondaryActionText: null
    },
    
    // Search and filters
    no_results: {
      icon: Search,
      title: 'No Results Found',
      description: 'We couldn\'t find anything matching your search. Try different keywords or filters.',
      actionText: 'Clear Filters',
      secondaryActionText: 'View All'
    },
    no_notifications: {
      icon: Inbox,
      title: 'All Caught Up!',
      description: 'You don\'t have any new notifications. We\'ll let you know when something needs your attention.',
      actionText: 'Notification Settings',
      secondaryActionText: null
    },
    
    // Support and help
    no_support_tickets: {
      icon: HelpCircle,
      title: 'No Support Tickets',
      description: 'You haven\'t submitted any support requests. If you need help, we\'re here for you.',
      actionText: 'Get Help',
      secondaryActionText: 'Browse FAQs'
    },
    
    // Errors and maintenance
    service_unavailable: {
      icon: AlertCircle,
      title: 'Service Temporarily Unavailable',
      description: 'This service is currently undergoing maintenance. Please try again in a few minutes.',
      actionText: 'Retry',
      secondaryActionText: 'Check Status'
    },
    connection_error: {
      icon: Wifi,
      title: 'Connection Problem',
      description: 'We\'re having trouble connecting to our servers. Please check your internet connection.',
      actionText: 'Retry',
      secondaryActionText: 'Refresh Page'
    },
    
    // General states
    general: {
      icon: Inbox,
      title: 'Nothing Here Yet',
      description: 'This section is empty right now. Content will appear here as it becomes available.',
      actionText: 'Refresh',
      secondaryActionText: null
    }
  };

  // Get the appropriate empty state configuration
  const config = emptyStates[type] || emptyStates.general;

  // Use provided props or fall back to config defaults
  const finalTitle = title || config.title;
  const finalDescription = description || config.description;
  const finalActionText = actionText || config.actionText;
  const finalSecondaryActionText = secondaryActionText !== undefined ? secondaryActionText : config.secondaryActionText;
  const IconComponent = illustration || config.icon;

  return (
    <div className={`flex flex-col items-center justify-center text-center py-12 px-6 ${className}`}>
      {/* Icon/Illustration */}
      <div className="mb-6">
        {React.isValidElement(illustration) ? (
          illustration
        ) : (
          <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
            <IconComponent className="h-8 w-8 text-gray-400" />
          </div>
        )}
      </div>

      {/* Title */}
      <h3 className="text-heading-lg text-secondary-darkgray-800 mb-3">
        {finalTitle}
      </h3>

      {/* Description */}
      <p className="text-body-base text-secondary-darkgray-600 mb-8 max-w-md">
        {finalDescription}
      </p>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        {finalActionText && onAction && (
          <Button
            variant="primary"
            size="md"
            onClick={onAction}
          >
            {finalActionText}
          </Button>
        )}
        
        {finalSecondaryActionText && onSecondaryAction && (
          <Button
            variant="outline"
            size="md"
            onClick={onSecondaryAction}
          >
            {finalSecondaryActionText}
          </Button>
        )}
      </div>
    </div>
  );
};

EmptyState.propTypes = {
  type: PropTypes.oneOf([
    'general', 'no_services', 'no_power', 'no_broadband', 'no_mobile',
    'no_bills', 'no_transactions', 'no_results', 'no_notifications',
    'no_support_tickets', 'service_unavailable', 'connection_error'
  ]),
  title: PropTypes.string,
  description: PropTypes.string,
  actionText: PropTypes.string,
  onAction: PropTypes.func,
  secondaryActionText: PropTypes.string,
  onSecondaryAction: PropTypes.func,
  illustration: PropTypes.oneOfType([PropTypes.element, PropTypes.elementType]),
  className: PropTypes.string
};

export default EmptyState;
