import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Smartphone, Phone, MessageSquare, Wifi, Settings, 
  AlertTriangle, BarChart3, Signal, ChevronRight, Home
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";
import PageHeader from "../../components/dashboard/shared/PageHeader";
import ComingSoonCard from "../../components/dashboard/shared/ComingSoonCard";

export default function MobilePage() {
  const { 
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

  const mobileData = dashboardData.mobile || {};
  const hasMobileService = userServices?.includes('mobile');
  const mobilePlan = portalData?.services?.selected_plans?.mobile;

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

  // Show different content based on whether user has mobile service
  if (!hasMobileService) {
    return (
      <ComingSoonCard
        title="Mobile"
        subtitle="Quick eSIM setup, easy controls, and no price jump after month three"
        description="Service Coming Soon"
        theme="mobile"
        actionText="Get Notified"
        serviceType="mobile"
        onAction={() => {
          console.log('User wants mobile service notifications');
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <PageHeader
        title="Mobile"
        subtitle="Quick eSIM setup, easy controls, and no price jump after month three"
        icon={Smartphone}
        statusText={mobileData.statusText || 'Pending Activation'}
        statusColor={mobileData.status === 'active' ? 'accent-green' : 'accent-orange'}
        theme="mobile"
        rightContent={
          <>
            <Signal className="h-4 w-4 text-accent-blue" />
            <div className="text-left">
              <div className="text-xs opacity-80">Status</div>
              <div className="text-sm font-semibold">
                {mobileData.status === 'active' ? 'Connected' : 
                 mobileData.status === 'activating' ? 'Activating' :
                 mobileData.status === 'pending' ? 'Pending Activation' :
                 mobileData.statusText || 'Coming Soon'}
              </div>
            </div>
          </>
        }
      />

      {/* Essential Mobile Components Only - Connection Details, Plan Details, Network Status */}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-3">
          {/* Connection Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Smartphone className="h-4 w-4 mr-2 text-accent-blue" />
                  Connection Details
                </h2>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-lg bg-accent-blue/5 border border-accent-blue/20">
                  <span className="text-sm text-gray-600">Connection Status</span>
                  <span className="text-sm font-semibold text-accent-blue">Connected</span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Network Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">4G LTE</span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Signal Strength</span>
                  <span className="text-sm font-semibold text-accent-green">Excellent</span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Data Used This Month</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {(mobileData.dataUsed || 0).toFixed(1)} GB / {mobilePlan?.charges?.data_allowance || mobileData.dataAllowance || 'Unlimited'}
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Plan Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-2 text-accent-blue" />
                  Plan Details
                </h2>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-lg bg-accent-blue/5 border border-accent-blue/20">
                  <span className="text-sm text-gray-600">Current Plan</span>
                  <span className="text-sm font-semibold text-accent-blue">
                    {mobilePlan?.name || 'Mobile Plan'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Data Allowance</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobilePlan?.charges?.data_allowance || 'Unlimited'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Monthly Cost</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    ${mobilePlan?.charges?.monthly_charge || mobilePlan?.rate || 0}/month
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Plan Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobilePlan?.plan_type?.charAt(0).toUpperCase() + mobilePlan?.plan_type?.slice(1) || 'Postpaid'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                  <span className="text-sm text-gray-600">Contract Term</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {mobilePlan?.term || 'No Contract'}
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar - Network Status Only */}
        <div className="space-y-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Signal className="h-4 w-4 mr-2 text-accent-blue" />
                  Network Status
                </h2>
              </div>

              <div className="text-center space-y-4">
                <div className="p-4 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="text-2xl font-bold text-accent-green mb-1">4G</div>
                  <div className="text-sm text-gray-600">Network Type</div>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 rounded bg-gray-50">
                    <div className="text-lg font-bold text-secondary-darkgray">-65 dBm</div>
                    <div className="text-xs text-gray-500">Signal</div>
                  </div>
                  <div className="text-center p-3 rounded bg-gray-50">
                    <div className="text-lg font-bold text-secondary-darkgray">4/5</div>
                    <div className="text-xs text-gray-500">Bars</div>
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