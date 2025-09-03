// src/pages/authenticated/Home.jsx (Acting as Authenticated Layout)

import React, { useState, useRef } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { DashboardProvider } from '../../context/DashboardContext';
import { useDashboard } from '../../context/DashboardContext';
import { useAuth } from '../../hooks/useAuth';
import { useNavigateWithLoader } from '../../hooks/useNavigationLoader';
import Drawer from '../../components/Drawer';
import SpotOnLogoDark from '../../assets/spoton-logo-reversed.webp';
import { 
  PanelLeft, 
  Bell, 
  Home as HomeIcon, 
  Zap, 
  Wifi, 
  Smartphone, 
  CreditCard, 
  HelpCircle, 
  Check,
  Grid3X3,
  User,
  LogOut,
  ChevronDown
} from 'lucide-react';

const BOTTOM_BAR_HEIGHT = 56;

function AuthenticatedLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { getUserDisplayName, getUserInitials, userServices } = useDashboard();
  const { navigateWithLoader } = useNavigateWithLoader();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isServicesSheetOpen, setIsServicesSheetOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [isLegalSectionOpen, setIsLegalSectionOpen] = useState(false);
  const bottomBarRef = useRef(null);
  const bottomScrollRef = useRef(null);

  // Navigation items
  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon, color: 'text-primary-turquoise', current: location.pathname === '/' },
    { name: 'Power', href: '/power', icon: Zap, color: 'text-yellow-500', current: location.pathname === '/power' },
    { name: 'Broadband', href: '/broadband', icon: Wifi, color: 'text-blue-500', current: location.pathname === '/broadband' },
    { name: 'Mobile', href: '/mobile', icon: Smartphone, color: 'text-green-500', current: location.pathname === '/mobile' },
    { name: 'Billing', href: '/billing', icon: CreditCard, color: 'text-purple-500', current: location.pathname === '/billing' },
    { name: 'Support', href: '/support', icon: HelpCircle, color: 'text-orange-500', current: location.pathname === '/support' },
  ];

  // Handle navigation with loading
  const handleNavigation = (href) => {
    navigateWithLoader(navigate, href);
  };

  // Handle bottom nav tap with loading
  const handleBottomNavTap = (e, href) => {
    e.preventDefault();
    navigateWithLoader(navigate, href);
  };

  // Available services for dynamic display
  const availableServices = [
    { name: 'Power', href: '/power', icon: Zap, color: 'text-yellow-500', label: 'Power' },
    { name: 'Broadband', href: '/broadband', icon: Wifi, color: 'text-blue-500', label: 'Broadband' },
    { name: 'Mobile', href: '/mobile', icon: Smartphone, color: 'text-green-500', label: 'Mobile' }
  ];

  // Handle services tap
  const handleServicesTap = (e) => {
    e.preventDefault();
    setIsServicesSheetOpen(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Navigation */}
      <nav className="bg-gradient-to-r from-gray-600 via-gray-700 to-gray-800 shadow-lg border-b border-gray-300">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 md:h-16 items-center justify-between">
            
            {/* Mobile Layout: Drawer + Logo + Bell */}
            <div className="md:hidden grid grid-cols-3 items-center w-full">
              {/* Left: Drawer */}
              <div className="justify-self-start">
                <motion.button
                  type="button"
                  onClick={() => setDrawerOpen(true)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="relative inline-flex items-center justify-center rounded-2xl bg-gray-700 p-3 text-gray-300 hover:bg-gray-600 hover:text-white transition-all duration-200 shadow-lg"
                >
                  <span className="sr-only">Open main menu</span>
                  <PanelLeft className="block h-4 w-4" aria-hidden="true" />
                </motion.button>
              </div>

              {/* Center: Logo */}
              <div className="justify-self-center">
                <motion.img
                  whileHover={{ scale: 1.05 }}
                  className="h-10 w-auto object-contain max-w-[180px]"
                  src={SpotOnLogoDark}
                  alt="SpotOn"
                />
              </div>

              {/* Right: Bell */}
              <div className="justify-self-end">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="relative inline-flex items-center justify-center rounded-2xl bg-gray-700 p-3 text-gray-300 hover:bg-gray-600 hover:text-white transition-all duration-200 shadow-lg"
                >
                  <span className="sr-only">View notifications</span>
                  <Bell className="block h-4 w-4" aria-hidden="true" />
                  <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
                </motion.button>
              </div>
            </div>

            {/* Desktop Layout: Logo + Navigation + Profile */}
            <div className="hidden md:flex flex-1 items-center">
              <div className="flex-shrink-0">
                <motion.img
                  whileHover={{ scale: 1.05 }}
                  className="h-8 md:h-9 lg:h-10 w-auto"
                  src={SpotOnLogoDark}
                  alt="SpotOn"
                />
              </div>
            </div>

            {/* Centered Navigation */}
            <div className="hidden md:flex flex-none justify-center">
              <div className="flex items-baseline gap-2">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <motion.button
                      key={item.name}
                      onClick={() => handleNavigation(item.href)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className={`group flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        item.current
                          ? 'bg-gray-600 text-white shadow-md'
                          : 'text-gray-200 hover:bg-gray-600 hover:text-white'
                      }`}
                    >
                      <Icon className={`h-4 w-4 mr-2 ${item.color || 'text-current'}`} />
                      {item.name}
                    </motion.button>
                  );
                })}
              </div>
            </div>

            {/* Right Side: Desktop Profile + Notifications */}
            <div className="hidden md:flex items-center space-x-3 md:flex-1 md:justify-end">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="relative p-2 text-gray-300 hover:text-white hover:bg-gray-600 rounded-full transition-all duration-200"
              >
                <Bell className="h-5 w-5" />
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
              </motion.button>
              
              {/* Profile Dropdown */}
              <div className="relative">
                <motion.button
                  onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center gap-1 p-2 text-gray-200 hover:text-white hover:bg-gray-600 rounded-lg transition-all duration-200"
                >
                  <div className="h-8 w-8 bg-primary-turquoise rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {getUserInitials()}
                    </span>
                  </div>
                  <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${isProfileDropdownOpen ? 'rotate-180' : ''}`} />
                </motion.button>

                {/* Dropdown Menu */}
                <AnimatePresence>
                  {isProfileDropdownOpen && (
                    <>
                      {/* Backdrop */}
                      <div 
                        className="fixed inset-0 z-10" 
                        onClick={() => setIsProfileDropdownOpen(false)}
                      />
                      
                      {/* Dropdown */}
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-lg border border-slate-600 py-1 z-20"
                      >
                        <motion.button
                          onClick={() => {
                            setIsProfileDropdownOpen(false);
                            handleNavigation('/profile');
                          }}
                          whileHover={{ backgroundColor: '#475569' }}
                          className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-200 hover:bg-slate-600 transition-colors"
                        >
                          <User className="h-4 w-4 text-gray-300" />
                          Profile
                        </motion.button>
                        
                        <div className="border-t border-slate-600 my-1" />
                        
                        <motion.button
                          onClick={() => {
                            setIsProfileDropdownOpen(false);
                            logout();
                          }}
                          whileHover={{ backgroundColor: '#7f1d1d' }}
                          className="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-400 hover:bg-red-900/50 hover:text-white transition-colors"
                        >
                          <LogOut className="h-4 w-4" />
                          Sign Out
                        </motion.button>
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Drawer Navigation */}
      <Drawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        title="Navigation"
        side="left"
        panelClassName="rounded-r-2xl bg-gradient-to-b from-gray-800 to-gray-900 border-r border-gray-700 text-gray-100"
      >
        <div className="flex flex-col h-full">
          <div className="flex-1">
            <nav className="space-y-1 px-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <motion.button
                    key={item.name}
                    onClick={() => {
                      setDrawerOpen(false);
                      handleNavigation(item.href);
                    }}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.98 }}
                    className={`w-full flex items-center gap-3 rounded-lg text-left font-medium text-sm transition-all duration-200 ${
                      item.current 
                        ? 'bg-primary-turquoise/20 text-primary-turquoise border border-primary-turquoise/30 px-4 py-3' 
                        : 'text-gray-300 hover:bg-gray-700/50 hover:text-white px-3 py-2.5'
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${item.current ? 'text-primary-turquoise' : item.color || 'text-gray-300'}`} />
                    <span className="font-medium">{item.name}</span>
                    {item.current && (
                      <Check className="h-4 w-4 text-primary-turquoise ml-auto" aria-hidden="true" />
                    )}
                  </motion.button>
                );
              })}
            </nav>
          </div>

          {/* Legal Section - moved above user info */}
          <div className="mt-4 p-4">
            {/* Legal Section - Collapsible */}
            <div className="mb-4">
              <motion.button
                onClick={() => setIsLegalSectionOpen(!isLegalSectionOpen)}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="w-full flex items-center justify-between px-3 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-md transition-all duration-200"
              >
                <span>Legals</span>
                <ChevronDown className={`h-3 w-3 transition-transform duration-200 ${isLegalSectionOpen ? 'rotate-180' : ''}`} />
              </motion.button>
              
              <AnimatePresence>
                {isLegalSectionOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="pt-0 space-y-1">
                      {/* Top Section: Consumer Care Policy */}
                      <div className="mb-1">
                        <button 
                          onClick={() => { setDrawerOpen(false); handleNavigation('/legal/consumercarepolicy'); }} 
                          className="w-full text-left px-1.5 py-0.5 text-xs text-gray-400 leading-tight"
                        >
                          Consumer Care Policy
                        </button>
                      </div>

                      {/* Middle Section: Plans */}
                      <div className="mb-1 space-y-0">
                        {/* Debug: Log userServices to console */}
                        {userServices && console.log('Legal Debug - userServices:', JSON.stringify(userServices, null, 2))}
                        
                        {userServices?.some(service => {
                          const serviceStr = JSON.stringify(service).toLowerCase();
                          const hasBroadband = serviceStr.includes('broadband') || 
                                             serviceStr.includes('internet') || 
                                             serviceStr.includes('fibre') || 
                                             serviceStr.includes('fiber') ||
                                             serviceStr.includes('adsl') ||
                                             serviceStr.includes('vdsl') ||
                                             serviceStr.includes('wifi') ||
                                             serviceStr.includes('web') ||
                                             serviceStr.includes('connection');
                          
                          // Also check specific fields
                          const typeMatch = service.type === 'broadband' || 
                                          service.type === 'internet' || 
                                          service.type === 'fibre' ||
                                          service.type === 'fiber';
                          
                          console.log('Broadband check for service:', service, 'hasBroadband:', hasBroadband, 'typeMatch:', typeMatch);
                          return hasBroadband || typeMatch;
                        }) && (
                          <button 
                            onClick={() => { setDrawerOpen(false); handleNavigation('/legal/broadbandterms'); }} 
                            className="w-full text-left px-1.5 py-0.5 text-xs text-gray-400 leading-tight"
                          >
                            Broadband Terms
                          </button>
                        )}
                        
                        {userServices?.some(service => service.type === 'mobile') && (
                          <button 
                            onClick={() => { setDrawerOpen(false); handleNavigation('/legal/mobileterms'); }} 
                            className="w-full text-left px-1.5 py-0.5 text-xs text-gray-400 leading-tight"
                          >
                            Mobile Terms
                          </button>
                        )}
                        
                        {userServices?.some(service => service.type === 'electricity' || service.type === 'power') && (
                          <button 
                            onClick={() => { setDrawerOpen(false); handleNavigation('/legal/powerterms'); }} 
                            className="w-full text-left px-1.5 py-0.5 text-xs text-gray-400 leading-tight"
                          >
                            Power Terms
                          </button>
                        )}
                      </div>

                      {/* Bottom Section: Terms of Service | Privacy Policy */}
                      <div className="flex items-center px-1.5">
                        <button 
                          onClick={() => { setDrawerOpen(false); handleNavigation('/legal/termsofservice'); }} 
                          className="text-left py-0.5 text-xs text-gray-400 leading-tight"
                        >
                          Terms of Service
                        </button>
                        <div className="w-px h-3 bg-gray-600 mx-3"></div>
                        <button 
                          onClick={() => { setDrawerOpen(false); handleNavigation('/legal/privacypolicy'); }} 
                          className="text-left py-0.5 text-xs text-gray-400 leading-tight"
                        >
                          Privacy Policy
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            
            {/* Separator Line */}
            <div className="border-t border-gray-700 my-4"></div>
            
            {/* User Info */}
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 bg-primary-turquoise rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-white text-sm font-medium">
                  {getUserInitials()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-white truncate">{getUserDisplayName()}</div>
                <div className="text-xs text-gray-400 truncate">{user?.email}</div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <motion.button 
                onClick={() => { setDrawerOpen(false); handleNavigation('/profile'); }} 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-gray-200 bg-gray-800 border border-gray-700 hover:bg-gray-700 transition-all duration-200"
              >
                <User className="h-4 w-4" />
                Profile
              </motion.button>
              <motion.button 
                onClick={() => { setDrawerOpen(false); logout(); }} 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-red-400 bg-gray-800 border border-gray-700 hover:bg-red-600/20 hover:text-white transition-all duration-200"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </motion.button>
            </div>
          </div>
        </div>
      </Drawer>

      {/* Main Content */}
      <main
        className="flex-1 md:pb-6"
        style={{ paddingBottom: `calc(${BOTTOM_BAR_HEIGHT}px + env(safe-area-inset-bottom, 0px))` }}
      >
        <div className="py-4">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </div>
      </main>

      {/* Mobile Bottom Navigation Bar */}
      {createPortal(
        <div
          ref={bottomBarRef}
          className="fixed bottom-0 left-0 right-0 lg:hidden bg-gradient-to-r from-gray-600 via-gray-700 to-gray-800 border-t border-gray-500 shadow-lg z-[9999] h-14"
          style={{ 
            paddingBottom: 'env(safe-area-inset-bottom, 0px)',
            transform: 'translateZ(0)',
            willChange: 'auto'
          }}
        >
          <div className="relative w-full">
            <div
              ref={bottomScrollRef}
              role="tablist"
              aria-label="Primary navigation"
              className="grid grid-cols-4 gap-1 px-2 py-1 h-14"
            >
              {/* Home */}
              <motion.button
                onClick={(e) => handleBottomNavTap(e, '/')}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`flex flex-col items-center justify-center px-1.5 py-1.5 rounded-md transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-turquoise h-12 ${
                  location.pathname === '/' || location.pathname === ''
                    ? 'bg-gray-600 text-primary-turquoise'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
                role="tab"
                aria-selected={(location.pathname === '/' || location.pathname === '').toString()}
              >
                <HomeIcon className="h-4 w-4 mb-1.5" />
                <span className="text-[10px] leading-none font-medium h-3">Home</span>
              </motion.button>

              {/* Services - Dynamic based on current service */}
              <motion.button
                onClick={handleServicesTap}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`flex flex-col items-center justify-center px-1.5 py-1.5 rounded-md transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-turquoise h-12 ${
                  location.pathname.includes('/power') || location.pathname.includes('/broadband') || location.pathname.includes('/mobile')
                    ? 'bg-gray-600 text-primary-turquoise'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
                role="tab"
              >
                {(() => {
                  // Find current service or default to Grid3X3
                  const currentService = availableServices.find(service => location.pathname === service.href);
                  if (currentService) {
                    const CurrentIcon = currentService.icon;
                    return (
                      <>
                        <CurrentIcon className={`h-4 w-4 mb-1.5 ${currentService.color}`} />
                        <span className="text-[10px] leading-none font-medium h-3">{currentService.label}</span>
                      </>
                    );
                  } else {
                    return (
                      <>
                        <Grid3X3 className="h-4 w-4 mb-1.5" />
                        <span className="text-[10px] leading-none font-medium h-3">Services</span>
                      </>
                    );
                  }
                })()}
              </motion.button>

              {/* Billing */}
              <motion.button
                onClick={(e) => handleBottomNavTap(e, '/billing')}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`flex flex-col items-center justify-center px-1.5 py-1.5 rounded-md transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-turquoise h-12 ${
                  location.pathname === '/billing'
                    ? 'bg-gray-600 text-primary-turquoise'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
                role="tab"
              >
                <CreditCard className="h-4 w-4 mb-1.5" />
                <span className="text-[10px] leading-none font-medium h-3">Billing</span>
              </motion.button>

              {/* Support */}
              <motion.button
                onClick={(e) => handleBottomNavTap(e, '/support')}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`flex flex-col items-center justify-center px-1.5 py-1.5 rounded-md transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-turquoise h-12 ${
                  location.pathname === '/support'
                    ? 'bg-gray-600 text-primary-turquoise'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
                role="tab"
              >
                <HelpCircle className="h-4 w-4 mb-1.5" />
                <span className="text-[10px] leading-none font-medium h-3">Support</span>
              </motion.button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Services Mini-Drawer */}
      <AnimatePresence>
        {isServicesSheetOpen && (
          <>
            <motion.div
              key="services-scrim"
              className="fixed inset-0 bg-black/20 z-[13500] lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsServicesSheetOpen(false)}
            />
            <motion.div
              key="services-mini-drawer"
              className="fixed left-4 right-4 bottom-20 z-[13600] bg-gray-800/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl overflow-hidden lg:hidden"
              initial={{ y: 100, opacity: 0, scale: 0.95 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 100, opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            >
              <div className="px-4 py-3 border-b border-gray-700/50">
                <h3 className="text-sm font-semibold text-white">Your Services</h3>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-3 gap-3">
                  {availableServices.map((service) => {
                    const Icon = service.icon;
                    const isCurrentService = location.pathname === service.path;
                    return (
                      <motion.button
                        key={service.name}
                        onClick={() => {
                          setIsServicesSheetOpen(false);
                          handleNavigation(service.href);
                        }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className={`relative group p-3 rounded-xl overflow-hidden border transition-all duration-300 ${
                          isCurrentService
                            ? 'bg-primary-turquoise/20 border-primary-turquoise/50 shadow-lg'
                            : 'bg-gray-700/50 border-gray-600/50 hover:bg-gray-600/50'
                        } min-h-[80px] flex flex-col items-center justify-center w-full`}
                      >
                        {/* Selected indicator */}
                        {isCurrentService && (
                          <div className="absolute top-2 right-2 w-2 h-2 bg-primary-turquoise rounded-full"></div>
                        )}

                        {/* Background gradient overlay */}
                        <div
                          className={`absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity duration-300 ${
                            service.color === 'text-yellow-500' ? 'from-yellow-400 to-yellow-600' :
                            service.color === 'text-blue-500' ? 'from-blue-400 to-blue-600' :
                            service.color === 'text-green-500' ? 'from-green-400 to-green-600' :
                            'from-gray-400 to-gray-600'
                          }`}
                        />

                        {/* Content */}
                        <div className="relative z-10 flex flex-col items-center text-center">
                          <div className={`p-2 rounded-full mb-1 transition-colors duration-300 ${
                            isCurrentService ? 'bg-gray-700/30' : 'bg-gray-600/50 group-hover:bg-gray-500/50'
                          }`}>
                            <Icon className={`h-5 w-5 ${service.color}`} />
                          </div>
                          <span className="text-xs font-semibold text-white leading-tight">{service.name}</span>
                        </div>
                      </motion.button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-gray-500">
            <div className="flex space-x-6 mb-2 sm:mb-0">
              <span>© {new Date().getFullYear()} SpotOn. All rights reserved.</span>
            </div>
            <div className="flex space-x-6">
              <button className="hover:text-gray-700 transition-colors duration-200">Privacy Policy</button>
              <button className="hover:text-gray-700 transition-colors duration-200">Terms of Service</button>
              <button className="hover:text-gray-700 transition-colors duration-200">Contact</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <DashboardProvider>
      <AuthenticatedLayout />
    </DashboardProvider>
  );
}