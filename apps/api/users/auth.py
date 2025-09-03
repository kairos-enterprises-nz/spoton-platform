"""
Enhanced staff authentication system with multi-tenant support
"""
# JWT imports removed - using Keycloak for authentication
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import logging
# JWT library removed - using Keycloak tokens only
from .models import APIToken

logger = logging.getLogger(__name__)
User = get_user_model()


# JWT token classes removed - all authentication now handled by Keycloak


class APITokenAuthentication(BaseAuthentication):
    """
    API Token authentication for service-to-service communication
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Token '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            api_token = APIToken.objects.select_related('user').get(
                key=token,
                is_active=True
            )
            
            # Check if token is expired
            if api_token.expires_at and api_token.expires_at < timezone.now():
                return None
            
            # Update last used
            api_token.last_used_at = timezone.now()
            api_token.save(update_fields=['last_used_at'])
            
            return (api_token.user, api_token)
            
        except APIToken.DoesNotExist:
            return None


class IsStaffOrReadOnly(BasePermission):
    """
    Custom permission to only allow staff users to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for staff
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsOwnerOrStaff(BasePermission):
    """
    Custom permission to only allow owners of an object or staff to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Staff can access everything
        if request.user.is_staff:
            return True
        
        # Users can only access their own objects
        return hasattr(obj, 'user') and obj.user == request.user


class IsTenantMemberOrStaff(BasePermission):
    """
    Custom permission for tenant-based access control
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff can access all tenants
        if request.user.is_staff:
            return True
        
        # Users must belong to a tenant
        return request.user.tenant is not None
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff can access all objects
        if request.user.is_staff:
            return True
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant') and obj.tenant:
            return obj.tenant == request.user.tenant
        
        # Check if object belongs to user
        if hasattr(obj, 'user') and obj.user:
            return obj.user == request.user
        
        return False


# Backward compatibility aliases
class IsStaffUser(BasePermission):
    """Base permission for staff access (backward compatibility)"""
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_staff
        )


class IsTenantMember(BasePermission):
    """Permission class that checks tenant membership (backward compatibility)"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superuser can access all tenants
        if request.user.is_superuser:
            return True
        
        # Check tenant header
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if tenant_slug and request.user.tenant:
            return request.user.tenant.slug == tenant_slug
        
        return True  # Allow if no tenant specified


class IsAdminUser(BasePermission):
    """Permission for admin-only access - superuser or Admin group members only (backward compatibility)"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return False
        
        # Superuser always has access
        if request.user.is_superuser:
            return True
        
        # Check if user is in Admin group
        return request.user.groups.filter(name='Admin').exists()
