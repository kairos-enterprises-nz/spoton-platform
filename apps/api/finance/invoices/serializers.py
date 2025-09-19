"""
Serializers for invoice API endpoints.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Invoice, InvoiceLine
from ..billing.models import Bill
from users.models import User, Tenant


class InvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items."""
    
    class Meta:
        model = InvoiceLine
        fields = [
            'id', 'description', 'service_type', 'quantity', 'unit',
            'unit_price', 'amount', 'service_period_start', 'service_period_end',
            'is_taxable', 'tax_rate', 'tax_amount', 'sort_order', 'section_header'
        ]
        read_only_fields = ['id']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for invoices with line items."""
    
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    bill_number = serializers.CharField(source='bill.bill_number', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'tenant', 'tenant_name', 'bill', 'bill_number',
            'customer', 'customer_name', 'customer_email',
            'invoice_number', 'status', 'payment_status',
            'issue_date', 'due_date', 'finalized_at', 'booked_at', 'emailed_at',
            'subtotal', 'tax_amount', 'total_amount', 'amount_paid', 'amount_due',
            'pdf_file_path', 'is_pdf_generated', 'is_emailed',
            'external_accounting_id', 'lines', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'customer_name', 'customer_email',
            'tenant_name', 'bill_number', 'lines', 'finalized_at', 'booked_at',
            'emailed_at', 'is_pdf_generated', 'is_emailed'
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for invoice lists."""
    
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    line_count = serializers.IntegerField(source='lines.count', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'customer_name', 'status', 'payment_status',
            'issue_date', 'due_date', 'total_amount', 'amount_due',
            'is_pdf_generated', 'is_emailed', 'line_count'
        ]
        read_only_fields = ['id', 'customer_name', 'line_count']


class InvoiceCreateSerializer(serializers.Serializer):
    """Serializer for creating invoices from bills."""
    
    bill_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of bill IDs to create invoices from"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="Whether to perform a dry run"
    )
    
    def validate_bill_ids(self, value):
        """Validate that bills exist and are eligible for invoice creation."""
        bills = Bill.objects.filter(id__in=value)
        
        if bills.count() != len(value):
            raise serializers.ValidationError("Some bills do not exist")
        
        # Check if bills already have invoices
        existing_invoices = Invoice.objects.filter(bill_id__in=value).values_list('bill_id', flat=True)
        if existing_invoices:
            raise serializers.ValidationError(
                f"Bills already have invoices: {list(existing_invoices)}"
            )
        
        # Check bill status
        invalid_bills = bills.exclude(status__in=['issued', 'pending']).values_list('bill_number', flat=True)
        if invalid_bills:
            raise serializers.ValidationError(
                f"Bills not in valid status for invoice creation: {list(invalid_bills)}"
            )
        
        return value


class InvoiceActionSerializer(serializers.Serializer):
    """Serializer for invoice actions (review, finalize, etc.)."""
    
    invoice_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of invoice IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=['review', 'finalize', 'generate_pdf', 'send_email', 'cancel'],
        help_text="Action to perform on invoices"
    )
    approved = serializers.BooleanField(
        default=True,
        help_text="Whether the action is approved (for review action)"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="Whether to perform a dry run"
    )
    
    def validate(self, data):
        """Validate invoice action parameters."""
        invoice_ids = data['invoice_ids']
        action = data['action']
        
        invoices = Invoice.objects.filter(id__in=invoice_ids)
        
        if invoices.count() != len(invoice_ids):
            raise serializers.ValidationError("Some invoices do not exist")
        
        # Validate invoice status for the action
        status_requirements = {
            'review': ['draft'],
            'finalize': ['review'],
            'generate_pdf': ['finalized'],
            'send_email': ['finalized'],
            'cancel': ['draft', 'review']
        }
        
        if action in status_requirements:
            valid_statuses = status_requirements[action]
            invalid_invoices = invoices.exclude(status__in=valid_statuses).values_list('invoice_number', flat=True)
            
            if invalid_invoices:
                raise serializers.ValidationError(
                    f"Invoices not in valid status for {action}: {list(invalid_invoices)}"
                )
        
        # Additional validations for specific actions
        if action == 'send_email':
            no_pdf_invoices = invoices.filter(is_pdf_generated=False).values_list('invoice_number', flat=True)
            if no_pdf_invoices:
                raise serializers.ValidationError(
                    f"Invoices do not have PDFs generated: {list(no_pdf_invoices)}"
                )
        
        return data


class InvoiceStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating invoice status."""
    
    class Meta:
        model = Invoice
        fields = ['status', 'payment_status', 'amount_paid']
        
    def validate_status(self, value):
        """Validate status transitions."""
        if self.instance:
            current_status = self.instance.status
            valid_transitions = {
                'draft': ['review', 'cancelled'],
                'review': ['finalized', 'cancelled'],
                'finalized': ['booked', 'cancelled'],
                'booked': ['emailed'],
                'emailed': [],
                'cancelled': []
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from {current_status} to {value}"
                )
        
        return value


class InvoiceAnalyticsSerializer(serializers.Serializer):
    """Serializer for invoice analytics data."""
    
    total_invoices = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    status_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of invoices by status"
    )
    payment_status_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Count of invoices by payment status"
    )
    service_breakdown = serializers.ListField(
        child=serializers.DictField(),
        help_text="Breakdown by service type"
    )
    monthly_trends = serializers.ListField(
        child=serializers.DictField(),
        help_text="Monthly invoice trends"
    )
    avg_processing_time_hours = serializers.FloatField(
        help_text="Average processing time in hours"
    )
    generated_at = serializers.DateTimeField()


class InvoiceDeliveryStatusSerializer(serializers.Serializer):
    """Serializer for invoice delivery status."""
    
    invoice_id = serializers.UUIDField()
    invoice_number = serializers.CharField()
    customer_email = serializers.EmailField()
    pdf_generated = serializers.BooleanField()
    email_sent = serializers.BooleanField()
    email_sent_at = serializers.DateTimeField(required=False)
    delivery_attempts = serializers.IntegerField()
    last_delivery_error = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['pending', 'delivered', 'failed', 'bounced']
    )


class BulkInvoiceActionResultSerializer(serializers.Serializer):
    """Serializer for bulk invoice action results."""
    
    action = serializers.CharField()
    total_requested = serializers.IntegerField()
    successful_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    processed_invoices = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of successfully processed invoice IDs"
    )
    failed_invoices = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of failed invoice IDs"
    )
    execution_time_seconds = serializers.FloatField()
    dry_run = serializers.BooleanField()


class InvoicePDFSerializer(serializers.Serializer):
    """Serializer for PDF generation requests."""
    
    invoice_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    regenerate = serializers.BooleanField(
        default=False,
        help_text="Whether to regenerate existing PDFs"
    )
    
    def validate_invoice_ids(self, value):
        """Validate invoice IDs for PDF generation."""
        invoices = Invoice.objects.filter(id__in=value)
        
        if invoices.count() != len(value):
            raise serializers.ValidationError("Some invoices do not exist")
        
        # Check if invoices are finalized
        non_finalized = invoices.exclude(status='finalized').values_list('invoice_number', flat=True)
        if non_finalized:
            raise serializers.ValidationError(
                f"Invoices must be finalized for PDF generation: {list(non_finalized)}"
            )
        
        return value


class InvoiceEmailSerializer(serializers.Serializer):
    """Serializer for email sending requests."""
    
    invoice_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    resend = serializers.BooleanField(
        default=False,
        help_text="Whether to resend to already emailed invoices"
    )
    test_mode = serializers.BooleanField(
        default=False,
        help_text="Whether to send test emails (to admin only)"
    )
    
    def validate_invoice_ids(self, value):
        """Validate invoice IDs for email sending."""
        invoices = Invoice.objects.filter(id__in=value)
        
        if invoices.count() != len(value):
            raise serializers.ValidationError("Some invoices do not exist")
        
        # Check if invoices have PDFs
        no_pdf = invoices.filter(is_pdf_generated=False).values_list('invoice_number', flat=True)
        if no_pdf:
            raise serializers.ValidationError(
                f"Invoices do not have PDFs generated: {list(no_pdf)}"
            )
        
        # Check if customers have email addresses
        no_email = invoices.filter(customer__email__isnull=True).values_list('invoice_number', flat=True)
        if no_email:
            raise serializers.ValidationError(
                f"Customers do not have email addresses: {list(no_email)}"
            )
        
        return value
