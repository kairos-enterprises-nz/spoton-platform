"""
Application layer models - to be configured later

Raw data import is handled by Airflow DAGs → TimescaleDB (direct SQL)
Application logic models will be configured later for business features.
"""

# Application layer models will be configured later
# Raw data import is handled by Airflow DAGs → TimescaleDB directly

import uuid
from django.db import models
from django.utils import timezone
from decimal import Decimal


class ElectricityTariff(models.Model):
    """
    Electricity-specific tariff structures for NZ market compliance
    Complements finance.pricing.Tariff with electricity domain specifics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='electricity_tariffs')
    
    # Reference to generic pricing tariff
    base_tariff = models.OneToOneField(
        'pricing.Tariff', on_delete=models.CASCADE, 
        related_name='electricity_specifics',
        help_text="Links to the generic tariff in finance.pricing"
    )
    
    # Electricity market identifiers
    tariff_code = models.CharField(max_length=50, unique=True)
    distributor_code = models.CharField(max_length=20, blank=True)
    network_tariff_code = models.CharField(max_length=50, blank=True)
    
    # NZ Electricity Authority compliance
    CATEGORY_CHOICES = [
        ('residential', 'Residential'),
        ('low_user', 'Low User'),
        ('standard_user', 'Standard User'),
        ('general', 'General'),
        ('controlled', 'Controlled Load'),
        ('uncontrolled', 'Uncontrolled Load'),
        ('tou', 'Time of Use'),
        ('demand', 'Demand'),
        ('capacity', 'Capacity'),
    ]
    tariff_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Load characteristics
    CONNECTION_TYPE_CHOICES = [
        ('single_phase', 'Single Phase'),
        ('three_phase', 'Three Phase'),
        ('lv', 'Low Voltage'),
        ('hv', 'High Voltage'),
    ]
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPE_CHOICES, default='single_phase')
    
    # Capacity limits
    capacity_kva_min = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Minimum capacity in kVA"
    )
    capacity_kva_max = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Maximum capacity in kVA"
    )
    
    # Usage thresholds
    low_user_threshold_kwh = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Low user threshold in kWh per month"
    )
    
    # Network and regulatory charges
    lines_charge_daily = models.DecimalField(
        max_digits=8, decimal_places=4, default=Decimal('0.0000'),
        help_text="Daily lines charge"
    )
    lines_charge_variable = models.DecimalField(
        max_digits=8, decimal_places=6, default=Decimal('0.000000'),
        help_text="Variable lines charge per kWh"
    )
    
    # Authority levies
    electricity_authority_levy = models.DecimalField(
        max_digits=8, decimal_places=6, default=Decimal('0.000000'),
        help_text="EA levy per kWh"
    )
    
    # Market settlement
    reconciliation_participant = models.CharField(max_length=100, blank=True)
    settlement_code = models.CharField(max_length=20, blank=True)
    
    # Meter requirements
    METER_TYPE_CHOICES = [
        ('accumulation', 'Accumulation'),
        ('interval', 'Interval'),
        ('smart', 'Smart Meter'),
        ('prepaid', 'Prepaid'),
    ]
    required_meter_type = models.CharField(
        max_length=20, choices=METER_TYPE_CHOICES, 
        default='accumulation'
    )
    
    # TOU applicability
    has_tou_pricing = models.BooleanField(default=False)
    has_seasonal_pricing = models.BooleanField(default=False)
    has_demand_charges = models.BooleanField(default=False)
    
    # Validity and status
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    
    # Metadata
    description = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    eligibility_criteria = models.JSONField(default=dict)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_electricity_tariffs'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'tariff_category']),
            models.Index(fields=['tariff_code']),
            models.Index(fields=['distributor_code', 'network_tariff_code']),
            models.Index(fields=['effective_date', 'expiry_date']),
            models.Index(fields=['is_published']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(expiry_date__isnull=True) | 
                      models.Q(expiry_date__gt=models.F('effective_date')),
                name='electricity_tariff_valid_date_range'
            )
        ]
    
    def __str__(self):
        return f"{self.tariff_code} - {self.tariff_category}"
    
    def is_active(self):
        """Check if tariff is currently active"""
        today = timezone.now().date()
        if today < self.effective_date:
            return False
        if self.expiry_date and today > self.expiry_date:
            return False
        return self.is_published


class RegisterTariffMapping(models.Model):
    """
    Maps meter registers to tariff components for billing calculations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    
    electricity_tariff = models.ForeignKey(
        'ElectricityTariff', on_delete=models.CASCADE,
        related_name='register_mappings'
    )
    
    # Register identification
    register_code = models.CharField(
        max_length=10,
        help_text="Register code (e.g., A+, A-, B1, B2, C1, C2)"
    )
    
    REGISTER_TYPE_CHOICES = [
        ('import_active', 'Import Active (A+)'),
        ('export_active', 'Export Active (A-)'),
        ('import_reactive', 'Import Reactive (B+)'),
        ('export_reactive', 'Export Reactive (B-)'),
        ('controlled_load', 'Controlled Load'),
        ('uncontrolled_load', 'Uncontrolled Load'),
        ('generation', 'Generation'),
    ]
    register_type = models.CharField(max_length=20, choices=REGISTER_TYPE_CHOICES)
    
    # Tariff component mapping
    TARIFF_COMPONENT_CHOICES = [
        ('energy_charge', 'Energy Charge'),
        ('demand_charge', 'Demand Charge'),
        ('capacity_charge', 'Capacity Charge'),
        ('controlled_load', 'Controlled Load'),
        ('generation_credit', 'Generation Credit'),
        ('reactive_charge', 'Reactive Charge'),
    ]
    tariff_component = models.CharField(max_length=20, choices=TARIFF_COMPONENT_CHOICES)
    
    # TOU period mapping (if applicable)
    tou_period = models.CharField(
        max_length=20, blank=True,
        help_text="TOU period (peak, shoulder, off_peak, etc.)"
    )
    
    # Calculation parameters
    multiplier = models.DecimalField(
        max_digits=6, decimal_places=4, default=Decimal('1.0000'),
        help_text="Multiplier for register readings"
    )
    
    is_billing_register = models.BooleanField(
        default=True,
        help_text="Whether this register is used for billing"
    )
    is_settlement_register = models.BooleanField(
        default=True,
        help_text="Whether this register is used for market settlement"
    )
    
    # Priority for overlapping periods
    priority = models.PositiveIntegerField(default=1)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['electricity_tariff', 'register_code']),
            models.Index(fields=['register_type', 'tariff_component']),
            models.Index(fields=['tou_period']),
        ]
        unique_together = [
            ('electricity_tariff', 'register_code', 'tou_period')
        ]
    
    def __str__(self):
        return f"{self.electricity_tariff.tariff_code} - {self.register_code} ({self.tariff_component})"


class TariffVersion(models.Model):
    """
    Version control for electricity tariff changes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    
    electricity_tariff = models.ForeignKey(
        'ElectricityTariff', on_delete=models.CASCADE,
        related_name='versions'
    )
    
    # Version details
    version_number = models.CharField(max_length=20)
    version_date = models.DateTimeField(default=timezone.now)
    
    # Change tracking
    CHANGE_TYPE_CHOICES = [
        ('creation', 'Initial Creation'),
        ('price_update', 'Price Update'),
        ('structure_change', 'Structure Change'),
        ('regulatory_update', 'Regulatory Update'),
        ('correction', 'Correction'),
        ('withdrawal', 'Withdrawal'),
    ]
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    change_description = models.TextField()
    change_reason = models.TextField(blank=True)
    
    # Tariff data snapshot
    tariff_data = models.JSONField(
        help_text="Complete tariff configuration at this version"
    )
    
    # Approval workflow
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_tariff_versions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Regulatory compliance
    regulatory_filing_reference = models.CharField(max_length=100, blank=True)
    ea_notification_sent = models.BooleanField(default=False)
    ea_notification_date = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tariff_versions'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['electricity_tariff', 'version_date']),
            models.Index(fields=['change_type', 'requires_approval']),
            models.Index(fields=['approved_at']),
        ]
        ordering = ['-version_date']
    
    def __str__(self):
        return f"{self.electricity_tariff.tariff_code} v{self.version_number} ({self.change_type})"
    
    def is_approved(self):
        """Check if version is approved"""
        if not self.requires_approval:
            return True
        return self.approved_by is not None and self.approved_at is not None


class TariffApplication(models.Model):
    """
    Tracks application of tariffs to specific connections/accounts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    
    # Applied to
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='tariff_applications')
    connection = models.ForeignKey('connections.Connection', on_delete=models.CASCADE, related_name='tariff_applications')
    
    # Tariff details
    electricity_tariff = models.ForeignKey(
        'ElectricityTariff', on_delete=models.PROTECT,
        related_name='applications'
    )
    
    # Application period
    applied_from = models.DateField()
    applied_to = models.DateField(null=True, blank=True)
    
    # Application reason
    APPLICATION_REASON_CHOICES = [
        ('new_connection', 'New Connection'),
        ('customer_request', 'Customer Request'),
        ('tariff_change', 'Tariff Change'),
        ('meter_upgrade', 'Meter Upgrade'),
        ('load_change', 'Load Change'),
        ('regulatory_requirement', 'Regulatory Requirement'),
        ('correction', 'Correction'),
    ]
    application_reason = models.CharField(max_length=25, choices=APPLICATION_REASON_CHOICES)
    
    # Override pricing (if applicable)
    has_custom_pricing = models.BooleanField(default=False)
    custom_pricing_details = models.JSONField(default=dict, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('superseded', 'Superseded'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Approval
    approved_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_tariff_applications'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    application_notes = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tariff_applications'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['account', 'connection', 'applied_from']),
            models.Index(fields=['electricity_tariff', 'status']),
            models.Index(fields=['applied_from', 'applied_to']),
            models.Index(fields=['status', 'approved_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(applied_to__isnull=True) | 
                      models.Q(applied_to__gt=models.F('applied_from')),
                name='tariff_application_valid_date_range'
            )
        ]
    
    def __str__(self):
        return f"{self.connection} - {self.electricity_tariff.tariff_code} ({self.applied_from})"
    
    def is_active(self):
        """Check if application is currently active"""
        if self.status != 'active':
            return False
            
        today = timezone.now().date()
        if today < self.applied_from:
            return False
            
        if self.applied_to and today > self.applied_to:
            return False
            
        return True
