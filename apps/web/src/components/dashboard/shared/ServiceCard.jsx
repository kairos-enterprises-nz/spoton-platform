import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';
import DashboardCard from './DashboardCard';

const ServiceCard = ({
  title,
  icon: Icon,
  value,
  subtitle,
  trend,
  trendValue,
  color = 'primary-turquoise',
  href,
  onClick,
  children,
  className = ''
}) => {
  const colorMap = {
    'primary-turquoise': {
      icon: 'text-primary-turquoise',
      bg: 'bg-primary-turquoise/10',
      border: 'border-primary-turquoise/20',
      hover: 'hover:bg-primary-turquoise/20'
    },
    'accent-blue': {
      icon: 'text-accent-blue',
      bg: 'bg-accent-blue/10',
      border: 'border-accent-blue/20',
      hover: 'hover:bg-accent-blue/20'
    },
    'accent-purple': {
      icon: 'text-accent-purple',
      bg: 'bg-accent-purple/10',
      border: 'border-accent-purple/20',
      hover: 'hover:bg-accent-purple/20'
    },
    'accent-green': {
      icon: 'text-accent-green',
      bg: 'bg-accent-green/10',
      border: 'border-accent-green/20',
      hover: 'hover:bg-accent-green/20'
    },
    'accent-red': {
      icon: 'text-accent-red',
      bg: 'bg-accent-red/10',
      border: 'border-accent-red/20',
      hover: 'hover:bg-accent-red/20'
    }
  };

  const colors = colorMap[color] || colorMap['primary-turquoise'];

  const CardContent = () => (
    <>
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-xl ${colors.bg} ${colors.border} border`}>
          <Icon className={`h-6 w-6 ${colors.icon}`} />
        </div>
        {(href || onClick) && (
          <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all duration-300" />
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        
        {value && (
          <div className="text-2xl font-bold text-secondary-darkgray">
            {value}
          </div>
        )}
        
        {subtitle && (
          <p className="text-sm text-gray-500">{subtitle}</p>
        )}
        
        {trend && trendValue && (
          <div className="flex items-center space-x-1">
            {trend === 'up' ? (
              <TrendingUp className="h-4 w-4 text-accent-green" />
            ) : (
              <TrendingDown className="h-4 w-4 text-accent-red" />
            )}
            <span className={`text-sm font-medium ${
              trend === 'up' ? 'text-accent-green' : 'text-accent-red'
            }`}>
              {trendValue}
            </span>
          </div>
        )}
      </div>

      {children && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {children}
        </div>
      )}
    </>
  );

  if (href) {
    return (
      <motion.a
        href={href}
        className={`block group ${className}`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <DashboardCard className={`cursor-pointer ${colors.hover}`}>
          <CardContent />
        </DashboardCard>
      </motion.a>
    );
  }

  if (onClick) {
    return (
      <motion.button
        onClick={onClick}
        className={`w-full text-left group ${className}`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <DashboardCard className={`cursor-pointer ${colors.hover}`}>
          <CardContent />
        </DashboardCard>
      </motion.button>
    );
  }

  return (
    <DashboardCard className={className}>
      <CardContent />
    </DashboardCard>
  );
};

ServiceCard.propTypes = {
  title: PropTypes.string.isRequired,
  icon: PropTypes.elementType.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  subtitle: PropTypes.string,
  trend: PropTypes.oneOf(['up', 'down']),
  trendValue: PropTypes.string,
  color: PropTypes.oneOf(['primary-turquoise', 'accent-blue', 'accent-purple', 'accent-green', 'accent-red']),
  href: PropTypes.string,
  onClick: PropTypes.func,
  children: PropTypes.node,
  className: PropTypes.string
};

export default ServiceCard; 