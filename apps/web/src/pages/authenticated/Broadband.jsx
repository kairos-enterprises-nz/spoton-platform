import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Wifi, Download, Upload, Activity, Settings, 
  AlertTriangle, Router, Globe, BarChart3, Gauge, Signal,
  ChevronRight
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";

export default function BroadbandPage() {
  const { 
    user, 
    dashboardData, 
    loading, 
    getUserDisplayName 
  } = useDashboard();

  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const broadbandData = dashboardData.broadband || {};

  // Mock speed test data
  const speedTestHistory = [
    { date: '2024-01-20', download: 95.2, upload: 18.4, ping: 12 },
    { date: '2024-01-19', download: 98.1, upload: 19.2, ping: 11 },
    { date: '2024-01-18', download: 92.8, upload: 17.9, ping: 13 },
    { date: '2024-01-17', download: 96.5, upload: 18.8, ping: 10 },
    { date: '2024-01-16', download: 94.3, upload: 18.1, ping: 12 }
  ];

  // Mock usage data for different periods
  const usageData = {
    day: [
      { time: '00:00', usage: 2.1, devices: 3 },
      { time: '03:00', usage: 0.8, devices: 1 },
      { time: '06:00', usage: 4.2, devices: 5 },
      { time: '09:00', usage: 8.5, devices: 7 },
      { time: '12:00', usage: 12.3, devices: 9 },
      { time: '15:00', usage: 15.8, devices: 11 },
      { time: '18:00', usage: 22.4, devices: 14 },
      { time: '21:00', usage: 18.7, devices: 12 }
    ],
    week: [
      { time: 'Mon', usage: 125.5, devices: 12 },
      { time: 'Tue', usage: 142.1, devices: 14 },
      { time: 'Wed', usage: 138.8, devices: 13 },
      { time: 'Thu', usage: 155.2, devices: 15 },
      { time: 'Fri', usage: 168.7, devices: 16 },
      { time: 'Sat', usage: 195.3, devices: 18 },
      { time: 'Sun', usage: 178.9, devices: 17 }
    ],
    month: [
      { time: 'Week 1', usage: 850, devices: 14 },
      { time: 'Week 2', usage: 920, devices: 15 },
      { time: 'Week 3', usage: 780, devices: 13 },
      { time: 'Week 4', usage: 890, devices: 14 }
    ]
  };

  const currentUsageData = usageData[selectedPeriod];
  const maxUsage = Math.max(...currentUsageData.map(d => d.usage));

  const getConnectionStatus = (speed) => {
    if (speed >= 90) return { status: 'Excellent', color: 'text-accent-green', bg: 'bg-accent-green/10' };
    if (speed >= 70) return { status: 'Good', color: 'text-primary-turquoise', bg: 'bg-primary-turquoise/10' };
    if (speed >= 50) return { status: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-50' };
    return { status: 'Poor', color: 'text-accent-red', bg: 'bg-accent-red/10' };
  };

  const currentConnectionStatus = getConnectionStatus(broadbandData.currentSpeed || 0);
  const latestSpeedTest = speedTestHistory[0];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-3 border-accent-purple border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-secondary-darkgray via-secondary-darkgray/95 to-secondary-darkgray border border-accent-purple/30 shadow-2xl">
          {/* Animated background pattern */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute inset-0 bg-gradient-to-r from-accent-purple/30 via-transparent to-primary-turquoise/30 animate-shimmer"></div>
            <svg className="w-full h-full" viewBox="0 0 100 20" preserveAspectRatio="none">
              <defs>
                <pattern id="broadband-grid" width="10" height="10" patternUnits="userSpaceOnUse">
                  <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-accent-purple/40"/>
                </pattern>
              </defs>
              <rect width="100" height="20" fill="url(#broadband-grid)" />
            </svg>
          </div>

          <div className="relative z-10 p-2 lg:p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center space-x-4 mb-6 lg:mb-0">
                <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-2xl bg-gradient-to-br from-accent-purple to-accent-purple/80 flex items-center justify-center shadow-lg shadow-accent-purple/30">
                  <Wifi className="h-8 w-8 lg:h-10 lg:w-10 text-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-2xl lg:text-4xl font-bold text-white">
                      SpotOn Broadband
                    </h1>
                    <div className="px-3 py-1 rounded-full bg-accent-purple/20 border border-accent-purple/40">
                      <span className="text-accent-purple text-sm font-semibold">Connected</span>
                    </div>
                  </div>
                  <p className="text-accent-lightturquoise text-sm lg:text-base mb-1">
                    High-speed internet connection
                  </p>
                  <p className="text-accent-lightturquoise/80 text-xs lg:text-sm">
                    Real-time speed monitoring and usage tracking
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4 text-accent-lightturquoise">
                <Signal className="h-5 w-5 text-accent-purple" />
                <div className="text-right">
                  <div className="text-xs opacity-80">Connection Status</div>
                  <div className="text-sm font-semibold">Online</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Current Status Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2"
      >
        <ServiceCard
          title="Download Speed"
          icon={Download}
          value={`${latestSpeedTest?.download || 0} Mbps`}
          subtitle="Latest test"
          color="accent-purple"
          className="hover:shadow-xl hover:shadow-accent-purple/20 transition-all duration-300"
        >
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${currentConnectionStatus.bg} ${currentConnectionStatus.color} border border-current/20`}>
            <Activity className="h-3 w-3 mr-1" />
            {currentConnectionStatus.status}
          </div>
        </ServiceCard>

        <ServiceCard
          title="Upload Speed"
          icon={Upload}
          value={`${latestSpeedTest?.upload || 0} Mbps`}
          subtitle="Latest test"
          color="accent-blue"
          className="hover:shadow-xl hover:shadow-accent-blue/20 transition-all duration-300"
        />

        <ServiceCard
          title="Data Usage"
          icon={BarChart3}
          value={`${broadbandData.monthlyUsage || 0} GB`}
          subtitle="This month"
          trend="up"
          trendValue="15% increase"
          color="primary-turquoise"
          className="hover:shadow-xl hover:shadow-primary-turquoise/20 transition-all duration-300"
        />

        <ServiceCard
          title="Connected Devices"
          icon={Router}
          value={`${broadbandData.connectedDevices || 0}`}
          subtitle="Active now"
          color="accent-green"
          className="hover:shadow-xl hover:shadow-accent-green/20 transition-all duration-300"
        />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-3">
          {/* Speed Test Results */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center mb-4 sm:mb-0">
                  <Gauge className="h-4 w-4 mr-3 text-accent-purple" />
                  Speed Test History
                </h2>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-4 py-2 bg-accent-purple text-white rounded-xl hover:bg-accent-purple/90 transition-all duration-300 shadow-lg shadow-accent-purple/20"
                >
                  Run Speed Test
                </motion.button>
              </div>

              <div className="space-y-4">
                {speedTestHistory.map((test, index) => (
                  <motion.div
                    key={test.date}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 * index }}
                    className="p-2 rounded-xl bg-gray-50/50 border border-gray-200/50 hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-all duration-300 group"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="text-sm font-semibold text-secondary-darkgray">
                        {new Date(test.date).toLocaleDateString()}
                      </div>
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <Download className="h-4 w-4 text-accent-purple" />
                          <span className="font-semibold text-accent-purple">{test.download} Mbps</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Upload className="h-4 w-4 text-accent-blue" />
                          <span className="font-semibold text-accent-blue">{test.upload} Mbps</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Activity className="h-4 w-4 text-accent-green" />
                          <span className="font-semibold text-accent-green">{test.ping}ms</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Speed bars */}
                    <div className="space-y-2">
                      <div className="relative">
                        <div className="h-3 bg-gray-100 rounded-full overflow-hidden shadow-inner">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(test.download / 100) * 100}%` }}
                            transition={{ duration: 1, delay: 0.2 + (0.1 * index) }}
                            className="h-full bg-gradient-to-r from-accent-purple via-accent-purple/90 to-accent-purple/80 rounded-full shadow-sm"
                          />
                        </div>
                        <div className="absolute inset-0 flex items-center px-3">
                          <span className="text-xs font-semibold text-white drop-shadow-sm">
                            Download: {test.download} Mbps
                          </span>
                        </div>
                      </div>
                      
                      <div className="relative">
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden shadow-inner">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(test.upload / 25) * 100}%` }}
                            transition={{ duration: 1, delay: 0.3 + (0.1 * index) }}
                            className="h-full bg-gradient-to-r from-accent-blue via-accent-blue/90 to-accent-blue/80 rounded-full shadow-sm"
                          />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-center">
                  <div className="p-4 rounded-xl bg-accent-purple/5 border border-accent-purple/20">
                    <div className="text-2xl lg:text-3xl font-bold text-accent-purple">
                      {(speedTestHistory.reduce((sum, test) => sum + test.download, 0) / speedTestHistory.length).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Avg Download</div>
                  </div>
                  <div className="p-4 rounded-xl bg-accent-blue/5 border border-accent-blue/20">
                    <div className="text-2xl lg:text-3xl font-bold text-accent-blue">
                      {(speedTestHistory.reduce((sum, test) => sum + test.upload, 0) / speedTestHistory.length).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Avg Upload</div>
                  </div>
                  <div className="p-4 rounded-xl bg-accent-green/5 border border-accent-green/20">
                    <div className="text-2xl lg:text-3xl font-bold text-accent-green">
                      {(speedTestHistory.reduce((sum, test) => sum + test.ping, 0) / speedTestHistory.length).toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Avg Ping (ms)</div>
                  </div>
                  <div className="p-4 rounded-xl bg-primary-turquoise/5 border border-primary-turquoise/20">
                    <div className="text-2xl lg:text-3xl font-bold text-primary-turquoise">
                      {Math.max(...speedTestHistory.map(t => t.download)).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Peak Speed</div>
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Usage Pattern */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center mb-4 sm:mb-0">
                  <Activity className="h-4 w-4 mr-3 text-accent-purple" />
                  Usage Pattern
                </h2>
                
                <div className="flex bg-gray-100 rounded-xl p-1 shadow-inner">
                  {['day', 'week', 'month'].map((period) => (
                    <button
                      key={period}
                      onClick={() => setSelectedPeriod(period)}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 capitalize ${
                        selectedPeriod === period
                          ? 'bg-accent-purple text-white shadow-lg shadow-accent-purple/30'
                          : 'text-gray-600 hover:text-secondary-darkgray hover:bg-white/50'
                      }`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                {currentUsageData.map((item, index) => (
                  <motion.div
                    key={item.time}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 * index }}
                    className="group"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-20 text-sm font-semibold text-gray-600">
                        {item.time}
                      </div>
                      <div className="flex items-center space-x-4 text-sm">
                        <span className="text-accent-purple font-semibold">{item.usage} GB</span>
                        <span className="text-accent-green font-semibold">{item.devices} devices</span>
                      </div>
                    </div>
                    <div className="relative">
                      <div className="h-10 bg-gray-100 rounded-xl overflow-hidden shadow-inner">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(item.usage / maxUsage) * 100}%` }}
                          transition={{ duration: 1, delay: 0.2 + (0.1 * index) }}
                          className="h-full bg-gradient-to-r from-accent-purple via-accent-purple/90 to-accent-purple/80 rounded-xl shadow-sm group-hover:shadow-md transition-shadow duration-300"
                        />
                      </div>
                      <div className="absolute inset-0 flex items-center px-4">
                        <span className="text-xs font-semibold text-white drop-shadow-sm">
                          {item.usage} GB • {item.devices} devices
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar */}
        <div className="space-y-3">
          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-3 text-accent-purple" />
                  Quick Actions
                </h2>
              </div>

              <div className="space-y-3">
                <motion.button
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-4 rounded-xl bg-gradient-to-r from-accent-purple/10 to-accent-purple/5 hover:from-accent-purple/20 hover:to-accent-purple/10 border border-accent-purple/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-purple/20">
                        <Gauge className="h-4 w-4 text-accent-purple" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Speed Test</div>
                        <div className="text-xs text-gray-500">Check connection</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-purple group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-4 rounded-xl bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 hover:from-accent-blue/20 hover:to-accent-blue/10 border border-accent-blue/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-blue/20">
                        <Router className="h-4 w-4 text-accent-blue" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Router Settings</div>
                        <div className="text-xs text-gray-500">Manage devices</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-blue group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-4 rounded-xl bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 hover:from-primary-turquoise/20 hover:to-primary-turquoise/10 border border-primary-turquoise/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-primary-turquoise/20">
                        <BarChart3 className="h-4 w-4 text-primary-turquoise" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Usage Report</div>
                        <div className="text-xs text-gray-500">Detailed analysis</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary-turquoise group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Connection Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Globe className="h-4 w-4 mr-3 text-accent-purple" />
                  Connection Details
                </h2>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Account Holder</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {getUserDisplayName()}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Service Address</span>
                  <span className="text-sm font-semibold text-secondary-darkgray text-right">
                    {user?.address || 'Not provided'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Plan Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {broadbandData.plan || 'Fibre 100/20'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Connection Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {broadbandData.connectionType || 'Fibre'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Router Model</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {broadbandData.routerModel || 'SpotOn Router Pro'}
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Network Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <AlertTriangle className="h-4 w-4 mr-3 text-accent-purple" />
                  Network Status
                </h2>
              </div>

              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-gradient-to-r from-accent-green/10 to-accent-green/5 border border-accent-green/30 shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-green">Connection stable</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-2 ml-6">
                    No issues detected with your broadband service
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-gradient-to-r from-accent-purple/10 to-accent-purple/5 border border-accent-purple/30 shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-accent-purple rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-purple">Speed optimal</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-2 ml-6">
                    Your connection is performing at expected speeds
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 border border-primary-turquoise/30 shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-primary-turquoise rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-primary-turquoise">Router online</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-2 ml-6">
                    Last seen: {currentTime.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}