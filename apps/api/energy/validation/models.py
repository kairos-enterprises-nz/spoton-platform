"""
Meter Reading Validation Models

This module implements the comprehensive meter reading validation architecture:
- Register mapping for different meter types and tariff groups
- Validation rules and business logic configuration
- Validation results and audit tracking
- TimescaleDB integration for time-series data
- Validation workflow orchestration
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from users.models import Tenant, User, VersionedModel, VersionedManager
from energy.connections.models import Connection
from energy.metering.timescale_models import MeteringPoint, Register
from django.core.exceptions import ValidationError


# ===========================
# VALIDATION WORKFLOW MODELS
# ===========================

class ValidationWorkflow(VersionedModel):
    """
    Defines validation workflows for different meter types and scenarios.
    Orchestrates the entire validation process from raw data to final readings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Workflow identification
    workflow_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Workflow scope
    meter_type = models.CharField(
        max_length=20,
        choices=[
            ('hhr', 'Half-Hourly Readings'),
            ('drr', 'Daily Register Readings'),
            ('nhh', 'Non-Half-Hourly'),
            ('bulk', 'Bulk Readings'),
        ]
    )
    
    # Workflow configuration
    validation_rules = models.JSONField(
        default=list,
        help_text="Ordered list of validation rule codes to apply"
    )
    
    estimation_config = models.JSONField(
        default=dict,
        help_text="Configuration for estimation methods and thresholds"
    )
    
    processing_config = models.JSONField(
        default=dict,
        help_text="Batch processing configuration and limits"
    )
    
    # Workflow behavior
    is_active = models.BooleanField(default=True)
    auto_approve_threshold = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal('95.00'),
        help_text="Quality threshold for auto-approval"
    )
    
    # Scheduling
    schedule_expression = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cron expression for automatic execution"
    )
    
    objects = VersionedManager()

    class Meta:
        db_table = 'energy_validation_workflow'
        verbose_name = 'Validation Workflow'
        verbose_name_plural = 'Validation Workflows'
        ordering = ['workflow_code']

    def __str__(self):
        return f"{self.workflow_code} - {self.name}"


class ValidationSession(models.Model):
    """
    Tracks validation sessions for audit and monitoring.
    Each session represents a complete validation run.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Session identification
    session_id = models.CharField(max_length=100, unique=True)
    workflow = models.ForeignKey(ValidationWorkflow, on_delete=models.CASCADE)
    
    # Session scope
    start_date = models.DateField()
    end_date = models.DateField()
    meter_filter = models.JSONField(
        default=dict,
        help_text="Filter criteria for meters to process"
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    
    # Progress tracking
    total_readings = models.IntegerField(default=0)
    processed_readings = models.IntegerField(default=0)
    valid_readings = models.IntegerField(default=0)
    invalid_readings = models.IntegerField(default=0)
    estimated_readings = models.IntegerField(default=0)
    
    # Quality metrics
    overall_quality_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_duration = models.DurationField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validation_sessions_created'
    )
    
    # Error information
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Results summary
    results_summary = models.JSONField(
        default=dict,
        help_text="Summary of validation results and statistics"
    )

    class Meta:
        db_table = 'energy_validation_session'
        verbose_name = 'Validation Session'
        verbose_name_plural = 'Validation Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'workflow']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"Session {self.session_id} ({self.status})"


class ValidationRuleExecution(models.Model):
    """
    Tracks execution of individual validation rules within a session.
    Provides detailed audit trail for rule application.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to session and rule
    session = models.ForeignKey(
        ValidationSession,
        on_delete=models.CASCADE,
        related_name='rule_executions'
    )
    rule = models.ForeignKey('ValidationRule', on_delete=models.CASCADE)
    
    # Execution details
    execution_order = models.IntegerField()
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Execution results
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped'),
        ],
        default='pending'
    )
    
    # Statistics
    readings_processed = models.IntegerField(default=0)
    readings_passed = models.IntegerField(default=0)
    readings_failed = models.IntegerField(default=0)
    
    # Performance metrics
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Rule-specific results
    rule_results = models.JSONField(
        default=dict,
        help_text="Rule-specific results and metadata"
    )

    class Meta:
        db_table = 'energy_validation_rule_execution'
        verbose_name = 'Validation Rule Execution'
        verbose_name_plural = 'Validation Rule Executions'
        ordering = ['session', 'execution_order']
        unique_together = ['session', 'rule']

    def __str__(self):
        return f"{self.rule.rule_code} in {self.session.session_id}"


class EstimationSession(models.Model):
    """
    Tracks estimation sessions for gap filling and data correction.
    Links to validation sessions for complete audit trail.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to validation session
    validation_session = models.ForeignKey(
        ValidationSession,
        on_delete=models.CASCADE,
        related_name='estimation_sessions'
    )
    
    # Estimation scope
    estimation_method = models.CharField(
        max_length=50,
        choices=[
            ('interpolation', 'Linear Interpolation'),
            ('historical_average', 'Historical Average'),
            ('pattern_matching', 'Pattern Matching'),
            ('peer_comparison', 'Peer Comparison'),
            ('seasonal_profile', 'Seasonal Profile'),
            ('carry_forward', 'Carry Forward'),
            ('zero_fill', 'Zero Fill'),
        ]
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Statistics
    gaps_identified = models.IntegerField(default=0)
    gaps_filled = models.IntegerField(default=0)
    average_confidence = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    estimation_results = models.JSONField(
        default=dict,
        help_text="Detailed estimation results and statistics"
    )

    class Meta:
        db_table = 'energy_validation_estimation_session'
        verbose_name = 'Estimation Session'
        verbose_name_plural = 'Estimation Sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"Estimation {self.estimation_method} for {self.validation_session.session_id}"


# ===========================
# REGISTER MAPPING MODELS
# ===========================

class TariffRegisterMap(models.Model):
    """
    Maps register codes to tariff groups and business classifications.
    This decouples vendor-specific codes from business logic.
    """
    register_code = models.CharField(max_length=50, primary_key=True)
    
    # Business classification
    tariff_group = models.CharField(
        max_length=50,
        choices=[
            ('day', 'Day Rate'),
            ('night', 'Night Rate'),
            ('controlled', 'Controlled Load'),
            ('inclusive', 'Inclusive/Single Rate'),
            ('generation', 'Generation'),
            ('peak', 'Peak Rate'),
            ('off_peak', 'Off Peak Rate'),
            ('shoulder', 'Shoulder Rate'),
        ],
        help_text="Business tariff classification"
    )
    
    # Technical flags
    is_controlled = models.BooleanField(default=False, help_text="Controlled load register")
    is_generation = models.BooleanField(default=False, help_text="Generation register")
    is_import = models.BooleanField(default=True, help_text="Import register (consumption)")
    is_export = models.BooleanField(default=False, help_text="Export register")
    
    # Validation settings
    typical_daily_min = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Typical minimum daily usage (kWh)"
    )
    typical_daily_max = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Typical maximum daily usage (kWh)"
    )
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'energy_validation_tariff_register_map'
        verbose_name = 'Tariff Register Mapping'
        verbose_name_plural = 'Tariff Register Mappings'

    def __str__(self):
        return f"{self.register_code} ({self.tariff_group})"


class MeterType(models.Model):
    """
    Defines different meter types and their characteristics.
    """
    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    
    # Meter characteristics
    is_smart = models.BooleanField(default=False, help_text="Smart meter with remote reading")
    supports_hhr = models.BooleanField(default=False, help_text="Supports half-hourly readings")
    supports_interval = models.BooleanField(default=False, help_text="Supports interval data")
    
    # Reading frequency
    typical_read_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('bi_monthly', 'Bi-Monthly'),
            ('quarterly', 'Quarterly'),
            ('daily', 'Daily'),
            ('hourly', 'Hourly'),
            ('half_hourly', 'Half Hourly'),
        ],
        default='monthly'
    )
    
    # Supported registers
    supported_registers = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="List of supported register codes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'energy_validation_meter_type'
        verbose_name = 'Meter Type'
        verbose_name_plural = 'Meter Types'

    def __str__(self):
        return f"{self.code} - {self.name}"


# ===========================
# VALIDATION RULE MODELS
# ===========================

class ValidationRule(VersionedModel):
    """
    Configurable validation rules for meter readings.
    Rules can be applied by meter type, register, or ICP characteristics.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Rule identification
    rule_code = models.CharField(max_length=50, unique=True, default='UNKNOWN')
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Rule type and category
    rule_type = models.CharField(
        max_length=30,
        choices=[
            ('range_check', 'Range Check'),
            ('spike_detection', 'Spike Detection'),
            ('continuity_check', 'Continuity Check'),
            ('consistency_check', 'Consistency Check'),
            ('seasonal_check', 'Seasonal Check'),
            ('peer_comparison', 'Peer Comparison'),
            ('trend_analysis', 'Trend Analysis'),
            ('missing_data', 'Missing Data Check'),
            ('plausibility_check', 'Plausibility Check'),
        ]
    )
    
    category = models.CharField(
        max_length=20,
        choices=[
            ('critical', 'Critical'),
            ('warning', 'Warning'),
            ('informational', 'Informational'),
        ],
        default='warning'
    )
    
    # Rule parameters (JSON for flexibility)
    parameters = models.JSONField(
        default=dict,
        help_text="Rule-specific parameters (thresholds, limits, etc.)"
    )
    
    # Application scope
    applies_to_meter_types = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        help_text="Meter types this rule applies to (empty = all)"
    )
    
    applies_to_registers = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Register codes this rule applies to (empty = all)"
    )
    
    applies_to_tariff_groups = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Tariff groups this rule applies to (empty = all)"
    )
    
    # Rule behavior
    is_active = models.BooleanField(default=True)
    is_blocking = models.BooleanField(
        default=False,
        help_text="If true, failing this rule blocks further processing"
    )
    
    # Estimation behavior
    triggers_estimation = models.BooleanField(
        default=False,
        help_text="If true, failing this rule triggers estimation"
    )
    
    estimation_method = models.CharField(
        max_length=30,
        choices=[
            ('historical_average', 'Historical Average'),
            ('linear_interpolation', 'Linear Interpolation'),
            ('seasonal_profile', 'Seasonal Profile'),
            ('peer_average', 'Peer Average'),
            ('zero_fill', 'Zero Fill'),
            ('carry_forward', 'Carry Forward'),
        ],
        blank=True,
        null=True
    )
    
    # Priority and ordering
    priority = models.IntegerField(
        default=100,
        help_text="Lower numbers = higher priority"
    )
    
    objects = VersionedManager()

    class Meta:
        db_table = 'energy_validation_validation_rule'
        verbose_name = 'Validation Rule'
        verbose_name_plural = 'Validation Rules'
        ordering = ['priority', 'rule_code']

    def __str__(self):
        return f"{self.rule_code} - {self.name}"


class ValidationRuleOverride(VersionedModel):
    """
    Allows overriding validation rules for specific ICPs or date ranges.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Reference to the rule being overridden
    rule = models.ForeignKey('ValidationRule', on_delete=models.CASCADE)
    
    # Override scope
    icp_id = models.CharField(max_length=50, blank=True, help_text="Specific ICP (empty = all)")
    register_code = models.CharField(max_length=50, blank=True, help_text="Specific register (empty = all)")
    
    # Override parameters
    parameters = models.JSONField(
        default=dict,
        help_text="Override parameters (merged with rule parameters)"
    )
    
    # Override behavior
    is_disabled = models.BooleanField(
        default=False,
        help_text="If true, disable this rule for the scope"
    )
    
    # Reason and approval
    reason = models.TextField(help_text="Reason for override")
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validation_overrides_approved'
    )
    
    objects = VersionedManager()

    class Meta:
        db_table = 'energy_validation_validation_rule_override'
        verbose_name = 'Validation Rule Override'
        verbose_name_plural = 'Validation Rule Overrides'
        unique_together = ['tenant', 'rule', 'icp_id', 'register_code', 'valid_from']
        ordering = ['-valid_from']

    def __str__(self):
        return f"Override for {self.rule.rule_code} on {self.icp_id or 'all ICPs'}"


# ===========================
# VALIDATION EXECUTION MODELS
# ===========================

class ValidationBatch(models.Model):
    """
    Tracks validation batches for audit and monitoring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Batch identification
    batch_id = models.CharField(max_length=100, unique=True)
    source_file = models.CharField(max_length=500, blank=True)
    
    # Batch scope
    start_date = models.DateField()
    end_date = models.DateField()
    meter_type = models.CharField(max_length=20, blank=True)
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    
    # Statistics
    total_readings = models.IntegerField(default=0)
    valid_readings = models.IntegerField(default=0)
    invalid_readings = models.IntegerField(default=0)
    estimated_readings = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_duration = models.DurationField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validation_batches_created'
    )
    
    # Error information
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'energy_validation_validation_batch'
        verbose_name = 'Validation Batch'
        verbose_name_plural = 'Validation Batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.batch_id} ({self.status})"


class ValidationResult(models.Model):
    """
    Stores validation results for individual meter readings.
    This is the main audit trail for validation decisions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to validation batch
    batch = models.ForeignKey(
        ValidationBatch,
        on_delete=models.CASCADE,
        related_name='results',
        null=True,
        blank=True
    )
    
    # Reading identification
    icp_id = models.CharField(max_length=50, db_index=True, default='UNKNOWN')
    register_code = models.CharField(max_length=50, db_index=True, default='UNKNOWN')
    read_at = models.DateTimeField(db_index=True, default=timezone.now)
    
    # Original reading data
    original_kwh = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    original_status = models.CharField(max_length=20, blank=True)
    
    # Validation results
    final_kwh = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    final_status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Valid'),
            ('estimated', 'Estimated'),
            ('invalid', 'Invalid'),
            ('suspicious', 'Suspicious'),
            ('missing', 'Missing'),
        ],
        null=True,
        blank=True
    )
    
    # Validation details
    is_estimated = models.BooleanField(default=False)
    estimation_method = models.CharField(max_length=30, blank=True)
    estimation_confidence = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence percentage (0-100)"
    )
    
    # Rule results (bitmask for failed rules)
    rule_fail_mask = models.BigIntegerField(default=0)
    failed_rules = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="List of failed rule codes"
    )
    
    # Warnings and notes
    warnings = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True
    )
    
    validation_notes = models.TextField(blank=True)
    
    # Processing metadata
    processed_at = models.DateTimeField(default=timezone.now)
    processing_time_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'energy_validation_validation_result'
        verbose_name = 'Validation Result'
        verbose_name_plural = 'Validation Results'
        indexes = [
            models.Index(fields=['batch', 'icp_id']),
            models.Index(fields=['icp_id', 'register_code', 'read_at']),
            models.Index(fields=['final_status']),
            models.Index(fields=['is_estimated']),
            models.Index(fields=['processed_at']),
        ]

    def __str__(self):
        return f"{self.icp_id} {self.register_code} @ {self.read_at} ({self.final_status})"


# ===========================
# ESTIMATION MODELS
# ===========================

class EstimationProfile(VersionedModel):
    """
    Stores estimation profiles for different customer segments.
    Used for seasonal and peer-based estimation methods.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Profile identification
    profile_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Profile scope
    meter_type = models.CharField(max_length=20, blank=True)
    tariff_group = models.CharField(max_length=50, blank=True)
    customer_segment = models.CharField(
        max_length=20,
        choices=[
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('industrial', 'Industrial'),
        ],
        blank=True
    )
    
    # Profile data (seasonal patterns, peer averages, etc.)
    profile_data = models.JSONField(
        default=dict,
        help_text="Profile-specific data (seasonal curves, peer statistics, etc.)"
    )
    
    # Usage statistics
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    objects = VersionedManager()

    class Meta:
        db_table = 'energy_validation_estimation_profile'
        verbose_name = 'Estimation Profile'
        verbose_name_plural = 'Estimation Profiles'
        ordering = ['profile_code']

    def __str__(self):
        return f"{self.profile_code} - {self.name}"


class EstimationHistory(models.Model):
    """
    Tracks estimation history for audit and improvement.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to validation result
    validation_result = models.OneToOneField(
        'ValidationResult',
        on_delete=models.CASCADE,
        related_name='estimation_history'
    )
    
    # Estimation details
    method_used = models.CharField(max_length=30)
    profile_used = models.ForeignKey(
        'EstimationProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Input data for estimation
    input_data = models.JSONField(
        default=dict,
        help_text="Data used for estimation (historical values, peer data, etc.)"
    )
    
    # Estimation quality metrics
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    quality_indicators = models.JSONField(
        default=dict,
        help_text="Quality metrics (variance, correlation, etc.)"
    )
    
    # Subsequent accuracy (filled when actual reading arrives)
    actual_kwh = models.DecimalField(
        max_digits=15, decimal_places=3,
        null=True, blank=True,
        help_text="Actual reading when it becomes available"
    )
    
    estimation_error = models.DecimalField(
        max_digits=10, decimal_places=3,
        null=True, blank=True,
        help_text="Difference between estimated and actual"
    )
    
    estimation_error_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Percentage error"
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'energy_validation_estimation_history'
        verbose_name = 'Estimation History'
        verbose_name_plural = 'Estimation Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"Estimation for {self.validation_result}"


# ===========================
# MONITORING & SUMMARY MODELS
# ===========================

class ValidationSummary(models.Model):
    """
    Daily/hourly summaries of validation results for monitoring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Summary period
    summary_date = models.DateField(db_index=True)
    summary_hour = models.IntegerField(null=True, blank=True, help_text="Hour for hourly summaries")
    
    # Scope
    meter_type = models.CharField(max_length=20, blank=True)
    register_code = models.CharField(max_length=50, blank=True)
    
    # Counts
    total_readings = models.IntegerField(default=0)
    valid_readings = models.IntegerField(default=0)
    invalid_readings = models.IntegerField(default=0)
    estimated_readings = models.IntegerField(default=0)
    suspicious_readings = models.IntegerField(default=0)
    missing_readings = models.IntegerField(default=0)
    
    # Quality metrics
    validation_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Percentage of valid readings"
    )
    
    estimation_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Percentage of estimated readings"
    )
    
    # Rule failure statistics
    rule_failures = models.JSONField(
        default=dict,
        help_text="Count of failures by rule code"
    )
    
    # Timing statistics
    avg_processing_time_ms = models.IntegerField(null=True, blank=True)
    max_processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'energy_validation_validation_summary'
        verbose_name = 'Validation Summary'
        verbose_name_plural = 'Validation Summaries'
        unique_together = ['tenant', 'summary_date', 'summary_hour', 'meter_type', 'register_code']
        indexes = [
            models.Index(fields=['tenant', 'summary_date']),
        ]

    def __str__(self):
        return f"Summary for {self.summary_date} {self.meter_type or ''} {self.register_code or ''}"


class ImportLog(models.Model):
    """
    Tracks ingestion audit by file/source/provider.
    Stored in primary PostgreSQL database.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Import details
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash of file contents")
    
    # Source information
    source = models.CharField(max_length=100, help_text="Data source name")
    provider = models.CharField(max_length=100, help_text="Data provider name")
    
    # Import type
    IMPORT_TYPE_CHOICES = [
        ('metering', 'Metering Data'),
        ('registry', 'Registry Data'),
        ('switching', 'Switching Data'),
        ('tariff', 'Tariff Data'),
        ('other', 'Other Data'),
    ]
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPE_CHOICES)
    
    # Processing details
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)
    
    # Error details
    error_details = models.JSONField(default=list, blank=True)
    
    # Processing metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'source', 'provider']),
            models.Index(fields=['file_name']),
            models.Index(fields=['import_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.status}) - {self.import_type}"

    def complete(self, processed_records, error_records=0, error_details=None):
        self.status = 'partial' if error_records > 0 else 'completed'
        self.processed_records = processed_records
        self.error_records = error_records
        self.error_details = error_details or []
        self.completed_at = timezone.now()
        self.save()

    def fail(self, error_details=None):
        self.status = 'failed'
        self.error_details = error_details or []
        self.completed_at = timezone.now()
        self.save()


class ChangeLog(models.Model):
    """
    Tracks database change tracking (manual override, corrections).
    Stored in primary PostgreSQL database.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Change details
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Entity information
    entity_type = models.CharField(max_length=100, help_text="Model or entity type")
    entity_id = models.CharField(max_length=100, help_text="Primary key of the entity")
    
    # Change information
    CHANGE_TYPE_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('override', 'Manual Override'),
        ('correction', 'Correction'),
    ]
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    
    # Change details
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    # Reason and authorization
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name="validation_change_logs"
    )
    
    # Additional details
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'entity_type', 'entity_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['changed_by']),
        ]

    def __str__(self):
        return f"{self.change_type} on {self.entity_type} {self.entity_id} by {self.changed_by}"


class ValidationAuditLog(models.Model):
    """
    Logs all validation actions, failures, and overrides for audit purposes.
    """
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="User who performed the action, if applicable."
    )
    action = models.CharField(
        max_length=50,
        choices=[
            ('validation_run', 'Validation Run'),
            ('estimation_run', 'Estimation Run'),
            ('override_created', 'Override Created'),
            ('rule_updated', 'Rule Updated'),
        ]
    )
    related_rule = models.ForeignKey('ValidationRule', null=True, blank=True, on_delete=models.SET_NULL)
    related_result = models.ForeignKey('ValidationResult', null=True, blank=True, on_delete=models.SET_NULL)
    details = models.JSONField(help_text="Details of the action, e.g., what changed.")

    class Meta:
        db_table = 'energy_validation_audit_log'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
