import PropTypes from 'prop-types';
import { Camera, CheckCircle } from 'lucide-react';

export default function ProfileHeader({ userData, accountInfo, onImageUpload }) {
  const defaultUser = {
    firstName: 'Jane',
    lastName: 'Doe',
    email: 'jane.doe@example.com'
  };

  const defaultAccount = {
    customerSince: '2020-03-15',
    accountStatus: 'Active'
  };

  const user = userData || defaultUser;
  const account = accountInfo || defaultAccount;

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 p-6 mb-6 transform hover:-translate-y-1">
      <div className="flex items-center">
        <div className="relative">
          <div className="h-20 w-20 bg-gradient-to-br from-[#40E0D0] to-[#364153] rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-md">
            {user.firstName[0]}{user.lastName[0]}
          </div>
          <button 
            onClick={onImageUpload}
            className="absolute -bottom-1 -right-1 bg-white rounded-full p-2 shadow-md border hover:bg-[#40E0D0]/10 transition-all duration-300 transform hover:scale-110"
          >
            <Camera className="h-4 w-4 text-[#364153]" />
          </button>
        </div>
        <div className="ml-6 flex-1">
          <h2 className="text-2xl font-bold text-[#364153]">{user.firstName} {user.lastName}</h2>
          <p className="text-gray-600">{user.email}</p>
          <p className="text-gray-500 text-sm">Customer since {new Date(account.customerSince).toLocaleDateString()}</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-[#40E0D0]/20 text-[#364153]">
            <CheckCircle className="h-4 w-4 mr-1 text-[#40E0D0]" />
            {account.accountStatus}
          </span>
        </div>
      </div>
    </div>
  );
}

ProfileHeader.propTypes = {
  userData: PropTypes.shape({
    firstName: PropTypes.string.isRequired,
    lastName: PropTypes.string.isRequired,
    email: PropTypes.string.isRequired
  }),
  accountInfo: PropTypes.shape({
    customerSince: PropTypes.string.isRequired,
    accountStatus: PropTypes.string.isRequired
  }),
  onImageUpload: PropTypes.func
}; 