import PropTypes from 'prop-types';
import { FileText } from 'lucide-react';

const defaultTransactions = [
  {
    id: 1,
    date: '2025-05-15',
    description: 'Power Bill - May 2025',
    amount: -142.50,
    status: 'pending',
    type: 'power'
  },
  {
    id: 2,
    date: '2025-05-01',
    description: 'Broadband Service - May 2025',
    amount: -89.99,
    status: 'pending',
    type: 'broadband'
  },
  {
    id: 3,
    date: '2025-04-22',
    description: 'Payment Received',
    amount: 198.75,
    status: 'completed',
    type: 'payment'
  },
  {
    id: 4,
    date: '2025-04-15',
    description: 'Power Bill - April 2025',
    amount: -138.20,
    status: 'completed',
    type: 'power'
  }
];

export default function RecentTransactions({ transactions: propTransactions, maxVisible = 4 }) {
  const transactions = propTransactions || defaultTransactions;

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'paid': return 'text-green-600 bg-green-100';
      case 'overdue': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'power': return '⚡';
      case 'broadband': return '🌐';
      case 'payment': return '💳';
      default: return '📄';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 p-6 transform hover:-translate-y-1">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold text-[#364153]">Recent Activity</h3>
        <FileText className="h-5 w-5 text-[#40E0D0]" />
      </div>
      <div className="space-y-3">
        {transactions.slice(0, maxVisible).map((transaction) => (
          <div key={transaction.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 rounded-lg px-2 transition-colors duration-200">
            <div className="flex items-center">
              <div className="w-9 h-9 rounded-full bg-[#40E0D0]/10 flex items-center justify-center mr-3 text-lg">
                {getTransactionIcon(transaction.type)}
              </div>
              <div>
                <div className="font-medium text-sm text-[#364153]">{transaction.description}</div>
                <div className="text-xs text-gray-500">{transaction.date}</div>
              </div>
            </div>
            <div className="text-right">
              <div className={`font-semibold ${transaction.amount > 0 ? 'text-green-600' : 'text-[#364153]'}`}>
                {transaction.amount > 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
              </div>
              <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.status)}`}>
                {transaction.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

RecentTransactions.propTypes = {
  transactions: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    date: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    amount: PropTypes.number.isRequired,
    status: PropTypes.oneOf(['pending', 'completed', 'paid', 'overdue']).isRequired,
    type: PropTypes.oneOf(['power', 'broadband', 'payment', 'other']).isRequired
  })),
  maxVisible: PropTypes.number
}; 