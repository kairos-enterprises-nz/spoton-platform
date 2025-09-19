import logging
from rest_framework.permissions import BasePermission
from django.conf import settings

logger = logging.getLogger(__name__)


class ClientScopedPermission(BasePermission):
    """
    Base permission class for client-scoped role-based access control.
    Uses Keycloak client roles to determine permissions.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission based on client roles"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get required roles for this view
        required_roles = self.get_required_roles(request, view)
        if not required_roles:
            return True  # No specific roles required
        
        # Get user's client roles from token claims
        user_roles = self.get_user_client_roles(request)
        
        # Check if user has any of the required roles
        return any(role in user_roles for role in required_roles)
    
    def get_required_roles(self, request, view):
        """
        Get required roles for this view.
        Can be overridden in subclasses or set as view attribute.
        """
        # Check view attribute first
        if hasattr(view, 'required_client_roles'):
            return view.required_client_roles
        
        # Check method-specific roles
        method_roles_attr = f'required_client_roles_{request.method.lower()}'
        if hasattr(view, method_roles_attr):
            return getattr(view, method_roles_attr)
        
        return []
    
    def get_user_client_roles(self, request):
        """Get user's client roles from Keycloak token claims"""
        if not hasattr(request, 'keycloak_claims'):
            return []
        
        claims = request.keycloak_claims
        client_id = request.keycloak_client_id
        
        if not client_id:
            return []
        
        # Extract client roles from token
        resource_access = claims.get('resource_access', {})
        client_access = resource_access.get(client_id, {})
        
        return client_access.get('roles', [])


class TenantAdminPermission(ClientScopedPermission):
    """Permission for tenant administrators"""
    
    def get_required_roles(self, request, view):
        return ['tenant-admin', 'admin']


class TenantManagerPermission(ClientScopedPermission):
    """Permission for tenant managers"""
    
    def get_required_roles(self, request, view):
        return ['tenant-admin', 'tenant-manager', 'admin']


class TenantUserPermission(ClientScopedPermission):
    """Permission for regular tenant users"""
    
    def get_required_roles(self, request, view):
        return ['tenant-admin', 'tenant-manager', 'tenant-user', 'user', 'admin']


class StaffPermission(ClientScopedPermission):
    """Permission for staff members"""
    
    def get_required_roles(self, request, view):
        return ['staff', 'admin', 'super-admin']
    
    def has_permission(self, request, view):
        """Check both client roles and realm groups for staff access"""
        logger.info(f"StaffPermission: has_permission called for {getattr(request, 'user', 'No user')} on {request.path}")
        
        # Always allow Django superusers (safety backstop in UAT)
        try:
            if getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_superuser:
                logger.info("StaffPermission: Granted via Django superuser bypass")
                return True
        except Exception:
            pass

        # BYPASS Django user system - check Keycloak claims directly
        if hasattr(request, 'keycloak_claims'):
            logger.info(f"StaffPermission: Found Keycloak claims, checking directly")
            
            # Check realm groups (for spoton-admin realm)
            user_groups = self.get_user_groups(request)
            logger.info(f"StaffPermission: user_groups={user_groups}")
            
            staff_groups = ['Staff', 'Admin', 'super-admin', 'technical-staff']
            has_staff_group = any(group in user_groups for group in staff_groups)
            
            if has_staff_group:
                logger.info(f"StaffPermission: Access granted via Keycloak groups")
                return True
            
            # Check client roles (for other realms)
            client_roles = self.get_user_client_roles(request)
            logger.info(f"StaffPermission: client_roles={client_roles}")
            
            required_roles = self.get_required_roles(request, view)
            has_client_role = any(role in client_roles for role in required_roles)
            
            if has_client_role:
                logger.info(f"StaffPermission: Access granted via client roles")
                return True
            
            logger.warning(f"StaffPermission: Access denied - no valid Keycloak roles or groups")
            return False
        
        # Fallback to Django user system (for non-Keycloak requests)
        if not request.user or not request.user.is_authenticated:
            logger.warning(f"StaffPermission: No Keycloak claims and user not authenticated")
            return False
        
        # Original Django-based permission check
        logger.info(f"StaffPermission: Falling back to Django user permissions")
        return super().has_permission(request, view)
    
    def get_user_groups(self, request):
        """Get user's groups from Keycloak token claims"""
        if not hasattr(request, 'keycloak_claims'):
            return []
        
        claims = request.keycloak_claims
        return claims.get('groups', [])


class TenantOwnerPermission(BasePermission):
    """
    Permission that checks if user owns/belongs to the tenant being accessed.
    Works with tenant-aware models.
    """
    
    def has_permission(self, request, view):
        """Basic authentication check"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific object"""
        # If object has tenant, check if user belongs to same tenant
        if hasattr(obj, 'tenant'):
            user_tenant = getattr(request, 'tenant_obj', None)
            return obj.tenant == user_tenant
        
        # If object is a User, check if it's the same user or staff
        if hasattr(obj, 'keycloak_id'):
            return (obj.keycloak_id == request.user.keycloak_id or 
                   self._is_staff_user(request))
        
        return True
    
    def _is_staff_user(self, request):
        """Check if user has staff privileges"""
        user_roles = self.get_user_client_roles(request)
        staff_roles = ['staff', 'admin', 'super-admin', 'tenant-admin']
        return any(role in user_roles for role in staff_roles)
    
    def get_user_client_roles(self, request):
        """Get user's client roles from Keycloak token claims"""
        if not hasattr(request, 'keycloak_claims'):
            return []
        
        claims = request.keycloak_claims
        client_id = request.keycloak_client_id
        
        if not client_id:
            return []
        
        # Extract client roles from token
        resource_access = claims.get('resource_access', {})
        client_access = resource_access.get(client_id, {})
        
        return client_access.get('roles', [])


class ReadWritePermissionMixin:
    """
    Mixin to provide different permissions for read vs write operations.
    """
    
    def get_required_roles(self, request, view):
        """Get roles based on HTTP method"""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return self.get_read_roles(request, view)
        else:
            return self.get_write_roles(request, view)
    
    def get_read_roles(self, request, view):
        """Roles required for read operations"""
        return getattr(view, 'read_roles', ['user'])
    
    def get_write_roles(self, request, view):
        """Roles required for write operations"""
        return getattr(view, 'write_roles', ['admin'])


class TenantReadWritePermission(ReadWritePermissionMixin, ClientScopedPermission):
    """Permission with different roles for read/write operations"""
    pass


class DynamicClientPermission(BasePermission):
    """
    Dynamic permission that checks roles based on view configuration.
    Supports complex permission logic with multiple clients and roles.
    """
    
    def has_permission(self, request, view):
        """Check permission based on view configuration"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get permission configuration from view
        permission_config = getattr(view, 'client_permission_config', {})
        
        if not permission_config:
            return True  # No restrictions configured
        
        # Get user's roles across all clients
        all_user_roles = self.get_all_user_roles(request)
        
        # Check each permission rule
        for rule in permission_config:
            if self.check_permission_rule(rule, all_user_roles, request):
                return True
        
        return False
    
    def get_all_user_roles(self, request):
        """Get user's roles from all clients in token"""
        if not hasattr(request, 'keycloak_claims'):
            return {}
        
        claims = request.keycloak_claims
        resource_access = claims.get('resource_access', {})
        
        # Return roles for each client
        all_roles = {}
        for client_id, client_data in resource_access.items():
            all_roles[client_id] = client_data.get('roles', [])
        
        return all_roles
    
    def check_permission_rule(self, rule, all_user_roles, request):
        """Check if user satisfies a specific permission rule"""
        client_id = rule.get('client_id')
        required_roles = rule.get('roles', [])
        method = rule.get('method', 'ALL')
        
        # Check HTTP method
        if method != 'ALL' and request.method != method:
            return False
        
        # Check client roles
        if client_id:
            user_roles = all_user_roles.get(client_id, [])
            return any(role in user_roles for role in required_roles)
        else:
            # Check roles across all clients
            for client_roles in all_user_roles.values():
                if any(role in client_roles for role in required_roles):
                    return True
        
        return False


# Convenience permission combinations
class CustomerPortalPermission(TenantUserPermission):
    """Permission for customer portal access"""
    pass


class StaffPortalPermission(StaffPermission):
    """Permission for staff portal access"""
    pass


class BillingPermission(ClientScopedPermission):
    """Permission for billing-related operations"""
    
    def get_required_roles(self, request, view):
        return ['billing-admin', 'billing-manager', 'tenant-admin', 'admin']


class MeteringPermission(ClientScopedPermission):
    """Permission for metering data access"""
    
    def get_required_roles(self, request, view):
        return ['metering-admin', 'metering-viewer', 'tenant-admin', 'admin']


# Example usage in views:
"""
class TenantViewSet(ModelViewSet):
    permission_classes = [TenantAdminPermission]
    required_client_roles = ['tenant-admin']
    
    # Or method-specific roles:
    required_client_roles_get = ['tenant-user']
    required_client_roles_post = ['tenant-admin']
    
    # Or complex configuration:
    client_permission_config = [
        {
            'client_id': 'customer-portal',
            'roles': ['user', 'premium'],
            'method': 'GET'
        },
        {
            'client_id': 'staff-portal', 
            'roles': ['staff'],
            'method': 'ALL'
        }
    ]
""" 