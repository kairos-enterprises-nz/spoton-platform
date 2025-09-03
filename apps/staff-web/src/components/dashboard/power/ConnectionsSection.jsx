import { useState } from 'react';
import PropTypes from 'prop-types';
import { Home, ChevronRight } from 'lucide-react';

const defaultConnections = [
  {
    id: 1,
    address: "123 Main Street, Apt 4B",
    plan: "Standard Variable Rate",
    status: "Active",
    meterNumber: "E-45872109",
    lastReading: "May 15, 2025"
  },
  {
    id: 2,
    address: "457 Cedar Lane, Unit 8",
    plan: "Fixed Rate - 12 months",
    status: "Active",
    meterNumber: "E-78124536",
    lastReading: "May 18, 2025"
  }
];

export default function ConnectionsSection({ connections: propConnections, onConnectionSelect }) {
  const [selectedConnection, setSelectedConnection] = useState(0);
  const connections = propConnections || defaultConnections;

  const handleConnectionSelect = (index) => {
    setSelectedConnection(index);
    if (onConnectionSelect) {
      onConnectionSelect(connections[index], index);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 mb-4 sm:mb-6 transform hover:-translate-y-1">
      <div className="p-4 sm:p-6 border-b border-gray-100">
        <h2 className="text-lg font-bold text-[#364153] flex items-center">
          <Home size={20} className="mr-2 text-[#40E0D0]" />
          Your Connections
        </h2>
      </div>
      
      <div className="p-3 sm:p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          {connections.map((connection, index) => (
            <div 
              key={connection.id}
              className={`border rounded-lg p-3 sm:p-4 cursor-pointer transition-all duration-300 ${
                selectedConnection === index 
                  ? "border-[#40E0D0] bg-[#40E0D0]/5" 
                  : "border-gray-200 hover:border-[#40E0D0]/50 hover:bg-[#40E0D0]/5"
              }`}
              onClick={() => handleConnectionSelect(index)}
            >
              <div className="flex justify-between mb-2">
                <h3 className="font-medium text-[#364153]">{connection.address}</h3>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  connection.status === "Active" 
                    ? "bg-green-100 text-green-700" 
                    : "bg-gray-100 text-gray-700"
                }`}>
                  {connection.status}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-3 sm:gap-4 text-sm mt-3">
                <div>
                  <p className="text-gray-500">Plan</p>
                  <p className="font-medium">{connection.plan}</p>
                </div>
                <div>
                  <p className="text-gray-500">Meter Number</p>
                  <p className="font-medium">{connection.meterNumber}</p>
                </div>
                <div>
                  <p className="text-gray-500">Last Reading</p>
                  <p className="font-medium">{connection.lastReading}</p>
                </div>
                <div>
                  <button className="text-[#40E0D0] hover:text-[#40E0D0]/70 font-medium flex items-center transition-all duration-300 group">
                    View Details <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform duration-300" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-3 sm:mt-4 text-center">
          <button className="text-[#40E0D0] hover:bg-[#40E0D0]/10 font-medium py-2 px-4 rounded-lg transition-all duration-300">
            + Add New Connection
          </button>
        </div>
      </div>
    </div>
  );
}

ConnectionsSection.propTypes = {
  connections: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    address: PropTypes.string.isRequired,
    plan: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    meterNumber: PropTypes.string.isRequired,
    lastReading: PropTypes.string.isRequired
  })),
  onConnectionSelect: PropTypes.func
}; 