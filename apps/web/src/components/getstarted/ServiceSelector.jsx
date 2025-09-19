import { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { Zap, Wifi, Smartphone } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const SERVICE_CONFIG = [
  {
    id: "electricity",
    icon: <Zap className="w-4 h-4 sm:w-6 sm:h-6 text-accent-lightturquoise" />,
    label: "Electricity",
    description: "Power your home",
    color: "from-[#40E0D0] to-[#4eb14e]",
    available: false, // Coming soon
  },
  {
    id: "broadband",
    icon: <Wifi className="w-4 h-4 sm:w-6 sm:h-6 text-accent-purple" />,
    label: "Broadband",
    description: "High-speed internet",
    color: "from-[#b14eb1] to-[#b14e4e]",
    available: true, // Available now
  },
  {
    id: "mobile",
    icon: <Smartphone className="w-4 h-4 sm:w-6 sm:h-6 text-accent-blue" />,
    label: "Mobile",
    description: "Fair mobile plans",
    color: "from-[#4e80b1] to-[#40E0D0]",
    available: false, // Coming soon
  },
];

export default function ServiceSelector({ onServicesSelected, value }) {
  const [selectedServices, setSelectedServices] = useState(value || {
    electricity: false,
    broadband: false,
    mobile: false,
  });

  useEffect(() => {
    console.log('[ServiceSelector] Services changed:', selectedServices);
    onServicesSelected(selectedServices);
  }, [selectedServices, onServicesSelected]);

  const handleServiceToggle = (serviceId) => {
    // Find the service config to check if it's available
    const serviceConfig = SERVICE_CONFIG.find(s => s.id === serviceId);
    
    // Don't allow toggling unavailable services
    if (!serviceConfig?.available) {
      return;
    }
    
    setSelectedServices((prev) => ({
      ...prev,
      [serviceId]: !prev[serviceId],
    }));
  };

  return (
    <div className="w-full max-w-2xl mx-auto px-2 sm:px-0">
      <div className="text-center mb-4 sm:mb-6">
        <h2 className="text-lg sm:text-xl font-bold mb-2">What services are you interested in?</h2>
        <p className="text-slate-300 text-xs sm:text-sm">Select one or more services to get started</p>
      </div>

      <div className="px-0 sm:px-6 md:px-12 py-3 items-center grid grid-cols-3 gap-1 sm:gap-4 md:gap-6 justify-center">
        <AnimatePresence>
          {SERVICE_CONFIG.map((service) => (
            <motion.button
              key={service.id}
              onClick={() => handleServiceToggle(service.id)}
              disabled={!service.available}
              className={`relative group p-2 sm:p-2 rounded-xl border-1 transition-all duration-300 min-h-[90px] sm:min-h-[120px] flex flex-col items-center justify-center w-full ${
                !service.available
                  ? "bg-slate-800/40 border-slate-600/50 cursor-not-allowed opacity-75 hover:opacity-85 hover:border-teal-500/30"
                  : selectedServices[service.id]
                  ? `bg-accent-lightturquoise/20 shadow-lg scale-105 border-slate-700`
                  : "bg-slate-800/50 hover:bg-slate-700/50 border-slate-700"
              }`}
              whileHover={service.available ? { scale: 1.02 } : {}}
              whileTap={service.available ? { scale: 0.98 } : {}}
            >
              {/* Tick mark for selected */}
              {selectedServices[service.id] && service.available && (
                <span className="absolute top-1 right-1 sm:top-2 sm:right-2 z-20 bg-accent-green/80 rounded-full p-0.5 sm:p-1 shadow">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-1.5 sm:h-2 w-1.5 sm:w-2 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              )}

              {/* Coming Soon badge for unavailable services */}
              {!service.available && (
                <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 z-30">
                  <div className="bg-slate-700/95 border border-teal-400/50 rounded-md px-2 py-0.5 text-[8px] font-semibold text-teal-200 shadow-md backdrop-blur-sm min-w-[48px] text-center whitespace-nowrap">
                    COMING SOON
                  </div>
                </div>
              )}

              {/* Background gradient overlay */}
              <div
                className={`absolute inset-0 bg-gradient-to-br ${service.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}
              />

              {/* Content */}
              <div className="relative z-10 flex flex-col items-center text-center">
                <div
                  className={`p-2 sm:p-3 rounded-full mb-0.5 sm:mb-1 transition-colors duration-300 ${
                    selectedServices[service.id]
                      ? "bg-slate-700/50"
                      : "bg-slate-700/50 group-hover:bg-slate-600/50"
                  }`}
                >
                  {service.icon}
                </div>
                <h3 className="text-xs sm:text-xs font-bold leading-tight">{service.label}</h3>
                <p className="text-[10px] sm:text-[11px] font-semibold text-slate-200 leading-tight">{service.description}</p>
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

ServiceSelector.propTypes = {
  onServicesSelected: PropTypes.func.isRequired,
  value: PropTypes.shape({
    electricity: PropTypes.bool,
    broadband: PropTypes.bool,
    mobile: PropTypes.bool,
  }),
};