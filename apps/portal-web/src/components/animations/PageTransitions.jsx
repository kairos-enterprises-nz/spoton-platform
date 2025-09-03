import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';

// Page transition variants
const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
    scale: 0.98
  },
  in: {
    opacity: 1,
    y: 0,
    scale: 1
  },
  out: {
    opacity: 0,
    y: -20,
    scale: 1.02
  }
};

const slideVariants = {
  initial: {
    opacity: 0,
    x: '100%'
  },
  in: {
    opacity: 1,
    x: 0
  },
  out: {
    opacity: 0,
    x: '-100%'
  }
};

const fadeVariants = {
  initial: {
    opacity: 0
  },
  in: {
    opacity: 1
  },
  out: {
    opacity: 0
  }
};

const scaleVariants = {
  initial: {
    opacity: 0,
    scale: 0.9
  },
  in: {
    opacity: 1,
    scale: 1
  },
  out: {
    opacity: 0,
    scale: 1.1
  }
};

// Page transition component
const PageTransition = ({ 
  children, 
  variant = 'default',
  duration = 0.4,
  className = ''
}) => {
  const location = useLocation();
  
  const variants = {
    default: pageVariants,
    slide: slideVariants,
    fade: fadeVariants,
    scale: scaleVariants
  };

  const transition = {
    type: 'tween',
    ease: 'easeInOut',
    duration: duration
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial="initial"
        animate="in"
        exit="out"
        variants={variants[variant]}
        transition={transition}
        className={className}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

// Staggered children animation
const StaggerContainer = ({ 
  children, 
  staggerDelay = 0.1,
  className = '',
  ...props 
}) => {
  const containerVariants = {
    initial: {},
    animate: {
      transition: {
        staggerChildren: staggerDelay
      }
    }
  };

  const itemVariants = {
    initial: {
      opacity: 0,
      y: 20
    },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'tween',
        ease: 'easeOut',
        duration: 0.4
      }
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="initial"
      animate="animate"
      className={className}
      {...props}
    >
      {React.Children.map(children, (child, index) => (
        <motion.div key={index} variants={itemVariants}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

// Entrance animations for individual components
const EntranceAnimation = ({ 
  children, 
  type = 'fadeUp',
  delay = 0,
  duration = 0.5,
  className = ''
}) => {
  const animations = {
    fadeUp: {
      initial: { opacity: 0, y: 30 },
      animate: { opacity: 1, y: 0 }
    },
    fadeDown: {
      initial: { opacity: 0, y: -30 },
      animate: { opacity: 1, y: 0 }
    },
    fadeLeft: {
      initial: { opacity: 0, x: -30 },
      animate: { opacity: 1, x: 0 }
    },
    fadeRight: {
      initial: { opacity: 0, x: 30 },
      animate: { opacity: 1, x: 0 }
    },
    scale: {
      initial: { opacity: 0, scale: 0.8 },
      animate: { opacity: 1, scale: 1 }
    },
    bounce: {
      initial: { opacity: 0, y: -100 },
      animate: { 
        opacity: 1, 
        y: 0,
        transition: {
          type: 'spring',
          bounce: 0.4,
          duration: duration
        }
      }
    }
  };

  const animation = animations[type] || animations.fadeUp;

  return (
    <motion.div
      initial={animation.initial}
      animate={animation.animate}
      transition={{
        delay: delay,
        duration: duration,
        ease: 'easeOut',
        ...animation.animate.transition
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

// Loading state animation
const LoadingAnimation = ({ 
  type = 'pulse',
  size = 'md',
  className = ''
}) => {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const pulseAnimation = {
    scale: [1, 1.2, 1],
    opacity: [0.5, 1, 0.5]
  };

  const spinAnimation = {
    rotate: [0, 360]
  };

  const animations = {
    pulse: pulseAnimation,
    spin: spinAnimation
  };

  return (
    <motion.div
      className={`${sizes[size]} rounded-full bg-primary-turquoise-500 ${className}`}
      animate={animations[type]}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut'
      }}
    />
  );
};

// Hover effect wrapper
const HoverEffect = ({ 
  children, 
  scale = 1.05,
  duration = 0.2,
  className = ''
}) => {
  return (
    <motion.div
      whileHover={{ scale: scale }}
      whileTap={{ scale: scale * 0.95 }}
      transition={{ duration: duration, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

// Floating action button with entrance animation
const FloatingActionButton = ({ 
  children, 
  onClick,
  position = 'bottom-right',
  theme = 'primary',
  className = ''
}) => {
  const positions = {
    'bottom-right': 'fixed bottom-6 right-6',
    'bottom-left': 'fixed bottom-6 left-6',
    'bottom-center': 'fixed bottom-6 left-1/2 transform -translate-x-1/2'
  };

  const themes = {
    primary: 'bg-primary-turquoise-500 hover:bg-primary-turquoise-600 text-white shadow-primary-turquoise/30',
    secondary: 'bg-white hover:bg-gray-50 text-secondary-darkgray-700 shadow-gray-500/30',
    danger: 'bg-error hover:bg-error-dark text-white shadow-red-500/30'
  };

  return (
    <motion.button
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      transition={{ 
        type: 'spring',
        stiffness: 260,
        damping: 20
      }}
      onClick={onClick}
      className={`
        ${positions[position]}
        ${themes[theme]}
        w-14 h-14 rounded-full shadow-lg
        flex items-center justify-center
        z-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-turquoise-500
        ${className}
      `}
    >
      {children}
    </motion.button>
  );
};

// Progress indicator with animation
const AnimatedProgress = ({ 
  value = 0, 
  max = 100,
  theme = 'primary',
  showValue = true,
  className = ''
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  const themes = {
    primary: 'bg-primary-turquoise-500',
    success: 'bg-success',
    warning: 'bg-warning',
    error: 'bg-error'
  };

  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between items-center mb-2">
        {showValue && (
          <motion.span 
            className="text-sm font-medium text-secondary-darkgray-700"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {Math.round(percentage)}%
          </motion.span>
        )}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <motion.div
          className={`h-full ${themes[theme]} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ 
            duration: 1,
            ease: 'easeOut'
          }}
        />
      </div>
    </div>
  );
};

PageTransition.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['default', 'slide', 'fade', 'scale']),
  duration: PropTypes.number,
  className: PropTypes.string
};

StaggerContainer.propTypes = {
  children: PropTypes.node.isRequired,
  staggerDelay: PropTypes.number,
  className: PropTypes.string
};

EntranceAnimation.propTypes = {
  children: PropTypes.node.isRequired,
  type: PropTypes.oneOf(['fadeUp', 'fadeDown', 'fadeLeft', 'fadeRight', 'scale', 'bounce']),
  delay: PropTypes.number,
  duration: PropTypes.number,
  className: PropTypes.string
};

LoadingAnimation.propTypes = {
  type: PropTypes.oneOf(['pulse', 'spin']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  className: PropTypes.string
};

HoverEffect.propTypes = {
  children: PropTypes.node.isRequired,
  scale: PropTypes.number,
  duration: PropTypes.number,
  className: PropTypes.string
};

FloatingActionButton.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func.isRequired,
  position: PropTypes.oneOf(['bottom-right', 'bottom-left', 'bottom-center']),
  theme: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  className: PropTypes.string
};

AnimatedProgress.propTypes = {
  value: PropTypes.number,
  max: PropTypes.number,
  theme: PropTypes.oneOf(['primary', 'success', 'warning', 'error']),
  showValue: PropTypes.bool,
  className: PropTypes.string
};

export {
  PageTransition,
  StaggerContainer,
  EntranceAnimation,
  LoadingAnimation,
  HoverEffect,
  FloatingActionButton,
  AnimatedProgress
};
