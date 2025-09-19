#!/usr/bin/env python
"""
Script to create database migrations for multi-tenant white-label architecture.
This script generates migrations to add tenant foreign keys to existing models.
"""

import os
import sys
import django
from django.core.management import call_command
from django.db import connection

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.apps import apps
from django.db import models


def create_tenant_migrations():
    """Create migrations for adding tenant fields to models"""
    
    # Models that need tenant foreign keys
    models_to_update = [
        # Energy models
        ('energy.export_core', 'ExportLog'),
        ('energy.export_core', 'ReconciliationSubmission'),
        ('energy.export_core', 'MarketSubmission'),
        ('energy.switching', 'SwitchRequest'),
        ('energy.switching', 'RegistryMessage'),
        
        # Finance models
        ('finance.pricing', 'ServicePlan'),
        ('finance.pricing', 'PricingRule'),
        ('finance.pricing', 'CustomerPricing'),
        ('finance.pricing', 'PriceCalculation'),
        
        # Web support models
        ('web_support.address_plans', 'Address'),
        ('web_support.onboarding', 'OnboardingProgress'),
        ('web_support.public_pricing', 'ElectricityPlan'),
        ('web_support.public_pricing', 'BroadbandPlan'),
        ('web_support.public_pricing', 'MobilePlan'),
    ]
    
    print("Creating tenant migrations...")
    
    for app_label, model_name in models_to_update:
        try:
            # Get the app config
            app_config = apps.get_app_config(app_label.split('.')[-1])
            
            # Create migration for this app
            print(f"Creating migration for {app_label}.{model_name}")
            
            # Run makemigrations for the specific app
            call_command('makemigrations', app_label.split('.')[-1], verbosity=1)
            
        except Exception as e:
            print(f"Error creating migration for {app_label}.{model_name}: {e}")
    
    print("\nMigrations created successfully!")
    print("Next steps:")
    print("1. Review the generated migrations")
    print("2. Run: python manage.py migrate")
    print("3. Run the RLS setup script: psql -f scripts/setup_row_level_security.sql")


def create_data_migration_script():
    """Create a data migration script to populate tenant fields"""
    
    script_content = '''
"""
Data migration to populate tenant fields for existing records.
This migration assigns all existing records to the first tenant.
"""

from django.db import migrations
from django.db.models import Q


def populate_tenant_fields(apps, schema_editor):
    """Populate tenant fields for existing records"""
    
    # Get the Tenant model
    Tenant = apps.get_model('users', 'Tenant')
    
    # Get the first tenant (default tenant)
    try:
        default_tenant = Tenant.objects.first()
        if not default_tenant:
            print("No tenants found. Creating default tenant...")
            default_tenant = Tenant.objects.create(
                name="Default Tenant",
                slug="default",
                contact_email="admin@spoton.energy",
                timezone="Pacific/Auckland",
                currency="NZD",
                is_active=True
            )
    except Exception as e:
        print(f"Error getting default tenant: {e}")
        return
    
    # Models to update with tenant references
    models_to_update = [
        # Energy models
        ('energy', 'ExportLog'),
        ('energy', 'ReconciliationSubmission'),
        ('energy', 'MarketSubmission'),
        ('energy', 'SwitchRequest'),
        ('energy', 'RegistryMessage'),
        
        # Finance models
        ('finance', 'ServicePlan'),
        ('finance', 'PricingRule'),
        ('finance', 'CustomerPricing'),
        ('finance', 'PriceCalculation'),
        
        # Web support models
        ('web_support', 'Address'),
        ('web_support', 'OnboardingProgress'),
        ('web_support', 'ElectricityPlan'),
        ('web_support', 'BroadbandPlan'),
        ('web_support', 'MobilePlan'),
    ]
    
    for app_label, model_name in models_to_update:
        try:
            Model = apps.get_model(app_label, model_name)
            
            # Update records that don't have tenant set
            updated_count = Model.objects.filter(
                Q(tenant__isnull=True) | Q(tenant_id__isnull=True)
            ).update(tenant=default_tenant)
            
            print(f"Updated {updated_count} {model_name} records with default tenant")
            
        except Exception as e:
            print(f"Error updating {app_label}.{model_name}: {e}")


def reverse_populate_tenant_fields(apps, schema_editor):
    """Reverse the tenant field population"""
    # This is a data migration, so we don't reverse it
    pass


class Migration(migrations.Migration):
    
    dependencies = [
        ('users', '0002_initial'),  # Adjust based on your tenant migration
        # Add other dependencies as needed
    ]
    
    operations = [
        migrations.RunPython(
            populate_tenant_fields,
            reverse_populate_tenant_fields
        ),
    ]
'''
    
    # Write the data migration script
    migration_path = 'scripts/0001_populate_tenant_fields.py'
    with open(migration_path, 'w') as f:
        f.write(script_content)
    
    print(f"Data migration script created at: {migration_path}")


def update_settings_for_multitenancy():
    """Update Django settings for multi-tenancy"""
    
    settings_updates = '''
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'core',  # Add core app with base models
]

# Add to MIDDLEWARE
MIDDLEWARE = [
    # ... existing middleware ...
    'utilitybyte.middleware.TenantAwareMiddleware',
    'utilitybyte.middleware.TenantSecurityMiddleware',
    'utilitybyte.middleware.DatabaseTransactionMiddleware',
]

# Multi-tenancy settings
TENANT_MODEL = 'users.Tenant'
TENANT_DOMAIN_MODEL = 'users.TenantDomain'

# Database settings for RLS
DATABASES = {
    'default': {
        # ... existing database config ...
        'OPTIONS': {
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
}

# Logging for tenant operations
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'tenant_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/tenant_operations.log',
        },
    },
    'loggers': {
        'utilitybyte.middleware': {
            'handlers': ['tenant_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'core.api_views': {
            'handlers': ['tenant_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
'''
    
    print("Settings updates needed:")
    print(settings_updates)


if __name__ == '__main__':
    print("SpotOn Multi-Tenant Migration Generator")
    print("=" * 50)
    
    # Create migrations
    create_tenant_migrations()
    
    # Create data migration script
    create_data_migration_script()
    
    # Show settings updates
    update_settings_for_multitenancy()
    
    print("\nMigration process completed!")
    print("Remember to:")
    print("1. Review all generated migrations")
    print("2. Test migrations in development environment")
    print("3. Update settings.py with the provided configuration")
    print("4. Run migrations: python manage.py migrate")
    print("5. Apply RLS policies: psql -f scripts/setup_row_level_security.sql") 