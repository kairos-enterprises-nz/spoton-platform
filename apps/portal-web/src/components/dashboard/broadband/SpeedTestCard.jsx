import { useState } from 'react';
import PropTypes from 'prop-types';
import { Activity } from 'lucide-react';

export default function SpeedTestCard({ speedTestData, onRunSpeedTest }) {
  const [speedTestRunning, setSpeedTestRunning] = useState(false);

  const defaultSpeedTest = {
    lastTest: "2025-05-20 14:30",
    download: 847,
    upload: 98,
    ping: 12,
    jitter: 2.1
  };

  const speedTest = speedTestData || defaultSpeedTest;

  const runSpeedTest = () => {
    setSpeedTestRunning(true);
    if (onRunSpeedTest) {
      onRunSpeedTest();
    }
    setTimeout(() => {
      setSpeedTestRunning(false);
    }, 3000);
  };

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 p-4 sm:p-6 transform hover:-translate-y-1 border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[#364153]">Speed Test</h3>
        <Activity className="h-5 w-5 text-[#40E0D0]" />
      </div>
      <div className="space-y-3 mb-4">
        <div className="flex justify-between">
          <span className="text-gray-600">Download</span>
          <span className="font-medium text-[#364153]">{speedTest.download} Mbps</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Upload</span>  
          <span className="font-medium text-[#364153]">{speedTest.upload} Mbps</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Ping</span>
          <span className="font-medium text-[#364153]">{speedTest.ping} ms</span>
        </div>
      </div>
      <div className="text-xs text-gray-500 mb-3">
        Last test: {speedTest.lastTest}
      </div>
      <button 
        onClick={runSpeedTest}
        disabled={speedTestRunning}
        className="w-full bg-[#40E0D0] hover:bg-[#40E0D0]/80 text-[#364153] py-2 px-4 rounded-lg transition-all duration-300 disabled:bg-gray-400 font-medium shadow-sm hover:shadow"
      >
        {speedTestRunning ? 'Testing...' : 'Run Speed Test'}
      </button>
    </div>
  );
}

SpeedTestCard.propTypes = {
  speedTestData: PropTypes.shape({
    lastTest: PropTypes.string.isRequired,
    download: PropTypes.number.isRequired,
    upload: PropTypes.number.isRequired,
    ping: PropTypes.number.isRequired,
    jitter: PropTypes.number
  }),
  onRunSpeedTest: PropTypes.func
}; 