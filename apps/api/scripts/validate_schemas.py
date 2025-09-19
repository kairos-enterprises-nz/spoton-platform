#!/usr/bin/env python
"""
Script to validate that schemas exist and tables are in correct locations.
"""
import os
import sys

# Only setup Django if not already configured
try:
    from django.conf import settings
    if not settings.configured:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
        django.setup()
except ImportError:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
    django.setup()

from django.db import connections

def validate_schemas():
    """Validate that schemas exist and critical tables are in correct locations."""
    print("🔍 Validating schema setup...")
    
    # Check critical tables exist in correct schemas
    checks = [
        ('users', 'users_user'),
        # Add more checks as needed when other apps are properly migrated
    ]
    
    failed = False
    
    for schema, table in checks:
        try:
            connection = connections[schema]
            cursor = connection.cursor()
            cursor.execute(f"SELECT to_regclass('{table}')")
            result = cursor.fetchone()[0]
            
            if result is None:
                print(f"❌ FAIL: Table {table} not found in {schema} schema")
                failed = True
            else:
                print(f"✅ OK: Table {table} exists in {schema} schema")
                
        except Exception as e:
            print(f"❌ ERROR checking {table}: {e}")
            failed = True
    
    # Also check that schemas exist
    schema_names = ['users', 'contracts', 'energy', 'finance', 'pricing', 'support']
    
    for schema_name in schema_names:
        try:
            connection = connections['default']  # Use default connection to check schema existence
            cursor = connection.cursor()
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            result = cursor.fetchone()
            
            if result:
                print(f"✅ OK: Schema '{schema_name}' exists")
            else:
                print(f"❌ FAIL: Schema '{schema_name}' does not exist")
                failed = True
                
        except Exception as e:
            print(f"❌ ERROR checking schema {schema_name}: {e}")
            failed = True
    
    # Check django_content_type table structure
    print(f"\n=== Validating Django Content Type Table ===")
    try:
        connection = connections['default']
        cursor = connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'django_content_type'
            ORDER BY column_name
        """)
        columns = [row[0] for row in cursor.fetchall()]
        expected_columns = ['app_label', 'id', 'model']
        
        if set(columns) == set(expected_columns):
            print(f"✅ OK: django_content_type has correct columns: {sorted(columns)}")
        else:
            print(f"❌ FAIL: django_content_type columns mismatch")
            print(f"   Expected: {sorted(expected_columns)}")
            print(f"   Found: {sorted(columns)}")
            failed = True
            
        # Check that 'name' column doesn't exist (it was removed in Django 5)
        if 'name' in columns:
            print("❌ FAIL: django_content_type still has deprecated 'name' column")
            failed = True
        else:
            print("✅ OK: django_content_type doesn't have deprecated 'name' column")
            
    except Exception as e:
        print(f"❌ ERROR checking django_content_type: {e}")
        failed = True

    if failed:
        print("❌ Schema validation failed!")
        return 1
    else:
        print("✅ All schema validations passed!")
        return 0

if __name__ == '__main__':
    sys.exit(validate_schemas()) 