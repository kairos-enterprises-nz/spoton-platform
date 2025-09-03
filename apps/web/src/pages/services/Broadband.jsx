import { useState } from 'react';
import { CheckCircleIcon, SignalIcon, CheckIcon, BoltIcon, ChevronDownIcon } from '@heroicons/react/20/solid';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import Loader from '../../components/Loader';

const broadbandPlans = [
  {
    name: 'Fibre',
    description: 'High-speed fibre broadband for homes that need a solid, reliable connection. Fast installs, stable peak-time speeds, clear pricing.',
    comingSoon: false,
    features: [
      'Basic: 50/10 Mbps — Ideal for light users',
      'Everyday: 300/100 Mbps — Great for families & remote work',
      'Max: 900/400 Mbps — Built for creators, gamers & high-demand use',
      'BYO router or rent from us — your choice',
      'Install ETAs shown at checkout — track your install',
    ],
  },
  {
    name: 'Fixed Wireless',
    description: 'Fast and flexible broadband delivered over 4G/5G. Easy setup, fair pricing, perfect for rentals and short stays.',
    comingSoon: true,
    features: [
      'Delivered over local 4G/5G network',
      'Great for rentals, small homes or short stays',
      'No technician needed — fast install',
      'Stable speeds for streaming, browsing & calls',
      'No loyalty tax — same fair price for everyone',
    ],
  },
  {
    name: 'Rural Broadband',
    description: 'Smart broadband solutions for rural and regional areas. Coverage checks included, fair use policy disclosed upfront.',
    comingSoon: true,
    features: [
      'Runs on 4G/5G towers or satellite',
      'Flexible data options suited to your area',
      'Speeds depend on coverage — we\'ll help check',
      'Supports most modern home needs',
      'Fair use policy disclosed upfront — no bill spikes',
    ],
  },
];

export default function Broadband() {
  const [loading, setLoading] = useState(false);
  const [isAccordionOpen, setIsAccordionOpen] = useState(false);
  const navigate = useNavigate();
  
  const handleStart = () => {
    if (window.location.pathname === '/getstarted') return;
    setLoading(true);
    setTimeout(() => {
      navigate('/getstarted');
    }, 600);
  };
  
  return (
    <div className="relative">
      {loading && <Loader fullscreen size="xl" />}

      {/* === HERO SECTION === */}
      <div className="relative isolate bg-gradient-to-br from-slate-50 via-white to-teal-50/30 py-24 sm:py-32">
        <div aria-hidden="true" className="absolute inset-0 -z-10 overflow-hidden blur-3xl">
          <div
            className="absolute top-0 right-0 aspect-[801/1036] w-[50rem] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-10"
            style={{ clipPath: 'polygon(63.1% 29.5%, 100% 17.1%, ...)' }}
          />
          <div
            className="absolute top-0 left-0 aspect-[801/1036] w-[50rem] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-10 scale-x-[-1]"
            style={{ clipPath: 'polygon(63.1% 29.5%, 100% 17.1%, ...)' }}
          />
        </div>

        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center text-gray-700">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
            Fast where it counts. Fair where it matters.
          </h1>
          <p className="mt-4 text-xl max-w-2xl mx-auto">
            Clear pricing, reliable service, and no loyalty tax. Broadband built on tomorrow's tech — without today's tricks.
          </p>

          <div className="mt-12 grid md:grid-cols-3 gap-4 max-w-4xl mx-auto">
            {[
              {
                icon: <SignalIcon className="h-5 w-5 text-white" />,
                title: 'Reliable speeds',
                desc: 'Consistent performance when you need it.',
              },
              {
                icon: <CheckCircleIcon className="h-5 w-5 text-white" />,
                title: 'No loyalty tax',
                desc: 'Same fair price for new and existing customers.',
              },
              {
                icon: <BoltIcon className="h-5 w-5 text-white" />,
                title: 'Simple setup',
                desc: 'Easy activation with clear next steps.',
              },
            ].map(({ icon, title, desc }, idx) => (
              <div key={idx} className="group relative bg-white border border-slate-200/80 rounded-xl p-4 shadow-md hover:shadow-lg transition-all duration-300 text-center hover:scale-[1.02]">
                <div className="flex items-center justify-center w-10 h-10 mx-auto rounded-lg bg-gradient-to-br from-teal-500 to-slate-600 mb-3 group-hover:scale-110 transition-transform duration-300 shadow-md">
                  {icon}
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-2 group-hover:text-teal-700 transition-colors">{title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-14">
            <button
              onClick={handleStart}
              className="cursor-pointer mt-6 inline-flex rounded-md bg-gradient-to-r from-accent-purple to-purple-500 px-4 py-2.5 text-lg font-semibold text-white shadow-xs hover:from-accent-red hover:to-accent-red hover:font-bold transition focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>

      {/* === PRICING SECTION === */}
      <div className="bg-gray-800 py-24 sm:py-32 px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold text-teal-400 uppercase">Plans</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-5xl">
            Pick your speed. Stay in control.
          </p>
          <p className="mt-4 text-xl text-gray-400 max-w-5xl mx-auto">
            Whether it's fibre, fixed wireless, or rural — we've got a broadband plan with transparent speeds and fair pricing. Stay in control with clear speeds and reliable service that doesn't punish loyalty.
          </p>
        </div>

        {/* Fair Pricing Promise Accordion */}
        <div className="mt-12 max-w-3xl mx-auto">
          <motion.div
            className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl overflow-hidden"
            initial={false}
          >
            <button
              onClick={() => setIsAccordionOpen(!isAccordionOpen)}
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-all duration-300"
            >
              <div>
                <h3 className="text-lg font-bold text-white mb-1">Our Service Promise</h3>
                <p className="text-gray-300 text-xs">Clarity, fairness, and long-term value.</p>
              </div>
              <motion.div
                animate={{ rotate: isAccordionOpen ? 180 : 0 }}
                transition={{ duration: 0.3 }}
                className="ml-4 flex-shrink-0"
              >
                <ChevronDownIcon className="h-5 w-5 text-teal-400" />
              </motion.div>
            </button>
            
            <AnimatePresence>
              {isAccordionOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.4, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-4 border-t border-white/10">
                    <div className="pt-4 space-y-3">
                      <div className="grid md:grid-cols-2 gap-4 text-left">
                        <div>
                          <h4 className="text-base font-semibold text-white mb-2 text-left">No Tricks Service</h4>
                          <ul className="space-y-1 text-xs text-gray-300">
                            <li className="flex items-start gap-2">
                              <CheckIcon className="h-3 w-3 text-teal-400 mt-0.5 flex-shrink-0" />
                              <span>Same price for everyone</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <CheckIcon className="h-3 w-3 text-teal-400 mt-0.5 flex-shrink-0" />
                              <span>No loyalty tax</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <CheckIcon className="h-3 w-3 text-teal-400 mt-0.5 flex-shrink-0" />
                              <span>Clear information upfront</span>
                            </li>
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-base font-semibold text-white mb-2 text-left">Broadband Service Promise</h4>
                          <p className="text-xs text-gray-300 leading-relaxed text-left">
                            Broadband with reliable speeds, transparent pricing, and service that delivers long-term value.
                          </p>
                        </div>
                      </div>
                      <div className="pt-2 flex flex-col sm:flex-row gap-2">
                        <a
                          href="/servicepromise"
                          className="inline-flex items-center justify-center px-4 py-2 bg-teal-500 hover:bg-teal-400 text-white font-semibold text-sm rounded-lg transition-all duration-300"
                        >
                          Learn More
                        </a>
                        <button
                          onClick={handleStart}
                          className="inline-flex items-center justify-center px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-semibold text-sm rounded-lg transition-all duration-300 border border-white/20"
                        >
                          Sign Me Up
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
          {broadbandPlans.map((plan, index) => (
            <div
              key={plan.name}
              className={`group relative overflow-hidden rounded-3xl p-8 transition-all duration-300 hover:scale-[1.02] ${
                index === 0 
                  ? 'bg-gradient-to-br from-teal-500 to-slate-600 text-white shadow-2xl ring-2 ring-teal-400/30' 
                  : plan.comingSoon 
                    ? 'bg-white/5 backdrop-blur-sm border border-white/10 opacity-75'
                    : 'bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 shadow-xl'
              }`}
            >
              {/* Popular Badge */}
              {index === 0 && (
                <div className="absolute top-4 right-4 z-20">
                  <span className="bg-slate-800 text-white text-xs font-medium px-2 py-1 rounded-md shadow-sm">
                    POPULAR
                  </span>
                </div>
              )}


              
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-3">{plan.name}</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{plan.description}</p>
              </div>

              <ul className="space-y-3 mb-8 text-left">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm text-gray-300">
                    <CheckIcon className="h-4 w-4 text-teal-400 mt-1 flex-shrink-0" />
                    <span className="leading-relaxed text-left">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-auto">
                {plan.comingSoon ? (
                  <div className="w-full rounded-xl px-4 py-3 text-sm font-semibold bg-slate-800/80 border border-teal-400/30 text-teal-200 text-center cursor-not-allowed relative overflow-hidden backdrop-blur-sm">
                    <div className="absolute inset-0 bg-gradient-to-r from-teal-500/8 to-slate-500/5"></div>
                    <span className="relative flex items-center justify-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-300/80"></div>
                      Coming Soon
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-300/60"></div>
                    </span>
                  </div>
                ) : (
                  <button
                    onClick={handleStart}
                    className={`w-full rounded-xl px-4 py-3 text-sm font-bold transition-all duration-300 ${
                      index === 0
                        ? 'bg-white text-slate-900 hover:bg-gray-100 shadow-lg hover:ring-2 hover:ring-teal-400/60 hover:ring-offset-2 hover:ring-offset-slate-800'
                        : 'bg-gradient-to-r from-teal-500 to-slate-600 text-white hover:from-teal-400 hover:to-slate-500 shadow-lg hover:ring-2 hover:ring-teal-400/60 hover:ring-offset-2 hover:ring-offset-slate-800'
                    }`}
                  >
                    Get Started
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>


    </div>
  );
}
