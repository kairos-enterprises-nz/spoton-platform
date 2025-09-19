"""
Application layer models - to be configured later

Raw data import is handled by Airflow DAGs → TimescaleDB (direct SQL)
Application logic models will be configured later for business features.
"""

# Application layer models will be configured later
# Raw data import is handled by Airflow DAGs → TimescaleDB directly

"""
TimescaleDB models for export and reconciliation data.
These models handle time-series export logs and EIEP submissions.
"""

import uuid
from django.db import models
from django.utils import timezone
from core.models import TenantAwareUUIDModel, TenantAwareMetadataModel


class ExportLog(TenantAwareUUIDModel, TenantAwareMetadataModel):
    """
    Tracks export operations for EIEP submissions and reconciliation data.
    Stored in primary PostgreSQL database.
    """
    
    # Export details
    export_type = models.CharField(
        max_length=30,
        choices=[
            ('eiep1a', 'EIEP-1A Daily Consumption'),
            ('eiep1b', 'EIEP-1B Interval Data'),
            ('eiep3', 'EIEP-3 Registry Data'),
            ('eiep13', 'EIEP-13 Network Billing'),
            ('gr010', 'GR-010 Reconciliation'),
            ('gr020', 'GR-020 Washing Machine'),
            ('custom', 'Custom Export'),
        ],
        help_text="Type of export operation"
    )
    
    # File details
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash")
    
    # Time range
    data_start_date = models.DateField(help_text="Start date of exported data")
    data_end_date = models.DateField(help_text="End date of exported data")
    
    # Processing details
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('transmitted', 'Transmitted'),
        ('acknowledged', 'Acknowledged'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    total_records = models.IntegerField(default=0)
    exported_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)
    
    # Recipients and transmission
    recipient = models.CharField(max_length=100, blank=True, help_text="Export recipient")
    transmission_method = models.CharField(
        max_length=20,
        choices=[
            ('sftp', 'SFTP'),
            ('email', 'Email'),
            ('api', 'API'),
            ('manual', 'Manual Download'),
        ],
        default='sftp'
    )
    transmission_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_details = models.JSONField(default=list, blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'energy_exportlog'
        indexes = [
            models.Index(fields=['tenant', 'export_type']),
            models.Index(fields=['status', 'started_at']),
            models.Index(fields=['data_start_date', 'data_end_date']),
            models.Index(fields=['recipient', 'transmission_method']),
        ]
    
    def __str__(self):
        return f"{self.export_type} - {self.file_name} ({self.status})"
    
    def mark_completed(self, exported_records, error_records=0):
        """Mark export as completed"""
        self.status = 'completed' if error_records == 0 else 'failed'
        self.completed_at = timezone.now()
        self.exported_records = exported_records
        self.error_records = error_records
        self.save()
    
    def mark_transmitted(self):
        """Mark export as transmitted"""
        self.status = 'transmitted'
        self.transmission_timestamp = timezone.now()
        self.save()


class ReconciliationSubmission(TenantAwareUUIDModel, TenantAwareMetadataModel):
    """
    Tracks reconciliation submissions to the market.
    Stored in primary PostgreSQL database.
    """
    
    # Submission details
    submission_type = models.CharField(
        max_length=20,
        choices=[
            ('initial', 'Initial Submission'),
            ('revision', 'Revision'),
            ('final', 'Final Submission'),
            ('washup', 'Wash-up'),
        ],
        help_text="Type of reconciliation submission"
    )
    
    # Trading period
    trading_date = models.DateField(help_text="Trading date")
    trading_period = models.IntegerField(help_text="Trading period (1-48)")
    
    # Market participant details
    participant_code = models.CharField(max_length=20, help_text="Market participant code")
    reconciliation_type = models.CharField(
        max_length=20,
        choices=[
            ('generation', 'Generation'),
            ('load', 'Load'),
            ('both', 'Generation and Load'),
        ],
        default='load'
    )
    
    # Data details
    total_volume = models.DecimalField(max_digits=15, decimal_places=4, help_text="Total volume in MWh")
    connection_count = models.IntegerField(help_text="Number of connections included")
    
    # Submission timing
    submission_deadline = models.DateTimeField(help_text="Deadline for this submission")
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready', 'Ready for Submission'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('revised', 'Revised'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # File references
    submission_file = models.CharField(max_length=255, blank=True)
    response_file = models.CharField(max_length=255, blank=True)
    
    # Market response
    market_response_code = models.CharField(max_length=10, blank=True)
    market_response_message = models.TextField(blank=True)
    market_response_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Validation
    validation_errors = models.JSONField(default=list, blank=True)
    validation_warnings = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'energy_reconciliationsubmission'
        indexes = [
            models.Index(fields=['tenant', 'trading_date', 'trading_period']),
            models.Index(fields=['participant_code', 'submission_type']),
            models.Index(fields=['status', 'submission_deadline']),
            models.Index(fields=['submitted_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'trading_date', 'trading_period', 'submission_type'],
                name='unique_reconciliation_submission'
            )
        ]
    
    def __str__(self):
        return f"{self.submission_type} - {self.trading_date} TP{self.trading_period}"
    
    def submit(self):
        """Mark submission as submitted"""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
    
    def accept_response(self, response_code, response_message=""):
        """Process accepted response from market"""
        self.status = 'accepted'
        self.market_response_code = response_code
        self.market_response_message = response_message
        self.market_response_timestamp = timezone.now()
        self.save()
    
    def reject_response(self, response_code, response_message=""):
        """Process rejected response from market"""
        self.status = 'rejected'
        self.market_response_code = response_code
        self.market_response_message = response_message
        self.market_response_timestamp = timezone.now()
        self.save()


class MarketSubmission(TenantAwareUUIDModel, TenantAwareMetadataModel):
    """
    Tracks all market submissions (EIEP, GR reports, etc.).
    Stored in primary PostgreSQL database.
    """
    
    # Submission identification
    submission_id = models.CharField(max_length=100, unique=True, help_text="Unique submission identifier")
    submission_type = models.CharField(
        max_length=20,
        choices=[
            ('eiep1a', 'EIEP-1A'),
            ('eiep1b', 'EIEP-1B'),
            ('eiep3', 'EIEP-3'),
            ('eiep13', 'EIEP-13'),
            ('gr010', 'GR-010'),
            ('gr020', 'GR-020'),
            ('other', 'Other'),
        ],
        help_text="Type of market submission"
    )
    
    # Timing
    reporting_period_start = models.DateField(help_text="Start of reporting period")
    reporting_period_end = models.DateField(help_text="End of reporting period")
    due_date = models.DateTimeField(help_text="Submission due date")
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Participant details
    participant_code = models.CharField(max_length=20, help_text="Market participant code")
    trader_code = models.CharField(max_length=20, blank=True, help_text="Trader code if different")
    
    # File details
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(null=True, blank=True)
    record_count = models.IntegerField(default=0, help_text="Number of records in submission")
    
    # Status tracking
    STATUS_CHOICES = [
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('submitted', 'Submitted'),
        ('processing', 'Processing'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('acknowledged', 'Acknowledged'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    
    # Market response
    acknowledgment_received = models.BooleanField(default=False)
    acknowledgment_timestamp = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Processing details
    processing_errors = models.JSONField(default=list, blank=True)
    processing_warnings = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'energy_marketsubmission'
        indexes = [
            models.Index(fields=['tenant', 'submission_type']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['reporting_period_start', 'reporting_period_end']),
            models.Index(fields=['participant_code']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'submission_id'],
                name='unique_market_submission_id'
            )
        ]
    
    def __str__(self):
        return f"{self.submission_type} - {self.submission_id} ({self.status})"
    
    def submit(self):
        """Mark submission as submitted"""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
    
    def acknowledge(self):
        """Mark submission as acknowledged"""
        self.acknowledgment_received = True
        self.acknowledgment_timestamp = timezone.now()
        self.status = 'acknowledged'
        self.save()
    
    def _validate_tenant_consistency(self):
        """Validate tenant consistency"""
        super()._validate_tenant_consistency()
        
        # Add any specific validation rules for market submissions
        if self.participant_code and self.tenant:
            # Could validate that participant_code matches tenant configuration
            pass
