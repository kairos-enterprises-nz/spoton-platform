import PropTypes from 'prop-types';
import { CheckCircle, AlertTriangle } from 'lucide-react';

export default function NetworkStatusBanner({ networkStatus }) {
  const defaultStatus = {
    status: "excellent",
    signal: "5G",
    lastOutage: "2025-04-12",
    nextMaintenance: "2025-06-01"
  };

  const status = networkStatus || defaultStatus;

  const getStatusColor = () => {
    switch (status.status) {
      case 'excellent': return 'bg-green-50 border-green-400';
      case 'good': return 'bg-blue-50 border-blue-400';
      case 'fair': return 'bg-yellow-50 border-yellow-400';
      case 'poor': return 'bg-red-50 border-red-400';
      default: return 'bg-gray-50 border-gray-400';
    }
  };

  const getStatusIcon = () => {
    if (status.status === 'excellent' || status.status === 'good') {
      return <CheckCircle className="h-5 w-5 text-green-600 mr-3" />;
    }
    return <AlertTriangle className="h-5 w-5 text-yellow-600 mr-3" />;
  };

  return (
    <div className={`mb-4 sm:mb-6 p-4 rounded-xl shadow-sm border-l-4 transition-all duration-300 hover:shadow-md ${getStatusColor()}`}>
      <div className="flex items-center">
        {getStatusIcon()}
        <div className="flex-1">
          <div className="font-medium text-[#364153]">
            Network Status: {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
          </div>
          <div className="text-sm text-gray-600">
            Signal: {status.signal} | Last outage: {status.lastOutage}
          </div>
        </div>
        <button className="text-[#4e80b1] hover:text-[#4e80b1]/70 font-medium text-sm transition-all duration-300">
          View Details
        </button>
      </div>
    </div>
  );
}

NetworkStatusBanner.propTypes = {
  networkStatus: PropTypes.shape({
    status: PropTypes.oneOf(['excellent', 'good', 'fair', 'poor']).isRequired,
    signal: PropTypes.string.isRequired,
    lastOutage: PropTypes.string.isRequired,
    nextMaintenance: PropTypes.string
  })
}; 