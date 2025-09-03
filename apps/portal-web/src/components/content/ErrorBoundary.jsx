import React from 'react';
import PropTypes from 'prop-types';
import { AlertTriangle, RefreshCw, Home, HelpCircle } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // In production, you would send this to your error tracking service
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom error UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <Card variant="elevated" padding="lg" className="text-center">
              <div className="mb-6">
                <div className="w-16 h-16 mx-auto bg-error-light rounded-full flex items-center justify-center mb-4">
                  <AlertTriangle className="h-8 w-8 text-error" />
                </div>
                <h1 className="text-heading-xl text-secondary-darkgray-800 mb-2">
                  Something went wrong
                </h1>
                <p className="text-body-base text-secondary-darkgray-600">
                  We're sorry, but something unexpected happened. This error has been reported to our team.
                </p>
              </div>

              {/* Error details (only in development) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="mb-6 p-4 bg-gray-100 rounded-lg text-left">
                  <h3 className="text-sm font-semibold text-gray-800 mb-2">Error Details:</h3>
                  <pre className="text-xs text-gray-600 overflow-auto max-h-32">
                    {this.state.error.toString()}
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              )}

              {/* Action buttons */}
              <div className="space-y-3">
                <Button
                  variant="primary"
                  size="md"
                  fullWidth
                  icon={<RefreshCw className="h-4 w-4" />}
                  onClick={this.handleRetry}
                >
                  Try Again
                </Button>
                
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    fullWidth
                    icon={<Home className="h-4 w-4" />}
                    onClick={this.handleGoHome}
                  >
                    Go Home
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    fullWidth
                    icon={<RefreshCw className="h-4 w-4" />}
                    onClick={this.handleReload}
                  >
                    Reload Page
                  </Button>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  fullWidth
                  icon={<HelpCircle className="h-4 w-4" />}
                  onClick={() => window.open('/support', '_blank')}
                >
                  Contact Support
                </Button>
              </div>

              {/* Additional help text */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-caption text-secondary-darkgray-500">
                  If this problem persists, please contact our support team with error code: ERR-{Date.now().toString(36).toUpperCase()}
                </p>
              </div>
            </Card>
          </div>
        </div>
      );
    }

    // Render children normally
    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.element,
  onError: PropTypes.func
};

// Higher-order component for easier usage
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

export default ErrorBoundary;
