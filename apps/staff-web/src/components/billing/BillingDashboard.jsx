import React from 'react';
import {
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useBillingDashboard, useBillingHealthCheck, useBillingWebSocket } from '../../hooks/useBillingData';
import { billingApi } from '../../services/billingApi';

const BillingDashboard = () => {
  const { data: dashboardData, isLoading: dashboardLoading, error: dashboardError } = useBillingDashboard();
  const { data: healthData, isLoading: healthLoading } = useBillingHealthCheck();
  const { updates, connectionStatus } = useBillingWebSocket();

  if (dashboardLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-gray-200 h-24 rounded-lg"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-200 h-64 rounded-lg"></div>
            <div className="bg-gray-200 h-64 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (dashboardError) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Failed to load dashboard
              </h3>
              <div className="mt-2 text-sm text-red-700">
                {dashboardError.message}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Active Runs',
      value: dashboardData?.active_runs || 0,
      icon: ArrowPathIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      name: 'Pending Bills',
      value: dashboardData?.pending_bills || 0,
      icon: ClockIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50'
    },
    {
      name: 'System Status',
      value: healthData?.overall_status === 'healthy' ? 'Healthy' : 'Issues',
      icon: healthData?.overall_status === 'healthy' ? CheckCircleIcon : ExclamationTriangleIcon,
      color: healthData?.overall_status === 'healthy' ? 'text-green-600' : 'text-red-600',
      bgColor: healthData?.overall_status === 'healthy' ? 'bg-green-50' : 'bg-red-50'
    },
    {
      name: 'WebSocket',
      value: connectionStatus === 'connected' ? 'Connected' : 'Disconnected',
      icon: connectionStatus === 'connected' ? CheckCircleIcon : XCircleIcon,
      color: connectionStatus === 'connected' ? 'text-green-600' : 'text-red-600',
      bgColor: connectionStatus === 'connected' ? 'bg-green-50' : 'bg-red-50'
    }
  ];

  return (
    <div className="p-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className={`${stat.bgColor} rounded-lg p-6`}>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon className={`h-8 w-8 ${stat.color}`} />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className={`text-lg font-medium ${stat.color}`}>
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Status */}
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Service Status
            </h3>
            <div className="space-y-4">
              {dashboardData?.service_status && Object.entries(dashboardData.service_status).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`
                      w-3 h-3 rounded-full mr-3
                      ${status.is_healthy ? 'bg-green-400' : 'bg-red-400'}
                    `} />
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {service}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {status.last_run 
                      ? billingApi.formatDate(status.last_run, { month: 'short', day: 'numeric' })
                      : 'Never run'
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Activity
            </h3>
            <div className="flow-root">
              <ul className="-mb-8">
                {dashboardData?.recent_activity?.slice(0, 5).map((activity, activityIdx) => (
                  <li key={activity.id}>
                    <div className="relative pb-8">
                      {activityIdx !== dashboardData.recent_activity.slice(0, 5).length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className={`
                            h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white
                            ${activity.status === 'completed' ? 'bg-green-500' : 
                              activity.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'}
                          `}>
                            <ChartBarIcon className="h-4 w-4 text-white" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              {activity.service_type} billing run{' '}
                              <span className="font-medium text-gray-900">
                                {activity.status}
                              </span>
                            </p>
                            <p className="text-xs text-gray-400">
                              {activity.bills_generated} bills, {billingApi.formatCurrency(activity.total_amount)}
                            </p>
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            {billingApi.formatDate(activity.created_at, { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Updates */}
      {updates.length > 0 && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-blue-900 mb-4">
              Live Updates
            </h3>
            <div className="space-y-2">
              {updates.slice(0, 3).map((update, index) => (
                <div key={index} className="text-sm text-blue-800">
                  <span className="font-medium">
                    {billingApi.formatDate(update.timestamp || new Date())}:
                  </span>{' '}
                  {update.message || 'System update received'}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* System Health Issues */}
      {healthData?.pending_issues?.length > 0 && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-red-900 mb-4">
              System Issues
            </h3>
            <ul className="space-y-2">
              {healthData.pending_issues.map((issue, index) => (
                <li key={index} className="flex items-start">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
                  <span className="text-sm text-red-800">{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default BillingDashboard;
