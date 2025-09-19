from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class ElectricityPlan(models.Model):
    """Model for electricity pricing plans with multi-tenancy and temporal support"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Explicit UUID PK
    PLAN_TYPES = [
        ('fixed', 'Fixed Price Plan'),
        ('tou', 'Time of Use Plan'),
        ('spot', 'Spot Plan'),
    ]
    
    TERMS = [
        ('12_month', '12 Month'),
        ('24_month', '24 Month'),
        ('open_term', 'Open Term'),
    ]
    
    # Primary identification
    pricing_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    plan_id = models.CharField(max_length=100, unique=True)  # Changed to CharField for tenant-specific IDs
    
    # Multi-tenancy support
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='electricity_plans')
    
    # Plan details
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    term = models.CharField(max_length=20, choices=TERMS)
    terms_url = models.CharField(max_length=200)
    
    # Geographic availability
    city = models.CharField(max_length=50)
    
    # Base pricing
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    rate_details = models.TextField()
    monthly_charge = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True) # New field
    
    # Standard user charges
    standard_daily_charge = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    standard_variable_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    
    # Low user charges
    low_user_daily_charge = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    low_user_variable_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    
    # Time-based charges (for TOU plans)
    peak_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    off_peak_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    low_user_peak_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    low_user_off_peak_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    
    # Spot pricing charges
    wholesale_rate = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    network_charge = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(0)], null=True, blank=True)
    
    # Temporal tracking for versioning
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Status and timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['plan_id']
        verbose_name = 'Electricity Plan'
        verbose_name_plural = 'Electricity Plans'
        indexes = [
            models.Index(fields=['tenant', 'city', 'is_active']),
            models.Index(fields=['tenant', 'plan_type', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'plan_id'],
                name='unique_electricity_plan_per_tenant'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city.capitalize()} ({self.tenant.name})"
    
    def get_charges_data(self):
        """Return structured charges data for API response"""
        def safe_float(value, default=0.0):
            """Safely convert value to float, returning default if None"""
            return float(value) if value is not None else default
        
        charges = {
            "standard": {
                "daily_charge": {"amount": safe_float(self.standard_daily_charge), "unit": "$/day"},
            },
            "lowUser": {
                "daily_charge": {"amount": safe_float(self.low_user_daily_charge), "unit": "$/day"},
            }
        }
        
        if self.plan_type == 'fixed':
            charges["standard"]["variable_charge"] = {"amount": safe_float(self.standard_variable_charge), "unit": "$/kWh"}
            charges["lowUser"]["variable_charge"] = {"amount": safe_float(self.low_user_variable_charge), "unit": "$/kWh"}
        elif self.plan_type == 'tou':
            charges["standard"]["peak_charge"] = {"amount": safe_float(self.peak_charge), "unit": "$/kWh"}
            charges["standard"]["off_peak_charge"] = {"amount": safe_float(self.off_peak_charge), "unit": "$/kWh"}
            charges["lowUser"]["peak_charge"] = {"amount": safe_float(self.low_user_peak_charge), "unit": "$/kWh"}
            charges["lowUser"]["off_peak_charge"] = {"amount": safe_float(self.low_user_off_peak_charge), "unit": "$/kWh"}
        elif self.plan_type == 'spot':
            charges["standard"]["wholesale_rate"] = {"amount": safe_float(self.wholesale_rate), "unit": "$/kWh"}
            charges["standard"]["network_charge"] = {"amount": safe_float(self.network_charge), "unit": "$/kWh"}
        
        return charges


class BroadbandPlan(models.Model):
    """Model for broadband pricing plans with multi-tenancy and temporal support"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Explicit UUID PK
    PLAN_TYPES = [
        ('fibre', 'Fibre Broadband'),
        ('wireless', 'Fixed Wireless'),
        ('rural', 'Rural Broadband'),
    ]
    
    TERMS = [
        ('12_month', '12 Month'),
        ('24_month', '24 Month'),
        ('open_term', 'Open Term'),
    ]
    
    # Primary identification
    pricing_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    plan_id = models.CharField(max_length=100, unique=True)  # Changed to CharField for tenant-specific IDs
    
    # Multi-tenancy support
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='broadband_plans')
    
    # Plan details
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    term = models.CharField(max_length=20, choices=TERMS)
    terms_url = models.CharField(max_length=200)
    
    # Geographic availability
    city = models.CharField(max_length=50)
    
    # Pricing
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    rate_details = models.TextField()
    monthly_charge = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Additional charges based on plan type
    setup_fee = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    data_allowance = models.CharField(max_length=50, default="Unlimited")  # e.g., "Unlimited", "500GB", etc.
    
    # Speed specifications
    download_speed = models.CharField(max_length=50, blank=True)  # e.g., "100 Mbps"
    upload_speed = models.CharField(max_length=50, blank=True)    # e.g., "20 Mbps"
    
    # Temporal tracking for versioning
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Status and timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['plan_id']
        verbose_name = 'Broadband Plan'
        verbose_name_plural = 'Broadband Plans'
        indexes = [
            models.Index(fields=['tenant', 'city', 'is_active']),
            models.Index(fields=['tenant', 'plan_type', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'plan_id'],
                name='unique_broadband_plan_per_tenant'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city.capitalize()} ({self.tenant.name})"
    
    def get_charges_data(self):
        """Return structured charges data for API response"""
        charges = {
            "monthly_charge": float(self.monthly_charge)
        }
        
        if self.setup_fee > 0:
            charges["setup_fee"] = float(self.setup_fee)
            
        return charges


class PricingRegion(models.Model):
    """Model to manage pricing regions and their availability"""
    
    SERVICE_TYPES = [
        ('electricity', 'Electricity'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
        ('both', 'Both Services'),
        ('all', 'All Services'),
    ]
    
    city = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    service_availability = models.CharField(max_length=20, choices=SERVICE_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Geographic coordinates (optional for future features)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_name']
        verbose_name = 'Pricing Region'
        verbose_name_plural = 'Pricing Regions'
    
    def __str__(self):
        return f"{self.display_name} ({self.city})"
    
    @property
    def electricity_available(self):
        return self.service_availability in ['electricity', 'both', 'all']
    
    @property
    def broadband_available(self):
        return self.service_availability in ['broadband', 'both', 'all']
    
    @property
    def mobile_available(self):
        return self.service_availability in ['mobile', 'all']


class MobilePlan(models.Model):
    """Model for mobile pricing plans with multi-tenancy and temporal support"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Explicit UUID PK
    PLAN_TYPES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
        ('business', 'Business'),
    ]
    
    TERMS = [
        ('12_month', '12 Month'),
        ('24_month', '24 Month'),
        ('open_term', 'Open Term'),
    ]
    
    # Primary identification
    pricing_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    plan_id = models.CharField(max_length=100, unique=True)  # Changed to CharField for tenant-specific IDs
    
    # Multi-tenancy support
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='mobile_plans')
    
    # Plan details
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    term = models.CharField(max_length=20, choices=TERMS)
    terms_url = models.CharField(max_length=200)
    
    # Geographic availability (universal across NZ)
    city = models.CharField(max_length=50, default='nz')
    
    # Base pricing
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    rate_details = models.TextField()
    monthly_charge = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Plan features
    data_allowance = models.CharField(max_length=50)  # e.g., "10GB", "Unlimited"
    minutes = models.CharField(max_length=50)  # e.g., "Unlimited", "100 minutes"
    texts = models.CharField(max_length=50)  # e.g., "Unlimited", "1000 texts"
    
    # Additional charges
    setup_fee = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    sim_card_fee = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    
    # Rate details
    data_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)  # Rate per GB after allowance
    minute_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)  # Rate per minute after allowance
    text_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)  # Rate per text after allowance
    
    # Additional features
    international_minutes = models.CharField(max_length=50, default='0')  # e.g., "30 minutes", "Unlimited"
    international_texts = models.CharField(max_length=50, default='0')  # e.g., "100 texts", "Unlimited"
    international_data = models.CharField(max_length=50, default='0')  # e.g., "1GB", "Unlimited"
    hotspot_data = models.CharField(max_length=50, default='0')  # e.g., "5GB", "Unlimited"
    rollover_data = models.BooleanField(default=False)  # Whether unused data rolls over
    data_speed = models.CharField(max_length=50, default='Full Speed')  # e.g., "Full Speed", "5Mbps"
    
    # Temporal tracking for versioning
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Status and timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plan_id']
        verbose_name = 'Mobile Plan'
        verbose_name_plural = 'Mobile Plans'
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['tenant', 'plan_type', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'plan_id'],
                name='unique_mobile_plan_per_tenant'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def get_charges_data(self):
        """Return structured charges data for API response"""
        charges = {
            "monthly_charge": float(self.monthly_charge),
            "setup_fee": float(self.setup_fee),
            "sim_card_fee": float(self.sim_card_fee),
            "data_rate": float(self.data_rate),
            "minute_rate": float(self.minute_rate),
            "text_rate": float(self.text_rate)
        }
        
        features = {
            "data_allowance": self.data_allowance,
            "minutes": self.minutes,
            "texts": self.texts,
            "international_minutes": self.international_minutes,
            "international_texts": self.international_texts,
            "international_data": self.international_data,
            "hotspot_data": self.hotspot_data,
            "rollover_data": self.rollover_data,
            "data_speed": self.data_speed
        }
        
        return {
            "charges": charges,
            "features": features
        }
