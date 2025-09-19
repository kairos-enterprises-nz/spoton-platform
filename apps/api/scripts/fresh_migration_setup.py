#!/usr/bin/env python
"""
Script to completely reset database and migrations for a clean start.
This will:
1. Drop all schemas and tables
2. Recreate schemas
3. Remove all migration files
4. Create fresh initial migrations
5. Apply migrations cleanly
"""
import os
import sys
import shutil
import glob
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
import django
django.setup()

from django.db import connections, transaction
from django.core.management import call_command
from django.apps import apps

def drop_all_schemas():
    """Drop all custom schemas and tables."""
    print("🗑️  Dropping all schemas and tables...")
    
    # Get all database connections
    for alias in ['default', 'users', 'contracts', 'energy', 'finance', 'pricing', 'support']:
        try:
            connection = connections[alias]
            cursor = connection.cursor()
            
            if alias == 'default':
                # Drop all tables in public schema
                cursor.execute("""
                    DROP SCHEMA IF EXISTS users CASCADE;
                    DROP SCHEMA IF EXISTS contracts CASCADE;
                    DROP SCHEMA IF EXISTS energy CASCADE;
                    DROP SCHEMA IF EXISTS finance CASCADE;
                    DROP SCHEMA IF EXISTS pricing CASCADE;
                    DROP SCHEMA IF EXISTS support CASCADE;
                    
                    -- Drop all tables in public schema
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                    END $$;
                """)
                print(f"✅ Dropped all schemas and public tables")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not clean {alias}: {e}")

def create_schemas():
    """Create all required schemas."""
    print("🏗️  Creating schemas...")
    
    connection = connections['default']
    cursor = connection.cursor()
    
    schemas = ['users', 'contracts', 'energy', 'finance', 'pricing', 'support']
    for schema in schemas:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        print(f"✅ Created schema: {schema}")

def remove_migration_files():
    """Remove all migration files except __init__.py."""
    print("🧹 Removing migration files...")
    
    # Get all Django apps
    django_apps = apps.get_app_configs()
    
    for app_config in django_apps:
        migrations_dir = Path(app_config.path) / 'migrations'
        if migrations_dir.exists():
            # Remove all migration files except __init__.py
            for migration_file in migrations_dir.glob('*.py'):
                if migration_file.name != '__init__.py':
                    migration_file.unlink()
                    print(f"  Removed: {migration_file}")
            
            # Remove __pycache__ directory
            pycache_dir = migrations_dir / '__pycache__'
            if pycache_dir.exists():
                shutil.rmtree(pycache_dir)

def create_fresh_migrations():
    """Create fresh initial migrations for all apps."""
    print("📝 Creating fresh migrations...")
    
    # Create migrations for all apps
    call_command('makemigrations')
    print("✅ Created fresh migrations")

def apply_migrations():
    """Apply migrations to all databases."""
    print("🔄 Applying migrations...")
    
    # First, fake the Django core migrations that we don't need to create tables for
    print("🔧 Setting up Django core migrations...")
    
    try:
        # Apply contenttypes and auth migrations to default database
        call_command('migrate', 'contenttypes', database='default', verbosity=0)
        call_command('migrate', 'auth', database='default', verbosity=0)
        call_command('migrate', 'admin', database='default', verbosity=0)
        call_command('migrate', 'sessions', database='default', verbosity=0)
        print("✅ Applied Django core migrations")
    except Exception as e:
        print(f"⚠️  Warning: Core migrations issue: {e}")
    
    # Apply migrations to all databases
    databases = ['default', 'users', 'contracts', 'energy', 'finance', 'pricing', 'support']
    
    for db in databases:
        try:
            print(f"📊 Migrating {db} database...")
            call_command('migrate', database=db, verbosity=0)
            print(f"✅ Migrated {db}")
        except Exception as e:
            print(f"❌ Error migrating {db}: {e}")

def create_superuser():
    """Create a default superuser."""
    print("👤 Creating superuser...")
    
    try:
        from users.models import User
        
        # Check if superuser already exists
        if not User.objects.filter(email='admin@spoton.co.nz').exists():
            User.objects.create_superuser(
                email='admin@spoton.co.nz',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            print("✅ Created superuser: admin@spoton.co.nz / admin123")
        else:
            print("✅ Superuser already exists")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not create superuser: {e}")

def move_tables_to_schemas():
    """Move tables from public schema to their intended schemas."""
    print("🚚 Moving tables to correct schemas...")
    
    connection = connections['default']
    cursor = connection.cursor()
    
    # Define which app's tables go into which schema
    app_schema_mapping = {
        'users': 'users', 'contracts': 'contracts', 'billing': 'finance',
        'invoices': 'finance', 'pricing': 'finance', 'connections': 'energy',
        'metering': 'energy', 'export_core': 'energy', 'tariffs': 'energy',
        'tariff_profile': 'energy', 'validation': 'energy', 'wits': 'energy',
        'reconciliation': 'energy', 'switching': 'energy', 'registry': 'energy',
        'submissions': 'energy', 'service_orders': 'energy', 'audit': 'energy',
        'support': 'support',
    }

    # Get all models from all apps
    all_models = apps.get_models(include_auto_created=True)
    
    for model in all_models:
        app_label = model._meta.app_label
        table_name = model._meta.db_table
        target_schema = app_schema_mapping.get(app_label)

        if not target_schema:
            print(f"  ➡️ Skipping {table_name} (app: {app_label}), stays in public.")
            continue

        try:
            print(f"  🚚 Moving {table_name} to {target_schema}...")
            # Use proper quoting for table names that might contain special characters
            cursor.execute(f'ALTER TABLE public.{connection.schema_editor().quote_name(table_name)} SET SCHEMA {target_schema}')
        except Exception as e:
            # It's okay if it fails (e.g., table not in public), just log it
            print(f"    ⚠️  Warning: Could not move table {table_name}: {e}")
            
    print("✅ Table moving process completed.")

def main():
    """Main function to reset everything."""
    print("🚀 Starting fresh migration setup...")
    print("⚠️  This will DESTROY all data in the database!")
    
    try:
        # Step 1: Drop everything
        drop_all_schemas()
        
        # Step 2: Create fresh migrations (files)
        remove_migration_files()
        create_fresh_migrations()
        
        # Step 3: Apply ALL migrations to the default (public) database
        print("🔄 Applying all migrations to public schema first...")
        call_command('migrate', database='default')
        print("✅ All migrations applied to public.")
        
        # Step 4: Create schemas
        create_schemas()
        
        # Step 5: Move tables from public to their correct schemas
        move_tables_to_schemas()
        
        # Step 6: Create superuser
        create_superuser()
        
        print("✅ Fresh migration setup completed successfully!")
        print("🌐 You can now start your application with clean migrations")
        print("👤 Login with: admin@spoton.co.nz / admin123")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during fresh setup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main()) 