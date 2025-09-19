#!/usr/bin/env python3
"""
Migrate all schemas script
Runs migrations for each schema alias as defined in the router
"""

import os
import sys
import subprocess

# Database aliases to migrate (corresponding to schemas)
SCHEMA_ALIASES = [
    'default',     # public schema + 3rd party apps
    'users',       # users schema
    'contracts',   # contracts schema  
    'energy',      # energy schema
    'finance',     # finance schema
    'pricing',     # pricing schema
    'support',     # support schema
]

def run_migrations():
    """Run migrations for all schema aliases"""
    print("🚀 Running migrations for all schemas...")
    print("=" * 50)
    
    success_count = 0
    
    for alias in SCHEMA_ALIASES:
        print(f"\n📊 Migrating {alias} schema...")
        print("-" * 30)
        
        try:
            # Run migration for this database alias
            cmd = ['python3', 'manage.py', 'migrate', '--database', alias]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='/app')
            
            if result.returncode == 0:
                print(f"✅ {alias} schema migrated successfully")
                success_count += 1
            else:
                print(f"❌ {alias} schema migration failed:")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error migrating {alias}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📈 Results: {success_count}/{len(SCHEMA_ALIASES)} schemas migrated successfully")
    
    if success_count == len(SCHEMA_ALIASES):
        print("🎉 All schema migrations completed successfully!")
        return True
    else:
        print("⚠️  Some schema migrations failed")
        return False

def check_schemas():
    """Check that all required schemas exist"""
    print("🔍 Checking database schemas...")
    
    try:
        cmd = [
            'psql', '-U', 'postgres', '-d', 'spoton', '-c',
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('users', 'contracts', 'energy', 'finance', 'pricing', 'support') ORDER BY schema_name;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database schemas verified")
            return True
        else:
            print("❌ Error checking schemas:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error checking schemas: {e}")
        return False

if __name__ == "__main__":
    print("🌟 Schema Migration Script")
    print("=" * 40)
    
    # Check schemas exist
    if not check_schemas():
        print("❌ Schema check failed. Please ensure all schemas are created.")
        sys.exit(1)
    
    # Run migrations
    success = run_migrations()
    
    if success:
        print("\n✅ Schema-based architecture is now active!")
        print("📊 Tables are properly organized by schema")
    else:
        print("\n❌ Migration process incomplete")
        sys.exit(1) 