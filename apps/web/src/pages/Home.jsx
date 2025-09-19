import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles, Zap, Shield, Smartphone, Star, CheckCircle, DollarSign, Clock } from 'lucide-react';

import Loader from '../components/Loader';

import GridImage1 from '../assets/GridImage1.webp';
import GridImage2 from '../assets/GridImage2.webp';
import GridImage3 from '../assets/GridImage3.webp';
import GridImage4 from '../assets/GridImage4.webp';
import GridImage5 from '../assets/GridImage5.webp';
import PricingIcon from '../assets/icons/pricing.webp';
import OptionsIcon from '../assets/icons/options.webp';
import SupportIcon from '../assets/icons/support.webp';
import PowerIcon from '../assets/icons/power.webp';
import BroadbandIcon from '../assets/icons/broadband.webp';
import PowerImage from '../assets/powerplan.webp';
import BroadbandImage from '../assets/broadbandplan.webp';
import MobileImage from '../assets/mobileplan.webp';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleStart = (path = '/getstarted') => {
    setLoading(true);
    setTimeout(() => {
      navigate(path);
    }, 1000);
  };

  const features = [
    {
      title: 'No loyalty tax',  
      icon: <DollarSign className="w-6 h-6 text-white" />,
      description: 'Same fair price for everyone. New or long-time customer, you pay the same.',
    },
    {
      title: 'Digital experience',
      icon: <Clock className="w-6 h-6 text-white" />,
      description: 'Sign up in minutes, manage in seconds. One dashboard for everything.',
    },
    {
      title: 'No promo traps',
      icon: <Shield className="w-6 h-6 text-white" />,
      description: 'What you see is what you pay. No honeymoon rates, no hidden hikes.',
    },
  ];

  const services = [
    {
      title: 'Power',
      icon: <img src={PowerIcon} alt="Power icon" className="w-8 h-8" />,
      image: PowerImage,
      features: [
        'Smarter power, minus the surprises',
        'Clear tariff model with usage insights',
        'Switch in minutes, clear daily charges',
      ],
    },
    {
      title: 'Broadband',
      icon: <img src={BroadbandIcon} alt="Broadband icon" className="w-8 h-8" />,
      image: BroadbandImage,
      features: [
        'Fast where it counts, fair where it matters',
        'Typical evening speeds published monthly',
        'Install timeframes with ETAs, track your install',
      ],
    },
    {
      title: 'Mobile',
      icon: <Smartphone className="w-8 h-8 text-white" />,
      image: MobileImage,
      features: [
        'Mobile that respects your time and wallet',
        'Quick eSIM setup, easy controls',
        'No price jump after month three',
      ],
    },
  ];

  const stats = [

  ];
  const stats1 = [
    { number: '50k+', label: 'Happy Customers' },
    { number: '99.9%', label: 'Uptime Guarantee' },
    { number: '24/7', label: 'Local Support' },
    { number: '5★', label: 'Customer Rating' },
  ];

  return (
    <>
      {loading && <Loader fullscreen />}
      <div className="bg-white overflow-hidden">
        <main>
          {/* Enhanced Hero Section */}
          <div className="relative isolate">
            {/* Simplified background patterns using theme colors */}
            <div className="absolute inset-0 -z-10 overflow-hidden">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full">
                <div className="absolute top-20 left-20 w-72 h-72 bg-gradient-to-r from-teal-400/10 to-teal-600/10 rounded-full blur-3xl animate-pulse" />
                <div className="absolute top-40 right-20 w-96 h-96 bg-gradient-to-r from-slate-400/10 to-slate-600/10 rounded-full blur-3xl animate-pulse delay-1000" />
                <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-gradient-to-r from-teal-500/10 to-slate-500/10 rounded-full blur-3xl animate-pulse delay-2000" />
              </div>
            </div>

            {/* Refined grid pattern */}
            <svg
              aria-hidden="true"
              className="absolute inset-x-0 top-0 -z-10 h-[64rem] w-full [mask-image:radial-gradient(32rem_32rem_at_center,white,transparent)] stroke-slate-200/30"
            >
              <defs>
                <pattern
                  x="50%"
                  y={-1}
                  id="grid-pattern"
                  width={200}
                  height={200}
                  patternUnits="userSpaceOnUse"
                >
                  <path d="M.5 200V.5H200" fill="none" />
                </pattern>
              </defs>
              <rect fill="url(#grid-pattern)" width="100%" height="100%" strokeWidth={0} />
            </svg>

            <div className="overflow-hidden">
              <div className="mx-auto max-w-7xl px-6 pt-36 pb-32 sm:pt-60 lg:px-8 lg:pt-32">
                <div className="mx-auto max-w-2xl gap-x-14 lg:mx-0 lg:flex lg:max-w-none lg:items-center">
                  <div className={`relative w-full lg:max-w-xl lg:shrink-0 xl:max-w-2xl transition-all duration-1000 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
                    {/* Wrap badge and headline for left alignment */}
                    <div className="flex flex-col items-start">
                      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-teal-50 to-slate-50 border border-teal-200/50 mb-8">
                        <div className="relative">
                          <Sparkles className="w-5 h-5 text-teal-600 animate-pulse" />
                          <div className="absolute inset-0 animate-ping">
                            <Sparkles className="w-5 h-5 text-teal-400 opacity-40" />
                          </div>
                        </div>
                        <span className="text-sm font-medium text-slate-700">Tomorrow&apos;s utilities delivered today</span>
                      </div>
                      <h1 className="text-5xl font-bold tracking-tight text-left text-pretty text-slate-900 sm:text-7xl">
                        <span className="relative">
                          <span className="bg-gradient-to-r from-teal-600 to-slate-600 bg-clip-text text-transparent">
                            Digital-first experience.
                          </span>
                          <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-teal-400 to-slate-400 rounded-full transform scale-x-0 animate-[scaleX_1s_ease-out_0.5s_forwards] origin-left" />
                        </span>
                        <br />
                        <span className="text-slate-900">Old-school fairness.</span>
                      </h1>
                    </div>
                    
                    <p className="mt-8 text-base text-left text-slate-600 leading-relaxed">
                      Power, broadband, and mobile — delivered with clarity, fairness, and long-term value.
                    </p>


                    {/* Refined CTA section */}
                    <div className="mt-12 flex flex-col items-start gap-6">
                      <button
                        onClick={() => handleStart('/getstarted')}
                        className="group relative overflow-hidden rounded-xl bg-gradient-to-r from-teal-600 to-slate-600 px-8 py-4 text-lg font-semibold text-white shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-slate-600 to-teal-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        <span className="relative flex items-center gap-2">
                          Get Started <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </span>
                      </button>
                      
                      <div className="flex items-center gap-4 text-sm text-slate-500 mt-4">
                        <div className="flex items-center gap-1">
                          <Shield className="w-4 h-4 text-teal-500" />
                          <span>No loyalty tax</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Zap className="w-4 h-4 text-teal-500" />
                          <span>Sign up in minutes</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Refined image grid */}
                  <div className={`mt-14 flex justify-end gap-8 sm:-mt-44 sm:justify-start sm:pl-20 lg:mt-0 lg:pl-0 transition-all duration-1000 delay-300 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
                    <div className="ml-auto w-44 flex-none space-y-8 pt-32 sm:ml-0 sm:pt-80 lg:order-last lg:pt-36 xl:order-none xl:pt-80">
                      <div className="group relative">
                        <img
                          alt=""
                          src={GridImage1}
                          className="aspect-2/3 w-full rounded-2xl bg-slate-900/5 object-cover shadow-xl group-hover:shadow-2xl transition-all duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 rounded-2xl ring-1 ring-slate-900/10 ring-inset group-hover:ring-teal-500/50 transition-all duration-300" />
                      </div>
                    </div>
                    <div className="mr-auto w-44 flex-none space-y-8 sm:mr-0 sm:pt-52 lg:pt-36">
                      <div className="group relative">
                        <img
                          alt=""
                          src={GridImage2}
                          className="aspect-2/3 w-full rounded-2xl bg-slate-900/5 object-cover shadow-xl group-hover:shadow-2xl transition-all duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 rounded-2xl ring-1 ring-slate-900/10 ring-inset group-hover:ring-teal-500/50 transition-all duration-300" />
                      </div>
                      <div className="group relative">
                        <img
                          alt=""
                          src={GridImage3}
                          className="aspect-2/3 w-full rounded-2xl bg-slate-900/5 object-cover shadow-xl group-hover:shadow-2xl transition-all duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 rounded-2xl ring-1 ring-slate-900/10 ring-inset group-hover:ring-teal-500/50 transition-all duration-300" />
                      </div>
                    </div>
                    <div className="w-44 flex-none space-y-8 pt-32 sm:pt-0">
                      <div className="group relative">
                        <img
                          alt=""
                          src={GridImage4}
                          className="aspect-2/3 w-full rounded-2xl bg-slate-900/5 object-cover shadow-xl group-hover:shadow-2xl transition-all duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 rounded-2xl ring-1 ring-slate-900/10 ring-inset group-hover:ring-teal-500/50 transition-all duration-300" />
                      </div>
                      <div className="group relative">
                        <img
                          alt=""
                          src={GridImage5}
                          className="aspect-2/3 w-full rounded-2xl bg-slate-900/5 object-cover shadow-xl group-hover:shadow-2xl transition-all duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 rounded-2xl ring-1 ring-slate-900/10 ring-inset group-hover:ring-teal-500/50 transition-all duration-300" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Refined Features Section */}
          <section className="relative py-32 px-6 sm:px-8 lg:px-12 overflow-hidden">
            {/* Cleaner background */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-teal-50/30" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(20,184,166,0.05),transparent)] opacity-70" />
            
            <div className="relative mx-auto max-w-6xl text-center">
              <div className="mb-20">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200/50 mb-8">
                  <Star className="w-4 h-4 text-teal-600" />
                  <span className="text-sm font-medium text-slate-700">What makes us different</span>
                </div>
                
                <h2 className="text-5xl font-black tracking-tight text-slate-900 mb-6">
                  Why Choose <span className="bg-gradient-to-r from-teal-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">SpotOn</span>?
                </h2>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
                  We deliver utilities the modern way: digital systems, instant signup, one clean dashboard, and honest pricing. No loyalty tax. No promo games. Whether it's power, broadband, or mobile, you'll spend less time managing and never pay more for staying.
                </p>
              </div>

              <div className="mb-20">
                <h3 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent mb-16">
                  Tomorrow&apos;s expectations, delivered today.
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {features.map(({ title, icon, description }, index) => (
                    <div
                      key={index}
                      onClick={() => handleStart('/getstarted')}
                      className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 text-center hover:scale-[1.02] cursor-pointer"
                    >
                      <div className="flex items-center justify-center w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-teal-500 to-slate-600 mb-4 shadow-lg">
                        {icon}
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-3">
                        {title}
                      </h3>
                      <p className="text-sm text-slate-600 leading-relaxed">
                        {description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Enhanced Services Section with Mobile */}
          <section className="relative py-32 px-6 sm:px-8 lg:px-12 overflow-hidden">
            {/* Refined dark background */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_30%,rgba(20,184,166,0.15),transparent)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_70%,rgba(148,163,184,0.1),transparent)]" />
            
            <div className="relative mx-auto max-w-7xl text-center">
              <div className="mb-20">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 mb-8">
                  <CheckCircle className="w-4 h-4 text-teal-400" />
                  <span className="text-sm font-medium text-white">Our Services</span>
                </div>
                
                <h2 className="text-5xl font-black tracking-tight text-white mb-6">
                  Choose what you need.{' '}
                  <span className="bg-gradient-to-r from-teal-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Add what fits.
                  </span>
                </h2>
                <p className="text-xl text-slate-300 max-w-4xl mx-auto leading-relaxed">
                  Start with one service or bundle them together. Our flexible approach grows with your needs.
                </p>
              </div>
              
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
                {services.map(({ title, features, icon, image }, i) => (
                  <div
                    key={i}
                    className={`group relative bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl overflow-hidden transition-all duration-500 ${
                      title === 'Power' || title === 'Mobile' 
                        ? 'hover:bg-slate-700/20 hover:border-slate-500/40 hover:scale-[1.01] hover:shadow-lg hover:shadow-teal-500/10' 
                        : 'hover:bg-white/15 hover:scale-105 hover:shadow-2xl'
                    }`}
                  >
                    {/* Image with consistent overlay */}
                    <div className="relative h-48 w-full overflow-hidden">
                      <img
                        src={image}
                        alt={`${title} preview`}
                        className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-teal-600/20 to-slate-600/20 group-hover:from-teal-600/30 group-hover:to-slate-600/30 transition-all duration-500" />
                    </div>
                    
                    <div className="p-6">
                      <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-600 to-slate-600 p-2.5 shadow-lg transition-transform duration-300 group-hover:rotate-3 group-hover:scale-110">
                          <div className="flex items-center justify-center w-full h-full bg-white/20 rounded-xl backdrop-blur-md">
                            {icon}
                          </div>
                        </div>
                        <h3 className="text-2xl font-bold text-white group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-teal-400 group-hover:to-slate-300 group-hover:bg-clip-text transition-all duration-300">
                          {title}
                        </h3>
                      </div>
                      
                      <ul className="space-y-3 text-slate-300 mb-8 text-left">
                        {features.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-3 leading-relaxed text-sm">
                            <div className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-teal-400 to-slate-400 mt-2 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                      
                      {title === 'Power' || title === 'Mobile' ? (
                        <div className="w-full py-3 px-6 rounded-2xl bg-slate-800/80 border border-teal-400/30 text-teal-200 font-semibold text-center cursor-not-allowed relative overflow-hidden backdrop-blur-sm">
                          <div className="absolute inset-0 bg-gradient-to-r from-teal-500/8 to-slate-500/5"></div>
                          <span className="relative flex items-center justify-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-teal-300/80"></div>
                            Coming Soon
                            <div className="w-1.5 h-1.5 rounded-full bg-teal-300/60"></div>
                          </span>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleStart(`/${title.toLowerCase()}`)}
                          className="group/btn w-full py-3 px-6 rounded-2xl bg-gradient-to-r from-teal-600 to-slate-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                        >
                          <span className="flex items-center justify-center gap-2">
                            Explore {title} Plans
                            <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
                          </span>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Final CTA with consistent theming */}
              <div className="text-center">
                <button
                  onClick={() => handleStart('/getstarted')}
                  className="group relative inline-flex items-center gap-3 text-white bg-gradient-to-r from-teal-600 to-slate-600 px-10 py-5 rounded-2xl text-xl font-bold shadow-2xl hover:shadow-3xl transform hover:scale-105 transition-all duration-300 overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-slate-600 to-teal-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <span className="relative flex items-center gap-3">
                    <Sparkles className="w-6 h-6 group-hover:rotate-12 transition-transform" />
                    Find the right plan for you
                    <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
                  </span>
                </button>
              </div>
            </div>
          </section>
        </main>
      </div>

      <style>{`
        @keyframes scaleX {
          to {
            transform: scaleX(1);
          }
        }
      `}</style>
    </>
  );
}