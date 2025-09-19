from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from core.models import TenantAwareUUIDModel, TenantAwareMetadataModel


class ServicePlan(TenantAwareUUIDModel, TenantAwareMetadataModel):
    """
    Generic service plans across all utility types for white-label brands
    """
    SERVICE_TYPE_CHOICES = [
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
        ('bundle', 'Multi-Service Bundle'),
    ]
    
    PLAN_TYPE_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
        ('fixed', 'Fixed Rate'),
        ('variable', 'Variable Rate'),
        ('tiered', 'Tiered Pricing'),
        ('unlimited', 'Unlimited'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    # Plan identification
    plan_code = models.CharField(max_length=50, db_index=True)
    plan_name = models.CharField(max_length=200)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    
    # Plan details
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    setup_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Service-specific configuration
    service_config = models.JSONField(default=dict, blank=True, help_text="Service-specific settings")
    pricing_tiers = models.JSONField(default=list, blank=True, help_text="Tiered pricing structure")
    
    # Contract terms
    minimum_term_months = models.IntegerField(default=0)
    early_termination_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Availability
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    available_from = models.DateTimeField()
    available_to = models.DateTimeField(null=True, blank=True)
    
    # Marketing
    is_featured = models.BooleanField(default=False)
    is_promotional = models.BooleanField(default=False)
    promotional_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    promotional_end_date = models.DateTimeField(null=True, blank=True)
    
    # White-label specific
    is_shared_across_brands = models.BooleanField(
        default=False,
        help_text="Whether this plan is shared across all tenant brands"
    )
    
    class Meta:
        db_table = 'finance_serviceplan'
        indexes = [
            models.Index(fields=['tenant', 'service_type', 'status']),
            models.Index(fields=['tenant', 'plan_code']),
            models.Index(fields=['tenant', 'is_featured', 'status']),
            models.Index(fields=['is_shared_across_brands']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'plan_code'],
                name='unique_plan_code_per_tenant'
            )
        ]
    
    def __str__(self):
        brand_info = f" (Brand: {self.tenant.name})" if self.tenant else ""
        return f"{self.plan_code} - {self.plan_name}{brand_info}"


class PricingRule(TenantAwareUUIDModel):
    """
    Generic pricing rules that can be applied to any service for white-label brands
    """
    RULE_TYPE_CHOICES = [
        ('usage_based', 'Usage Based'),
        ('time_based', 'Time Based'),
        ('volume_discount', 'Volume Discount'),
        ('loyalty_discount', 'Loyalty Discount'),
        ('promotional', 'Promotional'),
        ('peak_pricing', 'Peak Pricing'),
        ('off_peak_pricing', 'Off Peak Pricing'),
    ]
    
    CALCULATION_METHOD_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ('per_unit', 'Per Unit'),
        ('tiered', 'Tiered'),
    ]
    
    service_plan = models.ForeignKey(ServicePlan, on_delete=models.CASCADE, related_name='pricing_rules')
    
    # Rule details
    rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Calculation
    calculation_method = models.CharField(max_length=15, choices=CALCULATION_METHOD_CHOICES)
    rate_value = models.DecimalField(max_digits=12, decimal_places=6)
    unit = models.CharField(max_length=20, default='each')
    
    # Conditions
    min_usage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    max_usage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Time constraints
    time_start = models.TimeField(null=True, blank=True)
    time_end = models.TimeField(null=True, blank=True)
    days_of_week = models.JSONField(default=list, blank=True)
    months = models.JSONField(default=list, blank=True)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Priority for rule application
    priority = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'finance_pricingrule'
        indexes = [
            models.Index(fields=['tenant', 'service_plan', 'rule_type']),
            models.Index(fields=['tenant', 'valid_from', 'valid_to']),
            models.Index(fields=['tenant', 'priority']),
        ]
        ordering = ['priority', 'created_at']
    
    def __str__(self):
        return f"{self.service_plan.plan_code} - {self.rule_name} (Brand: {self.tenant.name})"
    
    def _validate_tenant_consistency(self):
        """Validate tenant consistency with service plan"""
        super()._validate_tenant_consistency()
        
        if self.service_plan and self.service_plan.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError("Pricing rule and service plan must belong to the same tenant/brand")


class CustomerPricing(TenantAwareUUIDModel):
    """
    Customer-specific pricing overrides and custom rates for white-label brands
    """
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_pricing')
    service_plan = models.ForeignKey(ServicePlan, on_delete=models.CASCADE)
    
    # Custom pricing
    custom_base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Custom rules
    custom_pricing_rules = models.JSONField(default=dict, blank=True)
    
    # Validity
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)
    
    # Approval
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pricing')
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'finance_customerpricing'
        indexes = [
            models.Index(fields=['tenant', 'customer', 'service_plan']),
            models.Index(fields=['tenant', 'effective_from', 'effective_to']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'customer', 'service_plan', 'effective_from'],
                name='unique_customer_pricing_per_tenant'
            )
        ]
    
    def __str__(self):
        return f"{self.customer} - {self.service_plan.plan_code} - Custom Pricing (Brand: {self.tenant.name})"
    
    def _validate_tenant_consistency(self):
        """Validate tenant consistency with service plan and customer"""
        super()._validate_tenant_consistency()
        
        if self.service_plan and self.service_plan.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError("Customer pricing and service plan must belong to the same tenant/brand")


class PriceCalculation(TenantAwareUUIDModel):
    """
    Store calculated prices for billing periods for white-label brands
    """
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_calculations')
    service_plan = models.ForeignKey(ServicePlan, on_delete=models.CASCADE)
    
    # Billing period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Usage data
    usage_data = models.JSONField(default=dict, blank=True)
    
    # Calculated amounts
    base_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    usage_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Calculation breakdown
    calculation_details = models.JSONField(default=dict, blank=True)
    applied_rules = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'finance_pricecalculation'
        indexes = [
            models.Index(fields=['tenant', 'customer', 'period_start']),
            models.Index(fields=['tenant', 'service_plan', 'period_start']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'customer', 'service_plan', 'period_start'],
                name='unique_calculation_per_tenant'
            )
        ]
    
    def __str__(self):
        return f"{self.customer} - {self.service_plan.plan_code} - {self.period_start.date()} (Brand: {self.tenant.name})"
    
    def _validate_tenant_consistency(self):
        """Validate tenant consistency with service plan and customer"""
        super()._validate_tenant_consistency()
        
        if self.service_plan and self.service_plan.tenant != self.tenant:
            from django.core.exceptions import ValidationError
            raise ValidationError("Price calculation and service plan must belong to the same tenant/brand")


class Tariff(models.Model):
    """
    Pricing plan with support for various tariff types including TOU, fixed, spot, and C&I
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'users.Tenant', 
        on_delete=models.CASCADE, 
        related_name='tariffs',
        null=True,
        blank=True
    )
    
    # Tariff identification
    tariff_code = models.CharField(max_length=50, unique=True)
    tariff_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Tariff type and structure
    TARIFF_TYPE_CHOICES = [
        ('tou', 'Time of Use'),
        ('fixed', 'Fixed Rate'),
        ('spot', 'Spot Price'),
        ('ci', 'Commercial & Industrial'),
        ('prepaid', 'Prepaid'),
        ('demand', 'Demand Based'),
        ('tiered', 'Tiered/Block Rate'),
    ]
    tariff_type = models.CharField(max_length=20, choices=TARIFF_TYPE_CHOICES)
    
    # Service type this tariff applies to
    SERVICE_TYPE_CHOICES = [
        ('electricity', 'Electricity'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
    ]
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    
    # Pricing structure
    base_rate = models.DecimalField(
        max_digits=10, decimal_places=6, 
        default=Decimal('0.000000'),
        help_text="Base rate per unit (kWh, GB, minute)"
    )
    daily_charge = models.DecimalField(
        max_digits=8, decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Fixed daily charge"
    )
    
    # Demand charges (for C&I)
    demand_charge = models.DecimalField(
        max_digits=10, decimal_places=6,
        default=Decimal('0.000000'),
        help_text="Demand charge per kVA or kW"
    )
    
    # Network and regulatory charges
    network_charge = models.DecimalField(
        max_digits=8, decimal_places=6,
        default=Decimal('0.000000'),
        help_text="Network/distribution charge"
    )
    regulatory_charge = models.DecimalField(
        max_digits=8, decimal_places=6,
        default=Decimal('0.000000'),
        help_text="Regulatory/compliance charge"
    )
    
    # Tax and GST
    gst_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.1500'),
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="GST rate as decimal (0.15 = 15%)"
    )
    
    # Availability and versioning
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Temporal validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Eligibility criteria
    min_consumption = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        help_text="Minimum monthly consumption requirement"
    )
    max_consumption = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Maximum monthly consumption limit"
    )
    
    # Customer type restrictions
    CUSTOMER_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('government', 'Government'),
        ('any', 'Any Customer Type'),
    ]
    eligible_customer_types = models.JSONField(
        default=list,
        help_text="List of eligible customer types"
    )
    
    # Metadata and configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Additional tariff configuration and parameters"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tariffs'
    )
    updated_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_tariffs'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'tariff_type', 'service_type']),
            models.Index(fields=['is_active', 'valid_from', 'valid_to']),
            models.Index(fields=['tariff_code']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=models.F('valid_from')),
                name='valid_date_range'
            ),
            models.UniqueConstraint(
                fields=['tenant', 'service_type', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_tariff_per_service'
            )
        ]
    
    def __str__(self):
        return f"{self.tariff_code} - {self.tariff_name} ({self.service_type})"
    
    def is_valid_at(self, date_time=None):
        """Check if tariff is valid at given datetime"""
        if date_time is None:
            date_time = timezone.now()
        
        if not self.is_active:
            return False
            
        if date_time < self.valid_from:
            return False
            
        if self.valid_to and date_time > self.valid_to:
            return False
            
        return True
    
    def is_eligible_for_customer(self, customer_type, consumption=None):
        """Check if customer is eligible for this tariff"""
        if not self.is_active:
            return False
            
        # Check customer type eligibility
        if self.eligible_customer_types and 'any' not in self.eligible_customer_types:
            if customer_type not in self.eligible_customer_types:
                return False
        
        # Check consumption limits
        if consumption is not None:
            if self.min_consumption and consumption < self.min_consumption:
                return False
            if self.max_consumption and consumption > self.max_consumption:
                return False
        
        return True


class TariffProfile(models.Model):
    """
    Defines TOU time blocks for tariffs (weekday, weekend, holidays)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'users.Tenant', 
        on_delete=models.CASCADE, 
        related_name='tariff_profiles',
        null=True,
        blank=True
    )
    tariff = models.ForeignKey(
        'Tariff', 
        on_delete=models.CASCADE, 
        related_name='profiles',
        null=True,
        blank=True
    )
    
    # Profile identification
    profile_name = models.CharField(max_length=100)
    profile_code = models.CharField(max_length=20)
    
    # Time period definition
    DAY_TYPE_CHOICES = [
        ('weekday', 'Weekday'),
        ('weekend', 'Weekend'),
        ('holiday', 'Public Holiday'),
        ('special', 'Special Event Day'),
    ]
    day_type = models.CharField(max_length=20, choices=DAY_TYPE_CHOICES)
    
    # Time blocks (can have multiple per profile)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Time block classification
    BLOCK_TYPE_CHOICES = [
        ('peak', 'Peak'),
        ('shoulder', 'Shoulder'),
        ('off_peak', 'Off Peak'),
        ('controlled', 'Controlled Load'),
        ('uncontrolled', 'Uncontrolled Load'),
        ('night', 'Night Rate'),
        ('super_off_peak', 'Super Off Peak'),
    ]
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPE_CHOICES)
    
    # Seasonal applicability
    SEASON_CHOICES = [
        ('all', 'All Year'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('spring', 'Spring'),
        ('autumn', 'Autumn'),
    ]
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all')
    
    # Date range for seasonal profiles
    season_start = models.DateField(null=True, blank=True)
    season_end = models.DateField(null=True, blank=True)
    
    # Priority for overlapping blocks
    priority = models.PositiveIntegerField(default=1)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tariff', 'day_type', 'block_type']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['season', 'season_start', 'season_end']),
        ]
        ordering = ['day_type', 'start_time', 'priority']
    
    def __str__(self):
        return f"{self.tariff.tariff_code} - {self.profile_name} ({self.day_type}, {self.block_type})"
    
    def applies_to_datetime(self, dt):
        """Check if this profile applies to a given datetime"""
        # Check day type
        if self.day_type == 'weekday' and dt.weekday() >= 5:  # Sat/Sun
            return False
        elif self.day_type == 'weekend' and dt.weekday() < 5:  # Mon-Fri
            return False
        
        # Check time range
        time_obj = dt.time()
        if self.start_time <= self.end_time:
            # Normal time range (e.g., 09:00 to 17:00)
            if not (self.start_time <= time_obj <= self.end_time):
                return False
        else:
            # Overnight time range (e.g., 23:00 to 06:00)
            if not (time_obj >= self.start_time or time_obj <= self.end_time):
                return False
        
        # Check seasonal applicability
        if self.season != 'all' and self.season_start and self.season_end:
            date_obj = dt.date()
            if not (self.season_start <= date_obj <= self.season_end):
                return False
        
        return True


class PriceBlock(models.Model):
    """
    Per-band price (fixed/variable) for each tariff profile block
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'users.Tenant', 
        on_delete=models.CASCADE, 
        related_name='price_blocks',
        null=True,
        blank=True
    )
    tariff_profile = models.ForeignKey('TariffProfile', on_delete=models.CASCADE, related_name='price_blocks')
    
    # Price structure
    unit_rate = models.DecimalField(
        max_digits=10, decimal_places=6,
        help_text="Price per unit (cents per kWh, dollars per GB, etc.)"
    )
    
    # Tiered pricing support
    tier_number = models.PositiveIntegerField(default=1)
    tier_threshold_min = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Minimum usage for this tier"
    )
    tier_threshold_max = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Maximum usage for this tier"
    )
    
    # Block pricing (for demand charges)
    block_size = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Size of pricing block (kW, kVA, etc.)"
    )
    
    # Loss factors and adjustments
    loss_factor = models.DecimalField(
        max_digits=6, decimal_places=4,
        default=Decimal('1.0000'),
        help_text="Loss factor multiplier"
    )
    
    # Price adjustments
    price_adjustment = models.DecimalField(
        max_digits=8, decimal_places=6,
        default=Decimal('0.000000'),
        help_text="Additional price adjustment (+ or -)"
    )
    
    # Validity period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    description = models.CharField(max_length=200, blank=True)
    configuration = models.JSONField(
        default=dict,
        help_text="Additional pricing configuration"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tariff_profile', 'tier_number']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        ordering = ['tier_number', 'tier_threshold_min']
    
    def __str__(self):
        return f"{self.tariff_profile} - Tier {self.tier_number}: ${self.unit_rate}"
    
    def is_valid_at(self, date_time=None):
        """Check if price block is valid at given datetime"""
        if date_time is None:
            date_time = timezone.now()
            
        if date_time < self.valid_from:
            return False
            
        if self.valid_to and date_time > self.valid_to:
            return False
            
        return True
    
    def applies_to_usage(self, usage_amount):
        """Check if this price block applies to given usage amount"""
        if self.tier_threshold_min is not None and usage_amount < self.tier_threshold_min:
            return False
            
        if self.tier_threshold_max is not None and usage_amount > self.tier_threshold_max:
            return False
            
        return True
    
    def calculate_charge(self, usage_amount, include_adjustments=True):
        """Calculate charge for given usage amount"""
        if not self.applies_to_usage(usage_amount):
            return Decimal('0.00')
        
        # Calculate applicable usage within this tier
        applicable_usage = usage_amount
        
        if self.tier_threshold_min is not None:
            applicable_usage = max(0, usage_amount - self.tier_threshold_min)
            
        if self.tier_threshold_max is not None:
            tier_size = self.tier_threshold_max - (self.tier_threshold_min or 0)
            applicable_usage = min(applicable_usage, tier_size)
        
        # Calculate base charge
        base_charge = applicable_usage * self.unit_rate
        
        if include_adjustments:
            # Apply loss factor
            base_charge *= self.loss_factor
            
            # Apply price adjustment
            base_charge += (applicable_usage * self.price_adjustment)
        
        return base_charge.quantize(Decimal('0.01'))


class CustomerTariffOverride(models.Model):
    """
    Customer-specific tariff overrides and custom pricing
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'users.Tenant', 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE, related_name='tariff_overrides')
    # connection = models.ForeignKey('energy.connections.Connection', on_delete=models.CASCADE, related_name='tariff_overrides')
    
    # Base tariff being overridden
    base_tariff = models.ForeignKey('Tariff', on_delete=models.CASCADE, related_name='customer_overrides')
    
    # Override details
    override_name = models.CharField(max_length=200)
    override_reason = models.TextField()
    
    # Custom pricing
    custom_base_rate = models.DecimalField(
        max_digits=10, decimal_places=6,
        null=True, blank=True,
        help_text="Override base rate"
    )
    custom_daily_charge = models.DecimalField(
        max_digits=8, decimal_places=4,
        null=True, blank=True,
        help_text="Override daily charge"
    )
    custom_demand_charge = models.DecimalField(
        max_digits=10, decimal_places=6,
        null=True, blank=True,
        help_text="Override demand charge"
    )
    
    # Discount/markup
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
        help_text="Discount percentage (negative for markup)"
    )
    
    # Fixed credit/charge
    monthly_credit = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fixed monthly credit (negative for charge)"
    )
    
    # Approval and authorization
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_tariff_overrides'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Validity period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tariff_overrides'
    )
    
    # Metadata
    override_details = models.JSONField(
        default=dict,
        help_text="Additional override configuration and notes"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['account', 'valid_from']),
            models.Index(fields=['base_tariff', 'is_approved']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=models.F('valid_from')),
                name='override_valid_date_range'
            )
        ]
    
    def __str__(self):
        return f"{self.account} - {self.override_name} (Override of {self.base_tariff.tariff_code})"
    
    def is_active(self, date_time=None):
        """Check if override is currently active"""
        if not self.is_approved:
            return False
            
        if date_time is None:
            date_time = timezone.now()
            
        if date_time < self.valid_from:
            return False
            
        if self.valid_to and date_time > self.valid_to:
            return False
            
        return True
    
    def get_effective_rate(self, base_rate):
        """Calculate effective rate after applying override"""
        if self.custom_base_rate is not None:
            effective_rate = self.custom_base_rate
        else:
            effective_rate = base_rate
        
        # Apply discount/markup
        if self.discount_percentage != 0:
            multiplier = (100 - self.discount_percentage) / 100
            effective_rate *= multiplier
        
        return effective_rate.quantize(Decimal('0.000001')) 