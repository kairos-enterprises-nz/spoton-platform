import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Smartphone, Wifi, CheckCircle } from 'lucide-react';
import DashboardCard from './DashboardCard';
import { getServiceInterests, updateServiceInterest } from '../../../services/serviceInterestService';

const ComingSoonCard = ({ 
  title, 
  subtitle,
  description,
  actionText, 
  onAction, 
  theme = 'default',
  serviceType,
  className = '' 
}) => {
  const [isNotificationSignedUp, setIsNotificationSignedUp] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load user's current interest status when component mounts
  useEffect(() => {
    if (serviceType) {
      getServiceInterests().then(interests => {
        if (interests) {
          const isInterested = serviceType === 'mobile' 
            ? interests.interested_in_mobile 
            : interests.interested_in_power;
          setIsNotificationSignedUp(isInterested);
        }
      }).catch(console.error);
    }
  }, [serviceType]);
  // Theme configurations
  const themeConfig = {
    default: {
      icon: Sparkles,
      iconColor: 'text-gray-500',
      bgColor: 'bg-gray-100',
      borderColor: 'border-gray-200',
      accentColor: 'primary-turquoise'
    },
    electricity: {
      icon: Zap,
      iconColor: 'text-primary-turquoise',
      bgColor: 'bg-gradient-to-br from-primary-turquoise/10 to-accent-lightturquoise/10',
      borderColor: 'border-primary-turquoise/30',
      accentColor: 'primary-turquoise',
      pattern: true
    },
    mobile: {
      icon: Smartphone,
      iconColor: 'text-accent-blue',
      bgColor: 'bg-gradient-to-br from-accent-blue/10 to-accent-blue/5',
      borderColor: 'border-accent-blue/30',
      accentColor: 'accent-blue'
    },
    internet: {
      icon: Wifi,
      iconColor: 'text-accent-purple',
      bgColor: 'bg-gradient-to-br from-accent-purple/10 to-accent-purple/5',
      borderColor: 'border-accent-purple/30',
      accentColor: 'accent-purple'
    }
  };

  const config = themeConfig[theme] || themeConfig.default;
  const IconComponent = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="space-y-3"
    >
      {/* Header with modern light design */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-white via-gray-50/90 to-white border border-gray-200/60 shadow-lg shadow-gray-200/50 backdrop-blur-sm">
        {/* Subtle themed background */}
        <div className="absolute inset-0 opacity-30">
          <div className={`absolute inset-0 ${config.bgColor}`}></div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.1)_0%,transparent_50%)]"></div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
          <div className={`w-full h-full rounded-full ${config.bgColor} blur-2xl`}></div>
        </div>
        <div className="absolute bottom-0 left-0 w-24 h-24 opacity-5">
          <div className={`w-full h-full rounded-full ${config.bgColor} blur-xl`}></div>
        </div>

        <div className="relative z-10 p-4 lg:p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center space-x-4 mb-6 lg:mb-0">
              <div className={`w-16 h-16 lg:w-18 lg:h-18 rounded-2xl ${config.bgColor} ${config.borderColor} border-2 flex items-center justify-center shadow-lg ring-1 ring-white/20`}>
                <IconComponent className={`h-7 w-7 lg:h-9 lg:w-9 ${config.iconColor}`} />
              </div>
              <div className="text-left">
                <h1 className="text-2xl lg:text-3xl font-bold text-gray-800 mb-3">
                  {title}
                </h1>
                <p className="text-gray-600 text-xs lg:text-sm font-medium leading-relaxed max-w-lg">
                  {subtitle}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4 text-gray-600 bg-white/60 backdrop-blur-sm rounded-2xl p-3 border border-gray-200/50 shadow-sm">
              <Sparkles className={`h-5 w-5 ${config.iconColor}`} />
              <div className="text-right">
                <div className="text-xs opacity-80">Status</div>
                <div className="text-sm font-semibold">Coming Soon</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Card */}
      <DashboardCard compact className={`${config.bgColor} ${config.borderColor} border ${className}`}>
        <div className="text-center py-8">
          <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl ${config.bgColor} ${config.borderColor} border-2 flex items-center justify-center`}>
            <IconComponent className={`h-8 w-8 ${config.iconColor}`} />
          </div>
          
          <h3 className="text-xl font-bold text-secondary-darkgray mb-2">
            {description || 'Service Coming Soon'}
          </h3>
          
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            {isNotificationSignedUp 
              ? "Thank you for your interest! We'll notify you as soon as it becomes available."
              : "We're working hard to bring you this service. We'll notify you as soon as it becomes available in your area."
            }
          </p>

          {actionText && !isNotificationSignedUp && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={async () => {
                if (loading) return;
                
                setLoading(true);
                try {
                  // Update service interest in backend
                  await updateServiceInterest(serviceType, true);
                  setIsNotificationSignedUp(true);
                  
                  if (onAction) {
                    onAction();
                  }
                  console.log(`User signed up for ${serviceType} notifications`);
                } catch (error) {
                  console.error('Failed to update service interest:', error);
                } finally {
                  setLoading(false);
                }
              }}
              className={`px-6 py-3 rounded-xl text-${config.accentColor} bg-${config.accentColor}/10 hover:bg-${config.accentColor}/20 transition-all duration-300 font-semibold border border-${config.accentColor}/30`}
            >
              {actionText}
            </motion.button>
          )}

          {/* Show notification confirmation */}
          {isNotificationSignedUp && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-center space-x-2 px-4 py-3 bg-accent-green/10 border border-accent-green/20 rounded-xl text-accent-green"
            >
              <CheckCircle className="h-5 w-5" />
              <span className="font-semibold">We will notify you once these services are live.</span>
            </motion.div>
          )}
        </div>
      </DashboardCard>
    </motion.div>
  );
};

ComingSoonCard.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  description: PropTypes.string,
  actionText: PropTypes.string,
  onAction: PropTypes.func,
  theme: PropTypes.oneOf(['default', 'electricity', 'mobile', 'internet']),
  serviceType: PropTypes.string,
  className: PropTypes.string
};

export default ComingSoonCard;

