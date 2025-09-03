import { useState } from "react";
import { motion } from "framer-motion";
import { 
  User, Shield, Bell, Globe, Save, Edit3, Eye, EyeOff, 
  Settings, Home, ChevronRight, Lock, Key, Calendar
} from "lucide-react";

import { useAuth } from "../../hooks/useAuth";
import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import PageHeader from "../../components/dashboard/shared/PageHeader";

export default function ProfilePage() {
  const { user } = useAuth();
  const { getUserDisplayName, portalData } = useDashboard();
  
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
    email: user?.email || '',
    phone: user?.mobile || user?.phone || '',
    address: portalData?.services?.service_address?.full_address || user?.address || '',
    city: portalData?.services?.service_address?.city || user?.city || '',
    postcode: portalData?.services?.service_address?.postal_code || user?.postcode || '',
    dateOfBirth: portalData?.personal_details?.dateOfBirth || user?.date_of_birth || '',
    language: user?.language || 'English',
    timezone: user?.timezone || 'Australia/Sydney',
    emailNotifications: user?.email_notifications ?? true,
    smsNotifications: user?.sms_notifications ?? false,
    marketingEmails: user?.marketing_emails ?? false,
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    // Handle save logic here
    console.log('Saving profile data:', formData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    // Reset form data
    setFormData({
      firstName: user?.first_name || '',
      lastName: user?.last_name || '',
      email: user?.email || '',
      phone: user?.phone || '',
      address: user?.address || '',
      city: user?.city || '',
      postcode: user?.postcode || '',
      dateOfBirth: user?.date_of_birth || '',
      language: user?.language || 'English',
      timezone: user?.timezone || 'Australia/Sydney',
      emailNotifications: user?.email_notifications ?? true,
      smsNotifications: user?.sms_notifications ?? false,
      marketingEmails: user?.marketing_emails ?? false,
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    setIsEditing(false);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <PageHeader
        title="Profile & Settings"
        subtitle="Manage your account information"
        description="Personal details and preferences"
        icon={User}
        statusText="Verified"
        statusColor="accent-green"
        theme="profile"
        rightContent={
          <>
            <Settings className="h-4 w-4 text-primary-turquoise" />
            <div className="text-right">
              <div className="text-xs opacity-80">Account Status</div>
              <div className="text-sm font-semibold">Verified</div>
            </div>
          </>
        }
      />

      {/* Account Summary - moved to top */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
      >
        <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
              <Home className="h-4 w-4 mr-2 text-primary-turquoise" />
              Account Summary
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-primary-turquoise/5 border border-primary-turquoise/20 text-center">
              <User className="h-8 w-8 text-primary-turquoise mx-auto mb-2" />
              <div className="text-lg font-bold text-primary-turquoise">
                {getUserDisplayName()}
              </div>
              <div className="text-xs text-gray-500">Account Holder</div>
            </div>

            <div className="p-4 rounded-lg bg-accent-green/5 border border-accent-green/20 text-center">
              <Shield className="h-8 w-8 text-accent-green mx-auto mb-2" />
              <div className="text-lg font-bold text-accent-green">
                {user?.account_number || `AC${user?.id?.toString().slice(-6) || '123456'}`}
              </div>
              <div className="text-xs text-gray-500">Account Number</div>
            </div>

            <div className="p-4 rounded-lg bg-accent-blue/5 border border-accent-blue/20 text-center">
              <Settings className="h-8 w-8 text-accent-blue mx-auto mb-2" />
              <div className="text-lg font-bold text-accent-blue">
                {portalData?.user_profile?.user_type || user?.user_type || 'Residential'}
              </div>
              <div className="text-xs text-gray-500">Account Type</div>
            </div>

            <div className="p-4 rounded-lg bg-accent-purple/5 border border-accent-purple/20 text-center">
              <Calendar className="h-8 w-8 text-accent-purple mx-auto mb-2" />
              <div className="text-lg font-bold text-accent-purple">
                {portalData?.user_profile?.date_joined ? new Date(portalData.user_profile.date_joined).getFullYear() : user?.date_joined ? new Date(user.date_joined).getFullYear() : 'N/A'}
              </div>
              <div className="text-xs text-gray-500">Member Since</div>
            </div>
          </div>
        </DashboardCard>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Personal Information - Make non-editable */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <User className="h-4 w-4 mr-2 text-primary-turquoise" />
                  Personal Information
                </h2>
                <div className="text-sm text-gray-500 italic">
                  View only - Contact support to make changes
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">First Name</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {user?.first_name || 'Not provided'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Last Name</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {user?.last_name || 'Not provided'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {user?.email || 'Not provided'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Phone Number</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {user?.mobile || user?.phone || 'Not provided'}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Service Address</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {portalData?.services?.service_address?.full_address || user?.address || 'Not provided'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">City</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {portalData?.services?.service_address?.city || user?.city || 'Not provided'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Postcode</label>
                  <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                    {portalData?.services?.service_address?.postal_code || user?.postcode || 'Not provided'}
                  </div>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Security Settings - Hidden as requested */}

          {/* Notification Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Bell className="h-4 w-4 mr-2 text-accent-blue" />
                  Notification Preferences
                </h2>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50/50">
                  <div>
                    <div className="font-semibold text-secondary-darkgray">Email Notifications</div>
                    <div className="text-sm text-gray-500">Receive account updates via email</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.emailNotifications}
                      onChange={(e) => handleInputChange('emailNotifications', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-turquoise/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-turquoise"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50/50">
                  <div>
                    <div className="font-semibold text-secondary-darkgray">SMS Notifications</div>
                    <div className="text-sm text-gray-500">Receive alerts via text message</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.smsNotifications}
                      onChange={(e) => handleInputChange('smsNotifications', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-turquoise/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-turquoise"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50/50">
                  <div>
                    <div className="font-semibold text-secondary-darkgray">Marketing Emails</div>
                    <div className="text-sm text-gray-500">Receive promotional offers and updates</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.marketingEmails}
                      onChange={(e) => handleInputChange('marketingEmails', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-turquoise/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-turquoise"></div>
                  </label>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar - Only Notification Preferences kept */}
        <div className="space-y-4">
          {/* Account Settings, Quick Actions, Data & Privacy - Hidden as requested */}
          
          {/* Simplified Account Information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <User className="h-4 w-4 mr-2 text-primary-turquoise" />
                  Account Details
                </h2>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Last Login</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Account Status</span>
                  <span className="text-sm font-semibold text-accent-green">
                    Active & Verified
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}