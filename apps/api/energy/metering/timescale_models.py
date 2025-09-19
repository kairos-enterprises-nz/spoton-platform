"""
TimescaleDB Models for Metering Data

This module defines the TimescaleDB hypertables for storing:
- Raw meter readings (meter_raw_*)
- Validated meter readings (meter_calc_*)

These tables are optimized for time-series data with proper partitioning and indexing.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from users.models import Tenant
from energy.connections.models import Connection
import uuid


class MeteringPoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name="metering_points")
    meter_number = models.CharField(max_length=50, help_text="Meter serial number")
    meter_point_code = models.CharField(max_length=50, blank=True, help_text="Utility-specific meter point code")
    meter_type = models.CharField(max_length=20, choices=[
        ("smart", "Smart Meter"), ("legacy", "Legacy Meter"), ("amr", "Automated Meter Reading"),
        ("interval", "Interval Meter"), ("prepay", "Prepayment Meter"), ("import", "Import Only"),
        ("export", "Export Only"), ("import_export", "Import/Export")
    ])
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    installation_date = models.DateField(null=True, blank=True)
    certification_date = models.DateField(null=True, blank=True)
    certification_expiry = models.DateField(null=True, blank=True)
    location_description = models.CharField(max_length=200, blank=True, help_text="E.g., 'Garage wall', 'Exterior south wall'")
    status = models.CharField(max_length=20, default="active", choices=[
        ("active", "Active"), ("inactive", "Inactive"), ("pending", "Pending Installation"),
        ("removed", "Removed"), ("faulty", "Faulty")
    ])
    is_interval_capable = models.BooleanField(default=True)
    is_remote_readable = models.BooleanField(default=True)
    interval_length_minutes = models.IntegerField(default=30, help_text="Typical interval length in minutes")
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'metering_meteringpoint'
        unique_together = ('tenant', 'meter_number')
        indexes = [
            models.Index(fields=['tenant', 'connection']),
            models.Index(fields=['meter_number']),
            models.Index(fields=['meter_type', 'status']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]

    def __str__(self):
        return f"{self.meter_number} ({self.connection.icp_id})"


class Register(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    metering_point = models.ForeignKey(MeteringPoint, on_delete=models.CASCADE, related_name='registers')
    register_number = models.CharField(max_length=50)
    register_code = models.CharField(max_length=50)
    tou_type = models.CharField(max_length=20, choices=[
        ('peak', 'Peak'), ('offpeak', 'Off-Peak'), ('shoulder', 'Shoulder'), ('all_day', 'All Day')
    ])
    unit = models.CharField(max_length=20, default='kWh')
    multiplier = models.DecimalField(max_digits=10, decimal_places=5, default=1.0)
    register_type = models.CharField(max_length=20, choices=[
        ('consumption', 'Consumption'), ('generation', 'Generation'), ('power_factor', 'Power Factor')
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'metering_register'
        indexes = [
            models.Index(fields=['tenant', 'metering_point']),
            models.Index(fields=['register_code']),
        ]

    def __str__(self):
        return f"{self.register_code} on {self.metering_point.meter_number}"


class TimescaleManager(models.Manager):
    """Custom manager for TimescaleDB models"""
    
    def create_hypertable(self, time_column='read_at', chunk_time_interval='7 days'):
        """Create hypertable for this model"""
        from django.db import connection
        
        table_name = self.model._meta.db_table
        
        with connection.cursor() as cursor:
            # Create hypertable
            cursor.execute(f"""
                SELECT create_hypertable(
                    '{table_name}',
                    '{time_column}',
                    chunk_time_interval => INTERVAL '{chunk_time_interval}',
                    if_not_exists => TRUE
                );
            """)
            
            # Create indexes for common queries
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_tenant_icp_time 
                ON {table_name} (tenant_id, icp_id, {time_column} DESC);
            """)
            
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_icp_register_time 
                ON {table_name} (icp_id, register_code, {time_column} DESC);
            """)
    
    def compress_chunks(self, older_than='30 days'):
        """Enable compression for old chunks"""
        from django.db import connection
        
        table_name = self.model._meta.db_table
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                ALTER TABLE {table_name} SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'tenant_id, icp_id'
                );
            """)
            
            cursor.execute(f"""
                SELECT add_compression_policy('{table_name}', INTERVAL '{older_than}');
            """)
    
    def create_retention_policy(self, retention_period='5 years'):
        """Create data retention policy"""
        from django.db import connection
        
        table_name = self.model._meta.db_table
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT add_retention_policy('{table_name}', INTERVAL '{retention_period}');
            """)


# ===========================
# RAW METER READING TABLES
# ===========================

class MeterRawInterval(models.Model):
    """
    Raw half-hourly meter readings as imported from source files.
    This is the exact snapshot of imported data per source file & register.
    """
    # Identification
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    icp_id = models.CharField(max_length=50, db_index=True)
    register_code = models.CharField(max_length=50, db_index=True)
    
    # Time series data
    read_at = models.DateTimeField(db_index=True, help_text="Reading timestamp")
    
    # Raw reading data
    kwh = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Raw kWh reading"
    )
    
    # Source information
    source_file_id = models.CharField(max_length=200, blank=True)
    source_file_name = models.CharField(max_length=500, blank=True)
    source_row_number = models.IntegerField(null=True, blank=True)
    
    # Import metadata
    import_batch_id = models.CharField(max_length=100, blank=True)
    imported_at = models.DateTimeField(default=timezone.now)
    
    # Raw status from source
    raw_status = models.CharField(max_length=20, blank=True)
    raw_quality = models.CharField(max_length=20, blank=True)
    
    # Additional raw fields (flexible JSON for vendor-specific data)
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional raw fields from source"
    )
    
    objects = TimescaleManager()

    class Meta:
        db_table = 'metering_raw_interval'
        verbose_name = 'Raw Interval Reading'
        verbose_name_plural = 'Raw Interval Readings'
        indexes = [
            models.Index(fields=['tenant', 'icp_id', 'read_at']),
            models.Index(fields=['icp_id', 'register_code', 'read_at']),
            models.Index(fields=['import_batch_id']),
            models.Index(fields=['imported_at']),
        ]
        # Unique constraint to prevent duplicate readings
        unique_together = ['tenant', 'icp_id', 'register_code', 'read_at', 'source_file_id']

    def __str__(self):
        return f"{self.icp_id} {self.register_code} @ {self.read_at}"


class MeterRawDaily(models.Model):
    """
    Raw daily meter readings for non-half-hourly meters.
    One total reading per register per day.
    """
    # Identification
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    icp_id = models.CharField(max_length=50, db_index=True)
    register_code = models.CharField(max_length=50, db_index=True)
    
    # Time series data
    read_date = models.DateField(db_index=True, help_text="Reading date")
    
    # Raw reading data
    kwh = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Raw kWh reading"
    )
    
    # Reading type
    reading_type = models.CharField(
        max_length=20,
        choices=[
            ('actual', 'Actual Reading'),
            ('estimated', 'Estimated Reading'),
            ('customer_read', 'Customer Self-Read'),
        ],
        default='actual'
    )
    
    # Source information
    source_file_id = models.CharField(max_length=200, blank=True)
    source_file_name = models.CharField(max_length=500, blank=True)
    source_row_number = models.IntegerField(null=True, blank=True)
    
    # Import metadata
    import_batch_id = models.CharField(max_length=100, blank=True)
    imported_at = models.DateTimeField(default=timezone.now)
    
    # Raw status from source
    raw_status = models.CharField(max_length=20, blank=True)
    raw_quality = models.CharField(max_length=20, blank=True)
    
    # Additional raw fields
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional raw fields from source"
    )
    
    objects = TimescaleManager()

    class Meta:
        db_table = 'metering_raw_daily'
        verbose_name = 'Raw Daily Reading'
        verbose_name_plural = 'Raw Daily Readings'
        indexes = [
            models.Index(fields=['tenant', 'icp_id', 'read_date']),
            models.Index(fields=['icp_id', 'register_code', 'read_date']),
            models.Index(fields=['import_batch_id']),
            models.Index(fields=['imported_at']),
        ]
        # Unique constraint to prevent duplicate readings
        unique_together = ['tenant', 'icp_id', 'register_code', 'read_date', 'source_file_id']

    def __str__(self):
        return f"{self.icp_id} {self.register_code} @ {self.read_date}"


# ===========================
# VALIDATED METER READING TABLES
# ===========================

class MeterCalcInterval(models.Model):
    """
    Validated half-hourly meter readings with estimation flags and statuses.
    This is the clean, rule-checked data for downstream consumption.
    """
    # Identification
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    icp_id = models.CharField(max_length=50, db_index=True)
    register_code = models.CharField(max_length=50, db_index=True)
    
    # Time series data
    read_at = models.DateTimeField(db_index=True, help_text="Reading timestamp")
    
    # Validated reading data
    kwh = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Validated kWh reading"
    )
    
    # Validation status
    status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Valid'),
            ('estimated', 'Estimated'),
            ('invalid', 'Invalid'),
            ('suspicious', 'Suspicious'),
            ('missing', 'Missing'),
        ],
        db_index=True
    )
    
    # Estimation information
    is_estimated = models.BooleanField(default=False, db_index=True)
    estimation_method = models.CharField(max_length=30, blank=True)
    estimation_confidence = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Validation results
    rule_fail_mask = models.BigIntegerField(default=0)
    failed_rules = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    
    # Quality indicators
    quality_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Warnings and flags
    warnings = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True
    )
    
    has_gaps = models.BooleanField(default=False)
    has_spikes = models.BooleanField(default=False)
    
    # Source traceability
    source_file_id = models.CharField(max_length=200, blank=True)
    validation_batch_id = models.CharField(max_length=100, blank=True)
    
    # Processing metadata
    validated_at = models.DateTimeField(default=timezone.now)
    validation_version = models.CharField(max_length=20, default='1.0')
    
    objects = TimescaleManager()

    class Meta:
        db_table = 'metering_calc_interval'
        verbose_name = 'Validated Interval Reading'
        verbose_name_plural = 'Validated Interval Readings'
        indexes = [
            models.Index(fields=['tenant', 'icp_id', 'read_at']),
            models.Index(fields=['icp_id', 'register_code', 'read_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_estimated']),
            models.Index(fields=['validation_batch_id']),
            models.Index(fields=['validated_at']),
        ]
        # Unique constraint for validated readings
        unique_together = ['tenant', 'icp_id', 'register_code', 'read_at']

    def __str__(self):
        return f"{self.icp_id} {self.register_code} @ {self.read_at} ({self.status})"


class MeterCalcDaily(models.Model):
    """
    Validated daily meter readings for non-half-hourly meters.
    Clean, rule-checked data with validation status.
    """
    # Identification
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    icp_id = models.CharField(max_length=50, db_index=True)
    register_code = models.CharField(max_length=50, db_index=True)
    
    # Time series data
    read_date = models.DateField(db_index=True, help_text="Reading date")
    
    # Validated reading data
    kwh = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Validated kWh reading"
    )
    
    # Validation status
    status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Valid'),
            ('estimated', 'Estimated'),
            ('invalid', 'Invalid'),
            ('suspicious', 'Suspicious'),
            ('missing', 'Missing'),
        ],
        db_index=True
    )
    
    # Estimation information
    is_estimated = models.BooleanField(default=False, db_index=True)
    estimation_method = models.CharField(max_length=30, blank=True)
    estimation_confidence = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Validation results
    rule_fail_mask = models.BigIntegerField(default=0)
    failed_rules = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    
    # Quality indicators
    quality_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Warnings and flags
    warnings = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True
    )
    
    # Source traceability
    source_file_id = models.CharField(max_length=200, blank=True)
    validation_batch_id = models.CharField(max_length=100, blank=True)
    
    # Processing metadata
    validated_at = models.DateTimeField(default=timezone.now)
    validation_version = models.CharField(max_length=20, default='1.0')
    
    objects = TimescaleManager()

    class Meta:
        db_table = 'metering_calc_daily'
        verbose_name = 'Validated Daily Reading'
        verbose_name_plural = 'Validated Daily Readings'
        indexes = [
            models.Index(fields=['tenant', 'icp_id', 'read_date']),
            models.Index(fields=['icp_id', 'register_code', 'read_date']),
            models.Index(fields=['status']),
            models.Index(fields=['is_estimated']),
            models.Index(fields=['validation_batch_id']),
            models.Index(fields=['validated_at']),
        ]
        # Unique constraint for validated readings
        unique_together = ['tenant', 'icp_id', 'register_code', 'read_date']

    def __str__(self):
        return f"{self.icp_id} {self.register_code} @ {self.read_date} ({self.status})"


# ===========================
# AGGREGATION HELPER MODELS
# ===========================

class MeterAggregateDaily(models.Model):
    """
    Pre-calculated daily aggregations for performance.
    Used for billing, reconciliation, and reporting.
    """
    # Identification
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    icp_id = models.CharField(max_length=50, db_index=True)
    
    # Time series data
    aggregate_date = models.DateField(db_index=True)
    
    # Aggregated data by tariff group
    day_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    night_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    controlled_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    generation_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    total_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    
    # Quality metrics
    total_intervals = models.IntegerField(default=0)
    valid_intervals = models.IntegerField(default=0)
    estimated_intervals = models.IntegerField(default=0)
    missing_intervals = models.IntegerField(default=0)
    
    # Flags
    has_estimates = models.BooleanField(default=False)
    has_gaps = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    
    # Processing metadata
    calculated_at = models.DateTimeField(default=timezone.now)
    calculation_version = models.CharField(max_length=20, default='1.0')
    
    objects = TimescaleManager()

    class Meta:
        db_table = 'metering_aggregate_daily'
        verbose_name = 'Daily Aggregate'
        verbose_name_plural = 'Daily Aggregates'
        indexes = [
            models.Index(fields=['tenant', 'icp_id', 'aggregate_date']),
            models.Index(fields=['aggregate_date']),
            models.Index(fields=['has_estimates']),
            models.Index(fields=['is_complete']),
        ]
        unique_together = ['tenant', 'icp_id', 'aggregate_date']

    def __str__(self):
        return f"{self.icp_id} @ {self.aggregate_date} ({self.total_kwh} kWh)"


class MeterAggregateMonthly(models.Model):
    """
    Pre-calculated monthly aggregations for billing and reporting.
    """
    # Identification
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    icp_id = models.CharField(max_length=50, db_index=True)
    
    # Time series data
    year = models.IntegerField(db_index=True)
    month = models.IntegerField(db_index=True)
    
    # Aggregated data by tariff group
    day_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    night_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    controlled_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    generation_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    total_kwh = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    
    # Quality metrics
    total_days = models.IntegerField(default=0)
    complete_days = models.IntegerField(default=0)
    estimated_days = models.IntegerField(default=0)
    
    # Flags
    has_estimates = models.BooleanField(default=False)
    has_gaps = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    
    # Processing metadata
    calculated_at = models.DateTimeField(default=timezone.now)
    calculation_version = models.CharField(max_length=20, default='1.0')
    
    objects = TimescaleManager()

    class Meta:
        db_table = 'metering_aggregate_monthly'
        verbose_name = 'Monthly Aggregate'
        verbose_name_plural = 'Monthly Aggregates'
        indexes = [
            models.Index(fields=['tenant', 'icp_id', 'year', 'month']),
            models.Index(fields=['year', 'month']),
            models.Index(fields=['has_estimates']),
            models.Index(fields=['is_complete']),
        ]
        unique_together = ['tenant', 'icp_id', 'year', 'month']

    def __str__(self):
        return f"{self.icp_id} @ {self.year}-{self.month:02d} ({self.total_kwh} kWh)" 


class MeteringAuditLog(models.Model):
    """
    Audit log for metering data processing operations.
    Tracks ETL processes, validation runs, and data quality checks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, db_index=True)
    
    # Process identification
    process_name = models.CharField(max_length=100, db_index=True)
    source_system = models.CharField(max_length=50, db_index=True)
    batch_id = models.CharField(max_length=100, blank=True)
    
    # Processing details
    records_processed = models.IntegerField(default=0)
    records_transformed = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    
    # Timing
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    processing_duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial Success'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # Details
    details = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'energy_meteringauditlog'
        verbose_name = 'Metering Audit Log'
        verbose_name_plural = 'Metering Audit Logs'
        indexes = [
            models.Index(fields=['tenant', 'process_name', 'created_at']),
            models.Index(fields=['source_system', 'status']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.process_name} - {self.source_system} ({self.status})"
    
    def calculate_duration(self):
        """Calculate processing duration if both start and end times are available"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.processing_duration_seconds = int(duration.total_seconds())
            return self.processing_duration_seconds
        return None
    
    def mark_completed(self, status='SUCCESS', details='', error_message=''):
        """Mark the audit log as completed with given status"""
        self.end_time = timezone.now()
        self.status = status
        self.details = details
        self.error_message = error_message
        self.calculate_duration()
        self.save(update_fields=['end_time', 'status', 'details', 'error_message', 'processing_duration_seconds', 'updated_at']) 