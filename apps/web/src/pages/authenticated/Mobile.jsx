import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Smartphone, Phone, MessageSquare, Wifi, Settings, 
  AlertTriangle, BarChart3, Signal, ChevronRight, Home
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";

export default function MobilePage() {
  const { 
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

  const mobileData = dashboardData.mobile || {};

  // Mock usage data for different periods
  const usageData = {
    day: [
      { time: '00:00', data: 0.1, calls: 0, sms: 0 },
      { time: '03:00', data: 0.05, calls: 0, sms: 0 },
      { time: '06:00', data: 0.3, calls: 2, sms: 1 },
      { time: '09:00', data: 0.8, calls: 5, sms: 3 },
      { time: '12:00', data: 1.2, calls: 3, sms: 2 },
      { time: '15:00', data: 0.9, calls: 4, sms: 1 },
      { time: '18:00', data: 1.5, calls: 8, sms: 5 },
      { time: '21:00', data: 2.1, calls: 6, sms: 4 }
    ],
    week: [
      { time: 'Mon', data: 2.5, calls: 25, sms: 15 },
      { time: 'Tue', data: 3.1, calls: 32, sms: 18 },
      { time: 'Wed', data: 2.8, calls: 28, sms: 12 },
      { time: 'Thu', data: 3.5, calls: 35, sms: 22 },
      { time: 'Fri', data: 4.2, calls: 42, sms: 28 },
      { time: 'Sat', data: 5.8, calls: 18, sms: 35 },
      { time: 'Sun', data: 4.9, calls: 15, sms: 25 }
    ],
    month: [
      { time: 'Week 1', data: 18.5, calls: 180, sms: 125 },
      { time: 'Week 2', data: 22.1, calls: 195, sms: 140 },
      { time: 'Week 3', data: 19.8, calls: 165, sms: 110 },
      { time: 'Week 4', data: 21.3, calls: 175, sms: 130 }
    ]
  };

  const currentUsageData = usageData[selectedPeriod];
  const maxData = Math.max(...currentUsageData.map(d => d.data));

  const getUsageStatus = (percentage) => {
    if (percentage < 50) return { status: 'Low', color: 'text-accent-green', bg: 'bg-accent-green/10' };
    if (percentage < 80) return { status: 'Normal', color: 'text-accent-blue', bg: 'bg-accent-blue/10' };
    return { status: 'High', color: 'text-accent-red', bg: 'bg-accent-red/10' };
  };

  const dataUsagePercentage = ((mobileData.dataUsed || 0) / (mobileData.dataAllowance || 100)) * 100;
  const currentUsageStatus = getUsageStatus(dataUsagePercentage);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-3 border-accent-blue border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-secondary-darkgray via-secondary-darkgray/95 to-secondary-darkgray border border-accent-blue/30 shadow-xl">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute inset-0 bg-gradient-to-r from-accent-blue/30 via-transparent to-primary-turquoise/30 animate-shimmer"></div>
          </div>

          <div className="relative z-10 p-2">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center space-x-3 mb-4 lg:mb-0">
                <div className="w-12 h-12 lg:w-16 lg:h-16 rounded-xl bg-gradient-to-br from-accent-blue to-accent-blue/80 flex items-center justify-center shadow-lg shadow-accent-blue/30">
                  <Smartphone className="h-4 w-4 lg:h-8 lg:w-8 text-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <h1 className="text-xl lg:text-3xl font-bold text-white">
                      SpotOn Mobile
                    </h1>
                    <div className="px-2 py-1 rounded-full bg-accent-blue/20 border border-accent-blue/40">
                      <span className="text-accent-blue text-xs font-semibold">Connected</span>
                    </div>
                  </div>
                  <p className="text-accent-lightturquoise text-sm lg:text-base mb-1">
                    Mobile service management
                  </p>
                  <p className="text-accent-lightturquoise/80 text-xs lg:text-sm">
                    Data, calls, and SMS tracking
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 text-accent-lightturquoise">
                <Signal className="h-5 w-5 text-accent-blue" />
                <div className="text-right">
                  <div className="text-xs opacity-80">Network Status</div>
                  <div className="text-sm font-semibold">4G Connected</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Current Usage Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2"
      >
        <ServiceCard
          title="Data Used"
          icon={BarChart3}
          value={`${mobileData.dataUsed || 0} GB`}
          subtitle="This month"
          color="accent-blue"
          className="hover:shadow-lg hover:shadow-accent-blue/20 transition-all duration-300"
        >
          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${currentUsageStatus.bg} ${currentUsageStatus.color} border border-current/20`}>
            <Signal className="h-3 w-3 mr-1" />
            {currentUsageStatus.status}
          </div>
        </ServiceCard>

        <ServiceCard
          title="Calls Made"
          icon={Phone}
          value={`${mobileData.callsMade || 0}`}
          subtitle="This month"
          color="accent-green"
          className="hover:shadow-lg hover:shadow-accent-green/20 transition-all duration-300"
        />

        <ServiceCard
          title="SMS Sent"
          icon={MessageSquare}
          value={`${mobileData.smsSent || 0}`}
          subtitle="This month"
          color="accent-purple"
          className="hover:shadow-lg hover:shadow-accent-purple/20 transition-all duration-300"
        />

        <ServiceCard
          title="Current Plan"
          icon={Settings}
          value={mobileData.plan || 'Unlimited'}
          subtitle="Active plan"
          color="primary-turquoise"
          className="hover:shadow-lg hover:shadow-primary-turquoise/20 transition-all duration-300"
        />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Usage Pattern */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center mb-3 sm:mb-0">
                  <BarChart3 className="h-5 w-5 mr-2 text-accent-blue" />
                  Usage Pattern
                </h2>
                
                <div className="flex bg-gray-100 rounded-lg p-1 shadow-inner">
                  {['day', 'week', 'month'].map((period) => (
                    <button
                      key={period}
                      onClick={() => setSelectedPeriod(period)}
                      className={`px-3 py-1.5 rounded-md text-sm font-semibold transition-all duration-300 capitalize ${
                        selectedPeriod === period
                          ? 'bg-accent-blue text-white shadow-lg shadow-accent-blue/30'
                          : 'text-gray-600 hover:text-secondary-darkgray hover:bg-white/50'
                      }`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                {currentUsageData.map((item, index) => (
                  <motion.div
                    key={item.time}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 * index }}
                    className="group"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-16 text-sm font-semibold text-gray-600">
                        {item.time}
                      </div>
                      <div className="flex items-center space-x-3 text-sm">
                        <span className="text-accent-blue font-semibold">{item.data} GB</span>
                        <span className="text-accent-green font-semibold">{item.calls} calls</span>
                        <span className="text-accent-purple font-semibold">{item.sms} SMS</span>
                      </div>
                    </div>
                    <div className="relative">
                      <div className="h-8 bg-gray-100 rounded-lg overflow-hidden shadow-inner">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(item.data / maxData) * 100}%` }}
                          transition={{ duration: 1, delay: 0.2 + (0.1 * index) }}
                          className="h-full bg-gradient-to-r from-accent-blue via-accent-blue/90 to-accent-blue/80 rounded-lg shadow-sm group-hover:shadow-md transition-shadow duration-300"
                        />
                      </div>
                      <div className="absolute inset-0 flex items-center px-3">
                        <span className="text-xs font-semibold text-white drop-shadow-sm">
                          {item.data} GB • {item.calls} calls • {item.sms} SMS
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 text-center">
                  <div className="p-3 rounded-lg bg-accent-blue/5 border border-accent-blue/20">
                    <div className="text-xl lg:text-2xl font-bold text-accent-blue">
                      {currentUsageData.reduce((sum, item) => sum + item.data, 0).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Total Data</div>
                  </div>
                  <div className="p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
                    <div className="text-xl lg:text-2xl font-bold text-accent-green">
                      {currentUsageData.reduce((sum, item) => sum + item.calls, 0)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Total Calls</div>
                  </div>
                  <div className="p-3 rounded-lg bg-accent-purple/5 border border-accent-purple/20">
                    <div className="text-xl lg:text-2xl font-bold text-accent-purple">
                      {currentUsageData.reduce((sum, item) => sum + item.sms, 0)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Total SMS</div>
                  </div>
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
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Smartphone className="h-5 w-5 mr-2 text-accent-blue" />
                  Plan Details
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-accent-blue/5 border border-accent-blue/20">
                  <div className="text-center">
                    <BarChart3 className="h-8 w-8 text-accent-blue mx-auto mb-2" />
                    <div className="text-lg font-bold text-accent-blue">
                      {mobileData.dataAllowance || 'Unlimited'}
                    </div>
                    <div className="text-xs text-gray-500">Data Allowance</div>
                    {mobileData.dataAllowance && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-accent-blue h-2 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(dataUsagePercentage, 100)}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {dataUsagePercentage.toFixed(1)}% used
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="text-center">
                    <Phone className="h-8 w-8 text-accent-green mx-auto mb-2" />
                    <div className="text-lg font-bold text-accent-green">
                      {mobileData.callAllowance || 'Unlimited'}
                    </div>
                    <div className="text-xs text-gray-500">Call Minutes</div>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-accent-purple/5 border border-accent-purple/20">
                  <div className="text-center">
                    <MessageSquare className="h-8 w-8 text-accent-purple mx-auto mb-2" />
                    <div className="text-lg font-bold text-accent-purple">
                      {mobileData.smsAllowance || 'Unlimited'}
                    </div>
                    <div className="text-xs text-gray-500">SMS Messages</div>
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-5 w-5 mr-2 text-accent-blue" />
                  Quick Actions
                </h2>
              </div>

              <div className="space-y-2">
                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 hover:from-accent-blue/20 hover:to-accent-blue/10 border border-accent-blue/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-blue/20">
                        <BarChart3 className="h-4 w-4 text-accent-blue" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Usage Report</div>
                        <div className="text-xs text-gray-500">Detailed analysis</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-blue group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-green/10 to-accent-green/5 hover:from-accent-green/20 hover:to-accent-green/10 border border-accent-green/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-green/20">
                        <Settings className="h-4 w-4 text-accent-green" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Plan Settings</div>
                        <div className="text-xs text-gray-500">Manage plan</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-green group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 hover:from-primary-turquoise/20 hover:to-primary-turquoise/10 border border-primary-turquoise/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-primary-turquoise/20">
                        <Wifi className="h-4 w-4 text-primary-turquoise" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Network Settings</div>
                        <div className="text-xs text-gray-500">APN & roaming</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary-turquoise group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Account Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Home className="h-5 w-5 mr-2 text-accent-blue" />
                  Account Details
                </h2>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Account Holder</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {getUserDisplayName()}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Mobile Number</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobileData.phoneNumber || 'Not provided'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Plan Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobileData.plan || 'Unlimited Plan'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Network</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobileData.network || 'SpotOn 4G'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Bill Cycle</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobileData.billCycle || '15th of month'}
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
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-accent-blue" />
                  Network Status
                </h2>
              </div>

              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-gradient-to-r from-accent-green/10 to-accent-green/5 border border-accent-green/30 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-green">Network operational</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-1 ml-4">
                    4G coverage available in your area
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 border border-accent-blue/30 shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-accent-blue rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-blue">Signal strength: Strong</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-1 ml-4">
                    Last updated: {currentTime.toLocaleTimeString()}
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