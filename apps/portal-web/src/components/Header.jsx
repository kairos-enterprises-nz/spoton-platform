import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
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

        {/* Desktop Nav */}
        <div className="hidden lg:flex lg:gap-x-18">
          {navigation.map((item) => (
            <button
              key={item.name}
              onClick={() => handleStart(item.href)}
              className="rounded-full px-4 py-1.5 border-transparent font-semibold text-lg text-gray-900 border-2 hover:bg-accent-purple hover:text-white hover:font-bold cursor-pointer"
            >
              {item.name}
            </button>
          ))}
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
              onClick={() => handleStart('/')}
              className="hidden lg:block bg-accent-green px-4 py-2 rounded-md text-white font-semibold shadow-sm hover:bg-accent-red hover:font-extrabold"
            >
              My Dashboard
            </button>
          )}
        </div>

        {/* Mobile Hamburger */}
        <div className="flex lg:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-700"
          >
            <span className="sr-only">Open main menu</span>
            <Bars3Icon className="size-6" aria-hidden="true" />
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      <Dialog open={mobileMenuOpen} onClose={setMobileMenuOpen} className="lg:hidden">
        <div className="fixed inset-0 z-40 bg-black/20" />
        <Dialog.Panel className="absolute top-0 right-0 z-50 w-full h-full max-h-screen bg-white px-6 py-6 overflow-y-auto sm:max-w-sm sm:ring-1 sm:ring-gray-900/10">
          {/* Logo */}
          <div className="flex flex-col items-center gap-y-4">
            <button onClick={() => handleStart('/')} className="p-1.5">
              <img src={Logo} alt="Spot On Logo" className="h-12 w-auto cursor-pointer" />
            </button>
          </div>

          <div className="mt-6 divide-y divide-gray-500/10 text-center">
            {/* Nav Items */}
            <div className="space-y-4 py-6 flex flex-col items-center">
              {navigation.map((item) => (
                <button
                  key={item.name}
                  onClick={() => {
                    setMobileMenuOpen(false)
                    handleStart(item.href)
                  }}
                  className="w-fit rounded-full px-4 py-2 text-lg font-semibold text-gray-900 hover:bg-accent-purple hover:text-white hover:font-bold"
                >
                  {item.name}
                </button>
              ))}
            </div>

            {/* Auth Actions */}
            <div className="py-6 space-y-4 flex flex-col items-center">
              {!isAuthenticated ? (
                <>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false)
                      handleStart('/login')
                    }}
                    className="w-fit rounded-full bg-gray-50 px-4 py-2 text-sm font-semibold text-secondary-darkgray shadow-sm ring-secondary-darkgray hover:bg-secondary-darkgray hover:text-white hover:font-bold"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false)
                      handleStart('/getstarted')
                    }}
                    className="w-fit rounded-md bg-accent-green px-3 py-2 text-sm font-semibold text-white shadow-xs hover:bg-accent-red hover:font-bold"
                  >
                    Join SpotOn
                  </button>
                </>
              ) : (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false)
                    handleStart('/')
                  }}
                  className="w-fit rounded-md bg-accent-green px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-accent-red"
                >
                  My Dashboard
                </button>
              )}
              {/* Close Button */}
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="w-full mt-6 text-sm text-gray-500 underline"
              >
                <XMarkIcon className="inline bg-gray-100 hover:bg-gray-400 hover:text-white rounded-2xl h-12 w-12 px-2 py-2" />
              </button>
            </div>
          </div>
        </Dialog.Panel>
      </Dialog>
    </header>
  )
}
