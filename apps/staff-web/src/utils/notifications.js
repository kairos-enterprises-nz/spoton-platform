/**
 * Simple notification system for the staff portal
 */

// Simple notification queue
let notificationQueue = [];
let notificationId = 0;

// Event listeners for notification updates
const listeners = new Set();

const addNotification = (type, message, duration = 5000) => {
  const id = ++notificationId;
  const notification = {
    id,
    type,
    message,
    timestamp: Date.now(),
    duration
  };
  
  notificationQueue.push(notification);
  
  // Notify listeners
  listeners.forEach(listener => listener(notificationQueue));
  
  // Auto remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }
  
  return id;
};

const removeNotification = (id) => {
  notificationQueue = notificationQueue.filter(n => n.id !== id);
  listeners.forEach(listener => listener(notificationQueue));
};

const clearNotifications = () => {
  notificationQueue = [];
  listeners.forEach(listener => listener(notificationQueue));
};

const subscribe = (listener) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

// Toast-like API for compatibility
export const toast = {
  success: (message, options = {}) => addNotification('success', message, options.duration),
  error: (message, options = {}) => addNotification('error', message, options.duration),
  warning: (message, options = {}) => addNotification('warning', message, options.duration),
  info: (message, options = {}) => addNotification('info', message, options.duration),
};

// Notification management
export const notifications = {
  getAll: () => [...notificationQueue],
  remove: removeNotification,
  clear: clearNotifications,
  subscribe
};
