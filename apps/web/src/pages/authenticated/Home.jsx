// src/pages/authenticated/Home.jsx (Acting as Authenticated Layout)

import { Disclosure } from '@headlessui/react';
import { Bars3Icon, XMarkIcon, BellIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
// --- React Router Imports ---
import { useNavigate, useLocation, Outlet } from 'react-router-dom'; // Link not used directly
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Wifi, Smartphone, CreditCard, HelpCircle, User, LogOut, Globe } from 'lucide-react';

import { useAuth } from '../../hooks/useAuth';
import { DashboardProvider, useDashboard } from '../../context/DashboardContext';

// Import Logos
import SpotOnLogoDark from '../../assets/spoton-logo-reversed.webp';
function AuthenticatedLayout() {
  const { user, logout } = useAuth();
  const { getUserDisplayName, getUserInitials } = useDashboard();
  const navigate = useNavigate();
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/authenticated', icon: Globe, current: location.pathname === '/authenticated' || location.pathname === '/authenticated/' },
    { name: 'Power', href: '/authenticated/power', icon: Zap, current: location.pathname === '/authenticated/power', color: 'text-primary-turquoise' },
    { name: 'Broadband', href: '/authenticated/broadband', icon: Wifi, current: location.pathname === '/authenticated/broadband', color: 'text-accent-purple' },
    { name: 'Mobile', href: '/authenticated/mobile', icon: Smartphone, current: location.pathname === '/authenticated/mobile', color: 'text-accent-blue' },
    { name: 'Billing', href: '/authenticated/billing', icon: CreditCard, current: location.pathname === '/authenticated/billing', color: 'text-accent-red' },
    { name: 'Support', href: '/authenticated/support', icon: HelpCircle, current: location.pathname === '/authenticated/support', color: 'text-accent-green' },
  ];

  const userNavigation = [
    { name: 'Profile', href: '/authenticated/profile', icon: User },
    { name: 'Settings', href: '/authenticated/settings', icon: Cog6ToothIcon },
    { name: 'Sign out', href: '#', icon: LogOut, onClick: logout },
  ];

  const handleNavigation = (href, onClick) => {
    if (onClick) {
      onClick();
    } else {
      navigate(href);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Disclosure as="nav" className="bg-gradient-to-r from-secondary-darkgray via-secondary-darkgray to-gray-900 shadow-xl border-b border-gray-700">
        {({ open }) => (
          <>
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="flex h-16 items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <motion.img
                      whileHover={{ scale: 1.05 }}
                      className="h-10 w-auto"
                      src={SpotOnLogoDark}
                      alt="SpotOn"
                    />
                  </div>
                </div>
                  <div className="hidden md:block">
                    <div className="ml-10 flex items-baseline space-x-2">
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
                                ? 'bg-gray-700 text-white shadow-lg'
                                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                            }`}
                          >
                            <Icon className={`h-4 w-4 mr-2 ${item.color || 'text-current'}`} />
                            {item.name}
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>
                <div className="hidden md:block">
                  <div className="ml-4 flex items-center md:ml-6 space-x-3">
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      type="button"
                      className="relative rounded-full bg-gray-700 p-2 text-gray-300 hover:text-white hover:bg-gray-600 transition-all duration-200"
                    >
                      <span className="sr-only">View notifications</span>
                      <BellIcon className="h-5 w-5" aria-hidden="true" />
                      <span className="absolute -top-1 -right-1 h-3 w-3 bg-accent-red rounded-full animate-pulse"></span>
                    </motion.button>

                    {/* Profile dropdown */}
                    <Disclosure>
                      {({ open: profileOpen }) => (
                        <>
                          <Disclosure.Button className="relative flex max-w-xs items-center rounded-full bg-gray-700 text-sm text-white hover:bg-gray-600 transition-all duration-200 p-2">
                            <span className="sr-only">Open user menu</span>
                            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary-turquoise to-accent-lightturquoise flex items-center justify-center text-white font-semibold text-sm">
                              {getUserInitials()}
                            </div>
                            <span className="ml-2 text-sm font-medium text-gray-300">
                              {getUserDisplayName()}
                            </span>
                          </Disclosure.Button>
                          <AnimatePresence>
                            {profileOpen && (
                              <Disclosure.Panel
                                as={motion.div}
                                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                                transition={{ duration: 0.2 }}
                                className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-lg bg-white py-1 shadow-xl ring-1 ring-black ring-opacity-5"
                              >
                                {userNavigation.map((item) => {
                                  const Icon = item.icon;
                                  return (
                                    <motion.button
                                      key={item.name}
                                      onClick={() => handleNavigation(item.href, item.onClick)}
                                      whileHover={{ x: 5 }}
                                      className="flex w-full items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-all duration-200"
                                    >
                                      <Icon className="h-4 w-4 mr-3 text-gray-500" />
                                      {item.name}
                                    </motion.button>
                                  );
                                })}
                              </Disclosure.Panel>
                            )}
                          </AnimatePresence>
                        </>
                      )}
                    </Disclosure>
                  </div>
                </div>
                <div className="-mr-2 flex md:hidden">
                  {/* Mobile menu button */}
                  <Disclosure.Button className="relative inline-flex items-center justify-center rounded-md bg-gray-700 p-2 text-gray-300 hover:bg-gray-600 hover:text-white">
                    <span className="sr-only">Open main menu</span>
                    {open ? (
                      <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                    ) : (
                      <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                    )}
                  </Disclosure.Button>
                </div>
              </div>
            </div>

            <AnimatePresence>
              {open && (
                <Disclosure.Panel
                  as={motion.div}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="md:hidden bg-gray-800 border-t border-gray-700"
                >
                  <div className="space-y-1 px-2 pb-3 pt-2">
                    {navigation.map((item) => {
                      const Icon = item.icon;
                      return (
                        <motion.button
                          key={item.name}
                          onClick={() => handleNavigation(item.href)}
                          whileHover={{ x: 5 }}
                          className={`group flex w-full items-center rounded-md px-3 py-2 text-base font-medium transition-all duration-200 ${
                            item.current
                              ? 'bg-gray-700 text-white'
                              : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                          }`}
                        >
                          <Icon className={`h-5 w-5 mr-3 ${item.color || 'text-current'}`} />
                          {item.name}
                        </motion.button>
                      );
                    })}
                  </div>
                  <div className="border-t border-gray-700 pb-3 pt-4">
                    <div className="flex items-center px-5">
                      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary-turquoise to-accent-lightturquoise flex items-center justify-center text-white font-semibold">
                        {getUserInitials()}
                      </div>
                      <div className="ml-3">
                        <div className="text-base font-medium text-white">{getUserDisplayName()}</div>
                        <div className="text-sm font-medium text-gray-400">{user?.email}</div>
                      </div>
                    </div>
                    <div className="mt-3 space-y-1 px-2">
                      {userNavigation.map((item) => {
                        const Icon = item.icon;
                        return (
                          <motion.button
                            key={item.name}
                            onClick={() => handleNavigation(item.href, item.onClick)}
                            whileHover={{ x: 5 }}
                            className="flex w-full items-center rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition-all duration-200"
                          >
                            <Icon className="h-5 w-5 mr-3 text-gray-500" />
                            {item.name}
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>
                </Disclosure.Panel>
              )}
            </AnimatePresence>
          </>
        )}
      </Disclosure>

      <main className="flex-1">
        <div className="py-4">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-gray-500">
            <div className="flex space-x-6 mb-2 sm:mb-0">
              <span>© 2024 SpotOn. All rights reserved.</span>
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
