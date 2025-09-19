import { useState } from 'react';
import GrafanaEmbed from '../components/staff/GrafanaEmbed';

const StaffEnergyAnalytics = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('now-24h');
  const [refreshInterval, setRefreshInterval] = useState('30s');

  const timeRangeOptions = [
    { value: 'now-1h', label: 'Last Hour' },
    { value: 'now-6h', label: 'Last 6 Hours' },
    { value: 'now-24h', label: 'Last 24 Hours' },
    { value: 'now-7d', label: 'Last 7 Days' },
    { value: 'now-30d', label: 'Last 30 Days' }
  ];

  const refreshOptions = [
    { value: '10s', label: '10 seconds' },
    { value: '30s', label: '30 seconds' },
    { value: '1m', label: '1 minute' },
    { value: '5m', label: '5 minutes' },
    { value: '15m', label: '15 minutes' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
    
      <div className="space-y-4">
        {/* Header */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Energy Analytics</h1>
              <p className="mt-1 text-sm text-gray-500">
                Real-time visualization of energy timeseries data powered by Grafana
              </p>
            </div>
            
            {/* Controls */}
            <div className="flex items-center space-x-4">
              <div>
                <label htmlFor="timeRange" className="block text-sm font-medium text-gray-700">
                  Time Range
                </label>
                <select
                  id="timeRange"
                  value={selectedTimeRange}
                  onChange={(e) => setSelectedTimeRange(e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {timeRangeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label htmlFor="refresh" className="block text-sm font-medium text-gray-700">
                  Refresh
                </label>
                <select
                  id="refresh"
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {refreshOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard */}
        <GrafanaEmbed
          dashboardUid="staff-energy-dashboard"
          title="Staff Energy Dashboard"
          height="800px"
          theme="light"
          refresh={refreshInterval}
          from={selectedTimeRange}
          to="now"
        />

        {/* Individual Panel Views */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Energy Consumption Panel */}
          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={1}
            title="Hourly Energy Consumption"
            height="400px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />

          {/* Wholesale Prices Panel */}
          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={2}
            title="Wholesale Energy Prices"
            height="400px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />
        </div>

        {/* Statistics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={3}
            title="24h Meter Readings"
            height="200px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />

          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={4}
            title="Data Quality Issues"
            height="200px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />

          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={5}
            title="Active Connections"
            height="200px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />

          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={6}
            title="Total Consumption"
            height="200px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />
        </div>

        {/* Additional Analysis Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Meter Types Distribution */}
          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={7}
            title="Meter Types Distribution"
            height="400px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />

          {/* Data Import Rate */}
          <GrafanaEmbed
            dashboardUid="staff-energy-dashboard"
            panelId={8}
            title="Data Import Rate"
            height="400px"
            theme="light"
            refresh={refreshInterval}
            from={selectedTimeRange}
            to="now"
          />
        </div>

        {/* Quick Actions */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                   <button
                 onClick={() => window.open(`http://${window.location.hostname}:3000/d/staff-energy-dashboard`, '_blank')}
                 className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
               >
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Open Full Dashboard
            </button>
            
                                                   <button
                 onClick={() => window.open(`http://${window.location.hostname}:3000/explore`, '_blank')}
                 className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
               >
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Explore Data
            </button>
            
                                                   <button
                 onClick={() => window.open(`http://${window.location.hostname}:3000/alerting/list`, '_blank')}
                 className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
               >
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM12 17H7l5 5v-5z" />
              </svg>
              Manage Alerts
            </button>
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-4 mx-3 md:mx-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Grafana</p>
                <p className="text-sm text-gray-500">Running on port 3000</p>
              </div>
            </div>
            
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">TimescaleDB</p>
                <p className="text-sm text-gray-500">Connected and healthy</p>
              </div>
            </div>
            
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Data Pipeline</p>
                <p className="text-sm text-gray-500">Active and processing</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    
    </div>
  );
};

export default StaffEnergyAnalytics;