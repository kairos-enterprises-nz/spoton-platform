import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Zap, TrendingDown, Clock, DollarSign, 
  Activity, Lightbulb, Home, BarChart3, Settings,
  Gauge, Sun, Moon
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";

export default function PowerPage() {
  const { 
    dashboardData, 
    loading, 
    isFeatureEnabled,
    getUserDisplayName 
  } = useDashboard();

  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000); // Update every minute
    return () => clearInterval(timer);
  }, []);

  const powerData = dashboardData.power || {};

  // Mock usage data for different periods
  const usageData = {
    day: [
      { time: '00:00', usage: 0.8, cost: 0.12 },
      { time: '03:00', usage: 0.5, cost: 0.08 },
      { time: '06:00', usage: 1.2, cost: 0.18 },
      { time: '09:00', usage: 2.1, cost: 0.32 },
      { time: '12:00', usage: 3.2, cost: 0.48 },
      { time: '15:00', usage: 2.8, cost: 0.42 },
      { time: '18:00', usage: 4.1, cost: 0.62 },
      { time: '21:00', usage: 3.5, cost: 0.53 }
    ],
    week: [
      { time: 'Mon', usage: 28.5, cost: 4.28 },
      { time: 'Tue', usage: 32.1, cost: 4.82 },
      { time: 'Wed', usage: 29.8, cost: 4.47 },
      { time: 'Thu', usage: 35.2, cost: 5.28 },
      { time: 'Fri', usage: 31.7, cost: 4.76 },
      { time: 'Sat', usage: 26.3, cost: 3.95 },
      { time: 'Sun', usage: 24.9, cost: 3.74 }
    ],
    month: [
      { time: 'Week 1', usage: 185, cost: 27.75 },
      { time: 'Week 2', usage: 198, cost: 29.70 },
      { time: 'Week 3', usage: 172, cost: 25.80 },
      { time: 'Week 4', usage: 165, cost: 24.75 }
    ]
  };

  const currentUsageData = usageData[selectedPeriod];
  const maxUsage = Math.max(...currentUsageData.map(d => d.usage));

  const getTimeOfDayIcon = () => {
    const hour = currentTime.getHours();
    if (hour >= 6 && hour < 18) {
      return <Sun className="h-4 w-4 text-yellow-500" />;
    }
    return <Moon className="h-4 w-4 text-blue-400" />;
  };

  const getUsageStatus = (usage) => {
    if (usage < 2) return { status: 'Low', color: 'text-accent-green', bg: 'bg-accent-green/10' };
    if (usage < 4) return { status: 'Normal', color: 'text-primary-turquoise', bg: 'bg-primary-turquoise/10' };
    return { status: 'High', color: 'text-accent-red', bg: 'bg-accent-red/10' };
  };

  const currentUsageStatus = getUsageStatus(powerData.currentUsage || 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-3 border-primary-turquoise border-t-transparent rounded-full"
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
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-secondary-darkgray via-secondary-darkgray/95 to-secondary-darkgray border border-primary-turquoise/30 shadow-2xl">
          {/* Animated background pattern */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute inset-0 bg-gradient-to-r from-primary-turquoise/30 via-transparent to-accent-green/30 animate-shimmer"></div>
            <svg className="w-full h-full" viewBox="0 0 100 20" preserveAspectRatio="none">
              <defs>
                <pattern id="power-grid" width="10" height="10" patternUnits="userSpaceOnUse">
                  <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-primary-turquoise/40"/>
                </pattern>
              </defs>
              <rect width="100" height="20" fill="url(#power-grid)" />
            </svg>
          </div>

          <div className="relative z-10 p-2 lg:p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center space-x-4 mb-6 lg:mb-0">
                <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-2xl bg-gradient-to-br from-primary-turquoise to-accent-lightturquoise flex items-center justify-center shadow-lg shadow-primary-turquoise/30">
                  <Zap className="h-8 w-8 lg:h-10 lg:w-10 text-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-2xl lg:text-4xl font-bold text-white">
                      SpotOn Power
                    </h1>
                    <div className="px-3 py-1 rounded-full bg-primary-turquoise/20 border border-primary-turquoise/40">
                      <span className="text-primary-turquoise text-sm font-semibold">Active</span>
                    </div>
                  </div>
                  <p className="text-accent-lightturquoise text-sm lg:text-base mb-1">
                    Monitor & manage electricity consumption
                  </p>
                  <p className="text-accent-lightturquoise/80 text-xs lg:text-sm">
                    Real-time usage tracking and insights
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4 text-accent-lightturquoise">
                {getTimeOfDayIcon()}
                <div className="text-right">
                  <div className="text-xs opacity-80">Last updated</div>
                  <div className="text-sm font-semibold">{currentTime.toLocaleTimeString()}</div>
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
          title="Current Usage"
          icon={Gauge}
          value={`${powerData.currentUsage || 0} kWh`}
          subtitle="Right now"
          color="primary-turquoise"
          className="hover:shadow-xl hover:shadow-primary-turquoise/20 transition-all duration-300"
        >
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${currentUsageStatus.bg} ${currentUsageStatus.color} border border-current/20`}>
            <Activity className="h-3 w-3 mr-1" />
            {currentUsageStatus.status}
          </div>
        </ServiceCard>

        <ServiceCard
          title="Monthly Usage"
          icon={BarChart3}
          value={`${powerData.monthlyUsage || 0} kWh`}
          subtitle="This month"
          trend="down"
          trendValue="12% below average"
          color="accent-green"
          className="hover:shadow-xl hover:shadow-accent-green/20 transition-all duration-300"
        />

        <ServiceCard
          title="Estimated Bill"
          icon={DollarSign}
          value={`$${powerData.costEstimate || 0}`}
          subtitle="This month"
          color="accent-red"
          className="hover:shadow-xl hover:shadow-accent-red/20 transition-all duration-300"
        />

        <ServiceCard
          title="Current Plan"
          icon={Settings}
          value={powerData.plan || 'Standard'}
          subtitle="Rate plan"
          color="accent-purple"
          className="hover:shadow-xl hover:shadow-accent-purple/20 transition-all duration-300"
        />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-2">
        {/* Main Usage Chart */}
        <div className="lg:col-span-3 space-y-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
                <h2 className="text-xl font-bold text-secondary-darkgray flex items-center mb-4 sm:mb-0">
                  <Activity className="h-4 w-4 mr-3 text-primary-turquoise" />
                  Usage Pattern & Cost Analysis
                </h2>
                
                <div className="flex bg-gray-100 rounded-xl p-1 shadow-inner">
                  {['day', 'week', 'month'].map((period) => (
                    <button
                      key={period}
                      onClick={() => setSelectedPeriod(period)}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 capitalize ${
                        selectedPeriod === period
                          ? 'bg-primary-turquoise text-white shadow-lg shadow-primary-turquoise/30'
                          : 'text-gray-600 hover:text-secondary-darkgray hover:bg-white/50'
                      }`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Bar Chart */}
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
                        <span className="text-primary-turquoise font-semibold">{item.usage} kWh</span>
                        <span className="text-accent-green font-semibold">${item.cost.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="relative">
                      <div className="h-10 bg-gray-100 rounded-xl overflow-hidden shadow-inner">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(item.usage / maxUsage) * 100}%` }}
                          transition={{ duration: 1, delay: 0.2 + (0.1 * index) }}
                          className="h-full bg-gradient-to-r from-primary-turquoise via-primary-turquoise/90 to-accent-lightturquoise rounded-xl shadow-sm group-hover:shadow-md transition-shadow duration-300"
                        />
                      </div>
                      <div className="absolute inset-0 flex items-center px-4">
                        <span className="text-xs font-semibold text-white drop-shadow-sm">
                          {item.usage} kWh • ${item.cost.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
                  <div className="p-4 rounded-xl bg-primary-turquoise/5 border border-primary-turquoise/20">
                    <div className="text-2xl lg:text-3xl font-bold text-primary-turquoise">
                      {currentUsageData.reduce((sum, item) => sum + item.usage, 0).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Total kWh</div>
                  </div>
                  <div className="p-4 rounded-xl bg-accent-green/5 border border-accent-green/20">
                    <div className="text-2xl lg:text-3xl font-bold text-accent-green">
                      ${currentUsageData.reduce((sum, item) => sum + item.cost, 0).toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Total Cost</div>
                  </div>
                  <div className="p-4 rounded-xl bg-accent-blue/5 border border-accent-blue/20">
                    <div className="text-2xl lg:text-3xl font-bold text-accent-blue">
                      {(currentUsageData.reduce((sum, item) => sum + item.usage, 0) / currentUsageData.length).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Average kWh</div>
                  </div>
                  <div className="p-4 rounded-xl bg-accent-purple/5 border border-accent-purple/20">
                    <div className="text-2xl lg:text-3xl font-bold text-accent-purple">
                      {Math.max(...currentUsageData.map(d => d.usage)).toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Peak kWh</div>
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Energy Insights */}
          {isFeatureEnabled('power', 'insights') && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
            >
              <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-secondary-darkgray flex items-center">
                    <Lightbulb className="h-4 w-4 mr-3 text-primary-turquoise" />
                    Energy Insights & Recommendations
                  </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                    className="p-5 rounded-xl bg-gradient-to-r from-accent-green/10 to-accent-green/5 border border-accent-green/30 shadow-sm hover:shadow-md transition-all duration-300"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="p-2 rounded-lg bg-accent-green/20">
                        <TrendingDown className="h-4 w-4 text-accent-green" />
                      </div>
                      <div>
                        <div className="font-bold text-accent-green text-lg">Great Progress!</div>
                        <div className="text-sm text-gray-600 mt-2">
                          You&apos;ve reduced your energy consumption by 12% compared to last month. 
                          Keep up the excellent work!
                        </div>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="p-5 rounded-xl bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 border border-primary-turquoise/30 shadow-sm hover:shadow-md transition-all duration-300"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="p-2 rounded-lg bg-primary-turquoise/20">
                        <Clock className="h-4 w-4 text-primary-turquoise" />
                      </div>
                      <div>
                        <div className="font-bold text-primary-turquoise text-lg">Peak Usage Time</div>
                        <div className="text-sm text-gray-600 mt-2">
                          Your highest energy usage typically occurs between 6-9 PM. 
                          Consider shifting some activities to off-peak hours.
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </DashboardCard>
            </motion.div>
          )}
        </div>

        {/* Compact Sidebar */}
        <div className="space-y-3">
          {/* Bill Summary & Quick Actions Combined */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-secondary-darkgray flex items-center">
                  <DollarSign className="h-4 w-4 mr-3 text-accent-red" />
                  Bill Summary
                </h2>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-accent-red/5 border border-accent-red/20">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-accent-red mb-1">${powerData.costEstimate || 89.50}</div>
                    <div className="text-sm text-gray-600 mb-2">Estimated This Month</div>
                    <div className="text-xs text-accent-green font-medium">$12.30 saved vs last month</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="p-3 rounded bg-gray-50/50">
                    <div className="text-lg font-bold text-secondary-darkgray">{powerData.currentUsage || 2.4}</div>
                    <div className="text-xs text-gray-500">Current kWh</div>
                  </div>
                  <div className="p-3 rounded bg-gray-50/50">
                    <div className="text-lg font-bold text-secondary-darkgray">{powerData.plan || 'Standard'}</div>
                    <div className="text-xs text-gray-500">Rate Plan</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full p-3 bg-accent-red text-white rounded-lg hover:bg-accent-red/90 transition-all duration-300 font-medium text-sm"
                  >
                    Pay Bill Now
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full p-3 bg-primary-turquoise/10 text-primary-turquoise rounded-lg hover:bg-primary-turquoise/20 transition-all duration-300 font-medium text-sm"
                  >
                    View Detailed Report
                  </motion.button>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Account & Status Combined */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-secondary-darkgray flex items-center">
                  <Home className="h-4 w-4 mr-3 text-primary-turquoise" />
                  Account Status
                </h2>
              </div>

              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-green">All systems normal</span>
                  </div>
                  <div className="text-xs text-gray-600">No issues detected with your power service</div>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                    <span className="text-sm text-gray-600 font-medium">Account Holder</span>
                    <span className="text-sm font-semibold text-secondary-darkgray">
                      {getUserDisplayName()}
                    </span>
                  </div>

                  <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                    <span className="text-sm text-gray-600 font-medium">Next Reading</span>
                    <span className="text-sm font-semibold text-secondary-darkgray">
                      {new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                    <span className="text-sm text-gray-600 font-medium">Rate Plan</span>
                    <span className="text-sm font-semibold text-secondary-darkgray">
                      {powerData.plan || 'Standard Variable'}
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary-turquoise mb-1">13</div>
                    <div className="text-xs text-gray-500">Days until next bill</div>
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