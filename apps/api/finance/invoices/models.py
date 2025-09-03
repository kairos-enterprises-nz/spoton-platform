from django.db import models
from django.conf import settings
from users.models import Tenant
from finance.billing.models import Bill
import uuid


class Invoice(models.Model):
    """
    Legal invoice artifact linked 1:1 to a finalized Bill
    """
    INVOICE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('finalized', 'Finalized'),
        ('booked', 'Booked'),
        ('emailed', 'Emailed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('overdue', 'Overdue'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Multi-tenancy
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True,
    )

    bill = models.OneToOneField(Bill, on_delete=models.PROTECT, related_name='invoice')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)

    # Identification & lifecycle
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=15, choices=INVOICE_STATUS_CHOICES, default='draft')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')

    # Dates
    issue_date = models.DateTimeField()
    due_date = models.DateTimeField()
    finalized_at = models.DateTimeField(null=True, blank=True)
    booked_at = models.DateTimeField(null=True, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)

    # Amounts (snapshotted from Bill at finalize time)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)

    # Delivery & artifacts
    pdf_file_path = models.CharField(max_length=500, blank=True)
    is_pdf_generated = models.BooleanField(default=False)
    is_emailed = models.BooleanField(default=False)

    # Accounting integration
    external_accounting_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_invoice'
        indexes = [
            models.Index(fields=['tenant', 'customer', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['invoice_number']),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} - {self.customer} - ${self.total_amount}"


class InvoiceLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invoice_lines',
        null=True,
        blank=True,
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')

    description = models.CharField(max_length=200)
    service_type = models.CharField(max_length=20, choices=[
        ('electricity', 'Electricity'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
    ])

    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit = models.CharField(max_length=20, default='each')
    unit_price = models.DecimalField(max_digits=10, decimal_places=6)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    service_period_start = models.DateTimeField(null=True, blank=True)
    service_period_end = models.DateTimeField(null=True, blank=True)

    is_taxable = models.BooleanField(default=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    sort_order = models.IntegerField(default=0)
    section_header = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_invoiceline'
        indexes = [
            models.Index(fields=['tenant', 'invoice', 'service_type']),
            models.Index(fields=['sort_order']),
        ]
        ordering = ['sort_order', 'created_at']

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number} - {self.description} - ${self.amount}"

