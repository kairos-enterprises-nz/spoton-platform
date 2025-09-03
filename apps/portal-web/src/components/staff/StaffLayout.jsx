import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useAuth } from '../../hooks/useAuth';
import { useTenant } from '../../context/TenantContext';
import StaffDebugInfo from './StaffDebugInfo';
import logo from '../../assets/utcologo.png';

const StaffLayout = ({ children }) => {
  // console.log('🏗️ StaffLayout: Component rendering'); // Removed to prevent spam
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showTenantDropdown, setShowTenantDropdown] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { tenants, selectedTenant, selectTenant, isSuperAdmin } = useTenant();

  // No need to load tenants here - handled by TenantContext

  // console.log('🏗️ StaffLayout: Current location:', location.pathname); // Removed to prevent spam

  const navigation = [
    // Only show Tenants for admin users (superuser or Admin group)
    ...(user?.is_superuser || user?.groups?.includes('Admin') ? [{
      name: 'Tenants',
      href: '/staff/tenants',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    }] : []),
    {
      name: 'Users',
      href: '/staff/users',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
    {
      name: 'Accounts',
      href: '/staff/accounts',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
    {
      name: 'Contracts',
      href: '/staff/contracts',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      name: 'Connections',
      href: '/staff/connections',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      )
    },
    {
      name: 'Plans',
      href: '/staff/plans',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      name: 'Energy Data',
      href: '/staff/energy',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      )
    },
    {
      name: 'Analytics',
      href: '/staff/energy/analytics',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      name: 'Reports',
      href: '/staff/reports',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      name: 'Validation Rules',
      href: '/staff/validation-rules',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      name: 'Validation Exceptions',
      href: '/staff/validation-exceptions',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      )
    },
    {
      name: 'System',
      href: '/staff/system',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      name: 'Airflow',
      href: '/staff/airflow',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      )
    },
    {
      name: 'Wiki',
      href: `/wiki/`,
      external: true,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    }
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isCurrentPath = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 flex z-40 md:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <SidebarContent 
            navigation={navigation} 
            isCurrentPath={isCurrentPath} 
            user={user} 
            onLogout={handleLogout}
            tenants={tenants}
            selectedTenant={selectedTenant}
            selectTenant={selectTenant}
            isSuperAdmin={isSuperAdmin}
            showTenantDropdown={showTenantDropdown}
            setShowTenantDropdown={setShowTenantDropdown}
          />
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <SidebarContent 
          navigation={navigation} 
          isCurrentPath={isCurrentPath} 
          user={user} 
          onLogout={handleLogout}
          tenants={tenants}
          selectedTenant={selectedTenant}
          selectTenant={selectTenant}
          isSuperAdmin={isSuperAdmin}
          showTenantDropdown={showTenantDropdown}
          setShowTenantDropdown={setShowTenantDropdown}
        />
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        {/* Top bar */}
        <div className="sticky top-0 z-10 md:hidden p-3 bg-white border-b border-gray-200">
          <button
            type="button"
            className="-ml-0.5 -mt-0.5 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
            onClick={() => setSidebarOpen(true)}
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        {/* Page content */}
        <main className="flex-1 min-h-0">
              {children}
        </main>
      </div>
      
      {/* Debug Info Component */}
      <StaffDebugInfo />
    </div>
  );
};

const SidebarContent = ({ navigation, isCurrentPath, user, onLogout, tenants, selectedTenant, selectTenant, isSuperAdmin, showTenantDropdown, setShowTenantDropdown }) => (
  <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
    {/* Logo */}
    <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
  <div className=" flex  left-0 items-start flex-shrink-0 px-0 ">
    <img 
      src={logo} 
      alt="Logo" 
      className="h-20 w-45 object-cover"
    />
  </div>
      {/* Navigation */}
      <nav className="mt-6 flex-1 px-3 space-y-1">
        {navigation.map((item) => {
          if (item.external) {
            return (
              <a
                key={item.name}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-150"
              >
                <span className="text-gray-400 group-hover:text-gray-500 mr-3 flex-shrink-0">
                  {item.icon}
                </span>
                {item.name}
                <svg className="ml-auto h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            );
          }
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`${
                isCurrentPath(item.href)
                  ? 'bg-indigo-100 text-indigo-900 border-r-2 border-indigo-500'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              } group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150`}
            >
              <span className={`${
                isCurrentPath(item.href) ? 'text-indigo-500' : 'text-gray-400 group-hover:text-gray-500'
              } mr-3 flex-shrink-0`}>
                {item.icon}
              </span>
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>

    {/* Tenant Selection - Only for super admins */}
    {isSuperAdmin && tenants.length > 0 && (
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="relative">
          <label className="block text-xs font-medium text-gray-700 mb-2">Current Tenant</label>
          <button
            onClick={() => setShowTenantDropdown(!showTenantDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 text-sm bg-gray-50 border border-gray-300 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <span className="truncate">
              {selectedTenant ? selectedTenant.name : 'All Tenants'}
            </span>
            <svg className="ml-2 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showTenantDropdown && (
            <div className="absolute bottom-full left-0 right-0 mb-1 bg-white border border-gray-300 rounded-md shadow-lg z-50 max-h-60 overflow-y-auto">
              {/* All Tenants Option */}
              <button
                onClick={() => {
                  selectTenant(null);
                  setShowTenantDropdown(false);
                }}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 border-b border-gray-200 ${
                  !selectedTenant ? 'bg-indigo-50 text-indigo-900' : 'text-gray-900'
                }`}
              >
                <div className="font-medium">All Tenants</div>
                <div className="text-xs text-gray-500">View data across all tenants</div>
              </button>
              
              {/* Individual Tenants */}
              {tenants.map((tenant) => (
                <button
                  key={tenant.id}
                  onClick={() => {
                    selectTenant(tenant);
                    setShowTenantDropdown(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 ${
                    selectedTenant?.id === tenant.id ? 'bg-indigo-50 text-indigo-900' : 'text-gray-900'
                  }`}
                >
                  <div className="font-medium">{tenant.name}</div>
                  <div className="text-xs text-gray-500">{tenant.slug}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    )}

    {/* User info */}
    <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
      <div className="flex items-center w-full">
        <div className="h-10 w-10 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-indigo-600 font-semibold">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </span>
        </div>
        <div className="ml-3 flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-700 truncate">
            {user?.first_name} {user?.last_name}
          </p>
          <p className="text-xs text-gray-500 truncate">{user?.job_title || 'Staff Member'}</p>
          {!user?.is_superuser && selectedTenant && (
            <p className="text-xs text-indigo-600 truncate">
              {selectedTenant.name}
            </p>
          )}
        </div>
        <button
          onClick={onLogout}
          className="ml-3 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-md p-1 flex-shrink-0"
          title="Logout"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  </div>
);

StaffLayout.propTypes = {
  children: PropTypes.node.isRequired,
};

SidebarContent.propTypes = {
  navigation: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    href: PropTypes.string.isRequired,
    icon: PropTypes.node.isRequired,
    external: PropTypes.bool,
  })).isRequired,
  isCurrentPath: PropTypes.func.isRequired,
  user: PropTypes.shape({
    first_name: PropTypes.string,
    last_name: PropTypes.string,
    job_title: PropTypes.string,
    is_superuser: PropTypes.bool,
  }),
  onLogout: PropTypes.func.isRequired,
  tenants: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    slug: PropTypes.string,
  })).isRequired,
  selectedTenant: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    slug: PropTypes.string,
  }),
  selectTenant: PropTypes.func.isRequired,
  isSuperAdmin: PropTypes.bool.isRequired,
  showTenantDropdown: PropTypes.bool.isRequired,
  setShowTenantDropdown: PropTypes.func.isRequired,
};

export default StaffLayout; 