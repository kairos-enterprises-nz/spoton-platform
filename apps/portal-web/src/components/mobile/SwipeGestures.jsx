import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { motion, useMotionValue, useTransform, PanInfo } from 'framer-motion';

const SwipeGestures = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 100,
  className = '',
  disabled = false,
  ...props
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const constraintsRef = useRef(null);
  
  // Motion values for tracking drag
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  
  // Transform values for visual feedback
  const rotateX = useTransform(y, [-200, 0, 200], [15, 0, -15]);
  const rotateY = useTransform(x, [-200, 0, 200], [-15, 0, 15]);
  const scale = useTransform(
    [x, y],
    ([latestX, latestY]) => {
      const distance = Math.sqrt(latestX * latestX + latestY * latestY);
      return Math.max(0.9, 1 - distance / 1000);
    }
  );

  const handleDragStart = () => {
    if (!disabled) {
      setIsDragging(true);
      // Add haptic feedback if available
      if (navigator.vibrate) {
        navigator.vibrate(5);
      }
    }
  };

  const handleDragEnd = (event, info) => {
    if (disabled) return;
    
    setIsDragging(false);
    
    const { offset, velocity } = info;
    const swipeThreshold = threshold;
    const velocityThreshold = 500;
    
    // Determine swipe direction based on offset and velocity
    const absOffsetX = Math.abs(offset.x);
    const absOffsetY = Math.abs(offset.y);
    const absVelocityX = Math.abs(velocity.x);
    const absVelocityY = Math.abs(velocity.y);
    
    // Check if it's a valid swipe (either distance or velocity based)
    const isHorizontalSwipe = absOffsetX > absOffsetY && 
      (absOffsetX > swipeThreshold || absVelocityX > velocityThreshold);
    const isVerticalSwipe = absOffsetY > absOffsetX && 
      (absOffsetY > swipeThreshold || absVelocityY > velocityThreshold);
    
    if (isHorizontalSwipe) {
      if (offset.x > 0 && onSwipeRight) {
        // Add stronger haptic feedback for successful swipe
        if (navigator.vibrate) {
          navigator.vibrate(20);
        }
        onSwipeRight(info);
      } else if (offset.x < 0 && onSwipeLeft) {
        if (navigator.vibrate) {
          navigator.vibrate(20);
        }
        onSwipeLeft(info);
      }
    } else if (isVerticalSwipe) {
      if (offset.y > 0 && onSwipeDown) {
        if (navigator.vibrate) {
          navigator.vibrate(20);
        }
        onSwipeDown(info);
      } else if (offset.y < 0 && onSwipeUp) {
        if (navigator.vibrate) {
          navigator.vibrate(20);
        }
        onSwipeUp(info);
      }
    }
    
    // Reset position
    x.set(0);
    y.set(0);
  };

  return (
    <div ref={constraintsRef} className={`relative overflow-hidden ${className}`}>
      <motion.div
        drag={!disabled}
        dragConstraints={constraintsRef}
        dragElastic={0.1}
        dragMomentum={false}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        style={{
          x,
          y,
          rotateX,
          rotateY,
          scale,
        }}
        className={`${isDragging ? 'cursor-grabbing' : 'cursor-grab'} select-none`}
        whileTap={{ scale: 0.98 }}
        transition={{ 
          type: 'spring',
          stiffness: 300,
          damping: 30
        }}
        {...props}
      >
        {children}
      </motion.div>
      
      {/* Visual indicators for swipe directions (optional) */}
      {isDragging && (
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div className="bg-black/20 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm">
            Swipe to interact
          </div>
        </div>
      )}
    </div>
  );
};

SwipeGestures.propTypes = {
  children: PropTypes.node.isRequired,
  onSwipeLeft: PropTypes.func,
  onSwipeRight: PropTypes.func,
  onSwipeUp: PropTypes.func,
  onSwipeDown: PropTypes.func,
  threshold: PropTypes.number,
  className: PropTypes.string,
  disabled: PropTypes.bool,
};

// Higher-order component for easy integration
export const withSwipeGestures = (Component, swipeProps = {}) => {
  const SwipeableComponent = (props) => (
    <SwipeGestures {...swipeProps}>
      <Component {...props} />
    </SwipeGestures>
  );
  
  SwipeableComponent.displayName = `withSwipeGestures(${Component.displayName || Component.name})`;
  return SwipeableComponent;
};

// Hook for swipe detection without wrapper component
export const useSwipeGestures = ({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 100,
  element
}) => {
  useEffect(() => {
    if (!element || typeof window === 'undefined') return;

    let startX = 0;
    let startY = 0;
    let startTime = 0;

    const handleTouchStart = (e) => {
      const touch = e.touches[0];
      startX = touch.clientX;
      startY = touch.clientY;
      startTime = Date.now();
    };

    const handleTouchEnd = (e) => {
      if (!e.changedTouches.length) return;

      const touch = e.changedTouches[0];
      const endX = touch.clientX;
      const endY = touch.clientY;
      const endTime = Date.now();

      const deltaX = endX - startX;
      const deltaY = endY - startY;
      const deltaTime = endTime - startTime;

      // Ignore very quick taps or very slow movements
      if (deltaTime < 100 || deltaTime > 1000) return;

      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);

      // Determine if it's a horizontal or vertical swipe
      if (absX > absY && absX > threshold) {
        if (deltaX > 0 && onSwipeRight) {
          onSwipeRight({ deltaX, deltaY, deltaTime });
        } else if (deltaX < 0 && onSwipeLeft) {
          onSwipeLeft({ deltaX, deltaY, deltaTime });
        }
      } else if (absY > absX && absY > threshold) {
        if (deltaY > 0 && onSwipeDown) {
          onSwipeDown({ deltaX, deltaY, deltaTime });
        } else if (deltaY < 0 && onSwipeUp) {
          onSwipeUp({ deltaX, deltaY, deltaTime });
        }
      }
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [element, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, threshold]);
};

export default SwipeGestures;
