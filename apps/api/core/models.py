"""
Core abstract models and managers for multi-tenant architecture.
Provides base classes with tenant isolation and row-level security.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid


class TenantAwareManager(models.Manager):
    """
    Custom manager that automatically filters by tenant.
    Provides tenant-aware querysets and validation.
    """
    
    def get_queryset(self):
        """Get queryset filtered by current tenant context"""
        from utilitybyte.middleware import get_tenant_context
        
        qs = super().get_queryset()
        
        # Get current tenant context
        tenant_context = get_tenant_context()
        if tenant_context and tenant_context.get('tenant_id'):
            # Only filter if we have a valid tenant context
            qs = qs.filter(tenant_id=tenant_context['tenant_id'])
        
        return qs
    
    def for_tenant(self, tenant):
        """Explicitly filter for a specific tenant"""
        return super().get_queryset().filter(tenant=tenant)
    
    def all_tenants(self):
        """Get all records across all tenants (admin use only)"""
        return super().get_queryset()
    
    def create(self, **kwargs):
        """Override create to ensure tenant is set"""
        if 'tenant' not in kwargs and 'tenant_id' not in kwargs:
            from utilitybyte.middleware import get_tenant_context
            tenant_context = get_tenant_context()
            if tenant_context and tenant_context.get('tenant_id'):
                kwargs['tenant_id'] = tenant_context['tenant_id']
        
        return super().create(**kwargs)


class TenantAwareModel(models.Model):
    """
    Abstract base model that provides tenant isolation.
    All business models should inherit from this.
    """
    
    tenant = models.ForeignKey(
        'users.Tenant',
        on_delete=models.CASCADE,
        db_index=True,
        related_name="%(app_label)s_%(class)s_records",
        help_text="Tenant this record belongs to",
        null=True,
        blank=True
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated"
    )
    
    objects = TenantAwareManager()
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
    
    def clean(self):
        """Validate tenant consistency across related models"""
        super().clean()
        
        # Validate tenant consistency with related models
        self._validate_tenant_consistency()
    
    def _validate_tenant_consistency(self):
        """
        Validate that all related models belong to the same tenant.
        Override in subclasses to add specific validation rules.
        """
        pass
    
    def save(self, *args, **kwargs):
        """Override save to ensure tenant is set and validated"""
        # Set tenant from context if not provided
        if not self.tenant_id:
            from utilitybyte.middleware import get_tenant_context
            tenant_context = get_tenant_context()
            if tenant_context and tenant_context.get('tenant_id'):
                self.tenant_id = tenant_context['tenant_id']
        
        # Set audit fields
        if not self.pk:  # Creating new record
            if not self.created_by:
                # Try to get current user from context
                pass  # Will be handled by middleware
        else:  # Updating existing record
            if not self.updated_by:
                # Try to get current user from context
                pass  # Will be handled by middleware
        
        # Validate before saving
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_tenant_field_name(cls):
        """Get the name of the tenant field for this model"""
        return 'tenant'
    
    def get_tenant(self):
        """Get the tenant this record belongs to"""
        return self.tenant


class VersionedTenantModel(TenantAwareModel):
    """
    Abstract model for tenant-aware versioned records.
    Provides temporal tracking with tenant isolation.
    """
    
    version = models.CharField(max_length=20, default='1.0')
    is_current = models.BooleanField(default=True, db_index=True)
    effective_date = models.DateTimeField(db_index=True)
    expiry_date = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'is_current']),
            models.Index(fields=['tenant', 'effective_date']),
            models.Index(fields=['tenant', 'version']),
        ]
    
    def clean(self):
        """Additional validation for versioned records"""
        super().clean()
        
        if self.expiry_date and self.effective_date and self.expiry_date <= self.effective_date:
            raise ValidationError("Expiry date must be after effective date")
    
    def create_new_version(self, **kwargs):
        """Create a new version of this record"""
        # Mark current version as not current
        self.is_current = False
        self.save()
        
        # Create new version
        new_version = self.__class__.objects.create(
            tenant=self.tenant,
            version=self._get_next_version(),
            is_current=True,
            **kwargs
        )
        
        return new_version
    
    def _get_next_version(self):
        """Generate next version number"""
        try:
            parts = self.version.split('.')
            major, minor = int(parts[0]), int(parts[1])
            return f"{major}.{minor + 1}"
        except (ValueError, IndexError):
            return "1.1"


class TenantAwareTimestampedModel(TenantAwareModel):
    """
    Abstract model for tenant-aware time-series data.
    Optimized for TimescaleDB hypertables.
    """
    
    timestamp = models.DateTimeField(db_index=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
        ]
        # This will be converted to TimescaleDB hypertable
        # partitioned by tenant and timestamp


class TenantAwareMetadataModel(TenantAwareModel):
    """
    Abstract model with flexible metadata storage.
    """
    
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True
    
    def set_metadata(self, key, value):
        """Set metadata key-value pair"""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value
    
    def get_metadata(self, key, default=None):
        """Get metadata value by key"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)


class TenantAwareUUIDModel(TenantAwareModel):
    """
    Abstract model with UUID primary key and tenant awareness.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True 