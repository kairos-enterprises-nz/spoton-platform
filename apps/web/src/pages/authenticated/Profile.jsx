import { useState } from "react";
import { motion } from "framer-motion";
import { 
  User, Shield, Bell, Globe, Save, Edit3, Eye, EyeOff, 
  Settings, Home, ChevronRight, Lock, Key
} from "lucide-react";

import { useAuth } from "../../hooks/useAuth";
import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";

export default function ProfilePage() {
  const { user } = useAuth();
  const { getUserDisplayName } = useDashboard();
  
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
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
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-secondary-darkgray via-secondary-darkgray/95 to-secondary-darkgray border border-primary-turquoise/30 shadow-xl">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute inset-0 bg-gradient-to-r from-primary-turquoise/30 via-transparent to-accent-lightturquoise/30 animate-shimmer"></div>
          </div>

          <div className="relative z-10 p-2 lg:p-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center space-x-3 mb-4 lg:mb-0">
                <div className="w-12 h-12 lg:w-16 lg:h-16 rounded-xl bg-gradient-to-br from-primary-turquoise to-accent-lightturquoise flex items-center justify-center shadow-lg shadow-primary-turquoise/30">
                  <User className="h-6 w-6 lg:h-8 lg:w-8 text-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <h1 className="text-xl lg:text-3xl font-bold text-white">
                      SpotOn Profile
                    </h1>
                    <div className="px-2 py-1 rounded-full bg-primary-turquoise/20 border border-primary-turquoise/40">
                      <span className="text-primary-turquoise text-xs font-semibold">Active</span>
                    </div>
                  </div>
                  <p className="text-accent-lightturquoise text-sm lg:text-base mb-1">
                    Manage your account settings
                  </p>
                  <p className="text-accent-lightturquoise/80 text-xs lg:text-sm">
                    Personal information and preferences
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 text-accent-lightturquoise">
                <Settings className="h-5 w-5 text-primary-turquoise" />
                <div className="text-right">
                  <div className="text-xs opacity-80">Account Status</div>
                  <div className="text-sm font-semibold">Verified</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Personal Information */}
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
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setIsEditing(!isEditing)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg font-medium text-sm transition-all duration-300 ${
                    isEditing 
                      ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' 
                      : 'bg-primary-turquoise text-white hover:bg-primary-turquoise/90'
                  }`}
                >
                  <Edit3 className="h-4 w-4" />
                  <span>{isEditing ? 'Cancel' : 'Edit'}</span>
                </motion.button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">First Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange('firstName', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.firstName || 'Not provided'}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Last Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.lastName}
                      onChange={(e) => handleInputChange('lastName', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.lastName || 'Not provided'}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.email || 'Not provided'}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Phone Number</label>
                  {isEditing ? (
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.phone || 'Not provided'}
                    </div>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Address</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) => handleInputChange('address', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.address || 'Not provided'}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">City</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.city}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.city || 'Not provided'}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Postcode</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={formData.postcode}
                      onChange={(e) => handleInputChange('postcode', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="px-3 py-2 bg-gray-50 rounded-lg text-secondary-darkgray">
                      {formData.postcode || 'Not provided'}
                    </div>
                  )}
                </div>
              </div>

              {isEditing && (
                <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleCancel}
                    className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-all duration-300 font-medium"
                  >
                    Cancel
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSave}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary-turquoise text-white rounded-lg hover:bg-primary-turquoise/90 transition-all duration-300 font-medium"
                  >
                    <Save className="h-4 w-4" />
                    <span>Save Changes</span>
                  </motion.button>
                </div>
              )}
            </DashboardCard>
          </motion.div>

          {/* Security Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Shield className="h-4 w-4 mr-2 text-accent-red" />
                  Security Settings
                </h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Current Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      value={formData.currentPassword}
                      onChange={(e) => handleInputChange('currentPassword', e.target.value)}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent-red focus:border-transparent transition-all duration-300"
                      placeholder="Enter current password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">New Password</label>
                    <input
                      type="password"
                      value={formData.newPassword}
                      onChange={(e) => handleInputChange('newPassword', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent-red focus:border-transparent transition-all duration-300"
                      placeholder="Enter new password"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm Password</label>
                    <input
                      type="password"
                      value={formData.confirmPassword}
                      onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent-red focus:border-transparent transition-all duration-300"
                      placeholder="Confirm new password"
                    />
                  </div>
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center space-x-2 px-4 py-2 bg-accent-red text-white rounded-lg hover:bg-accent-red/90 transition-all duration-300 font-medium"
                >
                  <Key className="h-4 w-4" />
                  <span>Update Password</span>
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>

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

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Account Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-2 text-primary-turquoise" />
                  Account Settings
                </h2>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Language</label>
                  <select
                    value={formData.language}
                    onChange={(e) => handleInputChange('language', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                  >
                    <option value="English">English</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="German">German</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Timezone</label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => handleInputChange('timezone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-turquoise focus:border-transparent transition-all duration-300"
                  >
                    <option value="Australia/Sydney">Sydney (AEDT)</option>
                    <option value="Australia/Melbourne">Melbourne (AEDT)</option>
                    <option value="Australia/Brisbane">Brisbane (AEST)</option>
                    <option value="Australia/Perth">Perth (AWST)</option>
                  </select>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-2 text-primary-turquoise" />
                  Quick Actions
                </h2>
              </div>

              <div className="space-y-2">
                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 hover:from-primary-turquoise/20 hover:to-primary-turquoise/10 border border-primary-turquoise/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-primary-turquoise/20">
                        <User className="h-4 w-4 text-primary-turquoise" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Update Profile</div>
                        <div className="text-xs text-gray-500">Edit personal info</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary-turquoise group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-red/10 to-accent-red/5 hover:from-accent-red/20 hover:to-accent-red/10 border border-accent-red/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-red/20">
                        <Lock className="h-4 w-4 text-accent-red" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Change Password</div>
                        <div className="text-xs text-gray-500">Update security</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-red group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 hover:from-accent-blue/20 hover:to-accent-blue/10 border border-accent-blue/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-blue/20">
                        <Bell className="h-4 w-4 text-accent-blue" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Notifications</div>
                        <div className="text-xs text-gray-500">Manage alerts</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-blue group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Account Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Home className="h-4 w-4 mr-2 text-primary-turquoise" />
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
                  <span className="text-sm text-gray-600">Customer ID</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.id || 'N/A'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Account Type</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.user_type || 'Standard'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Member Since</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.date_joined ? new Date(user.date_joined).getFullYear() : 'N/A'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-2 rounded bg-gray-50/50">
                  <span className="text-sm text-gray-600">Last Login</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Data & Privacy */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Shield className="h-4 w-4 mr-2 text-accent-green" />
                  Data & Privacy
                </h2>
              </div>

              <div className="space-y-2">
                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-green/10 to-accent-green/5 hover:from-accent-green/20 hover:to-accent-green/10 border border-accent-green/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-green/20">
                        <Globe className="h-4 w-4 text-accent-green" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Download Data</div>
                        <div className="text-xs text-gray-500">Export your data</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-green group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 3 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-3 rounded-lg bg-gradient-to-r from-accent-red/10 to-accent-red/5 hover:from-accent-red/20 hover:to-accent-red/10 border border-accent-red/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-red/20">
                        <User className="h-4 w-4 text-accent-red" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Delete Account</div>
                        <div className="text-xs text-gray-500">Permanently remove</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-red group-hover:translate-x-1 transition-all duration-300" />
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