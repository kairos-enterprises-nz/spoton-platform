import React from 'react';
import { Building2, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import { useTenant } from '../../context/TenantContext';

const TenantContextIndicator = ({ showDetails = false }) => {
  const { selectedTenant, tenants, isSuperAdmin, loading } = useTenant();

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-indigo-600 rounded-full"></div>
        <span className="text-sm">Loading tenant context...</span>
      </div>
    );
  }

  if (!isSuperAdmin && !selectedTenant) {
    return (
      <div className="flex items-center space-x-2 text-amber-600">
        <AlertTriangle className="h-4 w-4" />
        <span className="text-sm font-medium">No tenant context</span>
      </div>
    );
  }

  if (isSuperAdmin && !selectedTenant) {
    return (
      <div className="flex items-center space-x-2 text-blue-600">
        <Users className="h-4 w-4" />
        <span className="text-sm font-medium">All Tenants</span>
        {showDetails && (
          <span className="text-xs text-gray-500">({tenants.length} available)</span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-green-600">
      <CheckCircle className="h-4 w-4" />
      <Building2 className="h-4 w-4" />
      <div className="flex flex-col">
        <span className="text-sm font-medium">{selectedTenant.name}</span>
        {showDetails && (
          <span className="text-xs text-gray-500">{selectedTenant.slug}</span>
        )}
      </div>
    </div>
  );
};

export default TenantContextIndicator;
