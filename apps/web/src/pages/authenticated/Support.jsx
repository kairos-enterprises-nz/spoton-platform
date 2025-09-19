import { useState } from "react";
import { motion } from "framer-motion";
import { 
  HelpCircle, MessageSquare, Phone, Mail, Clock, Search,
  ChevronRight, User, FileText,
  Settings, Zap, Wifi, Smartphone
} from "lucide-react";

import { useDashboard } from "../../context/DashboardContext";
import DashboardCard from "../../components/dashboard/shared/DashboardCard";
import ServiceCard from "../../components/dashboard/shared/ServiceCard";

export default function SupportPage() {
  const { 
    user, 
    loading, 
    getUserDisplayName 
  } = useDashboard();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Mock FAQ data
  const faqCategories = [
    { id: 'all', name: 'All Topics', count: 24 },
    { id: 'billing', name: 'Billing', count: 8 },
    { id: 'technical', name: 'Technical', count: 6 },
    { id: 'account', name: 'Account', count: 5 },
    { id: 'services', name: 'Services', count: 5 }
  ];

  const faqItems = [
    {
      id: 1,
      question: "How do I view my current bill?",
      answer: "You can view your current bill in the Billing section of your dashboard.",
      category: 'billing',
      helpful: 15
    },
    {
      id: 2,
      question: "What should I do if my internet is slow?",
      answer: "Try restarting your router first. If the issue persists, run a speed test from your dashboard.",
      category: 'technical',
      helpful: 12
    },
    {
      id: 3,
      question: "How do I update my payment method?",
      answer: "Go to Billing > Payment Methods to update your payment information.",
      category: 'billing',
      helpful: 18
    },
    {
      id: 4,
      question: "Can I change my service plan?",
      answer: "Yes, you can upgrade or downgrade your plan by contacting our support team.",
      category: 'services',
      helpful: 9
    }
  ];

  // Mock support tickets
  const supportTickets = [
    {
      id: 'SPT-2024-001',
      subject: 'Internet connection issues',
      status: 'open',
      priority: 'high',
      created: '2024-01-15',
      lastUpdate: '2024-01-16'
    },
    {
      id: 'SPT-2024-002',
      subject: 'Billing inquiry',
      status: 'resolved',
      priority: 'medium',
      created: '2024-01-10',
      lastUpdate: '2024-01-12'
    }
  ];

  // Contact methods
  const contactMethods = [
    {
      id: 'phone',
      name: 'Phone Support',
      description: '24/7 support available',
      contact: '0800 SPOTON',
      icon: Phone,
      color: 'accent-green',
      available: true
    },
    {
      id: 'email',
      name: 'Email Support',
      description: 'Response within 24 hours',
      contact: 'support@spoton.co.nz',
      icon: Mail,
      color: 'accent-blue',
      available: true
    },
    {
      id: 'chat',
      name: 'Live Chat',
      description: 'Instant messaging support',
      contact: 'Start chat',
      icon: MessageSquare,
      color: 'primary-turquoise',
      available: false
    }
  ];

  const filteredFAQs = faqItems.filter(item => {
    const matchesSearch = item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.answer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return { bg: 'bg-accent-blue/10', text: 'text-accent-blue', border: 'border-accent-blue/30' };
      case 'resolved': return { bg: 'bg-accent-green/10', text: 'text-accent-green', border: 'border-accent-green/30' };
      case 'pending': return { bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' };
      default: return { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' };
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return { bg: 'bg-accent-red/10', text: 'text-accent-red', border: 'border-accent-red/30' };
      case 'medium': return { bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' };
      case 'low': return { bg: 'bg-accent-green/10', text: 'text-accent-green', border: 'border-accent-green/30' };
      default: return { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' };
    }
  };

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
            <div className="absolute inset-0 bg-gradient-to-r from-accent-green/30 via-transparent to-primary-turquoise/30 animate-shimmer"></div>
            <svg className="w-full h-full" viewBox="0 0 100 20" preserveAspectRatio="none">
              <defs>
                <pattern id="support-grid" width="10" height="10" patternUnits="userSpaceOnUse">
                  <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-accent-green/40"/>
                </pattern>
              </defs>
              <rect width="100" height="20" fill="url(#support-grid)" />
            </svg>
          </div>

          <div className="relative z-10 p-2 lg:p-4">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center space-x-4 mb-6 lg:mb-0">
                <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-2xl bg-gradient-to-br from-accent-green to-accent-green/80 flex items-center justify-center shadow-lg shadow-accent-green/30">
                  <HelpCircle className="h-8 w-8 lg:h-10 lg:w-10 text-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-2xl lg:text-4xl font-bold text-white">
                      SpotOn Support
                    </h1>
                    <div className="px-3 py-1 rounded-full bg-accent-green/20 border border-accent-green/40">
                      <span className="text-accent-green text-sm font-semibold">Available</span>
                    </div>
                  </div>
                  <p className="text-accent-lightturquoise text-sm lg:text-base mb-1">
                    Get help with your services and account
                  </p>
                  <p className="text-accent-lightturquoise/80 text-xs lg:text-sm">
                    24/7 support for all your needs
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4 text-accent-lightturquoise">
                <Clock className="h-5 w-5 text-accent-green" />
                <div className="text-right">
                  <div className="text-xs opacity-80">Support Hours</div>
                  <div className="text-sm font-semibold">24/7 Available</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Contact Methods */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
        className="grid grid-cols-1 md:grid-cols-3 gap-2"
      >
        {contactMethods.map((method) => (
          <ServiceCard
            key={method.id}
            title={method.name}
            icon={method.icon}
            value={method.contact}
            subtitle={method.description}
            color={method.color}
            className="hover:shadow-xl hover:shadow-current/20 transition-all duration-300"
          >
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
              method.available 
                ? 'bg-accent-green/10 text-accent-green border border-accent-green/20' 
                : 'bg-gray-100 text-gray-500 border border-gray-200'
            }`}>
              <div className={`w-2 h-2 rounded-full mr-2 ${method.available ? 'bg-accent-green animate-pulse' : 'bg-gray-400'}`}></div>
              {method.available ? 'Available' : 'Offline'}
            </div>
          </ServiceCard>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-3">
          {/* FAQ Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center mb-4 sm:mb-0">
                  <FileText className="h-4 w-4 mr-3 text-accent-green" />
                  Frequently Asked Questions
                </h2>
              </div>

              {/* Search and Filter */}
              <div className="flex flex-col sm:flex-row gap-4 mb-6">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search FAQs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-accent-green focus:ring-2 focus:ring-accent-green/20 transition-all duration-300"
                  />
                </div>
                <div className="flex bg-gray-100 rounded-xl p-1 shadow-inner">
                  {faqCategories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
                        selectedCategory === category.id
                          ? 'bg-accent-green text-white shadow-lg shadow-accent-green/30'
                          : 'text-gray-600 hover:text-secondary-darkgray hover:bg-white/50'
                      }`}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* FAQ Items */}
              <div className="space-y-4">
                {filteredFAQs.map((faq, index) => (
                  <motion.div
                    key={faq.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.1 * index }}
                    className="p-2 rounded-xl bg-gray-50/50 border border-gray-200/50 hover:border-accent-green/30 hover:bg-accent-green/5 transition-all duration-300 group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-secondary-darkgray mb-2 group-hover:text-accent-green transition-colors duration-300">
                          {faq.question}
                        </h3>
                        <p className="text-sm text-gray-600 mb-3">{faq.answer}</p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span className="px-2 py-1 bg-gray-200 rounded-full capitalize">{faq.category}</span>
                          <span>{faq.helpful} people found this helpful</span>
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-accent-green group-hover:translate-x-1 transition-all duration-300" />
                    </div>
                  </motion.div>
                ))}
              </div>

              {filteredFAQs.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <div className="text-sm font-medium">No FAQs found</div>
                  <div className="text-xs mt-1">Try adjusting your search or category filter</div>
                </div>
              )}
            </DashboardCard>
          </motion.div>

          {/* Support Tickets */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <MessageSquare className="h-4 w-4 mr-3 text-accent-green" />
                  Your Support Tickets
                </h2>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-4 py-2 bg-accent-green text-white rounded-xl hover:bg-accent-green/90 transition-all duration-300 shadow-lg shadow-accent-green/20"
                >
                  New Ticket
                </motion.button>
              </div>

              <div className="space-y-4">
                {supportTickets.length > 0 ? (
                  supportTickets.map((ticket, index) => {
                    const statusConfig = getStatusColor(ticket.status);
                    const priorityConfig = getPriorityColor(ticket.priority);
                    
                    return (
                      <motion.div
                        key={ticket.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.4, delay: 0.1 * index }}
                        className="p-2 rounded-xl border border-gray-200/50 hover:border-accent-green/30 hover:bg-accent-green/5 transition-all duration-300 group"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="font-semibold text-secondary-darkgray group-hover:text-accent-green transition-colors duration-300">
                              {ticket.subject}
                            </div>
                            <div className="text-sm text-gray-500 mt-1">Ticket #{ticket.id}</div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}>
                              {ticket.status}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${priorityConfig.bg} ${priorityConfig.text} ${priorityConfig.border}`}>
                              {ticket.priority}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>Created: {new Date(ticket.created).toLocaleDateString()}</span>
                          <span>Last update: {new Date(ticket.lastUpdate).toLocaleDateString()}</span>
                        </div>
                      </motion.div>
                    );
                  })
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <div className="text-gray-500 mb-2">No support tickets</div>
                    <div className="text-sm text-gray-400">
                      You haven&apos;t created any support tickets yet
                    </div>
                  </div>
                )}
              </div>
            </DashboardCard>
          </motion.div>
        </div>

        {/* Sidebar */}
        <div className="space-y-3">
          {/* Quick Help */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Settings className="h-4 w-4 mr-3 text-accent-green" />
                  Quick Help
                </h2>
              </div>

              <div className="space-y-3">
                <motion.button
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-4 rounded-xl bg-gradient-to-r from-primary-turquoise/10 to-primary-turquoise/5 hover:from-primary-turquoise/20 hover:to-primary-turquoise/10 border border-primary-turquoise/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-primary-turquoise/20">
                        <Zap className="h-5 w-5 text-primary-turquoise" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Power Issues</div>
                        <div className="text-xs text-gray-500">Outages & billing</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary-turquoise group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full group p-4 rounded-xl bg-gradient-to-r from-accent-purple/10 to-accent-purple/5 hover:from-accent-purple/20 hover:to-accent-purple/10 border border-accent-purple/30 transition-all duration-300 text-left shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-accent-purple/20">
                        <Wifi className="h-5 w-5 text-accent-purple" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Internet Help</div>
                        <div className="text-xs text-gray-500">Speed & connectivity</div>
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
                        <Smartphone className="h-5 w-5 text-accent-blue" />
                      </div>
                      <div>
                        <div className="font-semibold text-secondary-darkgray">Mobile Support</div>
                        <div className="text-xs text-gray-500">Plans & data</div>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-accent-blue group-hover:translate-x-1 transition-all duration-300" />
                  </div>
                </motion.button>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Account Information */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <User className="h-4 w-4 mr-3 text-accent-green" />
                  Account Information
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
                  <span className="text-sm text-gray-600 font-medium">Customer ID</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.id || 'N/A'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Email</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.email || 'N/A'}
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 rounded-lg bg-gray-50/50">
                  <span className="text-sm text-gray-600 font-medium">Phone</span>
                  <span className="text-sm font-semibold text-secondary-darkgray">
                    {user?.phone || 'Not provided'}
                  </span>
                </div>
              </div>
            </DashboardCard>
          </motion.div>

          {/* Support Hours */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6, ease: "easeOut" }}
          >
            <DashboardCard className="bg-gradient-to-br from-white to-slate-50/50 border border-gray-200/50 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-secondary-darkgray flex items-center">
                  <Clock className="h-4 w-4 mr-3 text-accent-green" />
                  Support Hours
                </h2>
              </div>

              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-gradient-to-r from-accent-green/10 to-accent-green/5 border border-accent-green/30 shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-accent-green rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-green">Phone Support</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-2 ml-6">
                    Available 24/7 for urgent issues
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-gradient-to-r from-accent-blue/10 to-accent-blue/5 border border-accent-blue/30 shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-accent-blue rounded-full animate-pulse"></div>
                    <span className="text-sm font-semibold text-accent-blue">Email Support</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-2 ml-6">
                    Response within 24 hours
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-200 shadow-sm">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                    <span className="text-sm font-semibold text-gray-600">Live Chat</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-2 ml-6">
                    Mon-Fri 8AM-6PM (Coming Soon)
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