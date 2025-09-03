import { useState } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { PanelLeft, Zap, Wifi, Smartphone, HelpCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useLoader } from '../../context/LoaderContext'
import Logo from '../../assets/utilitycopilot-logo.webp'
import { useAuth } from '../../hooks/useAuth'
import Drawer from '../Drawer.jsx'

const navigation = [
  { name: 'Power', href: '/power', icon: Zap, color: 'text-primary-turquoise' },
  { name: 'Broadband', href: '/broadband', icon: Wifi, color: 'text-accent-purple' },
  { name: 'Mobile', href: '/mobile', icon: Smartphone, color: 'text-accent-blue' },
  { name: 'Support', href: '/support', icon: HelpCircle, color: 'text-accent-green' },
]

export default function Header() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const { setLoading } = useLoader()
  const { isAuthenticated } = useAuth()

  const handleStart = (path) => {
    if (path === window.location.pathname) return
    
    // Special handling for authenticated dashboard - redirect to customer portal
    if (path === '/authenticated' && isAuthenticated) {
      window.location.href = `${import.meta.env.VITE_PORTAL_URL || 'https://uat.portal.spoton.co.nz'}/home`;
      return;
    }
    
    setLoading(true)
    setTimeout(() => {
      navigate(path)
    }, 500)
  }

  return (
    <header className="bg-slate-50/80 backdrop-blur-sm border-b border-slate-200/50">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-x-6 p-6 lg:px-8" aria-label="Global">
        {/* Logo */}
        <div className="flex lg:flex-1">
          <button onClick={() => handleStart('/')} className="-m-1.5 p-1.5">
            <span className="sr-only">Spot On</span>
            <img src={Logo} alt="Spot On Logo" className="h-12 w-auto cursor-pointer" />
          </button>
        </div>

        {/* Desktop Nav with icons */}
        <div className="hidden lg:flex lg:gap-x-6">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.name}
                onClick={() => handleStart(item.href)}
                className="group flex items-center gap-2 rounded-full px-4 py-1.5 border border-gray-200 font-semibold text-base text-gray-900 hover:bg-accent-purple hover:text-white hover:font-bold transition"
              >
                <Icon className={`h-4 w-4 ${item.color || 'text-gray-600'} group-hover:text-white transition-colors`} />
                {item.name}
              </button>
            );
          })}
        </div>

        {/* Desktop Actions */}
        <div className="flex flex-1 items-center justify-end gap-x-6">
          {!isAuthenticated ? (
            <>
              <button
                onClick={() => handleStart('/login')}
                className="hidden lg:block bg-gray-50 px-3 py-2 rounded-lg font-semibold text-secondary-darkgray shadow-sm ring-secondary-darkgray hover:bg-secondary-darkgray hover:text-white hover:font-bold"
              >
                Login
              </button>
              <button
                onClick={() => handleStart('/getstarted')}
                className="hidden lg:block bg-accent-green px-3 py-2 rounded-md text-white font-semibold shadow-xs hover:bg-accent-red hover:text-white hover:font-bold"
              >
                Join SpotOn
              </button>
            </>
          ) : (
            <button
              onClick={() => handleStart('/authenticated')}
              className="hidden lg:block bg-accent-green px-4 py-2 rounded-md text-white font-semibold shadow-sm hover:bg-accent-red hover:font-extrabold"
            >
              My Dashboard
            </button>
          )}
        </div>

        {/* Drawer Toggle (right side, rounded icon) */}
        <div className="flex lg:hidden">
          <motion.button
            type="button"
            onClick={() => setDrawerOpen(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="-m-2.5 inline-flex items-center justify-center rounded-2xl p-3 border border-gray-300 text-gray-700 bg-white/90 hover:bg-white hover:shadow-md transition-all duration-200"
          >
            <span className="sr-only">Open navigation</span>
            <PanelLeft className="size-5" aria-hidden="true" />
          </motion.button>
        </div>
      </nav>
      {/* Mobile Drawer - Enhanced Modern Design */}
      <Drawer 
        side="right" 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        title="Navigation"
        panelClassName="rounded-l-2xl bg-white"
      >
        <nav className="space-y-2 px-4">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <motion.button
                key={item.name}
                onClick={() => { setDrawerOpen(false); handleStart(item.href); }}
                whileHover={{ scale: 1.02, x: -4 }}
                whileTap={{ scale: 0.98 }}
                className="w-full flex items-center gap-3 text-left px-4 py-3 rounded-full border border-gray-200 font-semibold text-base text-gray-900 hover:bg-accent-purple hover:text-white hover:font-bold transition-all duration-200 bg-white shadow-sm"
              >
                <Icon className={`h-5 w-5 ${item.color || 'text-gray-600'}`} />
                {item.name}
              </motion.button>
            );
          })}
        </nav>
        
        {/* Light separator line */}
        <div className="mx-4 my-6 border-t border-gray-200"></div>
        
        <div className="px-4">
          {!isAuthenticated ? (
            <div className="space-y-3">
              <motion.button 
                onClick={() => { setDrawerOpen(false); handleStart('/login'); }} 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-gray-50 px-3 py-2 rounded-lg font-semibold text-secondary-darkgray shadow-sm hover:bg-secondary-darkgray hover:text-white hover:font-bold transition-all duration-200"
              >
                Login
              </motion.button>
              <motion.button 
                onClick={() => { setDrawerOpen(false); handleStart('/getstarted'); }} 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-accent-green px-3 py-2 rounded-md text-white font-semibold shadow-xs hover:bg-accent-red hover:text-white hover:font-bold transition-all duration-200"
              >
                Join SpotOn
              </motion.button>
            </div>
          ) : (
            <motion.button 
              onClick={() => { setDrawerOpen(false); handleStart('/authenticated'); }} 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full bg-accent-green px-3 py-2 rounded-md text-white font-semibold shadow-xs hover:bg-accent-red hover:text-white hover:font-bold transition-all duration-200"
            >
              My Dashboard
            </motion.button>
          )}
        </div>
      </Drawer>
    </header>
  )
}
