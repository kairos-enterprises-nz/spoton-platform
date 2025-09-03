"""
Application layer models - to be configured later

Raw data import is handled by Airflow DAGs → TimescaleDB (direct SQL)
Application logic models will be configured later for business features.
"""

# Application layer models will be configured later
# Raw data import is handled by Airflow DAGs → TimescaleDB directly

"""
Connection models for utility service connections (electricity/broadband/mobile)
"""

import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import Tenant


class Connection(models.Model):
    """
    Utility service connection (electricity/broadband/mobile)
    Each connection represents a service point for a specific utility type.
    Connections belong to contracts, not directly to accounts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='connections')
    # Account relationship (for backward compatibility during migration)
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='connections', null=True, blank=True)
    # Contract relationship (stored as UUID for cross-app compatibility)
    contract_id = models.UUIDField(null=True, blank=True, help_text="Contract ID - references ServiceContract")
    
    # Service address (location)
    service_address = models.ForeignKey(
        'users.Address', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='connections',
        help_text="Physical location of the service (not required for mobile)"
    )
    
    # Service type and classification
    SERVICE_TYPE_CHOICES = [
        ('electricity', 'Electricity'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
        ('gas', 'Gas'),
    ]
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    
    # Service-specific identifiers (must be unique per tenant and service type)
    connection_identifier = models.CharField(
        max_length=100, 
        help_text="Primary identifier (ICP, ONT, Phone Number, SIM IMEI)"
    )
    
    # Electricity-specific fields (match database schema)
    icp_code = models.CharField(max_length=15, blank=True, help_text="Installation Control Point code")
    gxp_code = models.CharField(max_length=10, blank=True, help_text="Grid Exit Point code")
    meter_number = models.CharField(max_length=20, blank=True)
    
    # Broadband-specific fields (match database schema)
    ont_serial = models.CharField(max_length=50, blank=True, help_text="ONT serial number")
    line_speed = models.CharField(max_length=20, blank=True, help_text="Line speed capability")
    
    # Mobile-specific fields (match database schema)
    mobile_number = models.CharField(max_length=20, blank=True, help_text="Mobile phone number")
    sim_iccid = models.CharField(max_length=22, blank=True, help_text="SIM card ICCID")
    device_imei = models.CharField(max_length=17, blank=True, help_text="Device IMEI")
    
    # Connection status
    STATUS_CHOICES = [
        ('pending', 'Pending Installation'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('switching', 'Switching Provider'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Installation and service dates (match database schema)
    installation_date = models.DateField(null=True, blank=True)
    activation_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # Temporal tracking for versioning
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Audit trail (match database schema)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Flexible metadata storage
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'energy_connection'
        indexes = [
            models.Index(fields=['tenant', 'service_type', 'status']),
            models.Index(fields=['account', 'service_type']),
            models.Index(fields=['connection_identifier', 'service_type']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            # Unique constraint for ICP codes per tenant
            models.UniqueConstraint(
                fields=['tenant', 'icp_code'],
                condition=models.Q(icp_code__isnull=False) & ~models.Q(icp_code=''),
                name='unique_icp_per_tenant'
            ),
            # Unique constraint for ONT serials per tenant
            models.UniqueConstraint(
                fields=['tenant', 'ont_serial'],
                condition=models.Q(ont_serial__isnull=False) & ~models.Q(ont_serial=''),
                name='unique_ont_per_tenant'
            ),
            # Unique constraint for mobile numbers per tenant
            models.UniqueConstraint(
                fields=['tenant', 'mobile_number'],
                condition=models.Q(mobile_number__isnull=False) & ~models.Q(mobile_number=''),
                name='unique_mobile_per_tenant'
            ),
            # Unique constraint for SIM ICCID per tenant
            models.UniqueConstraint(
                fields=['tenant', 'sim_iccid'],
                condition=models.Q(sim_iccid__isnull=False) & ~models.Q(sim_iccid=''),
                name='unique_sim_per_tenant'
            ),
            # Unique constraint for device IMEI per tenant
            models.UniqueConstraint(
                fields=['tenant', 'device_imei'],
                condition=models.Q(device_imei__isnull=False) & ~models.Q(device_imei=''),
                name='unique_imei_per_tenant'
            ),
        ]

    def __str__(self):
        try:
            account_number = self.account.account_number if self.account else "NO-ACCOUNT"
        except:
            account_number = f"MISSING-{str(self.account_id)[:8]}" if self.account_id else "NO-ACCOUNT"
        return f"{self.connection_identifier} ({self.service_type}) - {account_number}"

    def clean(self):
        """Validate connection data based on service type"""
        if self.service_type == 'electricity' and not self.icp_code:
            raise ValidationError("ICP code is required for electricity connections")
        
        # ONT serial is optional for broadband - address is sufficient for identification
        # if self.service_type == 'broadband' and not self.ont_serial:
        #     raise ValidationError("ONT serial is required for broadband connections")
        
        if self.service_type == 'mobile' and not (self.mobile_number or self.sim_iccid):
            raise ValidationError("Mobile number or SIM ICCID is required for mobile connections")
        
        # Validate that connection_identifier matches service-specific identifier
        if self.service_type == 'electricity' and self.icp_code:
            self.connection_identifier = self.icp_code
        elif self.service_type == 'broadband' and self.ont_serial:
            self.connection_identifier = self.ont_serial
        elif self.service_type == 'mobile' and self.mobile_number:
            self.connection_identifier = self.mobile_number
        
        # Validate temporal constraints
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError("Valid to date must be after valid from date")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if connection is currently active"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.valid_from <= now and
            (self.valid_to is None or self.valid_to > now)
        )

    @property
    def contract(self):
        """Get the contract this connection belongs to"""
        if not self.contract_id:
            return None
        
        from core.contracts.models import ServiceContract
        
        try:
            return ServiceContract.objects.get(id=self.contract_id)
        except ServiceContract.DoesNotExist:
            return None


class ConnectionPlan(models.Model):
    """
    Links connections to pricing plans with temporal tracking
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='connection_plans')
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name='plan_assignments')
    
    # Plan reference (stored as flexible identifiers to support different plan types)
    plan_id = models.CharField(max_length=100, help_text="Plan identifier")
    plan_name = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=50, help_text="Plan type (electricity/broadband/mobile)")
    
    # Assignment details
    assigned_date = models.DateField(default=timezone.now)
    assigned_by = models.ForeignKey(
        'users.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="plan_assignments_created"
    )
    
    # Temporal tracking for versioning
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Plan-specific metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Plan-specific configuration")

    class Meta:
        db_table = 'energy_connectionplan'
        indexes = [
            models.Index(fields=['tenant', 'connection', 'valid_from']),
            models.Index(fields=['plan_id', 'plan_type']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            # Ensure only one active plan per connection at any time
            models.UniqueConstraint(
                fields=['connection', 'valid_from'],
                condition=models.Q(valid_to__isnull=True),
                name='unique_active_plan_per_connection'
            ),
        ]

    def __str__(self):
        return f"{self.connection.connection_identifier} - {self.plan_name}"

    def clean(self):
        """Validate plan assignment"""
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError("Valid to date must be after valid from date")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if plan assignment is currently active"""
        now = timezone.now()
        return (
            self.valid_from <= now and
            (self.valid_to is None or self.valid_to > now)
        )
