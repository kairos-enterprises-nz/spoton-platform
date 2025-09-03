import PropTypes from 'prop-types';
import { TrendingUp, ChevronRight } from "lucide-react";

export default function BroadbandStatus({ broadbandData }) {
  const defaultData = {
    download: 285,
    upload: 42,
    latency: 18,
    plan: "Fiber Optic 300",
    dataUsed: "428 GB",
    dataLimit: "Unlimited",
    contractEnd: "Nov 12, 2025"
  };

  const data = broadbandData || defaultData;

  return (
    <div className="bg-white rounded-xl shadow-md p-3 sm:p-6 hover:shadow-lg transition-all duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 sm:mb-4">
        <h2 className="font-bold text-lg text-[#364153] mb-2 sm:mb-0 flex items-center">
          <span className="w-2 h-2 bg-[#b14eb1] rounded-full mr-2"></span>
          Broadband Status
        </h2>
        <button className="text-[#b14eb1] text-sm font-medium flex items-center hover:bg-[#b14eb1]/10 px-3 py-1.5 rounded-lg transition-all duration-300 group">
          Run Speed Test 
          <ChevronRight size={16} className="ml-1 transition-transform duration-300 group-hover:translate-x-1" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4">
        <div className="p-3 sm:p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 hover:shadow-md">
          <p className="text-gray-500 text-xs sm:text-sm">Download</p>
          <p className="text-lg sm:text-xl font-bold text-[#364153]">{data.download} Mbps</p>
          <p className="text-[#4eb14e] text-xs flex items-center">
            <TrendingUp size={12} className="mr-1" />
            +5% from average
          </p>
        </div>
        <div className="p-3 sm:p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 hover:shadow-md">
          <p className="text-gray-500 text-xs sm:text-sm">Upload</p>
          <p className="text-lg sm:text-xl font-bold text-[#364153]">{data.upload} Mbps</p>
          <p className="text-gray-500 text-xs">Normal</p>
        </div>
        <div className="p-3 sm:p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 hover:shadow-md">
          <p className="text-gray-500 text-xs sm:text-sm">Latency</p>
          <p className="text-lg sm:text-xl font-bold text-[#364153]">{data.latency} ms</p>
          <p className="text-[#4eb14e] text-xs">Excellent</p>
        </div>
      </div>

      <div className="mt-3 pt-3 sm:mt-4 sm:pt-4 border-t border-gray-100">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-0">
          <div className="bg-gray-50 px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg transition-colors duration-300 w-full sm:w-auto">
            <p className="text-gray-500 text-xs">Current Plan</p>
            <p className="font-medium text-[#364153] text-sm sm:text-base">{data.plan}</p>
          </div>
          <div className="bg-gray-50 px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg transition-colors duration-300 w-full sm:w-auto">
            <p className="text-gray-500 text-xs">Data Used</p>
            <p className="font-medium text-[#364153] text-sm sm:text-base">{data.dataUsed} / {data.dataLimit}</p>
          </div>
          <div className="bg-gray-50 px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg transition-colors duration-300 w-full sm:w-auto">
            <p className="text-gray-500 text-xs">Contract Until</p>
            <p className="font-medium text-[#364153] text-sm sm:text-base">{data.contractEnd}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

BroadbandStatus.propTypes = {
  broadbandData: PropTypes.shape({
    download: PropTypes.number,
    upload: PropTypes.number,
    latency: PropTypes.number,
    plan: PropTypes.string,
    dataUsed: PropTypes.string,
    dataLimit: PropTypes.string,
    contractEnd: PropTypes.string
  })
}; 