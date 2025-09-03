#!/usr/bin/env python
"""
Comprehensive migration script for SpotOn multi-tenancy implementation.
This script handles the migration in phases to avoid complex dependency issues.
"""

import os
import sys
import django
from django.core.management import call_command
from django.db import connection, transaction

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.apps import apps
from users.models import Tenant


def create_default_tenant():
    """Create default tenant if it doesn't exist"""
    print("Creating default tenant...")
    
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            tenant = Tenant.objects.create(
                name="SpotOn Energy",
                slug="spoton",
                contact_email="admin@spoton.energy",
                timezone="Pacific/Auckland",
                currency="NZD",
                is_active=True,
                business_number="123456789",
                service_limits={}
            )
            print(f"Created default tenant: {tenant.name}")
        else:
            print(f"Default tenant already exists: {tenant.name}")
        
        return tenant
    except Exception as e:
        print(f"Error creating default tenant: {e}")
        return None


def run_migration_phase(phase_name, apps_to_migrate=None):
    """Run a specific migration phase"""
    print(f"\n=== Phase {phase_name} ===")
    
    try:
        if apps_to_migrate:
            for app in apps_to_migrate:
                print(f"Creating migrations for {app}...")
                call_command('makemigrations', app, verbosity=1)
        else:
            print("Creating all migrations...")
            call_command('makemigrations', verbosity=1)
        
        print("Applying migrations...")
        call_command('migrate', verbosity=1)
        
        print(f"Phase {phase_name} completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in phase {phase_name}: {e}")
        return False


def populate_tenant_data():
    """Populate tenant data for existing records"""
    print("\n=== Populating Tenant Data ===")
    
    try:
        # Get default tenant
        default_tenant = Tenant.objects.first()
        if not default_tenant:
            print("No default tenant found!")
            return False
        
        # Update models that now have tenant fields
        models_to_update = [
            ('web_support', 'Address'),
            ('energy', 'Connection'),
            ('energy', 'ConnectionPlan'),
            ('finance', 'ServicePlan'),
            ('finance', 'PricingRule'),
            ('finance', 'CustomerPricing'),
            ('finance', 'PriceCalculation'),
        ]
        
        for app_label, model_name in models_to_update:
            try:
                Model = apps.get_model(app_label, model_name)
                
                # Update records without tenant
                updated_count = Model.objects.filter(tenant__isnull=True).update(
                    tenant=default_tenant
                )
                
                print(f"Updated {updated_count} {model_name} records with default tenant")
                
            except Exception as e:
                print(f"Error updating {app_label}.{model_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error populating tenant data: {e}")
        return False


def verify_tenant_isolation():
    """Verify that tenant isolation is working"""
    print("\n=== Verifying Tenant Isolation ===")
    
    try:
        # Check that all critical models have tenant fields
        models_to_check = [
            ('web_support', 'Address'),
            ('energy', 'Connection'),
            ('finance', 'ServicePlan'),
        ]
        
        for app_label, model_name in models_to_check:
            try:
                Model = apps.get_model(app_label, model_name)
                
                # Check if model has tenant field
                if hasattr(Model, 'tenant'):
                    total_count = Model.objects.count()
                    tenant_count = Model.objects.exclude(tenant__isnull=True).count()
                    
                    print(f"{model_name}: {tenant_count}/{total_count} records have tenant assigned")
                    
                    if tenant_count < total_count:
                        print(f"  WARNING: {total_count - tenant_count} records missing tenant!")
                else:
                    print(f"  WARNING: {model_name} does not have tenant field!")
                    
            except Exception as e:
                print(f"Error checking {app_label}.{model_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error verifying tenant isolation: {e}")
        return False


def setup_row_level_security():
    """Set up PostgreSQL Row Level Security"""
    print("\n=== Setting up Row Level Security ===")
    
    try:
        # Run the RLS setup script
        rls_script_path = os.path.join(os.path.dirname(__file__), 'setup_row_level_security.sql')
        
        if os.path.exists(rls_script_path):
            print("Applying RLS policies...")
            
            with open(rls_script_path, 'r') as f:
                sql_content = f.read()
            
            # Execute the SQL script
            with connection.cursor() as cursor:
                cursor.execute(sql_content)
            
            print("RLS policies applied successfully!")
            return True
        else:
            print(f"RLS script not found at: {rls_script_path}")
            return False
            
    except Exception as e:
        print(f"Error setting up RLS: {e}")
        return False


def main():
    """Main migration process"""
    print("SpotOn Multi-Tenancy Migration")
    print("=" * 50)
    
    # Phase 1: Create default tenant
    default_tenant = create_default_tenant()
    if not default_tenant:
        print("Failed to create default tenant. Exiting.")
        return False
    
    # Phase 2: Create and apply core migrations
    if not run_migration_phase("Core Models", ["core"]):
        print("Failed to migrate core models. Exiting.")
        return False
    
    # Phase 3: Create and apply specific app migrations
    apps_to_migrate = [
        "address_plans",
        "connections", 
        "pricing",
        "switching",
        "export_core"
    ]
    
    for app in apps_to_migrate:
        if not run_migration_phase(f"App {app}", [app]):
            print(f"Failed to migrate {app}. Continuing with next app...")
    
    # Phase 4: Populate tenant data
    if not populate_tenant_data():
        print("Failed to populate tenant data. Please check manually.")
    
    # Phase 5: Verify tenant isolation
    if not verify_tenant_isolation():
        print("Tenant isolation verification failed. Please check manually.")
    
    # Phase 6: Set up Row Level Security
    if not setup_row_level_security():
        print("Failed to set up RLS. Please run manually:")
        print("psql -f scripts/setup_row_level_security.sql")
    
    print("\n" + "=" * 50)
    print("Migration completed!")
    print("\nNext steps:")
    print("1. Update your Django settings with the middleware configuration")
    print("2. Test the tenant isolation in your application")
    print("3. Update your API views to use the tenant-aware base classes")
    print("4. Test subdomain-based tenant detection")
    
    return True


if __name__ == '__main__':
    with transaction.atomic():
        success = main()
        if not success:
            print("Migration failed. Rolling back...")
            transaction.set_rollback(True)
        else:
            print("Migration successful!") 