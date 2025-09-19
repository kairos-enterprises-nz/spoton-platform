# address_plans/models.py
from django.db import models


class Address(models.Model):
    """
    Address model for New Zealand addresses.
    Contains comprehensive address data from official sources.
    """
    
    address_id = models.IntegerField(help_text="Original address ID from source dataset")
    source_dataset = models.CharField(max_length=255, help_text="Source dataset identifier")
    change_id = models.IntegerField(help_text="Change tracking ID")
    
    # Address components
    full_address_number = models.CharField(max_length=255, blank=True)
    full_road_name = models.CharField(max_length=255, blank=True)
    full_address = models.CharField(max_length=1024, db_index=True)
    territorial_authority = models.CharField(max_length=255, blank=True)
    
    # Unit and level details
    unit_type = models.CharField(max_length=100, blank=True)
    unit_value = models.CharField(max_length=100, blank=True)
    level_type = models.CharField(max_length=100, blank=True)
    level_value = models.CharField(max_length=100, blank=True)
    
    # Address number components
    address_number_prefix = models.CharField(max_length=50, blank=True)
    address_number = models.CharField(max_length=50, blank=True)
    address_number_suffix = models.CharField(max_length=50, blank=True)
    address_number_high = models.CharField(max_length=50, blank=True)
    
    # Road name components
    road_name_prefix = models.CharField(max_length=50, blank=True)
    road_name = models.CharField(max_length=255, blank=True)
    road_type_name = models.CharField(max_length=100, blank=True)
    road_suffix = models.CharField(max_length=50, blank=True)
    
    # Water body details
    water_name = models.CharField(max_length=255, blank=True)
    water_body_name = models.CharField(max_length=255, blank=True)
    
    # Location details
    suburb_locality = models.CharField(max_length=255, blank=True, db_index=True)
    town_city = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Address classification
    address_class = models.CharField(max_length=100, blank=True)
    address_lifecycle = models.CharField(max_length=100, blank=True)
    
    # Coordinates
    gd2000_xcoord = models.FloatField(null=True, blank=True)
    gd2000_ycoord = models.FloatField(null=True, blank=True)
    shape_X = models.FloatField(null=True, blank=True)
    shape_Y = models.FloatField(null=True, blank=True)
    
    # ASCII versions for search
    road_name_ascii = models.CharField(max_length=255, blank=True)
    water_name_ascii = models.CharField(max_length=255, blank=True)
    water_body_name_ascii = models.CharField(max_length=255, blank=True)
    suburb_locality_ascii = models.CharField(max_length=255, blank=True)
    town_city_ascii = models.CharField(max_length=255, blank=True)
    full_road_name_ascii = models.CharField(max_length=255, blank=True)
    full_address_ascii = models.CharField(max_length=1024, blank=True)

    class Meta:
        db_table = 'address_plans_address'
        indexes = [
            models.Index(fields=['full_address']),
            models.Index(fields=['suburb_locality', 'town_city']),
            models.Index(fields=['address_id', 'source_dataset']),
        ]

    def __str__(self):
        return f"{self.full_address} ({self.suburb_locality})"
    
    @classmethod
    def get_shared_addresses(cls):
        """Get addresses that are shared across all tenants/brands"""
        return cls.objects.filter(is_shared=True)
    
    @classmethod
    def get_tenant_addresses(cls, tenant):
        """Get addresses specific to a tenant/brand plus shared ones"""
        return cls.objects.filter(
            models.Q(tenant=tenant) | models.Q(is_shared=True)
        ).filter(is_active=True)
