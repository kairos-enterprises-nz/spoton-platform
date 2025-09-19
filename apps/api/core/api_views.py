"""
Base API views for multi-tenant white-label architecture.
Provides tenant-aware querysets and validation for all API endpoints.
"""

from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.http import Http404
from utilitybyte.middleware import get_tenant_context, get_current_user
import logging

logger = logging.getLogger(__name__)


class TenantAwarePermission(permissions.BasePermission):
    """
    Permission class that enforces tenant isolation.
    Users can only access resources within their tenant/brand.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the tenant context"""
        # Allow access if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Get current tenant context
        tenant_context = get_tenant_context()
        if not tenant_context:
            return False
        
        # Superusers can access all tenants
        if request.user.is_superuser:
            return True
        
        # Check if user belongs to the current tenant
        return self._user_belongs_to_tenant(request.user, tenant_context)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object"""
        # Superusers can access all objects
        if request.user.is_superuser:
            return True
        
        # Check if object belongs to current tenant
        tenant_context = get_tenant_context()
        if not tenant_context:
            return False
        
        # Check if object has tenant field
        if hasattr(obj, 'tenant_id'):
            return str(obj.tenant_id) == str(tenant_context.get('tenant_id'))
        elif hasattr(obj, 'tenant'):
            return str(obj.tenant.id) == str(tenant_context.get('tenant_id'))
        
        # For objects without tenant field, check related objects
        return self._check_related_tenant_access(obj, tenant_context)
    
    def _user_belongs_to_tenant(self, user, tenant_context):
        """Check if user belongs to the current tenant"""
        try:
            # Check if user has account in current tenant
            if hasattr(user, 'accounts'):
                return user.accounts.filter(
                    tenant_id=tenant_context.get('tenant_id')
                ).exists()
            
            # Check if user has role in current tenant
            if hasattr(user, 'tenant_roles'):
                return user.tenant_roles.filter(
                    tenant_id=tenant_context.get('tenant_id')
                ).exists()
            
            return False
        except Exception as e:
            logger.warning(f"Error checking user tenant membership: {e}")
            return False
    
    def _check_related_tenant_access(self, obj, tenant_context):
        """Check tenant access through related objects"""
        try:
            # Check common related fields
            for field_name in ['account', 'contract', 'connection', 'customer']:
                if hasattr(obj, field_name):
                    related_obj = getattr(obj, field_name)
                    if related_obj and hasattr(related_obj, 'tenant_id'):
                        return str(related_obj.tenant_id) == str(tenant_context.get('tenant_id'))
            
            return False
        except Exception as e:
            logger.warning(f"Error checking related tenant access: {e}")
            return False


class TenantAwareQuerySetMixin:
    """
    Mixin that provides tenant-aware querysets.
    Automatically filters all queries by current tenant.
    """
    
    def get_queryset(self):
        """Get queryset filtered by current tenant"""
        queryset = super().get_queryset()
        
        # Skip tenant filtering for superusers
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return queryset
        
        # Get current tenant context
        tenant_context = get_tenant_context()
        if not tenant_context:
            # Return empty queryset if no tenant context
            return queryset.none()
        
        tenant_id = tenant_context.get('tenant_id')
        if not tenant_id:
            return queryset.none()
        
        # Filter by tenant field
        if hasattr(queryset.model, 'tenant_id'):
            return queryset.filter(tenant_id=tenant_id)
        elif hasattr(queryset.model, 'tenant'):
            return queryset.filter(tenant_id=tenant_id)
        
        # For models without direct tenant relationship, check related fields
        return self._filter_by_related_tenant(queryset, tenant_id)
    
    def _filter_by_related_tenant(self, queryset, tenant_id):
        """Filter queryset by related tenant fields"""
        model = queryset.model
        
        # Check common related fields
        for field_name in ['account__tenant_id', 'contract__tenant_id', 'connection__tenant_id', 'customer__tenant_id']:
            if self._has_related_field(model, field_name):
                return queryset.filter(**{field_name: tenant_id})
        
        # If no tenant relationship found, return empty queryset for safety
        logger.warning(f"No tenant relationship found for model {model.__name__}")
        return queryset.none()
    
    def _has_related_field(self, model, field_path):
        """Check if model has a related field path"""
        try:
            parts = field_path.split('__')
            current_model = model
            
            for part in parts[:-1]:  # Skip the last part (field name)
                field = current_model._meta.get_field(part)
                if field.is_relation:
                    current_model = field.related_model
                else:
                    return False
            
            # Check if final field exists
            final_field = parts[-1]
            current_model._meta.get_field(final_field)
            return True
        except Exception:
            return False


class TenantAwareValidationMixin:
    """
    Mixin that provides tenant-aware validation.
    Ensures all created/updated objects belong to current tenant.
    """
    
    def perform_create(self, serializer):
        """Create object with current tenant context"""
        tenant_context = get_tenant_context()
        if not tenant_context:
            raise ValidationError("No tenant context available")
        
        tenant_id = tenant_context.get('tenant_id')
        
        # Set tenant on the object being created
        if hasattr(serializer.Meta.model, 'tenant_id'):
            serializer.save(tenant_id=tenant_id)
        elif hasattr(serializer.Meta.model, 'tenant'):
            from users.models import Tenant
            tenant = Tenant.objects.get(id=tenant_id)
            serializer.save(tenant=tenant)
        else:
            # For models without direct tenant relationship, validate related objects
            self._validate_related_tenant_on_create(serializer, tenant_id)
    
    def perform_update(self, serializer):
        """Update object with tenant validation"""
        tenant_context = get_tenant_context()
        if not tenant_context:
            raise ValidationError("No tenant context available")
        
        tenant_id = tenant_context.get('tenant_id')
        
        # Validate that object belongs to current tenant
        instance = serializer.instance
        if hasattr(instance, 'tenant_id'):
            if str(instance.tenant_id) != str(tenant_id):
                raise PermissionDenied("Cannot update object from different tenant")
        elif hasattr(instance, 'tenant'):
            if str(instance.tenant.id) != str(tenant_id):
                raise PermissionDenied("Cannot update object from different tenant")
        
        # Save the update
        serializer.save()
    
    def _validate_related_tenant_on_create(self, serializer, tenant_id):
        """Validate tenant consistency for objects without direct tenant relationship"""
        validated_data = serializer.validated_data
        
        # Check common related fields
        for field_name in ['account', 'contract', 'connection', 'customer']:
            if field_name in validated_data:
                related_obj = validated_data[field_name]
                if hasattr(related_obj, 'tenant_id'):
                    if str(related_obj.tenant_id) != str(tenant_id):
                        raise ValidationError(f"Related {field_name} must belong to current tenant")
        
        serializer.save()


class TenantAwareViewSet(TenantAwareQuerySetMixin, TenantAwareValidationMixin, viewsets.ModelViewSet):
    """
    Base ViewSet for tenant-aware CRUD operations.
    Provides automatic tenant filtering and validation.
    """
    permission_classes = [TenantAwarePermission]
    
    def get_object(self):
        """Get object with tenant validation"""
        obj = super().get_object()
        
        # Additional tenant validation
        if not self.request.user.is_superuser:
            tenant_context = get_tenant_context()
            if tenant_context:
                if hasattr(obj, 'tenant_id'):
                    if str(obj.tenant_id) != str(tenant_context.get('tenant_id')):
                        raise Http404("Object not found")
                elif hasattr(obj, 'tenant'):
                    if str(obj.tenant.id) != str(tenant_context.get('tenant_id')):
                        raise Http404("Object not found")
        
        return obj
    
    @action(detail=False, methods=['get'])
    def tenant_info(self, request):
        """Get current tenant information"""
        tenant_context = get_tenant_context()
        if not tenant_context:
            return Response({"error": "No tenant context"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "tenant_id": tenant_context.get('tenant_id'),
            "tenant_name": tenant_context.get('tenant_name'),
            "tenant_slug": tenant_context.get('tenant_slug'),
            "currency": tenant_context.get('currency'),
            "timezone": tenant_context.get('timezone'),
        })


class TenantAwareListCreateAPIView(TenantAwareQuerySetMixin, TenantAwareValidationMixin, generics.ListCreateAPIView):
    """
    Base API view for listing and creating tenant-aware objects.
    """
    permission_classes = [TenantAwarePermission]


class TenantAwareRetrieveUpdateDestroyAPIView(TenantAwareQuerySetMixin, TenantAwareValidationMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Base API view for retrieving, updating, and deleting tenant-aware objects.
    """
    permission_classes = [TenantAwarePermission]
    
    def get_object(self):
        """Get object with tenant validation"""
        obj = super().get_object()
        
        # Additional tenant validation
        if not self.request.user.is_superuser:
            tenant_context = get_tenant_context()
            if tenant_context:
                if hasattr(obj, 'tenant_id'):
                    if str(obj.tenant_id) != str(tenant_context.get('tenant_id')):
                        raise Http404("Object not found")
                elif hasattr(obj, 'tenant'):
                    if str(obj.tenant.id) != str(tenant_context.get('tenant_id')):
                        raise Http404("Object not found")
        
        return obj


class TenantAwareListAPIView(TenantAwareQuerySetMixin, generics.ListAPIView):
    """
    Base API view for listing tenant-aware objects.
    """
    permission_classes = [TenantAwarePermission]


class TenantAwareCreateAPIView(TenantAwareValidationMixin, generics.CreateAPIView):
    """
    Base API view for creating tenant-aware objects.
    """
    permission_classes = [TenantAwarePermission]


class TenantAwareRetrieveAPIView(TenantAwareQuerySetMixin, generics.RetrieveAPIView):
    """
    Base API view for retrieving tenant-aware objects.
    """
    permission_classes = [TenantAwarePermission]
    
    def get_object(self):
        """Get object with tenant validation"""
        obj = super().get_object()
        
        # Additional tenant validation
        if not self.request.user.is_superuser:
            tenant_context = get_tenant_context()
            if tenant_context:
                if hasattr(obj, 'tenant_id'):
                    if str(obj.tenant_id) != str(tenant_context.get('tenant_id')):
                        raise Http404("Object not found")
                elif hasattr(obj, 'tenant'):
                    if str(obj.tenant.id) != str(tenant_context.get('tenant_id')):
                        raise Http404("Object not found")
        
        return obj


class SharedResourceMixin:
    """
    Mixin for resources that can be shared across tenants.
    Used for lookup tables like addresses, tariffs, etc.
    """
    
    def get_queryset(self):
        """Get queryset including shared resources"""
        queryset = super().get_queryset()
        
        # Skip tenant filtering for superusers
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return queryset
        
        # Get current tenant context
        tenant_context = get_tenant_context()
        if not tenant_context:
            return queryset.none()
        
        tenant_id = tenant_context.get('tenant_id')
        if not tenant_id:
            return queryset.none()
        
        # Include tenant-specific and shared resources
        if hasattr(queryset.model, 'is_shared'):
            return queryset.filter(
                models.Q(tenant_id=tenant_id) | models.Q(is_shared=True)
            )
        elif hasattr(queryset.model, 'is_shared_across_brands'):
            return queryset.filter(
                models.Q(tenant_id=tenant_id) | models.Q(is_shared_across_brands=True)
            )
        
        # Default to tenant-only filtering
        return queryset.filter(tenant_id=tenant_id)


class AuditTrailMixin:
    """
    Mixin that adds audit trail functionality to API views.
    Tracks who made changes and when for tenant operations.
    """
    
    def perform_create(self, serializer):
        """Create object with audit trail"""
        current_user = get_current_user()
        
        # Set audit fields if model supports them
        save_kwargs = {}
        if hasattr(serializer.Meta.model, 'created_by'):
            save_kwargs['created_by'] = current_user
        if hasattr(serializer.Meta.model, 'updated_by'):
            save_kwargs['updated_by'] = current_user
        
        # Call parent create method
        super().perform_create(serializer)
        
        # Log the creation
        logger.info(f"Created {serializer.Meta.model.__name__} {serializer.instance.id} by {current_user}")
    
    def perform_update(self, serializer):
        """Update object with audit trail"""
        current_user = get_current_user()
        
        # Set audit fields if model supports them
        save_kwargs = {}
        if hasattr(serializer.Meta.model, 'updated_by'):
            save_kwargs['updated_by'] = current_user
        
        # Call parent update method
        super().perform_update(serializer)
        
        # Log the update
        logger.info(f"Updated {serializer.Meta.model.__name__} {serializer.instance.id} by {current_user}")
    
    def perform_destroy(self, instance):
        """Delete object with audit trail"""
        current_user = get_current_user()
        
        # Log the deletion before it happens
        logger.info(f"Deleted {instance.__class__.__name__} {instance.id} by {current_user}")
        
        # Call parent destroy method
        super().perform_destroy(instance) 