#!/usr/bin/env python
"""
Simple tenant migration script that uses raw SQL to add tenant fields.
This bypasses Django's migration system for problematic models.
"""

import os
import sys
import django
from django.db import connection

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from users.models import Tenant


def get_default_tenant():
    """Get the default tenant"""
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            print("No tenant found! Creating default tenant...")
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
        return tenant
    except Exception as e:
        print(f"Error getting default tenant: {e}")
        return None


def add_tenant_fields_to_address():
    """Add tenant fields to address table using raw SQL"""
    print("Adding tenant fields to address table...")
    
    try:
        with connection.cursor() as cursor:
            # Check if tenant_id column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'address_plans_address' AND column_name = 'tenant_id';
            """)
            
            if not cursor.fetchone():
                print("Adding tenant_id column...")
                cursor.execute("""
                    ALTER TABLE address_plans_address 
                    ADD COLUMN tenant_id UUID REFERENCES users_tenant(id);
                """)
            
            # Check if created_at column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'address_plans_address' AND column_name = 'created_at';
            """)
            
            if not cursor.fetchone():
                print("Adding audit columns...")
                cursor.execute("""
                    ALTER TABLE address_plans_address 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    ADD COLUMN created_by_id UUID REFERENCES users_user(id),
                    ADD COLUMN updated_by_id UUID REFERENCES users_user(id);
                """)
            
            # Check if is_active column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'address_plans_address' AND column_name = 'is_active';
            """)
            
            if not cursor.fetchone():
                print("Adding multi-tenant columns...")
                cursor.execute("""
                    ALTER TABLE address_plans_address 
                    ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
                    ADD COLUMN is_shared BOOLEAN DEFAULT FALSE;
                """)
            
            print("Tenant fields added successfully!")
            return True
            
    except Exception as e:
        print(f"Error adding tenant fields: {e}")
        return False


def populate_tenant_data():
    """Populate tenant data for existing records"""
    print("Populating tenant data...")
    
    try:
        default_tenant = get_default_tenant()
        if not default_tenant:
            return False
        
        with connection.cursor() as cursor:
            # Update all records without tenant_id
            cursor.execute("""
                UPDATE address_plans_address 
                SET tenant_id = %s 
                WHERE tenant_id IS NULL;
            """, [default_tenant.id])
            
            updated_count = cursor.rowcount
            print(f"Updated {updated_count} address records with default tenant")
            
            return True
            
    except Exception as e:
        print(f"Error populating tenant data: {e}")
        return False


def create_indexes():
    """Create indexes for tenant fields"""
    print("Creating indexes...")
    
    try:
        with connection.cursor() as cursor:
            # Create tenant-based indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS address_plans_address_tenant_id_idx 
                ON address_plans_address(tenant_id);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS address_plans_address_tenant_active_idx 
                ON address_plans_address(tenant_id, is_active);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS address_plans_address_is_shared_idx 
                ON address_plans_address(is_shared);
            """)
            
            print("Indexes created successfully!")
            return True
            
    except Exception as e:
        print(f"Error creating indexes: {e}")
        return False


def main():
    """Main migration process"""
    print("SpotOn Simple Tenant Migration")
    print("=" * 40)
    
    # Step 1: Add tenant fields to address table
    if not add_tenant_fields_to_address():
        print("Failed to add tenant fields. Exiting.")
        return False
    
    # Step 2: Populate tenant data
    if not populate_tenant_data():
        print("Failed to populate tenant data. Exiting.")
        return False
    
    # Step 3: Create indexes
    if not create_indexes():
        print("Failed to create indexes. Continuing...")
    
    print("\n" + "=" * 40)
    print("Simple tenant migration completed!")
    print("\nNext steps:")
    print("1. Test the tenant isolation")
    print("2. Apply migrations to other models")
    print("3. Set up Row Level Security")
    
    return True


if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 