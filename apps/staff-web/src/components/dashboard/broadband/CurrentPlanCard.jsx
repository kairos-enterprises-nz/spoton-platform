import PropTypes from 'prop-types';
import { Wifi } from 'lucide-react';

export default function CurrentPlanCard({ planData }) {
  const defaultPlan = {
    name: "Fibre Max",
    speed: "900 Mbps",
    uploadSpeed: "100 Mbps",
    dataAllowance: "Unlimited",
    monthlyPrice: 89.99,
    contractEnd: "2025-12-15",
    features: ["Unlimited data", "Free router", "24/7 support", "No setup fee"]
  };

  const plan = planData || defaultPlan;

  return (
    <div className="bg-gradient-to-br from-[#40E0D0] to-[#364153] rounded-xl shadow-md hover:shadow-lg transition-all duration-300 p-6 text-white transform hover:-translate-y-1 relative overflow-hidden">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxkZWZzPjxwYXR0ZXJuIGlkPSJwYXR0ZXJuIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgcGF0dGVyblRyYW5zZm9ybT0icm90YXRlKDEzNSkiPjxwYXRoIGQ9Ik0gMjAgMjAgTCAyMCA0MCBNIDM1IDM1IEwgNDAgNDAgTSAxNSAxNSBMIDQwIDQwIE0gMCAwIEwgMzUgMzUgTSAwIDEwIEwgMzAgNDAgTSAwIDIwIEwgMjAgNDAgTSAwIDMwIEwgMTAgNDAiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2Utb3BhY2l0eT0iMC4xIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI3BhdHRlcm4pIi8+PC9zdmc+')] opacity-30 animate-shimmer transform hover:opacity-40 transition-opacity duration-700"></div>
      <div className="relative z-10">
        <div className="flex items-center mb-4">
          <Wifi className="h-6 w-6 mr-3" />
          <h2 className="text-xl font-semibold">Current Plan</h2>
        </div>
        <div className="mb-4">
          <div className="text-2xl font-bold mb-1">{plan.name}</div>
          <div className="text-white/80">Up to {plan.speed} download</div>
          <div className="text-white/80">{plan.dataAllowance} data</div>
        </div>
        <div className="pt-4 border-t border-white/20">
          <div className="flex justify-between items-center mb-2">
            <span className="text-white/80">Monthly Cost</span>
            <span className="font-semibold">${plan.monthlyPrice}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-white/80">Contract Until</span>
            <span className="font-semibold">{new Date(plan.contractEnd).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

CurrentPlanCard.propTypes = {
  planData: PropTypes.shape({
    name: PropTypes.string.isRequired,
    speed: PropTypes.string.isRequired,
    uploadSpeed: PropTypes.string,
    dataAllowance: PropTypes.string.isRequired,
    monthlyPrice: PropTypes.number.isRequired,
    contractEnd: PropTypes.string.isRequired,
    features: PropTypes.arrayOf(PropTypes.string)
  })
}; 