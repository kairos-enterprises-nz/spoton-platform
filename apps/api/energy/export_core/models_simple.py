"""
Export Core models - Simple version for testing
"""
from django.db import models
from users.models import Tenant
import uuid


class ExportTemplate(models.Model):
    """
    Simple test model to check if table creation works
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'energy_export_template'
    
    def __str__(self):
        return self.name 