#!/usr/bin/env python
"""
Simple migration script for core multi-tenancy models.
This script handles just the essential models to get multi-tenancy working.
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


def create_core_migration():
    """Create core app migration"""
    print("Creating core app migration...")
    
    try:
        call_command('makemigrations', 'core', verbosity=1)
        print("Core migration created successfully!")
        return True
    except Exception as e:
        print(f"Error creating core migration: {e}")
        return False


def apply_migrations():
    """Apply all migrations"""
    print("Applying migrations...")
    
    try:
        call_command('migrate', verbosity=1)
        print("Migrations applied successfully!")
        return True
    except Exception as e:
        print(f"Error applying migrations: {e}")
        return False


def main():
    """Main migration process"""
    print("SpotOn Core Multi-Tenancy Migration")
    print("=" * 40)
    
    # Step 1: Create default tenant
    if not create_default_tenant():
        print("Failed to create default tenant. Exiting.")
        return False
    
    # Step 2: Create core migration
    if not create_core_migration():
        print("Failed to create core migration. Exiting.")
        return False
    
    # Step 3: Apply migrations
    if not apply_migrations():
        print("Failed to apply migrations. Exiting.")
        return False
    
    print("\n" + "=" * 40)
    print("Core migration completed successfully!")
    print("\nNext steps:")
    print("1. Create migrations for individual apps")
    print("2. Populate tenant data for existing records")
    print("3. Set up Row Level Security")
    
    return True


if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 