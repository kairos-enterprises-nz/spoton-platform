/**
 * Environment-aware error handling utility
 * Different error handling strategies for UAT vs Production
 */

import logger from './logger.js';

const isUAT = typeof __IS_UAT__ !== 'undefined' ? __IS_UAT__ : false;
const isProduction = typeof __IS_PRODUCTION__ !== 'undefined' ? __IS_PRODUCTION__ : false;

class ErrorHandler {
  constructor() {
    this.environment = typeof __ENVIRONMENT__ !== 'undefined' ? __ENVIRONMENT__ : 'development';
    
    // Set up global error handlers
    this.setupGlobalErrorHandlers();
  }

  setupGlobalErrorHandlers() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(event.reason, 'Unhandled Promise Rejection');
      
      // Prevent the default browser behavior (console error) in production
      if (isProduction) {
        event.preventDefault();
      }
    });

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      this.handleError(event.error, 'JavaScript Error', {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
      
      // Don't prevent default in UAT so developers can see the error
      if (isProduction) {
        event.preventDefault();
      }
    });
  }

  handleError(error, context = 'Unknown', metadata = {}) {
    const errorInfo = {
      message: error?.message || 'Unknown error',
      stack: error?.stack,
      context,
      metadata,
      timestamp: new Date().toISOString(),
      environment: this.environment,
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    if (isUAT) {
      // In UAT: Log detailed error information
      logger.error('Error occurred:', errorInfo);
      
      // Show detailed error in console for debugging
      console.group('🚨 Error Details (UAT)');
      console.error('Error:', error);
      console.log('Context:', context);
      console.log('Metadata:', metadata);
      console.log('Stack trace:', error?.stack);
      console.groupEnd();
      
    } else if (isProduction) {
      // In Production: Log minimal information and send to monitoring service
      logger.error('Application error occurred');
      
      // Here you would typically send to a monitoring service like Sentry
      // this.sendToMonitoringService(errorInfo);
      
    } else {
      // Development: Full logging
      logger.error('Development Error:', errorInfo);
    }

    return errorInfo;
  }

  // Method to handle API errors specifically
  handleApiError(error, endpoint = 'unknown') {
    const apiErrorInfo = {
      endpoint,
      status: error?.response?.status,
      statusText: error?.response?.statusText,
      data: error?.response?.data,
      message: error?.message
    };

    if (isUAT) {
      logger.error('API Error (UAT):', apiErrorInfo);
      console.table(apiErrorInfo);
    } else if (isProduction) {
      logger.error('API request failed');
      // Send to monitoring service
    } else {
      logger.error('API Error (Dev):', apiErrorInfo);
    }

    return apiErrorInfo;
  }

  // Method to handle user-facing errors
  handleUserError(message, showToUser = true) {
    if (isUAT) {
      logger.warn('User Error (UAT):', message);
    } else if (isProduction) {
      logger.warn('User error occurred');
    }

    if (showToUser) {
      // Here you would typically show a user-friendly error message
      // For now, just return the message
      return isProduction 
        ? 'Something went wrong. Please try again.' 
        : message;
    }

    return message;
  }

  // Send error to monitoring service (placeholder)
  sendToMonitoringService(errorInfo) {
    // In a real application, you would send this to a service like:
    // - Sentry
    // - LogRocket
    // - Datadog
    // - Custom logging endpoint
    
    if (isProduction) {
      // Example: fetch('/api/errors', { method: 'POST', body: JSON.stringify(errorInfo) })
      logger.log('Would send to monitoring service:', { 
        message: errorInfo.message, 
        context: errorInfo.context 
      });
    }
  }
}

// Create singleton instance
const errorHandler = new ErrorHandler();

export default errorHandler; 