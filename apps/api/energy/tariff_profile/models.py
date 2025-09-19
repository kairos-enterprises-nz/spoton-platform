"""
Application layer models - to be configured later

Raw data import is handled by Airflow DAGs → TimescaleDB (direct SQL)
Application logic models will be configured later for business features.
"""

# Application layer models will be configured later
# Raw data import is handled by Airflow DAGs → TimescaleDB directly

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import datetime


class ElectricityTOUProfile(models.Model):
    """
    Electricity-specific Time of Use profiles for NZ market
    Complements finance.pricing.TariffProfile with electricity domain specifics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='electricity_tou_profiles')
    
    # Reference to generic pricing profile
    base_profile = models.OneToOneField(
        'pricing.TariffProfile', on_delete=models.CASCADE,
        related_name='electricity_specifics',
        help_text="Links to the generic TOU profile in finance.pricing"
    )
    
    # Profile identification
    profile_code = models.CharField(max_length=50, unique=True)
    profile_name = models.CharField(max_length=200)
    
    # NZ specific profile types
    PROFILE_TYPE_CHOICES = [
        ('residential_tou', 'Residential TOU'),
        ('commercial_tou', 'Commercial TOU'),
        ('industrial_tou', 'Industrial TOU'),
        ('controlled_load', 'Controlled Load'),
        ('uncontrolled_load', 'Uncontrolled Load'),
        ('generation', 'Generation Profile'),
        ('demand_profile', 'Demand Profile'),
        ('capacity_profile', 'Capacity Profile'),
    ]
    profile_type = models.CharField(max_length=25, choices=PROFILE_TYPE_CHOICES)
    
    # Network/distributor alignment
    distributor_code = models.CharField(max_length=20, blank=True)
    network_profile_code = models.CharField(max_length=50, blank=True)
    
    # Seasonal variations
    has_seasonal_variation = models.BooleanField(default=False)
    summer_start_month = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month when summer period starts (1-12)"
    )
    summer_end_month = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month when summer period ends (1-12)"
    )
    
    # Holiday handling
    HOLIDAY_TREATMENT_CHOICES = [
        ('weekend', 'Treat as Weekend'),
        ('weekday', 'Treat as Weekday'),
        ('special', 'Special Holiday Rates'),
        ('ignore', 'Ignore Holiday Status'),
    ]
    holiday_treatment = models.CharField(
        max_length=10, choices=HOLIDAY_TREATMENT_CHOICES, 
        default='weekend'
    )
    
    # DST handling
    dst_adjustment_method = models.CharField(
        max_length=20,
        choices=[
            ('skip_hour', 'Skip Missing Hour'),
            ('repeat_hour', 'Repeat Extra Hour'),
            ('pro_rata', 'Pro-rata Adjustment'),
        ],
        default='pro_rata'
    )
    
    # Validity period
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    description = models.TextField(blank=True)
    usage_notes = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_electricity_tou_profiles'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'profile_type']),
            models.Index(fields=['profile_code']),
            models.Index(fields=['distributor_code', 'network_profile_code']),
            models.Index(fields=['effective_date', 'expiry_date']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(expiry_date__isnull=True) | 
                      models.Q(expiry_date__gt=models.F('effective_date')),
                name='electricity_tou_profile_valid_date_range'
            )
        ]
    
    def __str__(self):
        return f"{self.profile_code} - {self.profile_name}"
    
    def is_currently_active(self):
        """Check if profile is currently active"""
        today = timezone.now().date()
        if today < self.effective_date:
            return False
        if self.expiry_date and today > self.expiry_date:
            return False
        return self.is_active


class TOUPeriodDefinition(models.Model):
    """
    Defines specific TOU periods within an electricity profile
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    
    tou_profile = models.ForeignKey(
        'ElectricityTOUProfile', on_delete=models.CASCADE,
        related_name='period_definitions'
    )
    
    # Period identification
    period_code = models.CharField(
        max_length=20,
        help_text="Period code (e.g., PEAK, SHOULDER, OFFPEAK, CONTROLLED)"
    )
    period_name = models.CharField(max_length=100)
    
    # Period classification
    PERIOD_TYPE_CHOICES = [
        ('peak', 'Peak'),
        ('shoulder', 'Shoulder'),
        ('off_peak', 'Off Peak'),
        ('controlled', 'Controlled Load'),
        ('night_boost', 'Night Boost'),
        ('weekend', 'Weekend'),
        ('holiday', 'Holiday'),
        ('demand', 'Demand Period'),
    ]
    period_type = models.CharField(max_length=15, choices=PERIOD_TYPE_CHOICES)
    
    # Seasonal applicability
    SEASON_CHOICES = [
        ('all_year', 'All Year'),
        ('summer', 'Summer Only'),
        ('winter', 'Winter Only'),
        ('shoulder_season', 'Shoulder Season'),
    ]
    applicable_season = models.CharField(
        max_length=15, choices=SEASON_CHOICES, default='all_year'
    )
    
    # Day type applicability
    applies_weekdays = models.BooleanField(default=True)
    applies_saturdays = models.BooleanField(default=False)
    applies_sundays = models.BooleanField(default=False)
    applies_holidays = models.BooleanField(default=False)
    
    # Time boundaries
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Handle overnight periods (e.g., 23:00 to 07:00)
    spans_midnight = models.BooleanField(default=False)
    
    # Priority for overlapping periods
    priority = models.PositiveIntegerField(default=1)
    
    # Billing characteristics
    is_billable_period = models.BooleanField(default=True)
    is_settlement_period = models.BooleanField(default=True)
    
    # Load control
    is_controlled_load = models.BooleanField(default=False)
    control_signal_required = models.BooleanField(default=False)
    
    # Metadata
    description = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tou_profile', 'period_code']),
            models.Index(fields=['period_type', 'applicable_season']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['priority']),
        ]
        unique_together = [
            ('tou_profile', 'period_code', 'applicable_season')
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(spans_midnight=True) | 
                      models.Q(end_time__gt=models.F('start_time')),
                name='tou_period_valid_time_range'
            )
        ]
    
    def __str__(self):
        return f"{self.tou_profile.profile_code} - {self.period_code} ({self.start_time}-{self.end_time})"
    
    def get_duration_minutes(self):
        """Calculate period duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        
        if self.spans_midnight:
            # Add 24 hours to end time for overnight periods
            return (end_minutes + 1440) - start_minutes
        else:
            return end_minutes - start_minutes
    
    def is_time_in_period(self, check_time, check_date=None):
        """Check if a given time falls within this period"""
        if check_date:
            # Check day type applicability
            weekday = check_date.weekday()  # 0=Monday, 6=Sunday
            
            if weekday < 5 and not self.applies_weekdays:  # Mon-Fri
                return False
            elif weekday == 5 and not self.applies_saturdays:  # Saturday
                return False
            elif weekday == 6 and not self.applies_sundays:  # Sunday
                return False
        
        # Check time boundaries
        if self.spans_midnight:
            return check_time >= self.start_time or check_time <= self.end_time
        else:
            return self.start_time <= check_time <= self.end_time


class TOUHolidayCalendar(models.Model):
    """
    Defines holidays for TOU profile calculations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    
    # Holiday identification
    holiday_name = models.CharField(max_length=100)
    holiday_date = models.DateField()
    
    # Holiday type
    HOLIDAY_TYPE_CHOICES = [
        ('public', 'Public Holiday'),
        ('regional', 'Regional Holiday'),
        ('provincial', 'Provincial Anniversary'),
        ('custom', 'Custom Holiday'),
        ('observance', 'Observance Day'),
    ]
    holiday_type = models.CharField(max_length=15, choices=HOLIDAY_TYPE_CHOICES)
    
    # Regional applicability
    region_code = models.CharField(max_length=20, blank=True)
    applies_nationwide = models.BooleanField(default=True)
    
    # TOU treatment
    TREATMENT_CHOICES = [
        ('weekend_rates', 'Apply Weekend Rates'),
        ('weekday_rates', 'Apply Weekday Rates'),
        ('special_rates', 'Apply Special Holiday Rates'),
        ('no_change', 'No Rate Change'),
    ]
    tou_treatment = models.CharField(
        max_length=15, choices=TREATMENT_CHOICES, 
        default='weekend_rates'
    )
    
    # Recurring holiday rules
    is_recurring = models.BooleanField(default=False)
    RECURRENCE_CHOICES = [
        ('annual', 'Annual (same date)'),
        ('relative', 'Relative (e.g., first Monday)'),
        ('easter', 'Easter-based calculation'),
        ('custom', 'Custom Rule'),
    ]
    recurrence_type = models.CharField(
        max_length=10, choices=RECURRENCE_CHOICES, blank=True
    )
    recurrence_rule = models.TextField(
        blank=True,
        help_text="JSON or text description of recurrence rule"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    description = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tou_holidays'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'holiday_date']),
            models.Index(fields=['holiday_type', 'region_code']),
            models.Index(fields=['is_active', 'applies_nationwide']),
            models.Index(fields=['holiday_date', 'tou_treatment']),
        ]
        unique_together = [
            ('tenant', 'holiday_name', 'holiday_date')
        ]
    
    def __str__(self):
        return f"{self.holiday_name} ({self.holiday_date})"
    
    def is_applicable_for_region(self, region_code=None):
        """Check if holiday applies to a specific region"""
        if self.applies_nationwide:
            return True
        if region_code and self.region_code:
            return self.region_code.upper() == region_code.upper()
        return False


class TOUProfileAssignment(models.Model):
    """
    Links TOU profiles to specific electricity tariffs or connections
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    
    # Assignment target
    # electricity_tariff = models.ForeignKey(
    #     'tariffs.ElectricityTariff', on_delete=models.CASCADE,
    #     related_name='tou_assignments'
    # )
    
    # TOU profile
    tou_profile = models.ForeignKey(
        'ElectricityTOUProfile', on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Assignment period
    assigned_from = models.DateField()
    assigned_to = models.DateField(null=True, blank=True)
    
    # Register mapping
    register_codes = models.JSONField(
        default=list,
        help_text="List of register codes this profile applies to"
    )
    
    # Priority for multiple profiles
    priority = models.PositiveIntegerField(default=1)
    
    # Assignment reason
    ASSIGNMENT_REASON_CHOICES = [
        ('tariff_creation', 'Tariff Creation'),
        ('profile_update', 'Profile Update'),
        ('regulatory_change', 'Regulatory Change'),
        ('customer_request', 'Customer Request'),
        ('meter_change', 'Meter Change'),
        ('correction', 'Correction'),
    ]
    assignment_reason = models.CharField(
        max_length=20, choices=ASSIGNMENT_REASON_CHOICES
    )
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('superseded', 'Superseded'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    
    # Approval
    approved_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_tou_assignments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    assignment_notes = models.TextField(blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tou_assignments'
    )
    
    class Meta:
        indexes = [
            # models.Index(fields=['electricity_tariff', 'assigned_from']),
            models.Index(fields=['tou_profile', 'status']),
            models.Index(fields=['assigned_from', 'assigned_to']),
            models.Index(fields=['status', 'priority']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(assigned_to__isnull=True) | 
                      models.Q(assigned_to__gt=models.F('assigned_from')),
                name='tou_assignment_valid_date_range'
            )
        ]
    
    def __str__(self):
        return f"{self.tou_profile.profile_code} assignment"
    
    def is_active_on_date(self, check_date):
        """Check if assignment is active on a specific date"""
        if self.status != 'active':
            return False
            
        if check_date < self.assigned_from:
            return False
            
        if self.assigned_to and check_date > self.assigned_to:
            return False
            
        return True
