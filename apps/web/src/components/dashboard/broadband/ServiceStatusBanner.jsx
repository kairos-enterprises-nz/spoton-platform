import PropTypes from 'prop-types';
import { CheckCircle, AlertTriangle } from 'lucide-react';

export default function ServiceStatusBanner({ serviceStatus }) {
  const defaultStatus = {
    status: "online",
    uptime: "99.8%",
    lastOutage: "2025-04-12",
    nextMaintenance: "2025-06-01"
  };

  const status = serviceStatus || defaultStatus;

  return (
    <div className={`mb-4 sm:mb-6 p-4 rounded-xl shadow-sm border-l-4 transition-all duration-300 hover:shadow-md ${
      status.status === 'online' 
        ? 'bg-green-50 border-green-400' 
        : 'bg-red-50 border-red-400'
    }`}>
      <div className="flex items-center">
        {status.status === 'online' ? (
          <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
        )}
        <div className="flex-1">
          <div className="font-medium text-[#364153]">
            Service Status: {status.status === 'online' ? 'Online' : 'Issues Detected'}
          </div>
          <div className="text-sm text-gray-600">
            Uptime: {status.uptime} | Last outage: {status.lastOutage}
          </div>
        </div>
        <button className="text-[#40E0D0] hover:text-[#40E0D0]/70 font-medium text-sm transition-all duration-300">
          View Details
        </button>
      </div>
    </div>
  );
}

ServiceStatusBanner.propTypes = {
  serviceStatus: PropTypes.shape({
    status: PropTypes.oneOf(['online', 'offline', 'issues']).isRequired,
    uptime: PropTypes.string.isRequired,
    lastOutage: PropTypes.string.isRequired,
    nextMaintenance: PropTypes.string
  })
}; 