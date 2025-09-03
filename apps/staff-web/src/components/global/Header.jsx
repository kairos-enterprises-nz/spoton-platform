import { useState } from 'react'
import Drawer from '../Drawer.jsx'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { PanelLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useLoader } from '../../context/LoaderContext'
import Logo from '../../assets/utilitycopilot-logo.webp'
import { useAuth } from '../../hooks/useAuth'

const navigation = [
  { name: 'Power', href: '/power' },
  { name: 'Broadband', href: '/broadband' },
  { name: 'Mobile', href: '/mobile' },
  { name: 'Support', href: '/support' },
]

export default function Header() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const { setLoading } = useLoader()
  const { isAuthenticated } = useAuth()

  const handleStart = (path) => {
    if (path === window.location.pathname) return
    setLoading(true)
    setTimeout(() => {
      navigate(path)
    }, 500)
  }

  return (
    <header className="bg-white">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-x-6 p-6 lg:px-8" aria-label="Global">
        {/* Logo */}
        <div className="flex lg:flex-1">
          <button onClick={() => handleStart('/')} className="-m-1.5 p-1.5">
            <span className="sr-only">Spot On</span>
            <img src={Logo} alt="Spot On Logo" className="h-12 w-auto cursor-pointer" />
          </button>
        </div>

        {/* Desktop Nav removed to unify drawer-only layout */}

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

        {/* Drawer Toggle */}
        <div className="flex lg:hidden">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-700"
          >
            <span className="sr-only">Open navigation</span>
            <PanelLeft className="size-6" aria-hidden="true" />
          </button>
        </div>
      </nav>
      {/* Mobile Drawer */}
      <Drawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} title="Menu">
        <div className="mb-3">
          <button onClick={() => { setDrawerOpen(false); handleStart('/'); }} className="p-1.5">
            <img src={Logo} alt="Spot On Logo" className="h-10 w-auto" />
          </button>
        </div>
        <nav className="space-y-1">
          {navigation.map((item) => (
            <button
              key={item.name}
              onClick={() => { setDrawerOpen(false); handleStart(item.href); }}
              className="w-full text-left px-3 py-2 rounded-md text-gray-700 hover:bg-gray-50"
            >
              {item.name}
            </button>
          ))}
        </nav>
        <div className="mt-4 border-t pt-3">
          {!isAuthenticated ? (
            <div className="space-y-2">
               <button onClick={() => { setDrawerOpen(false); handleStart('/login'); }} className="w-full rounded-md bg-gray-50 px-3 py-2 text-sm font-semibold text-secondary-darkgray shadow-sm ring-1 ring-gray-200 hover:bg-secondary-darkgray hover:text-white">
                Login
              </button>
              <button onClick={() => { setDrawerOpen(false); handleStart('/getstarted'); }} className="w-full rounded-md bg-accent-green px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-accent-red">
                Join SpotOn
              </button>
            </div>
          ) : (
            <button onClick={() => { setDrawerOpen(false); handleStart('/authenticated'); }} className="w-full rounded-md bg-accent-green px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-accent-red">
              My Dashboard
            </button>
          )}
        </div>
      </Drawer>
    </header>
  )
}
