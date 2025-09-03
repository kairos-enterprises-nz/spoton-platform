import Logo from '../../assets/spoton-logo-reversed.webp'
import { useNavigate } from 'react-router-dom';
import { useLoader } from '../../context/LoaderContext'

const navigation = {
  solutions: [
    { name: 'Power', href: '/power' },
    { name: 'Broadband', href: '/broadband' },
    { name: 'Mobile', href: '/mobile' },
  ],
  support: [
    { name: 'Browse Help Topics', href: '/support' },
    { name: 'General FAQs', href: '/support/general' },
    { name: 'Billing & Payments', href: '/support/billing' },
    { name: 'Technical Support', href: '/support/technical' },
    { name: 'Contact Us', href: '/support/contact' },
  ],
  legal: [
    { name: 'Consumer Care Policy', href: '/legal/consumercarepolicy' },
    // { name: 'Power', href: '/legal/powerterms' }, // Disabled - service not available
    { name: 'Broadband', href: '/legal/broadbandterms' }, 
    // { name: 'Mobile', href: '/legal/mobileterms' }, // Disabled - service not available
  ],
};

export default function Footer() {
  const navigate = useNavigate();
  const { setLoading } = useLoader();

  const handleNavigate = (path) => {
    if (window.location.pathname === path) return;
    setLoading(true);
    setTimeout(() => {
      navigate(path);
    }, 400);
  };

  return (
    <footer className="bg-gray-800">
      <div className="mx-auto max-w-7xl px-6 py-16 sm:py-24 lg:px-8 lg:py-24">
        <div className="xl:grid xl:grid-cols-3 xl:gap-8">
          <button onClick={() => handleNavigate('/')} className="inline-block cursor-pointer">
            <img
              alt="SpotOn"
              src={Logo}
              className="h-12"
            />
          </button>

          <div className="mt-16 grid grid-cols-2 gap-8 xl:col-span-2 xl:mt-0">
            <div className="md:grid md:grid-cols-2 md:gap-8 text-left">
              <div>
                <h3 className="text-md/6 font-semibold text-accent-green">Services</h3>
                <ul role="list" className="mt-6 space-y-2">
                  {navigation.solutions.map((item) => (
                    <li key={item.name}>
                      <button
                        onClick={() => handleNavigate(item.href)}
                        className="text-sm text-white hover:text-primary-turquoise hover:font-bold cursor-pointer"
                      >
                        {item.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-10 md:mt-0 text-left">
                <h3 className="text-md/6 font-semibold text-accent-green">Support</h3>
                <ul role="list" className="mt-6 space-y-2">
                  {navigation.support.map((item) => (
                    <li key={item.name}>
                      <button
                        onClick={() => handleNavigate(item.href)}
                        className="text-sm text-white hover:text-primary-turquoise hover:font-bold cursor-pointer"
                      >
                        {item.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="md:grid md:grid-cols-1 md:gap-8 text-left">
              <div className="mt-10 md:mt-0">
                <h3 className="text-md/6 font-semibold text-accent-green">Legal</h3>
                <ul role="list" className="mt-6 space-y-2">
                  {navigation.legal.map((item) => (
                    <li key={item.name}>
                      <button
                        onClick={() => handleNavigate(item.href)}
                        className="text-sm text-white hover:text-primary-turquoise hover:font-bold cursor-pointer"
                      >
                        {item.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-100/50 pt-8 md:flex md:items-center md:justify-between">
          <p className="mt-8 text-sm/6 text-gray-200 md:order-0 md:mt-0">
            &copy; 2025 SpotOn. All rights reserved.
          </p>
          <div className="mt-8 md:mt-0 flex space-x-6">
            <button
              onClick={() => handleNavigate('/legal/termsofservice')}
              className="text-sm text-gray-200 hover:text-primary-turquoise hover:font-bold cursor-pointer"
            >
              Terms of Service
            </button>
            <button
              onClick={() => handleNavigate('/legal/privacypolicy')}
              className="text-sm text-gray-200 hover:text-primary-turquoise hover:font-bold cursor-pointer"
            >
              Privacy Policy
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}
