from django.db import models
from django.conf import settings
# from energy.connections.models import Connection  # Temporarily commented out
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError

# Import assignment models
from .plan_assignments import ContractPlanAssignment, ContractConnectionAssignment


class ContractManager(models.Manager):
    """Custom manager to handle tenant-aware queries"""
    
    def get_queryset(self):
        """Always include tenant in queries for RLS-style filtering"""
        return super().get_queryset()
    
    def for_tenant(self, tenant):
        """Filter contracts for a specific tenant"""
        return self.get_queryset().filter(tenant=tenant)


class ServiceContract(models.Model):
    """
    Service contracts for all utility types with time-slice support
    Contracts belong to accounts, not directly to users
    """
    CONTRACT_TYPE_CHOICES = [
        ('electricity', 'Electricity Supply'),
        ('gas', 'Gas Supply'),
        ('broadband', 'Broadband Service'),
        ('mobile', 'Mobile Service'),
        ('bundle', 'Multi-Service Bundle'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ]
    
    BILLING_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('annual', 'Annual'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Multi-tenancy support - CRITICAL for RLS-style filtering
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='service_contracts', db_index=True)
    
    # Contract identification
    contract_number = models.CharField(max_length=50, unique=True)
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='contracts')
    
    # Contract details
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    service_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Contract terms
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Status and lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Billing configuration
    billing_frequency = models.CharField(max_length=20, choices=BILLING_FREQUENCY_CHOICES, default='monthly')
    billing_day = models.IntegerField(default=1, help_text="Day of month/quarter for billing")
    
    # Financial terms
    base_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_required = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Temporal tracking for versioning
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contracts_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contracts_updated"
    )
    
    # Flexible metadata storage
    metadata = models.JSONField(default=dict, blank=True)

    # Use custom manager for tenant-aware queries
    objects = ContractManager()

    class Meta:
        db_table = 'contracts_servicecontract'
        unique_together = ('tenant', 'contract_number')
        indexes = [
            models.Index(fields=['tenant', 'account', 'status']),
            models.Index(fields=['contract_type', 'status']),
            models.Index(fields=['valid_from', 'valid_to']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['tenant']),  # Critical for RLS performance
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.service_name}"

    def clean(self):
        """Validate contract data and tenant consistency"""
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")
        
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError("Valid to date must be after valid from date")
        
        # Ensure account and contract belong to same tenant
        if self.account and self.account.tenant != self.tenant:
            raise ValidationError("Contract and account must belong to the same tenant")

    def save(self, *args, **kwargs):
        self.clean()
        
        # Generate contract number if not provided
        if not self.contract_number:
            self.contract_number = self.generate_contract_number()
        
        super().save(*args, **kwargs)

    @staticmethod
    def generate_contract_number():
        """Generate unique contract number as CON########
        Uses the numeric portion of existing contract_number values to avoid MAX on UUID fields.
        """
        from django.db.models import Max
        from django.db.models.functions import Cast
        from django.db.models import IntegerField
        from django.db.models import Value
        from django.db.models.expressions import Subquery

        # Extract numeric tail using database function via casting approach:
        # Fallback approach: fetch last 1 by created_at and increment; if none, start at 1
        last_numeric = None
        try:
            # Filter only well-formed numbers and take max over the numeric suffix
            # Because regex extraction is DB-specific, do a lightweight Python-side fallback
            last_num = 0
            for cn in ServiceContract.objects.values_list('contract_number', flat=True).iterator():
                if isinstance(cn, str) and cn.startswith('CON') and cn[3:].isdigit():
                    n = int(cn[3:])
                    if n > last_num:
                        last_num = n
            last_numeric = last_num
        except Exception:
            last_numeric = None
        next_num = (last_numeric or 0) + 1
        return f"CON{str(next_num).zfill(8)}"

    @property
    def is_active(self):
        """Check if contract is currently active"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now and
            (self.end_date is None or self.end_date > now) and
            self.valid_from <= now and
            (self.valid_to is None or self.valid_to > now)
        )


class ContractService(models.Model):
    """
    Individual services within a contract (for bundle contracts)
    Now properly in public schema with tenant filtering
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ensure tenant consistency through the contract relationship
    contract = models.ForeignKey(ServiceContract, on_delete=models.CASCADE, related_name='services')
    # connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name='contract_services', null=True, blank=True)  # Temporarily commented out
    
    # Service details
    service_type = models.CharField(max_length=20)  # Temporarily removed choices reference
    service_plan = models.CharField(max_length=100)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Service-specific configuration
    service_config = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    activation_date = models.DateTimeField(null=True, blank=True)
    deactivation_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contracts_contractservice'
        indexes = [
            models.Index(fields=['contract', 'service_type']),
            # Note: tenant filtering happens through contract relationship
            # models.Index(fields=['connection']),  # Temporarily commented out
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.service_type}"

    @property
    def tenant(self):
        """Get tenant through contract relationship"""
        return self.contract.tenant if self.contract else None


class ContractAmendment(models.Model):
    """
    Track contract amendments and changes
    """
    AMENDMENT_TYPE_CHOICES = [
        ('rate_change', 'Rate Change'),
        ('term_extension', 'Term Extension'),
        ('service_addition', 'Service Addition'),
        ('service_removal', 'Service Removal'),
        ('address_change', 'Address Change'),
        ('billing_change', 'Billing Change'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    contract = models.ForeignKey(ServiceContract, on_delete=models.CASCADE, related_name='amendments')
    amendment_number = models.CharField(max_length=50)
    
    # Amendment details
    amendment_type = models.CharField(max_length=20, choices=AMENDMENT_TYPE_CHOICES)
    description = models.TextField()
    reason = models.TextField()
    
    # Changes
    changes_summary = models.JSONField(default=dict, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Dates
    requested_date = models.DateTimeField()
    effective_date = models.DateTimeField()
    approved_date = models.DateTimeField(null=True, blank=True)
    implemented_date = models.DateTimeField(null=True, blank=True)
    
    # Status and approval
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_amendments')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_amendments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['amendment_number']),
        ]
        unique_together = ['contract', 'amendment_number']
    
    def __str__(self):
        return f"{self.contract.contract_number} - Amendment {self.amendment_number}"


class ContractDocument(models.Model):
    """
    Store contract-related documents
    """
    DOCUMENT_TYPE_CHOICES = [
        ('contract', 'Main Contract'),
        ('amendment', 'Amendment'),
        ('terms', 'Terms & Conditions'),
        ('schedule', 'Rate Schedule'),
        ('application', 'Application Form'),
        ('authorization', 'Authorization'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    contract = models.ForeignKey(ServiceContract, on_delete=models.CASCADE, related_name='documents')
    amendment = models.ForeignKey(ContractAmendment, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    
    # Document details
    document_type = models.CharField(max_length=15, choices=DOCUMENT_TYPE_CHOICES)
    document_name = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    is_current = models.BooleanField(default=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['contract', 'document_type']),
            models.Index(fields=['is_current', 'version']),
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.document_name}" 


class ContractTemplate(models.Model):
    """
    Contract templates for different service types and customer segments
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='contract_templates')
    
    # Template identification
    template_code = models.CharField(max_length=50, unique=True)
    template_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Service type this template applies to
    SERVICE_TYPE_CHOICES = [
        ('electricity', 'Electricity'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
        ('multi_service', 'Multi-Service Bundle'),
    ]
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    
    # Customer segment
    CUSTOMER_SEGMENT_CHOICES = [
        ('residential', 'Residential'),
        ('small_business', 'Small Business'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('government', 'Government'),
    ]
    customer_segment = models.CharField(max_length=20, choices=CUSTOMER_SEGMENT_CHOICES)
    
    # Contract terms template
    terms_template = models.TextField(help_text="Contract terms template with placeholders")
    
    # Default contract parameters
    default_term_months = models.PositiveIntegerField(
        default=12,
        help_text="Default contract term in months"
    )
    minimum_term_months = models.PositiveIntegerField(
        default=1,
        help_text="Minimum allowable contract term"
    )
    maximum_term_months = models.PositiveIntegerField(
        default=36,
        help_text="Maximum allowable contract term"
    )
    
    # Pricing defaults
    has_early_termination_fee = models.BooleanField(default=False)
    early_termination_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Early termination fee amount"
    )
    
    # Cooling-off period
    cooling_off_days = models.PositiveIntegerField(
        default=10,
        help_text="Cooling-off period in days"
    )
    
    # Required clauses and compliance
    required_clauses = models.JSONField(
        default=list,
        help_text="List of required legal clauses"
    )
    compliance_requirements = models.JSONField(
        default=dict,
        help_text="Regulatory compliance requirements"
    )
    
    # Template status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    effective_date = models.DateTimeField(default=timezone.now)
    supersedes = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='superseded_by'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_contract_templates'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'service_type', 'customer_segment']),
            models.Index(fields=['is_active', 'effective_date']),
            models.Index(fields=['template_code']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'service_type', 'customer_segment', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_template_per_segment'
            )
        ]
    
    def __str__(self):
        return f"{self.template_code} - {self.template_name} ({self.service_type})"


class ContractStatus(models.TextChoices):
    CREATED = 'CREATED', 'Created'
    READY = 'READY', 'Ready for Switching'
    SWITCH_GAIN = 'SWITCH_GAIN', 'Switch Gain in Progress'
    ACTIVE = 'ACTIVE', 'Active'
    SWITCH_LOSS = 'SWITCH_LOSS', 'Switch Loss in Progress'
    SWITCH_WITHDRAWAL_PENDING = 'SWITCH_WITHDRAWAL_PENDING', 'Switch Withdrawal Pending'
    INACTIVE = 'INACTIVE', 'Inactive'
    CANCELLED = 'CANCELLED', 'Cancelled'


class ElectricityContract(models.Model):
    """
    Electricity-specific contract with ICP, tariff, and network details
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='electricity_contracts')
    
    # Contract identification
    contract_number = models.CharField(max_length=50, unique=True)
    
    # Parties
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='electricity_contracts')
    # connection = models.ForeignKey('energy.connections.Connection', on_delete=models.CASCADE, related_name='electricity_contracts')
    
    # Contract template
    template = models.ForeignKey('ContractTemplate', on_delete=models.PROTECT, related_name='electricity_contracts')
    
    # Electricity-specific details
    icp_code = models.CharField(max_length=15)
    gxp_code = models.CharField(max_length=10, blank=True)
    network_company = models.CharField(max_length=100, blank=True)
    
    # Tariff and pricing
    tariff = models.ForeignKey(
        'pricing.Tariff', on_delete=models.PROTECT, 
        related_name='electricity_contracts'
    )
    
    # Load characteristics
    LOAD_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('low_user', 'Low User'),
        ('standard_user', 'Standard User'),
        ('controlled_load', 'Controlled Load'),
        ('uncontrolled_load', 'Uncontrolled Load'),
        ('time_of_use', 'Time of Use'),
    ]
    load_type = models.CharField(max_length=20, choices=LOAD_TYPE_CHOICES)
    
    # Capacity and demand
    agreed_capacity_kva = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Agreed maximum demand in kVA"
    )
    maximum_demand_kw = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Maximum demand in kW"
    )
    
    # Meter details
    meter_number = models.CharField(max_length=50, blank=True)
    meter_type = models.CharField(
        max_length=20,
        choices=[
            ('accumulation', 'Accumulation'),
            ('interval', 'Interval'),
            ('smart', 'Smart Meter'),
        ],
        blank=True
    )
    
    # Network tariff and charges
    network_tariff_code = models.CharField(max_length=50, blank=True)
    distribution_charge = models.DecimalField(
        max_digits=8, decimal_places=6,
        default=Decimal('0.000000'),
        help_text="Distribution charge per kWh"
    )
    transmission_charge = models.DecimalField(
        max_digits=8, decimal_places=6,
        default=Decimal('0.000000'),
        help_text="Transmission charge per kWh"
    )
    
    # Contract terms
    contract_start_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    term_months = models.PositiveIntegerField()
    
    # Pricing overrides
    custom_unit_rate = models.DecimalField(
        max_digits=10, decimal_places=6,
        null=True, blank=True,
        help_text="Custom unit rate override"
    )
    custom_daily_charge = models.DecimalField(
        max_digits=8, decimal_places=4,
        null=True, blank=True,
        help_text="Custom daily charge override"
    )
    
    # Status and workflow
    status = models.CharField(max_length=30, choices=ContractStatus.choices, default=ContractStatus.CREATED)
    
    ready_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Timestamp when status first transitioned to READY. Marks the start of the NT submission SLA.")
    
    # Legal and compliance
    signed_date = models.DateField(null=True, blank=True)
    signed_by_customer = models.BooleanField(default=False)
    signed_by_retailer = models.BooleanField(default=False)
    
    # Termination details
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.CharField(max_length=200, blank=True)
    early_termination_fee_applied = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_electricity_contracts'
    )
    
    class Meta:
        db_table = 'contracts_electricitycontract'
        indexes = [
            models.Index(fields=['tenant', 'account', 'status']),
            models.Index(fields=['icp_code', 'contract_start_date']),
            # models.Index(fields=['connection', 'status']),
            models.Index(fields=['contract_start_date', 'contract_end_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(contract_end_date__isnull=True) | 
                      models.Q(contract_end_date__gt=models.F('contract_start_date')),
                name='electricity_contract_valid_date_range'
            )
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.icp_code} ({self.status})"
    
    def is_active(self):
        """Check if contract is currently active"""
        if self.status != 'active':
            return False
        
        today = timezone.now().date()
        if today < self.contract_start_date:
            return False
            
        if self.contract_end_date and today > self.contract_end_date:
            return False
            
        return True


class BroadbandContract(models.Model):
    """
    Broadband service contract with address, ONT, and plan details
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='broadband_contracts')
    
    # Contract identification
    contract_number = models.CharField(max_length=50, unique=True)
    
    # Parties
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='broadband_contracts')
    # connection = models.ForeignKey('energy.connections.Connection', on_delete=models.CASCADE, related_name='broadband_contracts')
    
    # Contract template
    template = models.ForeignKey('ContractTemplate', on_delete=models.PROTECT, related_name='broadband_contracts')
    
    # Service address
    service_address = models.ForeignKey(
        'users.Address', on_delete=models.PROTECT,
        related_name='broadband_contracts'
    )
    
    # Technology and infrastructure
    TECHNOLOGY_CHOICES = [
        ('fibre', 'Fibre'),
        ('vdsl', 'VDSL'),
        ('adsl', 'ADSL'),
        ('cable', 'Cable'),
        ('wireless', 'Wireless'),
        ('satellite', 'Satellite'),
    ]
    technology_type = models.CharField(max_length=20, choices=TECHNOLOGY_CHOICES)
    
    # Equipment details
    ont_serial = models.CharField(max_length=50, blank=True)
    router_serial = models.CharField(max_length=50, blank=True)
    equipment_provided = models.JSONField(
        default=list,
        help_text="List of equipment provided by ISP"
    )
    
    # Service plan
    plan_name = models.CharField(max_length=100)
    download_speed_mbps = models.PositiveIntegerField(help_text="Download speed in Mbps")
    upload_speed_mbps = models.PositiveIntegerField(help_text="Upload speed in Mbps")
    data_allowance_gb = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Monthly data allowance in GB (null for unlimited)"
    )
    
    # Service level agreement
    uptime_guarantee_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('99.50'),
        help_text="Uptime guarantee percentage"
    )
    support_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic Support'),
            ('standard', 'Standard Support'),
            ('premium', 'Premium Support'),
        ],
        default='standard'
    )
    
    # Installation details
    installation_date = models.DateField(null=True, blank=True)
    installation_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    installation_notes = models.TextField(blank=True)
    
    # Contract terms
    contract_start_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    term_months = models.PositiveIntegerField()
    
    # Pricing
    monthly_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Monthly service fee"
    )
    setup_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Status and workflow
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_installation', 'Pending Installation'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Legal and compliance
    signed_date = models.DateField(null=True, blank=True)
    signed_by_customer = models.BooleanField(default=False)
    cooling_off_expires = models.DateField(null=True, blank=True)
    
    # Termination details
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.CharField(max_length=200, blank=True)
    early_termination_fee_applied = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_broadband_contracts'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'account', 'status']),
            models.Index(fields=['ont_serial', 'status']),
            # models.Index(fields=['connection', 'status']),
            models.Index(fields=['contract_start_date', 'contract_end_date']),
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.plan_name} ({self.status})"
    
    def is_active(self):
        """Check if contract is currently active"""
        if self.status != 'active':
            return False
        
        today = timezone.now().date()
        if today < self.contract_start_date:
            return False
            
        if self.contract_end_date and today > self.contract_end_date:
            return False
            
        return True


class MobileContract(models.Model):
    """
    Mobile service contract with phone numbers, SIM, and plan details
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='mobile_contracts')
    
    # Contract identification
    contract_number = models.CharField(max_length=50, unique=True)
    
    # Parties
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='mobile_contracts')
    # connection = models.ForeignKey('energy.connections.Connection', on_delete=models.CASCADE, related_name='mobile_contracts')
    
    # Contract template
    template = models.ForeignKey('ContractTemplate', on_delete=models.PROTECT, related_name='mobile_contracts')
    
    # Mobile service details
    mobile_number = models.CharField(max_length=20)
    sim_id = models.CharField(max_length=50, blank=True)
    iccid = models.CharField(max_length=22, blank=True, help_text="SIM card ICCID")
    
    # Device details
    device_imei = models.CharField(max_length=17, blank=True)
    device_make = models.CharField(max_length=50, blank=True)
    device_model = models.CharField(max_length=100, blank=True)
    device_provided = models.BooleanField(default=False)
    
    # Service plan
    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('prepaid', 'Prepaid'),
            ('postpaid', 'Postpaid'),
            ('hybrid', 'Hybrid'),
        ]
    )
    
    # Allowances
    voice_minutes = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Monthly voice minutes (null for unlimited)"
    )
    sms_count = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Monthly SMS count (null for unlimited)"
    )
    data_allowance_gb = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Monthly data allowance in GB (null for unlimited)"
    )
    
    # Network and coverage
    NETWORK_TYPE_CHOICES = [
        ('2g', '2G'),
        ('3g', '3G'),
        ('4g', '4G LTE'),
        ('5g', '5G'),
    ]
    network_type = models.CharField(max_length=10, choices=NETWORK_TYPE_CHOICES, default='4g')
    
    # International services
    international_roaming = models.BooleanField(default=False)
    international_calling = models.BooleanField(default=False)
    
    # Contract terms
    contract_start_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    term_months = models.PositiveIntegerField()
    
    # Pricing
    monthly_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Monthly service fee"
    )
    activation_fee = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Device financing (if applicable)
    device_cost = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    device_monthly_payment = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    device_payment_months = models.PositiveIntegerField(default=0)
    
    # Status and workflow
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_activation', 'Pending Activation'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Activation details
    activation_date = models.DateField(null=True, blank=True)
    porting_required = models.BooleanField(default=False)
    previous_provider = models.CharField(max_length=100, blank=True)
    
    # Legal and compliance
    signed_date = models.DateField(null=True, blank=True)
    signed_by_customer = models.BooleanField(default=False)
    cooling_off_expires = models.DateField(null=True, blank=True)
    
    # Termination details
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.CharField(max_length=200, blank=True)
    early_termination_fee_applied = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_mobile_contracts'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'account', 'status']),
            models.Index(fields=['mobile_number', 'status']),
            # models.Index(fields=['connection', 'status']),
            models.Index(fields=['contract_start_date', 'contract_end_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'mobile_number'],
                condition=models.Q(status__in=['active', 'suspended']),
                name='unique_active_mobile_number_per_tenant'
            )
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.mobile_number} ({self.status})"
    
    def is_active(self):
        """Check if contract is currently active"""
        if self.status != 'active':
            return False
        
        today = timezone.now().date()
        if today < self.contract_start_date:
            return False
            
        if self.contract_end_date and today > self.contract_end_date:
            return False
            
        return True


class ContractVersion(models.Model):
    """
    Version history for contract changes and amendments
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='contract_versions')
    
    # Contract reference (generic foreign key pattern)
    CONTRACT_TYPE_CHOICES = [
        ('electricity', 'Electricity Contract'),
        ('broadband', 'Broadband Contract'),
        ('mobile', 'Mobile Contract'),
    ]
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    contract_id = models.UUIDField()
    
    # Version details
    version_number = models.CharField(max_length=20)
    version_date = models.DateTimeField(default=timezone.now)
    
    # Change details
    change_type = models.CharField(
        max_length=20,
        choices=[
            ('creation', 'Initial Creation'),
            ('amendment', 'Amendment'),
            ('renewal', 'Renewal'),
            ('termination', 'Termination'),
            ('suspension', 'Suspension'),
            ('reactivation', 'Reactivation'),
        ]
    )
    change_description = models.TextField()
    change_reason = models.TextField(blank=True)
    
    # Contract data snapshot
    contract_data = models.JSONField(
        help_text="Complete contract data at this version"
    )
    
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_contract_versions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Legal and compliance
    legal_review_required = models.BooleanField(default=False)
    legal_reviewed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='legal_reviewed_contract_versions'
    )
    legal_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_contract_versions'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'contract_type', 'contract_id']),
            models.Index(fields=['version_date', 'change_type']),
            models.Index(fields=['requires_approval', 'approved_at']),
        ]
        ordering = ['-version_date']
    
    def __str__(self):
        return f"{self.contract_type} {self.contract_id} - v{self.version_number} ({self.change_type})"
    
    def is_approved(self):
        """Check if version is approved"""
        if not self.requires_approval:
            return True
        return self.approved_by is not None and self.approved_at is not None 