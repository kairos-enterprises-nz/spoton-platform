from django.db import models
from django.conf import settings
# from core.contracts.models import ServiceContract
from users.models import Tenant
import uuid


class BillingCycle(models.Model):
    """
    Defines billing cycles for different utilities and customers
    """
    CYCLE_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('annual', 'Annual'),
    ]
    
    SERVICE_TYPE_CHOICES = [
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
        ('bundle', 'Multi-Service Bundle'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='billing_cycles',
        null=True,
        blank=True
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='billing_cycles',
        null=True,
        blank=True
    )
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    
    cycle_type = models.CharField(max_length=15, choices=CYCLE_TYPE_CHOICES, default='monthly')
    cycle_day = models.IntegerField(default=1, help_text="Day of month for billing")
    
    # Current cycle information
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    next_bill_date = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_billingcycle'
        indexes = [
            models.Index(fields=['tenant', 'customer', 'service_type']),
            models.Index(fields=['next_bill_date']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['tenant', 'customer', 'service_type']
    
    def __str__(self):
        return f"{self.customer} - {self.service_type} - {self.cycle_type}"


class Bill(models.Model):
    """
    Main bill record supporting multi-utility billing
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Multi-tenancy
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='bills',
        null=True,
        blank=True
    )
    
    # Bill identification
    bill_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bills',
        null=True,
        blank=True
    )
    
    # Billing period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Bill dates
    issue_date = models.DateTimeField()
    due_date = models.DateTimeField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    # Idempotency inputs (nullable if unknown at creation)
    idempotency_key = models.CharField(max_length=200, blank=True)
    
    # Status and metadata
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    is_combined_bill = models.BooleanField(default=False, help_text="Multi-utility bill")
    
    # Payment information
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # File references
    pdf_file_path = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_bill'
        indexes = [
            models.Index(fields=['tenant', 'customer', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['bill_number']),
            models.Index(fields=['issue_date']),
        ]
    
    def __str__(self):
        return f"Bill {self.bill_number} - {self.customer} - ${self.total_amount}"


class BillLineItem(models.Model):
    """
    Individual line items within a bill (utility-specific sections)
    """
    ITEM_TYPE_CHOICES = [
        ('energy_charge', 'Energy Charge'),
        ('demand_charge', 'Demand Charge'),
        ('fixed_charge', 'Fixed Charge'),
        ('network_charge', 'Network Charge'),
        ('transmission_charge', 'Transmission Charge'),
        ('service_charge', 'Service Charge'),
        ('tax', 'Tax'),
        ('discount', 'Discount'),
        ('credit', 'Credit'),
        ('adjustment', 'Adjustment'),
        ('late_fee', 'Late Fee'),
        ('connection_fee', 'Connection Fee'),
        ('disconnection_fee', 'Disconnection Fee'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='bill_line_items',
        null=True,
        blank=True
    )
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='line_items')
    # service_contract = models.ForeignKey(ServiceContract, on_delete=models.CASCADE, null=True, blank=True)
    
    # Line item details
    item_type = models.CharField(max_length=25, choices=ITEM_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    service_type = models.CharField(max_length=20, choices=BillingCycle.SERVICE_TYPE_CHOICES)
    
    # Quantity and pricing
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit = models.CharField(max_length=20, default='each')
    unit_price = models.DecimalField(max_digits=10, decimal_places=6)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Period information
    service_period_start = models.DateTimeField(null=True, blank=True)
    service_period_end = models.DateTimeField(null=True, blank=True)
    
    # Tax information
    is_taxable = models.BooleanField(default=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Sorting and grouping
    sort_order = models.IntegerField(default=0)
    section_header = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'finance_billlineitem'
        indexes = [
            models.Index(fields=['tenant', 'bill', 'service_type']),
            models.Index(fields=['item_type']),
            models.Index(fields=['sort_order']),
        ]
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return f"{self.bill.bill_number} - {self.description} - ${self.amount}"


class BillAdjustment(models.Model):
    """
    Track adjustments made to bills
    """
    ADJUSTMENT_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('correction', 'Correction'),
        ('refund', 'Refund'),
        ('write_off', 'Write Off'),
    ]
    
    REASON_CHOICES = [
        ('billing_error', 'Billing Error'),
        ('meter_error', 'Meter Error'),
        ('customer_complaint', 'Customer Complaint'),
        ('system_error', 'System Error'),
        ('goodwill', 'Goodwill'),
        ('regulatory', 'Regulatory'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='bill_adjustments',
        null=True,
        blank=True
    )
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='adjustments')
    
    adjustment_type = models.CharField(max_length=15, choices=ADJUSTMENT_TYPE_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    description = models.TextField()
    reference_number = models.CharField(max_length=50, blank=True)
    
    # Authorization
    authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    authorization_date = models.DateTimeField()
    
    # Processing
    is_processed = models.BooleanField(default=False)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['bill', 'adjustment_type']),
            models.Index(fields=['authorization_date']),
        ]
    
    def __str__(self):
        return f"{self.bill.bill_number} - {self.adjustment_type} - ${self.amount}"


class Payment(models.Model):
    """
    Track payments against bills
    """
    PAYMENT_METHOD_CHOICES = [
        ('direct_debit', 'Direct Debit'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('automatic', 'Automatic Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Multi-tenancy
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='payments',
        null=True,
        blank=True
    )
    
    # Payment identification
    payment_reference = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payments',
        null=True,
        blank=True
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField()
    
    # Status and processing
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    processed_date = models.DateTimeField(null=True, blank=True)
    
    # External references
    external_reference = models.CharField(max_length=100, blank=True)
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    
    # Allocation to bills
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unallocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['customer', 'payment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_reference']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_reference} - {self.customer} - ${self.amount}"


class PaymentAllocation(models.Model):
    """
    Track how payments are allocated to specific bills
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='payment_allocations',
        null=True,
        blank=True
    )
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='allocations')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payment_allocations')
    
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    allocation_date = models.DateTimeField()
    
    # Allocation details
    allocated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['payment', 'bill']),
            models.Index(fields=['allocation_date']),
        ]
        unique_together = ['payment', 'bill']
    
    def __str__(self):
        return f"{self.payment.payment_reference} -> {self.bill.bill_number} - ${self.allocated_amount}"


class BillingRun(models.Model):
    """
    Track billing run batches for processing and auditing
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='billing_runs',
        null=True,
        blank=True
    )
    run_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=BillingCycle.SERVICE_TYPE_CHOICES)
    
    # Run parameters
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    run_date = models.DateTimeField()

    # Idempotency key components
    idempotency_key = models.CharField(max_length=200, blank=True, help_text="tenant|service|contract|period_start|period_end")
    
    # Processing details
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    total_customers = models.IntegerField(default=0)
    bills_generated = models.IntegerField(default=0)
    bills_failed = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_billed_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    error_log = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['service_type', 'run_date']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'service_type', 'period_start', 'period_end', 'run_date'], name='unique_billing_run_per_period'),
        ]
    
    def __str__(self):
        return f"{self.run_name} - {self.service_type} - {self.status}"

# Ensure Django discovers registry models declared outside this module
from .models_registry import ServiceRegistry, BillingConfig  # noqa: E402,F401
