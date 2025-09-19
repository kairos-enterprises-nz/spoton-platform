import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Wifi, Download, Upload, Activity, Settings, 
  AlertTriangle, Router, Globe, BarChart3, Gauge, Signal,
  ChevronRight, DollarSign
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";
import PageHeader from "../../components/dashboard/shared/PageHeader";
import ComingSoonCard from "../../components/dashboard/shared/ComingSoonCard";

export default function BroadbandPage() {
  const { 
    user, 
    dashboardData, 
    portalData,
    loading, 
    getUserDisplayName,
    userServices 
  } = useDashboard();

  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const broadbandData = dashboardData.broadband || {};
  const hasBroadbandService = userServices?.includes('broadband');
  const broadbandPlan = portalData?.services?.selected_plans?.broadband;

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

  // If service not contracted, show coming soon
  if (!hasBroadbandService) {
    return (
      <ComingSoonCard
        title="SpotOn Broadband"
        subtitle="Broadband service not included in your plan"
        theme="internet"
        actionText="Contact Support"
        onAction={() => {
          // TODO: Implement contact support
          console.log('User wants to add broadband service');
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <PageHeader
        title="Broadband"
        subtitle="Clear pricing, reliable service, and no loyalty tax. Broadband built on tomorrow's tech"
        icon={Wifi}
        statusText={broadbandData.statusText || 'Pending Activation'}
        statusColor={broadbandData.status === 'active' ? 'accent-green' : 'accent-orange'}
        theme="broadband"
        rightContent={
          <>
            <Signal className="h-4 w-4 text-accent-purple" />
            <div className="text-left">
              <div className="text-xs opacity-80">Status</div>
              <div className="text-sm font-semibold">
                {broadbandData.status === 'active' ? 'Connected' : 
                 broadbandData.status === 'installing' ? 'Installing' :
                 broadbandData.status === 'pending' ? 'Pending Activation' :
                 broadbandData.statusText || 'Pending Activation'}
              </div>
            </div>
          </>
        }
      />

      {/* Current Status Overview (compact) */}
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
          compact
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
          compact
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
          compact
          className="hover:shadow-xl hover:shadow-primary-turquoise/20 transition-all duration-300"
        />

        <ServiceCard
          title="Connected Devices"
          icon={Router}
          value={`${broadbandData.connectedDevices || 0}`}
          subtitle="Active now"
          color="accent-green"
          compact
          className="hover:shadow-xl hover:shadow-accent-green/20 transition-all duration-300"
        />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-3">
          {/* Connection Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Globe className="h-4 w-4 mr-3 text-accent-purple" />
                  Connection Details
                </h2>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Connection Status</span>
                  <span className="text-sm font-semibold text-accent-green flex items-center">
                    <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse mr-2"></div>
                    Connected
                  </span>
                </div>

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

          {/* Plan Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-3 text-accent-purple" />
                  Plan Details
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-accent-purple/5 border border-accent-purple/20 text-center">
                  <Download className="h-6 w-6 text-accent-purple mx-auto mb-2" />
                  <div className="text-xl font-bold text-accent-purple">
                    {latestSpeedTest?.download || 100} Mbps
                  </div>
                  <div className="text-xs text-gray-500">Download Speed</div>
                </div>

                <div className="p-4 rounded-lg bg-accent-blue/5 border border-accent-blue/20 text-center">
                  <Upload className="h-6 w-6 text-accent-blue mx-auto mb-2" />
                  <div className="text-xl font-bold text-accent-blue">
                    {latestSpeedTest?.upload || 20} Mbps
                  </div>
                  <div className="text-xs text-gray-500">Upload Speed</div>
                </div>

                <div className="p-4 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20 text-center">
                  <DollarSign className="h-6 w-6 text-primary-turquoise mx-auto mb-2" />
                  <div className="text-xl font-bold text-primary-turquoise">
                    ${broadbandData.monthlyPrice || '53.15'}
                  </div>
                  <div className="text-xs text-gray-500">Monthly Price</div>
                </div>
              </div>

              <div className="mt-4 p-3 rounded-lg bg-gray-50/50">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 font-medium">Plan Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {broadbandData.plan || 'Fibre 100/20'}
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar */}
        <div className="space-y-3">
          {/* Network Status - Compact */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <AlertTriangle className="h-4 w-4 mr-3 text-accent-purple" />
                  Network Status
                </h2>
              </div>

              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-green">Connection stable</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-accent-purple/5 border border-accent-purple/20">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-accent-purple rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-purple">Speed optimal</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-primary-turquoise rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-primary-turquoise">Router online</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 ml-4">
                    Last seen: {currentTime.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Quick Actions - Compact */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-3 text-accent-purple" />
                  Quick Actions
                </h2>
              </div>

              <div className="space-y-2">
                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-purple/10 to-accent-purple/5 hover:from-accent-purple/20 hover:to-accent-purple/10 border border-accent-purple/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Gauge className="h-4 w-4 text-accent-purple" />
                      <div className="font-semibold text-secondary-darkgray text-sm">Speed Test</div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-purple group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 hover:from-accent-blue/20 hover:to-accent-blue/10 border border-accent-blue/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Router className="h-4 w-4 text-accent-blue" />
                      <div className="font-semibold text-secondary-darkgray text-sm">Router Settings</div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-blue group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}