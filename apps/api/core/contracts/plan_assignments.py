"""
Plan assignment models for linking registry plans to contracts
"""

import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class ContractPlanAssignment(models.Model):
    """
    Links registry plans (ElectricityPlan, BroadbandPlan, etc.) to contracts.
    This allows contracts to have assigned plans from the available registry.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='contract_plan_assignments')
    contract = models.ForeignKey('ServiceContract', on_delete=models.CASCADE, related_name='plan_assignments')
    
    # Plan reference (links to registry plans)
    PLAN_TYPE_CHOICES = [
        ('electricity', 'Electricity Plan'),
        ('broadband', 'Broadband Plan'),
        ('mobile', 'Mobile Plan'),
        ('gas', 'Gas Plan'),
    ]
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    plan_id = models.CharField(max_length=50, help_text="ID of the plan in the registry (ElectricityPlan.plan_id, etc.)")
    plan_name = models.CharField(max_length=200, help_text="Cached plan name for quick access")
    
    # Assignment details
    assigned_date = models.DateField(default=timezone.now)
    assigned_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Validity period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'contracts_contractplanassignment'
        verbose_name = 'Contract Plan Assignment'
        verbose_name_plural = 'Contract Plan Assignments'
        indexes = [
            models.Index(fields=['contract', 'plan_type']),
            models.Index(fields=['plan_id', 'plan_type']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['contract', 'plan_type', 'valid_from'],
                name='unique_contract_plan_assignment_per_period'
            )
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} -> {self.plan_name} ({self.plan_type})"
    
    @property
    def registry_plan(self):
        """Get the actual plan object from the registry"""
        if self.plan_type == 'electricity':
            from web_support.public_pricing.models import ElectricityPlan
            try:
                return ElectricityPlan.objects.get(plan_id=self.plan_id)
            except ElectricityPlan.DoesNotExist:
                return None
        elif self.plan_type == 'broadband':
            from web_support.public_pricing.models import BroadbandPlan
            try:
                return BroadbandPlan.objects.get(plan_id=self.plan_id)
            except BroadbandPlan.DoesNotExist:
                return None
        elif self.plan_type == 'mobile':
            from web_support.public_pricing.models import MobilePlan
            try:
                return MobilePlan.objects.get(plan_id=self.plan_id)
            except MobilePlan.DoesNotExist:
                return None
        return None
    
    @property
    def is_active(self):
        """Check if assignment is currently active"""
        now = timezone.now()
        return (
            self.valid_from <= now and
            (self.valid_to is None or self.valid_to > now)
        )
    
    def clean(self):
        """Validate assignment data"""
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError("Valid to date must be after valid from date")
        
        # Validate that plan exists in registry
        if not self.registry_plan:
            raise ValidationError(f"Plan {self.plan_id} not found in {self.plan_type} registry")
    
    def save(self, *args, **kwargs):
        # Auto-populate plan_name from registry if not set
        if not self.plan_name and self.registry_plan:
            self.plan_name = self.registry_plan.name
        
        self.clean()
        super().save(*args, **kwargs)


class ContractConnectionAssignment(models.Model):
    """
    Links connections to contracts (assignment system for connections).
    This allows contracts to have assigned connections from available connection pool.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='contract_connection_assignments')
    contract = models.ForeignKey('ServiceContract', on_delete=models.CASCADE, related_name='connection_assignments')
    connection_id = models.UUIDField(help_text="ID of the connection (energy.connections.Connection)")
    
    # Assignment details
    assigned_date = models.DateField(default=timezone.now)
    assigned_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Validity period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'contracts_contractconnectionassignment'
        verbose_name = 'Contract Connection Assignment'
        verbose_name_plural = 'Contract Connection Assignments'
        indexes = [
            models.Index(fields=['contract', 'connection_id']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['contract', 'connection_id'],
                name='unique_contract_connection_assignment'
            )
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number} -> Connection {self.connection_id}"
    
    @property
    def connection(self):
        """Get the actual connection object"""
        from energy.connections.models import Connection
        try:
            return Connection.objects.get(id=self.connection_id)
        except Connection.DoesNotExist:
            return None
    
    @property
    def is_active(self):
        """Check if assignment is currently active"""
        now = timezone.now()
        return (
            self.status in ['assigned', 'active'] and
            self.valid_from <= now and
            (self.valid_to is None or self.valid_to > now)
        )