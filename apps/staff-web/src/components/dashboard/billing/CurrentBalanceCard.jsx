import PropTypes from 'prop-types';
import { DollarSign, Calendar } from 'lucide-react';

export default function CurrentBalanceCard({ balanceData, onPayNow }) {
  const defaultBalance = {
    total: 247.83,
    power: 142.50,
    broadband: 89.99,
    fees: 15.34,
    dueDate: '2025-06-05'
  };

  const balance = balanceData || defaultBalance;

  return (
    <div className="bg-gradient-to-br from-[#40E0D0] to-[#364153] rounded-xl shadow-md hover:shadow-lg transition-all duration-300 p-6 text-white transform hover:-translate-y-1 relative overflow-hidden">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCI+PHBhdGggZD0iTTIgMmw1NiA1Nk0zOCAyTDIgMzhtNTYgMjBMMjIgNThtMzYtNTZMMiA1OCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2Utb3BhY2l0eT0iMC4xIiBmaWxsPSJub25lIi8+PC9zdmc+')] opacity-30 animate-shimmer"></div>
      <div className="absolute -right-16 -top-16 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:bg-white/15 transition-all duration-700 transform group-hover:scale-110"></div>
      <div className="relative z-10 transform transition-transform duration-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Current Balance</h2>
          <DollarSign className="h-6 w-6 text-white/80" />
        </div>
        <div className="mb-4">
          <div className="text-3xl font-bold mb-2">${balance.total.toFixed(2)}</div>
          <div className="flex items-center text-white/80">
            <Calendar className="h-4 w-4 mr-2" />
            Due: {new Date(balance.dueDate).toLocaleDateString()}
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
          <div>
            <div className="text-white/70 text-sm">Power</div>
            <div className="font-semibold">${balance.power}</div>
          </div>
          <div>
            <div className="text-white/70 text-sm">Broadband</div>
            <div className="font-semibold">${balance.broadband}</div>
          </div>
          <div>
            <div className="text-white/70 text-sm">Fees</div>
            <div className="font-semibold">${balance.fees}</div>
          </div>
        </div>
        <button 
          onClick={onPayNow}
          className="mt-6 w-full bg-white text-[#364153] font-semibold py-2 px-4 rounded-lg hover:bg-white/90 transition-all duration-300 transform hover:scale-105"
        >
          Pay Now
        </button>
      </div>
    </div>
  );
}

CurrentBalanceCard.propTypes = {
  balanceData: PropTypes.shape({
    total: PropTypes.number.isRequired,
    power: PropTypes.number.isRequired,
    broadband: PropTypes.number.isRequired,
    fees: PropTypes.number.isRequired,
    dueDate: PropTypes.string.isRequired
  }),
  onPayNow: PropTypes.func
}; 