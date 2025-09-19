# This file is intentionally left blank.
# Core metering models are now defined in energy.metering.timescale_models
# to separate them from other application models.

from django.db import models
from users.models import Tenant
import uuid


class IntervalReadRaw(models.Model):
    """
    Raw interval meter readings with enhanced metadata columns.
    This table stores normalized HHR data from all MEP providers.
    Schema reflects proper ICP → Meter → Register hierarchy.
    """
    id = models.BigAutoField(primary_key=True)
    connection_id = models.CharField(max_length=100, help_text="Installation Control Point identifier")
    register_code = models.CharField(max_length=20, help_text="Register code (e.g., A+)")
    timestamp = models.DateTimeField(help_text="Reading timestamp")
    day = models.DateField(help_text="Reading date (extracted from timestamp)")
    trading_period = models.IntegerField(blank=True, null=True, help_text="Trading period number (1-48 for normal days, 1-46 for DST spring, 1-50 for DST autumn)")
    value = models.DecimalField(max_digits=12, decimal_places=4, help_text="Reading value")
    unit = models.CharField(max_length=10, default="kWh", help_text="Measurement unit")
    quality_flag = models.CharField(
        max_length=20,
        choices=[
            ("raw", "Raw"),
            ("valid", "Valid"),
            ("suspect", "Suspect"),
            ("error", "Error"),
            ("manual_override", "Manual Override"),
        ],
        default="raw",
        help_text="Data quality indicator"
    )
    
    # Key metering information fields (in logical order)
    flow_direction = models.CharField(max_length=10, blank=True, null=True, help_text="Energy flow direction (X=Export, I=Import)")
    register_content_code = models.CharField(max_length=50, blank=True, null=True, help_text="Register content code (UN24, EG24, IN19, etc.)")
    meter_channel_number = models.CharField(max_length=20, blank=True, null=True, help_text="Meter channel number (051, 052, 001, 002, etc.)")
    
    # Source and processing fields
    source = models.CharField(max_length=50, blank=True, help_text="Data source (MEP provider)")
    import_id = models.UUIDField(blank=True, null=True, help_text="Import batch ID")
    
    # Comprehensive metadata field
    metadata = models.JSONField(default=dict, blank=True, help_text="Comprehensive metadata from source tables including all available fields")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'metering_processed.interval_reads_raw'
        managed = False  # This table is managed by TimescaleDB
        indexes = [
            models.Index(fields=['connection_id', 'timestamp']),
            models.Index(fields=['register_code', 'timestamp']),
            models.Index(fields=['day']),
            models.Index(fields=['trading_period']),
            models.Index(fields=['quality_flag']),
            models.Index(fields=['flow_direction']),
            models.Index(fields=['register_content_code']),
            models.Index(fields=['meter_channel_number']),
            models.Index(fields=['source']),
            models.Index(fields=['import_id']),
        ]
        unique_together = ['connection_id', 'register_code', 'timestamp']

    def __str__(self):
        return f"ICP:{self.connection_id} → Register:{self.register_code} → Channel:{self.meter_channel_number} @ {self.timestamp}"


class DailyRegisterRead(models.Model):
    """
    Daily register readings with enhanced metadata columns.
    This table stores normalized DRR data from all MEP providers.
    Schema reflects proper ICP → Meter → Register hierarchy.
    """
    id = models.BigAutoField(primary_key=True)
    tenant_id = models.UUIDField(help_text="Tenant UUID")
    icp_id = models.CharField(max_length=100, help_text="Installation Control Point identifier")
    register_code = models.CharField(max_length=20, help_text="Register code (e.g., A+)")
    reading_date = models.DateField(help_text="Reading date")
    start_reading = models.DecimalField(max_digits=12, decimal_places=4, help_text="Start reading value")
    end_reading = models.DecimalField(max_digits=12, decimal_places=4, help_text="End reading value")
    consumption = models.DecimalField(max_digits=12, decimal_places=4, help_text="Consumption (end - start)")
    unit = models.CharField(max_length=10, default="kWh", help_text="Measurement unit")
    read_type = models.CharField(max_length=20, help_text="Reading type (actual, estimated, etc.)")
    quality_flag = models.CharField(
        max_length=20,
        choices=[
            ("valid", "Valid"),
            ("suspect", "Suspect"),
            ("error", "Error"),
            ("estimated", "Estimated"),
        ],
        default="valid",
        help_text="Data quality indicator"
    )
    source = models.CharField(max_length=50, blank=True, help_text="Data source (MEP provider)")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ICP → Meter → Register hierarchy columns
    meter_serial_number = models.CharField(max_length=255, blank=True, null=True, help_text="Physical meter serial number")
    meter_register_id = models.CharField(max_length=255, blank=True, null=True, help_text="Register ID specific to this meter")
    
    # Enhanced metadata columns
    read_timestamp = models.DateTimeField(blank=True, null=True, help_text="Original read timestamp from MEP")
    validation_flag = models.CharField(max_length=255, blank=True, null=True, help_text="Validation flag from MEP")
    source_file_name = models.CharField(max_length=255, blank=True, null=True, help_text="Source file name")

    class Meta:
        db_table = 'metering_processed.daily_register_reads'
        managed = False  # This table is managed by TimescaleDB
        indexes = [
            models.Index(fields=['tenant_id', 'icp_id', 'reading_date']),
            models.Index(fields=['icp_id', 'register_code', 'reading_date']),
            models.Index(fields=['source']),
            models.Index(fields=['meter_serial_number', 'meter_register_id']),
        ]
        unique_together = ['tenant_id', 'icp_id', 'register_code', 'reading_date', 'source']

    def __str__(self):
        return f"ICP:{self.icp_id} → Meter:{self.meter_serial_number} → Register:{self.register_code} @ {self.reading_date}"
