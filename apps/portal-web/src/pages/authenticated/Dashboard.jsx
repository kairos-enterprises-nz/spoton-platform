import { useNavigate } from "react-router-dom";
import { useDashboard } from "../../context/DashboardContext";
import { useAuth } from "../../hooks/useAuth";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";
import { Zap, Wifi, Smartphone, CreditCard, TrendingUp, Bell, Home } from 'lucide-react';

export default function DashboardContentPage() {
  const { 
    dashboardData, 
    portalData,
    userServices,
    loading
  } = useDashboard();
  const { user } = useAuth();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="w-12 h-12 border-3 border-primary-turquoise-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Get greeting based on time of day
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  // Calculate stats from data
  const totalMonthlyBill = portalData?.billing?.estimated_monthly_bill || 129.98;
  const activeServices = userServices?.length || 1;
  const upcomingPayments = totalMonthlyBill > 0 ? 1 : 0;
  const notifications = 3;

  return (
    <div className="space-y-6">
      {/* Welcome Card */}
      <DashboardCard 
        gradient={true}
        gradientFrom="from-primary-turquoise"
        gradientTo="to-primary-turquoise-600"
        className="text-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold mb-2">
              {getGreeting()}, {user?.first_name || 'Test'}!
            </h1>
            <p className="text-primary-turquoise-100">
              Here's what's happening with your SpotOn services
            </p>
          </div>
          <div className="hidden md:block">
            <Home className="h-16 w-16 text-primary-turquoise-200" />
          </div>
        </div>
      </DashboardCard>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ServiceCard
          title="Monthly Bill"
          icon={CreditCard}
          value={`$${totalMonthlyBill.toFixed(2)}`}
          subtitle="-12% vs last month"
          trend="down"
          trendValue="-12%"
          color="accent-green"
          onClick={() => navigate('/billing')}
        />
        
        <ServiceCard
          title="Active Services"
          icon={Bell}
          value={activeServices.toString()}
          subtitle="Connected services running"
          color="primary-turquoise"
        />
        
        <ServiceCard
          title="Due Soon"
          icon={Bell}
          value={upcomingPayments.toString()}
          subtitle="Payment due bills pending"
          color="accent-red"
          onClick={() => navigate('/billing')}
        />
        
        <ServiceCard
          title="Notifications"
          icon={Bell}
          value={notifications.toString()}
          subtitle="New updates unread items"
          color="accent-blue"
        />
      </div>

      {/* Services Overview */}
      <DashboardCard>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-secondary-darkgray">Your Services</h2>
          <button className="text-sm text-primary-turquoise hover:text-primary-turquoise-600 font-medium">
            Manage Services
          </button>
        </div>
        <p className="text-gray-600 mb-6">Monitor and manage your SpotOn services</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ServiceCard
            title="Power"
            icon={Zap}
            subtitle="Clean energy, transparent pricing"
            value="Inactive"
            color="accent-red"
            onClick={() => navigate('/power')}
          />
          
          <ServiceCard
            title="Broadband"
            icon={Wifi}
            subtitle="Ultra-fast fiber internet"
            value="Active"
            color="primary-turquoise"
            onClick={() => navigate('/broadband')}
            className="border-2 border-primary-turquoise"
          >
            <div className="text-sm font-medium text-secondary-darkgray">
              $79.99/month
            </div>
          </ServiceCard>
          
          <ServiceCard
            title="Mobile"
            icon={Smartphone}
            subtitle="Simple plans, no surprises"
            value="Coming Soon"
            color="accent-blue"
            onClick={() => navigate('/mobile')}
          />
        </div>
      </DashboardCard>

      {/* Recent Activity and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardCard>
          <h3 className="text-lg font-semibold text-secondary-darkgray mb-4">Recent Activity</h3>
          <p className="text-gray-600 mb-4">Latest updates on your services and account</p>
          
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <CreditCard className="h-5 w-5 text-accent-green" />
              <div>
                <p className="font-medium text-sm">Payment processed</p>
                <p className="text-xs text-gray-600">March power bill - $89.50</p>
              </div>
            </div>
          </div>
        </DashboardCard>

        <DashboardCard>
          <h3 className="text-lg font-semibold text-secondary-darkgray mb-4">Quick Actions</h3>
          <p className="text-gray-600 mb-4">Common tasks and shortcuts</p>
          
          <button 
            onClick={() => navigate('/billing')}
            className="w-full bg-accent-red text-white px-4 py-3 rounded-lg font-medium hover:bg-accent-red-600 transition-colors"
          >
            Pay Bill
          </button>
        </DashboardCard>
      </div>
    </div>
  );
}