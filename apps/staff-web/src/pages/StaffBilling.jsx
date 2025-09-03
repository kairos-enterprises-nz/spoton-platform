import React, { useState } from 'react';
import { 
  ChartBarIcon, 
  CogIcon, 
  DocumentTextIcon, 
  PlayIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';
import BillingDashboard from '../components/billing/BillingDashboard';
import BillingRunManager from '../components/billing/BillingRunManager';
import BillManager from '../components/billing/BillManager';
import InvoiceManager from '../components/billing/InvoiceManager';
import ServiceConfiguration from '../components/billing/ServiceConfiguration';

const StaffBilling = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: ChartBarIcon,
      description: 'Overview and system status'
    },
    {
      id: 'runs',
      label: 'Billing Runs',
      icon: PlayIcon,
      description: 'Create and manage billing runs'
    },
    {
      id: 'bills',
      label: 'Bills',
      icon: ClipboardDocumentListIcon,
      description: 'Review and manage bills'
    },
    {
      id: 'invoices',
      label: 'Invoices',
      icon: DocumentTextIcon,
      description: 'Invoice lifecycle management'
    },
    {
      id: 'config',
      label: 'Configuration',
      icon: CogIcon,
      description: 'Service and system configuration'
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <BillingDashboard />;
      case 'runs':
        return <BillingRunManager />;
      case 'bills':
        return <BillManager />;
      case 'invoices':
        return <InvoiceManager />;
      case 'config':
        return <ServiceConfiguration />;
      default:
        return <BillingDashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              Billing Management
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              Manage billing operations, runs, invoices, and system configuration
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                    ${isActive
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon
                    className={`
                      -ml-0.5 mr-2 h-5 w-5
                      ${isActive
                        ? 'text-indigo-500'
                        : 'text-gray-400 group-hover:text-gray-500'
                      }
                    `}
                    aria-hidden="true"
                  />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 min-h-[600px]">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default StaffBilling;
