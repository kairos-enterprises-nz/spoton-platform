import PropTypes from 'prop-types';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Calendar, Download } from 'lucide-react';

const defaultDailyData = [
  { name: "12AM", usage: 0.8 },
  { name: "4AM", usage: 0.5 },
  { name: "8AM", usage: 2.1 },
  { name: "12PM", usage: 1.7 },
  { name: "4PM", usage: 2.3 },
  { name: "8PM", usage: 3.5 },
  { name: "11PM", usage: 1.9 }
];

const defaultMonthlyData = [
  { name: "Jan", usage: 310 },
  { name: "Feb", usage: 290 },
  { name: "Mar", usage: 250 },
  { name: "Apr", usage: 220 },
  { name: "May", usage: 185 }
];

export default function UsageChart({ 
  data, 
  type = "daily", 
  title, 
  showDownload = false,
  onDownload 
}) {
  const chartData = data || (type === "daily" ? defaultDailyData : defaultMonthlyData);
  const chartTitle = title || (type === "daily" ? "Daily Usage" : "Monthly Consumption");

  const summaryData = {
    daily: {
      todayUsage: "12.8 kWh",
      dailyAverage: "14.3 kWh",
      peakTime: "7:00 PM - 9:00 PM"
    },
    monthly: {
      mayUsage: "185 kWh",
      vsLastMonth: "-16%",
      projected: "210 kWh",
      estBill: "$94.50"
    }
  };

  const summary = summaryData[type];

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 p-4 sm:p-6 transform hover:-translate-y-1">
      <div className="flex justify-between items-center mb-4 sm:mb-6">
        <h2 className="font-bold text-lg text-[#364153]">{chartTitle}</h2>
        <div className="flex items-center gap-2">
          {type === "daily" && (
            <div className="flex items-center">
              <span className="text-gray-500 mr-2 text-sm">May 22, 2025</span>
              <button className="p-1 rounded hover:bg-[#40E0D0]/10 transition-all duration-300">
                <Calendar size={16} className="text-gray-500" />
              </button>
            </div>
          )}
          {showDownload && (
            <button 
              onClick={onDownload}
              className="text-[#40E0D0] text-sm font-medium flex items-center group hover:text-[#40E0D0]/70 transition-all duration-300"
            >
              Download Report 
              <Download size={14} className="ml-1 group-hover:translate-y-0.5 transition-transform duration-300" />
            </button>
          )}
        </div>
      </div>
      
      <div className="w-full h-60 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          {type === "daily" ? (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value} kWh`, 'Usage']} />
              <Bar dataKey="usage" fill="#40E0D0" radius={[4, 4, 0, 0]} />
            </BarChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value} kWh`, 'Usage']} />
              <Line 
                type="monotone" 
                dataKey="usage" 
                stroke="#40E0D0" 
                strokeWidth={2}
                dot={{ r: 4, fill: "#40E0D0" }}
                activeDot={{ r: 6, fill: "#40E0D0" }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
      
      {type === "daily" ? (
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mt-4 pt-4 border-t border-gray-100 space-y-3 sm:space-y-0">
          <div>
            <p className="text-gray-500 text-sm">Today&apos;s Usage</p>
            <p className="font-medium">{summary.todayUsage}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Daily Average</p>
            <p className="font-medium">{summary.dailyAverage}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Peak Time</p>
            <p className="font-medium">{summary.peakTime}</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-4 pt-4 border-t border-gray-100">
          <div>
            <p className="text-gray-500 text-sm">May Usage</p>
            <p className="font-medium">{summary.mayUsage}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">vs. Last Month</p>
            <p className="text-green-500 font-medium">{summary.vsLastMonth}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Projected</p>
            <p className="font-medium">{summary.projected}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Est. Bill</p>
            <p className="font-medium">{summary.estBill}</p>
          </div>
        </div>
      )}
    </div>
  );
}

UsageChart.propTypes = {
  data: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    usage: PropTypes.number.isRequired
  })),
  type: PropTypes.oneOf(['daily', 'monthly']),
  title: PropTypes.string,
  showDownload: PropTypes.bool,
  onDownload: PropTypes.func
}; 