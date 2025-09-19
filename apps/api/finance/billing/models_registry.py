from django.db import models
from users.models import Tenant
import uuid


class ServiceRegistry(models.Model):
    """
    Registry of billable services and their handler paths
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='service_registry_entries',
        null=True,
        blank=True,
    )

    service_code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=100)
    billing_type = models.CharField(max_length=20, choices=[('prepaid', 'Prepaid'), ('postpaid', 'Postpaid')])
    frequency = models.CharField(max_length=10, choices=[('weekly', 'Weekly'), ('monthly', 'Monthly')])
    period = models.CharField(max_length=10, choices=[('prepaid', 'Prepaid'), ('postpaid', 'Postpaid')])
    inclusion_rule = models.CharField(max_length=100, blank=True)
    applies_to_next_month = models.BooleanField(default=False)
    billing_handler = models.CharField(max_length=200)
    tariff_handler = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_service_registry'
        unique_together = ['tenant', 'service_code']
        indexes = [
            models.Index(fields=['tenant', 'service_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.service_code} - {self.name}"


class BillingConfig(models.Model):
    """
    Per-contract rules and overrides for billing
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='billing_configs', null=True, blank=True)
    # contract = models.ForeignKey('core.contracts.ServiceContract', on_delete=models.CASCADE)
    service_code = models.CharField(max_length=50)

    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finance_billing_config'
        indexes = [
            models.Index(fields=['tenant', 'service_code']),
            models.Index(fields=['is_active']),
        ]

