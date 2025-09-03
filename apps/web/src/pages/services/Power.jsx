import { useState } from 'react';
import { CheckCircleIcon, CheckIcon, BoltIcon, CurrencyDollarIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/20/solid';
import { ChartNoAxesCombinedIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import Loader from '../../components/Loader';

const plans = [
  {
    name: 'Spot Pass',
    description: 'Pay the real-time wholesale market rate for power. Great for tech-savvy users who want to ride the market.',
    comingSoon: true,
    features: [
      'Wholesale rate + transparent service fee',
      'Dynamic pricing based on usage time',
      'Works brilliantly with solar/battery setups',
      'Clear breakdown on every bill — no surprises',
    ],
  },
  {
    name: 'Shift Saver',
    description: 'Time-based pricing for more control. Cheaper at off-peak hours — perfect for EV charging and smart usage.',
    comingSoon: true,
    features: [
      'Rate varies by time of day',
      'Encourages smart usage habits',
      'Cancel with notice — upgrade/downgrade anytime',
      'Ideal for modern households with flexible schedules',
    ],
  },
  {
    name: 'Flat Sure',
    description: 'Lock in a consistent rate for easier budgeting. Perfect for households that want predictability.',
    comingSoon: true,
    features: [
      'Flat rate per kWh — simple and clear',
      'No bill shock, no monthly surprises',
      'Cancel with notice — upgrade/downgrade anytime',
      'Great for stable usage patterns',
    ],
  },
];

export default function Power() {
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
            style={{ clipPath: 'polygon(63.1% 29.5%, 100% 17.1%, 84.9% 44.1%, 45.3% 78.2%, 27.8% 48.9%, 3.1% 31.8%, 17.9% 17.1%, 36.1% 3.2%, 63.1% 29.5%)' }}
          />
          <div
            className="absolute top-0 left-0 aspect-[801/1036] w-[50rem] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-10 scale-x-[-1]"
            style={{ clipPath: 'polygon(63.1% 29.5%, 100% 17.1%, 84.9% 44.1%, 45.3% 78.2%, 27.8% 48.9%, 3.1% 31.8%, 17.9% 17.1%, 36.1% 3.2%, 63.1% 29.5%)' }}
          />
        </div>

        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center text-gray-700">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
            Smarter power, minus the surprises.
          </h1>
          <p className="mt-4 text-xl max-w-4xl mx-auto">
            Hassle-free switching, usage insights, and a fair tariff model you can actually understand.
          </p>

          <div className="mt-12 grid md:grid-cols-3 gap-4 max-w-4xl mx-auto">
            {[
              {
                icon: <CurrencyDollarIcon className="h-5 w-5 text-white" />,
                title: 'Tariffs to suit your case',
                desc: 'Different tariffs for different purposes, all clearly explained.',
              },
              {
                icon: <CheckCircleIcon className="h-5 w-5 text-white" />,
                title: 'Usage insights',
                desc: 'Live usage data and clear daily charges.',
              },
              {
                icon: <BoltIcon className="h-5 w-5 text-white" />,
                title: 'No loyalty tax',
                desc: 'Same fair pricing across all tariffs.',
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

          {/* Get Started button removed - service not yet available */}
        </div>
      </div>

      {/* === PLANS SECTION === */}
      <div className="bg-gray-800 py-24 sm:py-32 px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold text-teal-400 uppercase">Plans</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-5xl">
            Choose your tariff. Control your costs.
          </p>
          <p className="mt-4 text-xl text-gray-400">
            Whether you prefer market rates, time-based pricing, or fixed costs — we have a fair tariff for you.
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
                          <h4 className="text-base font-semibold text-white mb-2 text-left">Power Service Promise</h4>
                          <p className="text-xs text-gray-300 leading-relaxed text-left">
                            Power plans with transparent tariffs, real-time insights, and fair pricing that delivers long-term value.
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
                        {/* Sign Me Up button hidden until service is available */}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={plan.name}
              className={`group relative overflow-hidden rounded-3xl p-8 transition-all duration-300 hover:scale-[1.02] ${
                plan.comingSoon 
                  ? 'bg-white/5 backdrop-blur-sm border border-white/10 opacity-75'
                  : 'bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/15 shadow-xl'
              }`}
            >



              
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
                      index === 1
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
