"""
Serializers for billing API endpoints.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Bill, BillLineItem, BillingRun, BillingCycle, Payment, PaymentAllocation
from .models_registry import ServiceRegistry, BillingConfig
from users.models import User, Tenant


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for tenant information."""
    
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'code', 'is_active']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ServiceRegistrySerializer(serializers.ModelSerializer):
    """Serializer for service registry configuration."""
    
    class Meta:
        model = ServiceRegistry
        fields = [
            'id', 'tenant', 'service_code', 'name', 'billing_type', 
            'frequency', 'period', 'inclusion_rule', 'applies_to_next_month',
            'billing_handler', 'tariff_handler', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BillingCycleSerializer(serializers.ModelSerializer):
    """Serializer for billing cycle configuration."""
    
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = BillingCycle
        fields = [
            'id', 'tenant', 'tenant_name', 'customer', 'customer_name',
            'service_type', 'cycle_type', 'cycle_day', 'current_period_start',
            'current_period_end', 'next_bill_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'customer_name', 'tenant_name']


class BillLineItemSerializer(serializers.ModelSerializer):
    """Serializer for bill line items."""
    
    class Meta:
        model = BillLineItem
        fields = [
            'id', 'description', 'service_type', 'quantity', 'unit',
            'unit_price', 'amount', 'service_period_start', 'service_period_end',
            'is_taxable', 'tax_rate', 'tax_amount', 'sort_order'
        ]
        read_only_fields = ['id']


class BillSerializer(serializers.ModelSerializer):
    """Serializer for bills with line items."""
    
    line_items = BillLineItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = Bill
        fields = [
            'id', 'tenant', 'tenant_name', 'bill_number', 'customer', 'customer_name',
            'period_start', 'period_end', 'issue_date', 'due_date',
            'subtotal', 'tax_amount', 'total_amount', 'amount_paid', 'amount_due',
            'status', 'is_combined_bill', 'payment_method', 'payment_reference',
            'paid_date', 'line_items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'customer_name', 'tenant_name', 'line_items'
        ]


class BillingRunSerializer(serializers.ModelSerializer):
    """Serializer for billing runs."""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = BillingRun
        fields = [
            'id', 'tenant', 'tenant_name', 'run_name', 'service_type',
            'period_start', 'period_end', 'run_date', 'status',
            'total_customers', 'bills_generated', 'bills_failed',
            'started_at', 'completed_at', 'duration_minutes',
            'total_billed_amount', 'error_log', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'tenant_name', 'duration_minutes',
            'bills_generated', 'bills_failed', 'total_billed_amount'
        ]
    
    def get_duration_minutes(self, obj):
        """Calculate run duration in minutes."""
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return round(duration.total_seconds() / 60, 2)
        return None


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments."""
    
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'tenant', 'payment_reference', 'customer', 'customer_name',
            'amount', 'payment_method', 'payment_date', 'status',
            'processed_date', 'external_reference', 'gateway_transaction_id',
            'allocated_amount', 'unallocated_amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'customer_name']


class BillingRunCreateSerializer(serializers.Serializer):
    """Serializer for creating billing runs."""
    
    service_type = serializers.ChoiceField(
        choices=['electricity', 'broadband', 'mobile'],
        help_text="Service type to run billing for"
    )
    period_start = serializers.DateTimeField(
        help_text="Start of billing period"
    )
    period_end = serializers.DateTimeField(
        help_text="End of billing period"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="Whether to perform a dry run (no actual changes)"
    )
    execute_immediately = serializers.BooleanField(
        default=False,
        help_text="Whether to execute the run immediately after creation"
    )
    
    def validate(self, data):
        """Validate billing run parameters."""
        if data['period_start'] >= data['period_end']:
            raise serializers.ValidationError("Period start must be before period end")
        
        if data['period_end'] > timezone.now():
            raise serializers.ValidationError("Period end cannot be in the future")
        
        # Check if period is reasonable (not more than 1 year)
        if (data['period_end'] - data['period_start']).days > 365:
            raise serializers.ValidationError("Billing period cannot exceed 365 days")
        
        return data


class BillingDashboardSerializer(serializers.Serializer):
    """Serializer for billing dashboard statistics."""
    
    active_runs = serializers.IntegerField(help_text="Number of active billing runs")
    pending_bills = serializers.IntegerField(help_text="Number of pending bills")
    recent_activity = serializers.ListField(
        child=serializers.DictField(),
        help_text="Recent billing activity"
    )
    service_status = serializers.DictField(
        child=serializers.DictField(),
        help_text="Status of each service"
    )
    last_updated = serializers.DateTimeField(help_text="When stats were last updated")


class BulkBillActionSerializer(serializers.Serializer):
    """Serializer for bulk bill actions."""
    
    bill_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of bill IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'generate_invoices'],
        help_text="Action to perform on bills"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="Whether to perform a dry run"
    )


class BillingExecutionResultSerializer(serializers.Serializer):
    """Serializer for billing execution results."""
    
    billing_run_id = serializers.UUIDField()
    service_type = serializers.CharField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(required=False)
    bills_created = serializers.IntegerField()
    bills_failed = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    errors = serializers.ListField(child=serializers.CharField(), required=False)
    dry_run = serializers.BooleanField()


class ServiceConfigurationSerializer(serializers.Serializer):
    """Serializer for service configuration management."""
    
    service_code = serializers.CharField()
    name = serializers.CharField()
    billing_type = serializers.ChoiceField(choices=['prepaid', 'postpaid'])
    frequency = serializers.ChoiceField(choices=['weekly', 'monthly'])
    is_active = serializers.BooleanField()
    billing_handler = serializers.CharField()
    tariff_handler = serializers.CharField(required=False, allow_blank=True)


class BillingStatsSerializer(serializers.Serializer):
    """Serializer for billing statistics."""
    
    total_bills_this_month = serializers.IntegerField()
    total_amount_this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    successful_runs_this_month = serializers.IntegerField()
    failed_runs_this_month = serializers.IntegerField()
    average_processing_time_minutes = serializers.FloatField()
    bills_by_service = serializers.DictField()
    monthly_trends = serializers.ListField(child=serializers.DictField())
    generated_at = serializers.DateTimeField()


class BillingHealthCheckSerializer(serializers.Serializer):
    """Serializer for billing system health check."""
    
    overall_status = serializers.ChoiceField(choices=['healthy', 'warning', 'critical'])
    services = serializers.DictField(
        child=serializers.DictField(),
        help_text="Health status of each service"
    )
    last_successful_runs = serializers.DictField(
        child=serializers.DateTimeField(),
        help_text="Last successful run for each service"
    )
    pending_issues = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of pending issues"
    )
    system_metrics = serializers.DictField(
        help_text="System performance metrics"
    )
    checked_at = serializers.DateTimeField()
