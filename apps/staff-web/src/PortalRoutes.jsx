import React from 'react';
import { Routes, Route } from 'react-router-dom';

// Simple staff dashboard component
const StaffDashboard = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">SpotOn Staff Portal</h1>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Welcome to Staff Portal</h2>
              <p className="text-gray-600 mb-4">
                The staff portal is operational and ready for use.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium text-blue-900">System Status</h3>
                  <p className="text-blue-700 text-sm">All systems operational</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium text-green-900">User Management</h3>
                  <p className="text-green-700 text-sm">Customer accounts & profiles</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-medium text-purple-900">Energy Data</h3>
                  <p className="text-purple-700 text-sm">Metering & billing analytics</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function PortalRoutes() {
  return (
    <Routes>
      <Route path="*" element={<StaffDashboard />} />
    </Routes>
  );
}