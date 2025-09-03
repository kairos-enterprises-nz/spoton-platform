#!/usr/bin/env python
"""
Script to set up proper schema-based migrations.
This script will:
1. Create all required schemas
2. Move existing tables to appropriate schemas
3. Update migration history
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.db import connections
from django.core.management import call_command

def setup_schema_migration():
    """Set up proper schema-based migrations."""
    print("🔧 Setting up schema-based migrations...")
    
    # Step 1: Create all required schemas
    print("📊 Creating schemas...")
    schemas = ['users', 'contracts', 'energy', 'finance', 'pricing', 'support']
    
    for schema_name in schemas:
        try:
            connection = connections['default']
            cursor = connection.cursor()
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')
            print(f"✅ Schema '{schema_name}' created or already exists")
        except Exception as e:
            print(f"❌ Error creating schema {schema_name}: {e}")
            return 1
    
    # Step 2: Move users tables to users schema
    print("🔄 Moving users tables to users schema...")
    try:
        connection = connections['default']
        cursor = connection.cursor()
        
        # Get all tables that should be in users schema
        users_tables = [
            'users_user',
            'users_user_groups',
            'users_user_user_permissions',
            'users_tenant',
            'users_account',
            'users_accountaddress',
            'users_address',
            'users_otp',
            'users_tenantuserrole',
            'users_useraccountrole',
            'users_userchangelog',
            'users_userservicecontract',
            'users_usertenantrole',
            'user_details_userdetails',
        ]
        
        for table in users_tables:
            # Check if table exists in public schema
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, [table])
            
            if cursor.fetchone()[0]:
                # Move table to users schema
                cursor.execute(f'ALTER TABLE public.{table} SET SCHEMA users;')
                print(f"✅ Moved table '{table}' to users schema")
            else:
                print(f"⚠️  Table '{table}' not found in public schema")
        
        # Update sequences as well
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences 
            WHERE sequence_schema = 'public' 
            AND sequence_name LIKE 'users_%'
        """)
        
        sequences = cursor.fetchall()
        for (seq_name,) in sequences:
            cursor.execute(f'ALTER SEQUENCE public.{seq_name} SET SCHEMA users;')
            print(f"✅ Moved sequence '{seq_name}' to users schema")
            
    except Exception as e:
        print(f"❌ Error moving users tables: {e}")
        return 1
    
    # Step 3: Update migration history
    print("📝 Updating migration history...")
    try:
        # Mark users migrations as applied in users database
        connection = connections['users']
        cursor = connection.cursor()
        
        # Insert migration records for users app
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('users', '0001_initial', NOW())
            ON CONFLICT (app, name) DO NOTHING
        """)
        
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('users', '0002_rename_users_accou_tenant__0ff753_idx_users_users_tenant__5db63c_idx_and_more', NOW())
            ON CONFLICT (app, name) DO NOTHING
        """)
        
        print("✅ Updated migration history for users schema")
        
    except Exception as e:
        print(f"❌ Error updating migration history: {e}")
        return 1
    
    print("✅ Schema migration setup completed!")
    return 0

if __name__ == '__main__':
    sys.exit(setup_schema_migration()) 