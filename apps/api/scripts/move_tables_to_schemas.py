#!/usr/bin/env python
"""
Script to move tables from public schema to their intended schemas.
"""
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
import django
django.setup()

from django.db import connections
from django.apps import apps

def get_app_schema_mapping():
    """Get mapping of app labels to their intended schemas."""
    return {
        'users': 'users',
        'contracts': 'contracts', 
        'billing': 'finance',
        'pricing': 'finance',
        'connections': 'energy',
        'metering': 'energy',
        'export_core': 'energy',
        'tariffs': 'energy',
        'tariff_profile': 'energy',
        'validation': 'energy',
        'wits': 'energy',
        # Keep these in public
        'address_plans': 'public',
        'public_pricing': 'public',
        'user_details': 'public',
        # Django core apps stay in public
        'admin': 'public',
        'auth': 'public',
        'contenttypes': 'public',
        'sessions': 'public',
    }

def move_tables_to_schemas():
    """Move tables from public schema to their intended schemas."""
    print("🚚 Moving tables to correct schemas...")
    
    connection = connections['default']
    cursor = connection.cursor()
    
    # Get all apps and their models
    app_schema_mapping = get_app_schema_mapping()
    
    moved_tables = []
    
    for app_config in apps.get_app_configs():
        app_label = app_config.label
        target_schema = app_schema_mapping.get(app_label)
        
        if not target_schema or target_schema == 'public':
            continue
            
        print(f"\n📦 Processing app: {app_label} -> {target_schema} schema")
        
        # Get all models for this app
        for model in app_config.get_models():
            table_name = model._meta.db_table
            
            # Skip tables that already have schema prefix in name
            if '.' in table_name:
                print(f"  ⚠️  Skipping {table_name} (already has schema prefix)")
                continue
            
            try:
                # Check if table exists in public schema
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_tables 
                        WHERE schemaname = 'public' 
                        AND tablename = %s
                    )
                """, [table_name])
                
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    # Move table to target schema
                    cursor.execute(f"""
                        ALTER TABLE public.{table_name} 
                        SET SCHEMA {target_schema}
                    """)
                    moved_tables.append(f"public.{table_name} -> {target_schema}.{table_name}")
                    print(f"  ✅ Moved: {table_name} -> {target_schema}")
                else:
                    print(f"  ⚠️  Table {table_name} not found in public schema")
                    
            except Exception as e:
                print(f"  ❌ Error moving {table_name}: {e}")
    
    # Handle special cases - tables with schema prefixes in names
    print(f"\n🔧 Handling tables with schema prefixes in names...")
    
    # Get tables that have schema prefixes in their names
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND (tablename LIKE 'users.%' OR 
             tablename LIKE 'contracts.%' OR
             tablename LIKE 'energy.%')
    """)
    
    prefixed_tables = cursor.fetchall()
    
    for (table_name,) in prefixed_tables:
        try:
            if table_name.startswith('users.'):
                # Move to users schema and rename
                new_name = table_name.replace('users.', '')
                cursor.execute(f'ALTER TABLE public."{table_name}" SET SCHEMA users')
                cursor.execute(f'ALTER TABLE users."{table_name}" RENAME TO {new_name}')
                moved_tables.append(f'public."{table_name}" -> users.{new_name}')
                print(f"  ✅ Moved and renamed: {table_name} -> users.{new_name}")
                
            elif table_name.startswith('contracts.'):
                # Move to contracts schema and rename  
                new_name = table_name.replace('contracts.', '')
                cursor.execute(f'ALTER TABLE public."{table_name}" SET SCHEMA contracts')
                cursor.execute(f'ALTER TABLE contracts."{table_name}" RENAME TO {new_name}')
                moved_tables.append(f'public."{table_name}" -> contracts.{new_name}')
                print(f"  ✅ Moved and renamed: {table_name} -> contracts.{new_name}")
                
        except Exception as e:
            print(f"  ❌ Error handling {table_name}: {e}")
    
    print(f"\n✅ Table movement completed!")
    print(f"📊 Summary: {len(moved_tables)} tables moved")
    
    for move in moved_tables:
        print(f"  - {move}")
    
    return len(moved_tables)

def verify_table_locations():
    """Verify tables are in correct schemas."""
    print(f"\n🔍 Verifying table locations...")
    
    connection = connections['default']
    cursor = connection.cursor()
    
    # Check key tables in each schema
    checks = [
        ('users', 'users_user'),
        ('users', 'users_tenant'), 
        ('finance', 'billing_bill'),
        ('energy', 'metering_meteringpoint'),
        ('contracts', 'servicecontract'),
    ]
    
    all_good = True
    
    for schema, table in checks:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_tables 
                WHERE schemaname = %s 
                AND tablename = %s
            )
        """, [schema, table])
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print(f"  ✅ {schema}.{table} - OK")
        else:
            print(f"  ❌ {schema}.{table} - MISSING")
            all_good = False
    
    return all_good

def main():
    """Main function."""
    print("🚀 Starting table schema migration...")
    
    try:
        # Move tables
        moved_count = move_tables_to_schemas()
        
        # Verify
        all_good = verify_table_locations()
        
        if all_good and moved_count > 0:
            print("✅ Table schema migration completed successfully!")
            return 0
        elif moved_count == 0:
            print("ℹ️  No tables needed to be moved")
            return 0
        else:
            print("❌ Some tables may not be in correct locations")
            return 1
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main()) 