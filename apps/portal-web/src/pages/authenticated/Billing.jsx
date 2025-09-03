import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  CreditCard, DollarSign, Download, Receipt, 
  AlertCircle, CheckCircle, Clock, FileText,
  TrendingUp, Wallet, Calendar as CalendarIcon
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";
import PageHeader from "../../components/dashboard/shared/PageHeader";

export default function BillingPage() {
  const { 
    user, 
    dashboardData, 
    loading, 
    getUserDisplayName 
  } = useDashboard();

  const [selectedPeriod, setSelectedPeriod] = useState('6months');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  // Mock billing data
  const billingData = {
    currentBalance: 0,
    nextBillAmount: 156.47,
    nextBillDate: '2025-06-15',
    paymentMethod: 'Auto Pay - **** 4532',
    billingCycle: '15th of each month',
    accountCredit: 25.00,
    ...dashboardData.billing
  };

  // Mock billing history
  const billingHistory = {
    '6months': [
      { month: 'May 2025', amount: 142.35, status: 'paid', date: '2025-05-15', services: ['Power: $89.20', 'Broadband: $53.15'] },
      { month: 'Apr 2025', amount: 158.90, status: 'paid', date: '2025-04-15', services: ['Power: $95.75', 'Broadband: $53.15', 'Mobile: $10.00'] },
      { month: 'Mar 2025', amount: 145.67, status: 'paid', date: '2025-03-15', services: ['Power: $92.52', 'Broadband: $53.15'] },
      { month: 'Feb 2025', amount: 167.23, status: 'paid', date: '2025-02-15', services: ['Power: $104.08', 'Broadband: $53.15', 'Mobile: $10.00'] },
      { month: 'Jan 2025', amount: 139.45, status: 'paid', date: '2025-01-15', services: ['Power: $86.30', 'Broadband: $53.15'] },
      { month: 'Dec 2024', amount: 152.80, status: 'paid', date: '2024-12-15', services: ['Power: $89.65', 'Broadband: $53.15', 'Mobile: $10.00'] }
    ],
    '12months': [
      { month: 'May 2025', amount: 142.35, status: 'paid', date: '2025-05-15' },
      { month: 'Apr 2025', amount: 158.90, status: 'paid', date: '2025-04-15' },
      { month: 'Mar 2025', amount: 145.67, status: 'paid', date: '2025-03-15' },
      { month: 'Feb 2025', amount: 167.23, status: 'paid', date: '2025-02-15' },
      { month: 'Jan 2025', amount: 139.45, status: 'paid', date: '2025-01-15' },
      { month: 'Dec 2024', amount: 152.80, status: 'paid', date: '2024-12-15' },
      { month: 'Nov 2024', amount: 148.92, status: 'paid', date: '2024-11-15' },
      { month: 'Oct 2024', amount: 156.78, status: 'paid', date: '2024-10-15' },
      { month: 'Sep 2024', amount: 143.21, status: 'paid', date: '2024-09-15' },
      { month: 'Aug 2024', amount: 159.34, status: 'paid', date: '2024-08-15' },
      { month: 'Jul 2024', amount: 147.89, status: 'paid', date: '2024-07-15' },
      { month: 'Jun 2024', amount: 151.45, status: 'paid', date: '2024-06-15' }
    ]
  };

  const currentHistory = billingHistory[selectedPeriod];
  const maxAmount = Math.max(...currentHistory.map(bill => bill.amount));
  const avgAmount = currentHistory.reduce((sum, bill) => sum + bill.amount, 0) / currentHistory.length;

  const getStatusColor = (status) => {
    switch (status) {
      case 'paid': return { bg: 'bg-accent-green/10', text: 'text-accent-green', icon: CheckCircle };
      case 'pending': return { bg: 'bg-yellow-50', text: 'text-yellow-600', icon: Clock };
      case 'overdue': return { bg: 'bg-accent-red/10', text: 'text-accent-red', icon: AlertCircle };
      default: return { bg: 'bg-gray-50', text: 'text-gray-600', icon: Clock };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-primary-turquoise border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <PageHeader
        title="Billing & Payments"
        subtitle="Manage bills & account balance"
        description="Track your spending and payment history"
        icon={CreditCard}
        statusText="Up to date"
        statusColor="accent-green"
        theme="billing"
        rightContent={
          <>
            <Clock className="h-4 w-4 text-accent-green" />
            <div className="text-right">
              <div className="text-xs opacity-80">Last updated</div>
              <div className="text-sm font-semibold">{currentTime.toLocaleTimeString()}</div>
            </div>
          </>
        }
      />

      {/* Account Status - moved to top */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
      >
        <DashboardCard compact className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-secondary-darkgray flex items-center">
              <Wallet className="h-4 w-4 mr-2 text-primary-turquoise" />
              Account Status
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-accent-green/5 border border-accent-green/20 text-center">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <div className="h-2 w-2 bg-accent-green rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold text-accent-green">Payment up to date</span>
              </div>
              <div className="text-2xl font-bold text-accent-green">$0.00</div>
              <div className="text-xs text-gray-500">Current Balance</div>
            </div>

            <div className="p-4 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20 text-center">
              <CalendarIcon className="h-6 w-6 text-primary-turquoise mx-auto mb-2" />
              <div className="text-xl font-bold text-primary-turquoise">
                {new Date(billingData.nextBillDate).toLocaleDateString()}
              </div>
              <div className="text-xs text-gray-500">Next Bill Due</div>
            </div>

            <div className="p-4 rounded-lg bg-accent-purple/5 border border-accent-purple/20 text-center">
              <DollarSign className="h-6 w-6 text-accent-purple mx-auto mb-2" />
              <div className="text-xl font-bold text-accent-purple">
                ${billingData.accountCredit.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">Account Credit</div>
            </div>
          </div>
        </DashboardCard>
      </motion.div>

      {/* Redundant billing tiles removed as requested */}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-2">
        {/* Main Content */}
        <div className="lg:col-span-3 space-y-3">
          {/* Billing History */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard compact>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
                <h2 className="text-xl font-semibold text-secondary-darkgray flex items-center mb-4 sm:mb-0">
                  <FileText className="h-4 w-4 mr-3 text-accent-red" />
                  Billing History & Analysis
                </h2>
                
                <div className="flex bg-gray-100 rounded-lg p-1">
                  {['6months', '12months'].map((period) => (
                    <button
                      key={period}
                      onClick={() => setSelectedPeriod(period)}
                      className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-300 ${
                        selectedPeriod === period
                          ? 'bg-accent-red text-white shadow-sm'
                          : 'text-gray-600 hover:text-secondary-darkgray'
                      }`}
                    >
                      {period === '6months' ? '6 Months' : '12 Months'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                {currentHistory.slice(0, 4).map((bill, index) => {
                  const statusConfig = getStatusColor(bill.status);
                  const StatusIcon = statusConfig.icon;
                  
                  return (
                    <motion.div
                      key={bill.month}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: 0.1 * index }}
                      className="p-4 rounded-lg border border-gray-200 hover:border-accent-red/30 transition-all duration-300 hover:shadow-sm"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${statusConfig.bg}`}>
                            <StatusIcon className={`h-4 w-4 ${statusConfig.text}`} />
                          </div>
                          <div>
                            <div className="font-medium text-secondary-darkgray">{bill.month}</div>
                            <div className="text-sm text-gray-500">
                              Due: {new Date(bill.date).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-lg font-bold text-secondary-darkgray">
                            ${bill.amount.toFixed(2)}
                          </div>
                          <div className={`text-xs font-medium capitalize ${statusConfig.text}`}>
                            {bill.status}
                          </div>
                        </div>
                      </div>

                      {bill.services && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <div className="text-xs text-gray-500 mb-2">Service breakdown:</div>
                          <div className="flex flex-wrap gap-2">
                            {bill.services.map((service, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded-md"
                              >
                                {typeof service === 'string'
                                  ? service
                                  : service && typeof service === 'object'
                                    ? service.name || JSON.stringify(service)
                                    : String(service)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-3 flex justify-end">
                        <button className="text-accent-red hover:text-accent-red/80 text-sm font-medium flex items-center space-x-1">
                          <Download className="h-4 w-4" />
                          <span>Download</span>
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {currentHistory.length > 4 && (
                <div className="mt-4 text-center">
                  <button className="text-accent-red hover:text-accent-red/80 text-sm font-medium">
                    View {currentHistory.length - 4} more bills
                  </button>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-center">
                  <div className="p-4 rounded-lg bg-accent-red/5 border border-accent-red/20">
                    <div className="text-2xl font-bold text-accent-red">
                      ${currentHistory.reduce((sum, bill) => sum + bill.amount, 0).toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">Total Paid</div>
                  </div>
                  <div className="p-4 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20">
                    <div className="text-2xl font-bold text-primary-turquoise">
                      ${avgAmount.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">Average Bill</div>
                  </div>
                  <div className="p-4 rounded-lg bg-accent-purple/5 border border-accent-purple/20">
                    <div className="text-2xl font-bold text-accent-purple">
                      ${maxAmount.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">Highest Bill</div>
                  </div>
                  {/* Saved vs Peak removed */}
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Payment Method */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard compact>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-secondary-darkgray flex items-center">
                  <CreditCard className="h-4 w-4 mr-2 text-accent-red" />
                  Payment Method
                </h2>
              </div>

              <div className="p-4 rounded-lg bg-gradient-to-r from-accent-red/10 to-accent-red/5 border border-accent-red/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-accent-red/20">
                      <CreditCard className="h-4 w-4 text-accent-red" />
                    </div>
                    <div>
                      <div className="font-medium text-secondary-darkgray">Auto Pay Enabled</div>
                      <div className="text-sm text-gray-600">{billingData.paymentMethod}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm text-accent-green font-medium">Active</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Billing Cycle:</span>
                    <span className="font-medium text-secondary-darkgray">{billingData.billingCycle}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Next Payment:</span>
                    <span className="font-medium text-secondary-darkgray">
                      {new Date(billingData.nextBillDate).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Compact Sidebar */}
        <div className="space-y-3">
          {/* Billing Schedule */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard compact>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-secondary-darkgray flex items-center">
                  <CalendarIcon className="h-4 w-4 mr-2 text-accent-red" />
                  Billing Schedule
                </h2>
              </div>

              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-accent-red/5 border border-accent-red/20">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Billing Cycle</span>
                    <span className="text-sm font-bold text-accent-red">{billingData.billingCycle}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Next Bill Date</span>
                    <span className="text-sm font-bold text-primary-turquoise">
                      {new Date(billingData.nextBillDate).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Auto Pay</span>
                    <span className="text-sm font-bold text-accent-green">Enabled</span>
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Account Summary - Compact */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard compact>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-secondary-darkgray flex items-center">
                  <Wallet className="h-4 w-4 mr-2 text-primary-turquoise" />
                  Account Summary
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
                  <span className="text-sm text-gray-600">Account Number</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    ****{user?.id?.toString().slice(-4) || '1234'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Payment Method</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    Auto Pay
                  </span>
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <div className="text-center">
                    <div className="text-xl font-bold text-primary-turquoise mb-1">
                      {Math.ceil((new Date(billingData.nextBillDate) - new Date()) / (1000 * 60 * 60 * 24))}
                    </div>
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