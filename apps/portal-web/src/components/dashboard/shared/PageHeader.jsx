import PropTypes from 'prop-types';
import { motion } from 'framer-motion';

const PageHeader = ({ 
  title, 
  subtitle, 
  description,
  icon: Icon,
  statusText = "Active",
  statusColor = "primary-turquoise",
  rightContent,
  theme = "default"
}) => {
  // Theme configurations for different services
  // To add a new service theme:
  // 1. Add theme name to the PropTypes oneOf array below
  // 2. Add theme configuration here with gradient, iconBg, and borderColor
  // 3. Use the theme name in your service page PageHeader component
  const themeConfig = {
    default: {
      gradient: 'from-primary-turquoise/30 via-transparent to-accent-green/30',
      iconBg: 'from-primary-turquoise to-accent-lightturquoise',
      borderColor: 'border-primary-turquoise/30'
    },
    power: {
      gradient: 'from-primary-turquoise/30 via-transparent to-accent-green/30',
      iconBg: 'from-primary-turquoise to-accent-lightturquoise',
      borderColor: 'border-primary-turquoise/30'
    },
    broadband: {
      gradient: 'from-accent-purple/30 via-transparent to-primary-turquoise/30',
      iconBg: 'from-accent-purple to-accent-purple/80',
      borderColor: 'border-accent-purple/30'
    },
    mobile: {
      gradient: 'from-accent-blue/30 via-transparent to-primary-turquoise/30',
      iconBg: 'from-accent-blue to-accent-blue/80',
      borderColor: 'border-accent-blue/30'
    },
    billing: {
      gradient: 'from-accent-red/30 via-transparent to-primary-turquoise/30',
      iconBg: 'from-accent-red to-accent-red/80',
      borderColor: 'border-accent-red/30'
    },
    support: {
      gradient: 'from-accent-green/30 via-transparent to-primary-turquoise/30',
      iconBg: 'from-accent-green to-accent-green/80',
      borderColor: 'border-accent-green/30'
    },
    profile: {
      gradient: 'from-primary-turquoise/30 via-transparent to-accent-lightturquoise/30',
      iconBg: 'from-primary-turquoise to-accent-lightturquoise',
      borderColor: 'border-primary-turquoise/30'
    }
  };

  const config = themeConfig[theme] || themeConfig.default;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-white via-gray-50/90 to-white border border-gray-200/60 shadow-lg shadow-gray-200/50 backdrop-blur-sm">
        {/* Subtle background pattern */}
        <div className="absolute inset-0 opacity-30">
          <div className={`absolute inset-0 bg-gradient-to-r ${config.gradient}`}></div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.1)_0%,transparent_50%)]"></div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
          <div className={`w-full h-full rounded-full bg-gradient-to-br ${config.iconBg} blur-2xl`}></div>
        </div>
        <div className="absolute bottom-0 left-0 w-24 h-24 opacity-5">
          <div className={`w-full h-full rounded-full bg-gradient-to-br ${config.iconBg} blur-xl`}></div>
        </div>

        <div className="relative z-10 p-4 lg:p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center space-x-4 mb-6 lg:mb-0">
              {Icon && (
                <div className={`w-12 h-12 lg:w-14 lg:h-14 rounded-xl bg-gradient-to-br ${config.iconBg} flex items-center justify-center shadow-lg shadow-primary-turquoise/20 ring-1 ring-white/20`}>
                  <Icon className="h-5 w-5 lg:h-6 lg:w-6 text-white" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h1 className="text-lg lg:text-xl font-bold text-gray-800 mb-1">
                  {title}
                </h1>
                <p className="text-gray-600 text-sm lg:text-base mb-1 font-medium leading-relaxed">
                  {subtitle}
                </p>
                {description && (
                  <p className="text-gray-500 text-xs lg:text-sm">
                    {description}
                  </p>
                )}
              </div>
            </div>

            {rightContent && (
              <div className="flex items-center space-x-4 text-gray-600 bg-white/60 backdrop-blur-sm rounded-2xl p-3 border border-gray-200/50 shadow-sm">
                {rightContent}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

PageHeader.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  description: PropTypes.string,
  icon: PropTypes.elementType,
  statusText: PropTypes.string,
  statusColor: PropTypes.string,
  rightContent: PropTypes.node,
  theme: PropTypes.oneOf(['default', 'power', 'broadband', 'mobile', 'billing', 'support', 'profile'])
};

export default PageHeader;
