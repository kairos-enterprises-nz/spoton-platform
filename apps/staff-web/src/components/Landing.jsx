import React from "react";

const Landing = () => {
  return (
    <div className="flex justify-center items-start min-h-screen bg-white p-6">
      <div className="bg-white rounded-2xl p-6 w-full max-w-3xl mx-auto text-center">
        {/* Welcome Section */}
        <h1 className="text-3xl font-bold text-gray-800 mb-4">🎉 Welcome to Your Dashboard!</h1>
        <p className="text-gray-600 mt-2 mb-6">You have successfully authorized your account. See what you can do:</p>

        {/* Action List */}
        <ul className="mt-4 space-y-4 text-gray-700 flex flex-col items-center">
          <li className="flex items-center space-x-2">
            <span className="text-green-500">✅</span>
            <span>View your profile</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="text-blue-500">🔑</span>
            <span>Change account settings</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="text-purple-500">📊</span>
            <span>Access reports</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="text-red-500">📞</span>
            <span>Contact support</span>
          </li>
        </ul>

        {/* Additional Content Section */}
        <div className="mt-6 bg-gray-50 p-4 rounded-lg">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">New Features</h2>
          <p className="text-gray-600 mb-4">Check out the latest updates and features available on your dashboard. Stay tuned for more enhancements!</p>

          {/* Quick Links */}
          <div className="space-y-2">
            <p className="text-gray-800 font-semibold">Quick Links:</p>
            <ul className="space-y-1 text-gray-700">
              <li><a href="#" className="text-blue-500 hover:underline">Documentation</a></li>
              <li><a href="#" className="text-blue-500 hover:underline">FAQ</a></li>
              <li><a href="#" className="text-blue-500 hover:underline">Community Forum</a></li>
            </ul>
          </div>
        </div>

        {/* Call-to-Action */}
        <button className="mt-6 px-6 py-3 bg-blue-500 text-white rounded-lg shadow-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400 transition">
          Go to Profile
        </button>
      </div>
    </div>
  );
};

export default Landing;
