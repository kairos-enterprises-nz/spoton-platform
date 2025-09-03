import { useState, useEffect } from "react";
import PropTypes from 'prop-types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const mockPowerData = {
  day: [
    { name: "12 AM", usage: 0.5, color: "#40E0D0" },
    { name: "3 AM", usage: 0.3, color: "#40E0D0" },
    { name: "6 AM", usage: 1.2, color: "#40E0D0" },
    { name: "9 AM", usage: 2.5, color: "#40E0D0" },
    { name: "12 PM", usage: 3.8, color: "#40E0D0" },
    { name: "3 PM", usage: 4.2, color: "#40E0D0" },
    { name: "6 PM", usage: 5.1, color: "#40E0D0" },
    { name: "9 PM", usage: 2.8, color: "#40E0D0" },
  ],
  week: [
    { name: "Mon", usage: 4.2, color: "#40E0D0" },
    { name: "Tue", usage: 3.8, color: "#40E0D0" },
    { name: "Wed", usage: 5.1, color: "#40E0D0" },
    { name: "Thu", usage: 6.3, color: "#40E0D0" },
    { name: "Fri", usage: 4.9, color: "#40E0D0" },
    { name: "Sat", usage: 3.5, color: "#40E0D0" },
    { name: "Sun", usage: 3.2, color: "#40E0D0" },
  ],
  month: [
    { name: "Week 1", usage: 32, color: "#40E0D0" },
    { name: "Week 2", usage: 35, color: "#40E0D0" },
    { name: "Week 3", usage: 28, color: "#40E0D0" },
    { name: "Week 4", usage: 30, color: "#40E0D0" },
  ],
};

export default function PowerUsageChart({ data, initialView = "week" }) {
  const [currentView, setCurrentView] = useState(initialView);
  const [powerData, setPowerData] = useState(mockPowerData.week);
  const [isLoading, setIsLoading] = useState(false);

  // Update chart data when view changes
  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      const dataToUse = data || mockPowerData;
      setPowerData(dataToUse[currentView]);
      setIsLoading(false);
    }, 300);
    
    return () => clearTimeout(timer);
  }, [currentView, data]);

  const summaryData = {
    currentPlan: "Standard Variable Rate",
    monthlyAverage: "142 kWh",
    costEstimate: "$86.42"
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-3 sm:p-6 hover:shadow-lg transition-all duration-300 relative">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-3 sm:mb-6">
        <h2 className="font-bold text-lg text-[#364153] mb-2 sm:mb-0 flex items-center">
          <span className="w-2 h-2 bg-[#40E0D0] rounded-full mr-2 animate-pulse"></span>
          Power Usage
        </h2>
        <div className="flex bg-gray-100 rounded-lg overflow-hidden shadow-sm text-xs">
          <button
            className={`px-2 py-1.5 sm:px-3 sm:py-1.5 sm:text-sm font-medium ${currentView === "day" ? "bg-[#40E0D0] text-[#364153]" : "text-gray-600 hover:bg-gray-200"} transition-colors duration-300`}
            onClick={() => setCurrentView("day")}
          >
            Day
          </button>
          <button
            className={`px-2 py-1.5 sm:px-3 sm:py-1.5 sm:text-sm font-medium ${currentView === "week" ? "bg-[#40E0D0] text-[#364153]" : "text-gray-600 hover:bg-gray-200"} transition-colors duration-300`}
            onClick={() => setCurrentView("week")}
          >
            Week
          </button>
          <button
            className={`px-2 py-1.5 sm:px-3 sm:py-1.5 sm:text-sm font-medium ${currentView === "month" ? "bg-[#40E0D0] text-[#364153]" : "text-gray-600 hover:bg-gray-200"} transition-colors duration-300`}
            onClick={() => setCurrentView("month")}
          >
            Month
          </button>
        </div>
      </div>
      <div className="w-full h-64 sm:h-72 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10 rounded-lg">
            <div className="w-8 h-8 border-4 border-[#40E0D0]/30 border-t-[#40E0D0] rounded-full animate-spin"></div>
          </div>
        )}
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={powerData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="name" tick={{ fill: '#364153' }} />
            <YAxis tick={{ fill: '#364153' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#fff', 
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              itemStyle={{ color: '#364153' }}
              formatter={(value) => [`${value} kWh`, 'Usage']}
              labelFormatter={(label) => `Time: ${label}`}
              cursor={{ fill: 'rgba(64, 224, 208, 0.1)' }}
            />
            <Bar 
              dataKey="usage" 
              fill="#40E0D0" 
              radius={[4, 4, 0, 0]} 
              animationDuration={1500}
              animationEasing="ease-in-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mt-3 pt-3 sm:mt-4 sm:pt-4 border-t border-gray-100 gap-2 sm:gap-0">
        <div className="bg-gray-50 px-2 py-2 sm:px-3 sm:py-2 rounded-lg hover:bg-gray-100 transition-colors duration-300 w-full sm:w-auto">
          <p className="text-gray-500 text-xs">Current Plan</p>
          <p className="font-medium text-[#364153] text-sm sm:text-base">{summaryData.currentPlan}</p>
        </div>
        <div className="bg-gray-50 px-2 py-2 sm:px-3 sm:py-2 rounded-lg hover:bg-gray-100 transition-colors duration-300 w-full sm:w-auto">
          <p className="text-gray-500 text-xs">Monthly Average</p>
          <p className="font-medium text-[#364153] text-sm sm:text-base">{summaryData.monthlyAverage}</p>
        </div>
        <div className="bg-gray-50 px-2 py-2 sm:px-3 sm:py-2 rounded-lg hover:bg-gray-100 transition-colors duration-300 w-full sm:w-auto">
          <p className="text-gray-500 text-xs">Cost Estimate</p>
          <p className="font-medium text-[#364153] text-sm sm:text-base">{summaryData.costEstimate}</p>
        </div>
      </div>
    </div>
  );
}

PowerUsageChart.propTypes = {
  data: PropTypes.shape({
    day: PropTypes.array,
    week: PropTypes.array,
    month: PropTypes.array
  }),
  initialView: PropTypes.oneOf(['day', 'week', 'month'])
}; 