import PropTypes from 'prop-types';
import { motion } from 'framer-motion';

const DashboardCard = ({ 
  children, 
  className = '', 
  gradient = false,
  gradientFrom = 'from-primary-turquoise',
  gradientTo = 'to-secondary-darkgray',
  hover = true,
  padding = 'p-6',
  ...props 
}) => {
  const baseClasses = `
    rounded-2xl shadow-sm border border-gray-100/50 backdrop-blur-sm
    transition-all duration-300 ease-out
    ${hover ? 'hover:shadow-lg hover:-translate-y-1 hover:border-primary-turquoise/20' : ''}
    ${gradient 
      ? `bg-gradient-to-br ${gradientFrom} ${gradientTo} text-white` 
      : 'bg-white/80'
    }
    ${padding}
    ${className}
  `;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={baseClasses}
      {...props}
    >
      {children}
    </motion.div>
  );
};

DashboardCard.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  gradient: PropTypes.bool,
  gradientFrom: PropTypes.string,
  gradientTo: PropTypes.string,
  hover: PropTypes.bool,
  padding: PropTypes.string
};

export default DashboardCard; 