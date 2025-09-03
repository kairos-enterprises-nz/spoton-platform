import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { 
  Zap, Wifi, Smartphone, Bell, Settings,
  Activity, CheckCircle, DollarSign, Home,
  CreditCard, HelpCircle, AlertTriangle, Phone, Mail, TrendingUp,
  Calendar, Target, Award, BarChart3
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";

export default function DashboardContentPage() {
  const { 
    dashboardData, 
    loading, 
    isComponentVisible,
    getUserDisplayName,
    getUserInitials
  } = useDashboard();

  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [notifications, setNotifications] = useState([
    { id: 1, type: 'info', message: 'Your power usage is 12% below average this month', time: '2 hours ago' },
    { id: 2, type: 'success', message: 'Internet speed test completed - 95.2 Mbps', time: '1 day ago' },
    { id: 3, type: 'warning', message: 'Bill due in 5 days - $127.50', time: '2 days ago' }
  ]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success': return CheckCircle;
      case 'warning': return AlertTriangle;
      default: return Bell;
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success': return 'text-accent-green bg-accent-green/10 border-accent-green/20';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-primary-turquoise bg-primary-turquoise/10 border-primary-turquoise/20';
    }
  };

  // Calculate key metrics - ensure all values are properly converted
  const totalMonthlyBill = 127.50;
  const savingsThisMonth = 18.75;
  const totalServices = 3; // Fixed value instead of potentially undefined userServices?.length
  const upcomingPayments = 1;

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
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-secondary-darkgray via-secondary-darkgray/95 to-secondary-darkgray border border-primary-turquoise/30 shadow-xl">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute inset-0 bg-gradient-to-r from-primary-turquoise/30 via-transparent to-accent-purple/30 animate-shimmer"></div>
          </div>

          <div className="relative z-10 p-2">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center space-x-4 mb-4 lg:mb-0">
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-turquoise to-accent-lightturquoise flex items-center justify-center text-white font-bold text-xl shadow-lg">
                  {getUserInitials()}
                </div>
                <div>
                  <h1 className="text-2xl lg:text-3xl font-bold text-white">
                    {getGreeting()}, {getUserDisplayName()}!
                  </h1>
                  <p className="text-accent-lightturquoise text-base">
                    Here&apos;s your account overview
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-6 text-accent-lightturquoise">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">${totalMonthlyBill.toFixed(2)}</div>
                  <div className="text-xs opacity-80">Monthly Bill</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-accent-green">${savingsThisMonth.toFixed(2)}</div>
                  <div className="text-xs opacity-80">Saved This Month</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Key Metrics Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-2"
      >
        <ServiceCard
          title="Total Services"
          icon={Home}
          value={totalServices.toString()}
          subtitle="Active services"
          color="primary-turquoise"
          className="hover:shadow-lg hover:shadow-primary-turquoise/20 transition-all duration-300"
        />

        <ServiceCard
          title="This Month"
          icon={DollarSign}
          value={`$${totalMonthlyBill.toFixed(2)}`}
          subtitle="Estimated bill"
          color="accent-red"
          className="hover:shadow-lg hover:shadow-accent-red/20 transition-all duration-300"
        />

        <ServiceCard
          title="Savings"
          icon={TrendingUp}
          value={`$${savingsThisMonth.toFixed(2)}`}
          subtitle="vs last month"
          trend="down"
          trendValue="12% reduction"
          color="accent-green"
          className="hover:shadow-lg hover:shadow-accent-green/20 transition-all duration-300"
        />

        <ServiceCard
          title="Due Soon"
          icon={Calendar}
          value={upcomingPayments.toString()}
          subtitle="Payment due"
          color="accent-purple"
          className="hover:shadow-lg hover:shadow-accent-purple/20 transition-all duration-300"
        />
      </motion.div>

      {/* Service Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-2"
      >
        {isComponentVisible('power') && (
          <ServiceCard
            title="Power"
            icon={Zap}
            value={`${(dashboardData.power?.currentUsage || 2.4).toFixed(1)} kWh`}
            subtitle="Current usage"
            trend="down"
            trendValue="12% below avg"
            color="primary-turquoise"
            href="/authenticated/power"
            className="hover:shadow-lg hover:shadow-primary-turquoise/20 transition-all duration-300"
          >
            <div className="mt-2 text-xs text-gray-500">
              Monthly: ${(dashboardData.power?.costEstimate || 89.50).toFixed(2)}
            </div>
          </ServiceCard>
        )}

        {isComponentVisible('broadband') && (
          <ServiceCard
            title="Broadband"
            icon={Wifi}
            value={`${(dashboardData.broadband?.speed || 95.2).toFixed(1)} Mbps`}
            subtitle="Download speed"
            color="accent-purple"
            href="/authenticated/broadband"
            className="hover:shadow-lg hover:shadow-accent-purple/20 transition-all duration-300"
          >
            <div className="mt-2 text-xs text-gray-500">
              Monthly: $53.15 • {dashboardData.broadband?.connectedDevices || 12} devices
            </div>
          </ServiceCard>
        )}

        {isComponentVisible('mobile') && (
          <ServiceCard
            title="Mobile"
            icon={Smartphone}
            value={`${(dashboardData.mobile?.dataUsed || 8.2).toFixed(1)} GB`}
            subtitle="Data used this month"
            color="accent-blue"
            href="/authenticated/mobile"
            className="hover:shadow-lg hover:shadow-accent-blue/20 transition-all duration-300"
          >
            <div className="mt-2 text-xs text-gray-500">
              {Math.round(((dashboardData.mobile?.dataUsed || 8.2) / 20) * 100)}% of allowance used
            </div>
          </ServiceCard>
        )}
      </motion.div>

      {/* Main Dashboard Grid - Better balanced layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-2">
        {/* Main Content - Takes 3 columns */}
        <div className="lg:col-span-3 space-y-3">
          {/* Recent Activity & Quick Actions Combined */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-secondary-darkgray flex items-center">
                  <Activity className="h-4 w-4 mr-3 text-primary-turquoise" />
                  Recent Activity
                </h2>
                <button className="text-primary-turquoise hover:text-primary-turquoise/80 text-sm font-medium">
                  View All
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-4 p-4 rounded-lg bg-gray-50/50 hover:bg-gray-100/50 transition-colors duration-200">
                  <div className="w-10 h-10 rounded-full bg-accent-green/20 flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-accent-green" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-secondary-darkgray">Payment processed successfully</div>
                    <div className="text-sm text-gray-500">Power bill - $89.50 • 2 hours ago</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-accent-green">-$89.50</div>
                  </div>
                </div>

                <div className="flex items-center space-x-4 p-4 rounded-lg bg-gray-50/50 hover:bg-gray-100/50 transition-colors duration-200">
                  <div className="w-10 h-10 rounded-full bg-primary-turquoise/20 flex items-center justify-center">
                    <Wifi className="h-4 w-4 text-primary-turquoise" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-secondary-darkgray">Speed test completed</div>
                    <div className="text-sm text-gray-500">Download: 95.2 Mbps • 1 day ago</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-primary-turquoise">95.2 Mbps</div>
                  </div>
                </div>

                <div className="flex items-center space-x-4 p-4 rounded-lg bg-gray-50/50 hover:bg-gray-100/50 transition-colors duration-200">
                  <div className="w-10 h-10 rounded-full bg-accent-blue/20 flex items-center justify-center">
                    <Smartphone className="h-4 w-4 text-accent-blue" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-secondary-darkgray">Data usage alert</div>
                    <div className="text-sm text-gray-500">80% of monthly allowance used • 2 days ago</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-accent-blue">16 GB</div>
                  </div>
                </div>
              </div>

              {/* Quick Actions Row */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-lg font-semibold text-secondary-darkgray mb-4">Quick Actions</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/authenticated/billing')}
                    className="group p-4 rounded-lg bg-gradient-to-r from-accent-red/10 to-accent-red/5 hover:from-accent-red/20 hover:to-accent-red/10 border border-accent-red/30 transition-all duration-300 text-center"
                  >
                    <DollarSign className="h-4 w-4 text-accent-red mx-auto mb-2" />
                    <div className="text-sm font-semibold text-secondary-darkgray">Pay Bill</div>
                    <div className="text-xs text-gray-500">$127.50 due</div>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/authenticated/power')}
                    className="group p-4 rounded-lg bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 hover:from-primary-turquoise/20 hover:to-primary-turquoise/10 border border-primary-turquoise/30 transition-all duration-300 text-center"
                  >
                    <BarChart3 className="h-4 w-4 text-primary-turquoise mx-auto mb-2" />
                    <div className="text-sm font-semibold text-secondary-darkgray">Usage Report</div>
                    <div className="text-xs text-gray-500">View details</div>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/authenticated/support')}
                    className="group p-4 rounded-lg bg-gradient-to-r from-accent-green/10 to-accent-green/5 hover:from-accent-green/20 hover:to-accent-green/10 border border-accent-green/30 transition-all duration-300 text-center"
                  >
                    <HelpCircle className="h-4 w-4 text-accent-green mx-auto mb-2" />
                    <div className="text-sm font-semibold text-secondary-darkgray">Get Help</div>
                    <div className="text-xs text-gray-500">Support center</div>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/authenticated/settings')}
                    className="group p-4 rounded-lg bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 hover:from-accent-blue/20 hover:to-accent-blue/10 border border-accent-blue/30 transition-all duration-300 text-center"
                  >
                    <Settings className="h-4 w-4 text-accent-blue mx-auto mb-2" />
                    <div className="text-sm font-semibold text-secondary-darkgray">Settings</div>
                    <div className="text-xs text-gray-500">Manage account</div>
                  </motion.button>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Monthly Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-secondary-darkgray flex items-center">
                  <Target className="h-4 w-4 mr-3 text-primary-turquoise" />
                  This Month&apos;s Summary
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20">
                  <div className="text-3xl font-bold text-primary-turquoise mb-2">$127.50</div>
                  <div className="text-sm text-gray-600 mb-1">Total Bill</div>
                  <div className="text-xs text-accent-green font-medium">$18.75 saved</div>
                </div>

                <div className="text-center p-4 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="text-3xl font-bold text-accent-green mb-2">88%</div>
                  <div className="text-sm text-gray-600 mb-1">Efficiency Score</div>
                  <div className="text-xs text-accent-green font-medium">+5% improvement</div>
                </div>

                <div className="text-center p-4 rounded-lg bg-accent-blue/5 border border-accent-blue/20">
                  <div className="text-3xl font-bold text-accent-blue mb-2">3</div>
                  <div className="text-sm text-gray-600 mb-1">Active Services</div>
                  <div className="text-xs text-gray-500">All operational</div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar - Takes 2 columns, more compact */}
        <div className="lg:col-span-2 space-y-3">
          {/* Payment Information - Consolidated */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <CreditCard className="h-4 w-4 mr-2 text-accent-red" />
                  Payment Overview
                </h2>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-accent-red/5 border border-accent-red/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-secondary-darkgray">Next Bill Due</span>
                    <span className="text-sm font-bold text-accent-red">5 days</span>
                  </div>
                  <div className="text-2xl font-bold text-accent-red mb-1">$127.50</div>
                  <div className="text-xs text-gray-500">Auto Pay enabled</div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 rounded bg-gray-50/50">
                    <div className="text-lg font-bold text-secondary-darkgray">$89.50</div>
                    <div className="text-xs text-gray-500">Power</div>
                  </div>
                  <div className="text-center p-3 rounded bg-gray-50/50">
                    <div className="text-lg font-bold text-secondary-darkgray">$38.00</div>
                    <div className="text-xs text-gray-500">Broadband</div>
                  </div>
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => navigate('/authenticated/billing')}
                  className="w-full p-3 bg-accent-red text-white rounded-lg hover:bg-accent-red/90 transition-all duration-300 font-medium text-sm"
                >
                  Pay Now
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Notifications - Compact */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Bell className="h-4 w-4 mr-2 text-primary-turquoise" />
                  Alerts
                </h2>
                {notifications.length > 0 && (
                  <span className="px-2 py-1 bg-primary-turquoise/10 text-primary-turquoise text-xs font-semibold rounded-full">
                    {notifications.length}
                  </span>
                )}
              </div>

              <div className="space-y-3">
                <AnimatePresence>
                  {notifications.length > 0 ? (
                    notifications.slice(0, 2).map((notification) => {
                      const Icon = getNotificationIcon(notification.type);
                      return (
                        <motion.div
                          key={notification.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 20 }}
                          transition={{ duration: 0.3 }}
                          className={`p-3 rounded-lg border ${getNotificationColor(notification.type)}`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-3">
                              <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                              <div className="flex-1">
                                <div className="text-sm font-medium text-secondary-darkgray">
                                  {notification.message}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                  {notification.time}
                                </div>
                              </div>
                            </div>
                            <button
                              onClick={() => dismissNotification(notification.id)}
                              className="text-gray-400 hover:text-gray-600 ml-2"
                            >
                              ×
                            </button>
                          </div>
                        </motion.div>
                      );
                    })
                  ) : (
                    <div className="text-center py-4 text-gray-500">
                      <Bell className="h-4 w-4 mx-auto mb-2 opacity-50" />
                      <div className="text-sm">All caught up!</div>
                    </div>
                  )}
                </AnimatePresence>
                {notifications.length > 2 && (
                  <button className="w-full text-center text-primary-turquoise text-sm font-medium py-2">
                    View {notifications.length - 2} more
                  </button>
                )}
              </div>
            </DashboardCard>
          </motion.div>

          {/* Support & Account - Combined */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Award className="h-4 w-4 mr-2 text-accent-green" />
                  Account Status
                </h2>
              </div>

              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-green">All systems operational</span>
                  </div>
                  <div className="text-xs text-gray-600">Account in good standing</div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="p-3 rounded bg-gray-50/50">
                    <div className="text-lg font-bold text-secondary-darkgray">{getUserDisplayName()}</div>
                    <div className="text-xs text-gray-500">Account Holder</div>
                  </div>
                  <div className="p-3 rounded bg-gray-50/50">
                    <div className="text-lg font-bold text-secondary-darkgray">2024</div>
                    <div className="text-xs text-gray-500">Member Since</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/authenticated/support')}
                    className="flex items-center justify-center space-x-2 p-3 rounded-lg bg-accent-green/10 hover:bg-accent-green/20 transition-all duration-300"
                  >
                    <Phone className="h-4 w-4 text-accent-green" />
                    <span className="text-sm font-medium text-accent-green">Call</span>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigate('/authenticated/support')}
                    className="flex items-center justify-center space-x-2 p-3 rounded-lg bg-accent-blue/10 hover:bg-accent-blue/20 transition-all duration-300"
                  >
                    <Mail className="h-4 w-4 text-accent-blue" />
                    <span className="text-sm font-medium text-accent-blue">Email</span>
                  </motion.button>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}