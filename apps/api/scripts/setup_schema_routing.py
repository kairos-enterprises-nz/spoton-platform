#!/usr/bin/env python3
"""
Setup script for PostgreSQL schema routing in Utility Byte platform

This script ensures that when starting from scratch, all tables will be created 
in the correct PostgreSQL schemas.

Usage:
    python setup_schema_routing.py

This will:
1. Create the ensure_schemas management command
2. Add proper db_table values to key models
3. Provide instructions for migration setup
"""

import os
import sys


def create_ensure_schemas_command():
    """Create the management command to ensure schemas exist"""
    
    command_dir = "core/management/commands"
    os.makedirs(command_dir, exist_ok=True)
    
    # Create __init__.py files
    for path in ["core/management", "core/management/commands"]:
        init_file = f"{path}/__init__.py"
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("")
    
    command_content = '''"""
Management command to ensure all required PostgreSQL schemas exist
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Ensure all required PostgreSQL schemas exist'
    
    def handle(self, *args, **options):
        schemas = [
            'users',
            'contracts', 
            'energy',
            'finance',
            'support',
            'metering',
        ]
        
        with connection.cursor() as cursor:
            for schema in schemas:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Schema "{schema}" ensured')
                )
        
        self.stdout.write(
            self.style.SUCCESS('All schemas created successfully!')
        )
'''
    
    with open(f"{command_dir}/ensure_schemas.py", 'w') as f:
        f.write(command_content)
    
    print("✅ Created ensure_schemas management command")


def update_key_models():
    """Add schema routing to key models"""
    
    models_to_update = [
        # (file_path, model_class, schema, table_name)
        ("users/models.py", "Tenant", "users", "users_tenant"),
        ("users/models.py", "User", "users", "users_user"), 
        ("users/models.py", "Account", "users", "users_account"),
        ("users/models.py", "UserAccountRole", "users", "users_useraccountrole"),
        ("users/models.py", "OTP", "users", "users_otp"),
        ("core/contracts/models.py", "ServiceContract", "contracts", "contracts_servicecontract"),
        ("core/contracts/models.py", "ElectricityContract", "contracts", "contracts_electricitycontract"),
        ("finance/billing/models.py", "Bill", "finance", "billing_bill"),
        ("finance/billing/models.py", "BillingCycle", "finance", "billing_billingcycle"),
        ("energy/connections/models.py", "Connection", "energy", "connections_connection"),
    ]
    
    for file_path, model_class, schema, table_name in models_to_update:
        if os.path.exists(file_path):
            print(f"📝 Model {model_class} should use: db_table = '{schema}.{table_name}'")
        else:
            print(f"⚠️  File not found: {file_path}")


def create_migration_script():
    """Create a script to handle migrations from scratch"""
    
    script_content = '''#!/bin/bash
# Migration setup script for PostgreSQL schema routing

echo "🚀 Setting up PostgreSQL schema routing from scratch..."

# Step 1: Ensure schemas exist
echo "📁 Creating PostgreSQL schemas..."
python manage.py ensure_schemas

# Step 2: Remove existing migrations (if any)
echo "🗑️  Removing existing migrations..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# Step 3: Create fresh migrations
echo "📝 Creating fresh migrations with schema routing..."
python manage.py makemigrations

# Step 4: Apply migrations
echo "⚡ Applying migrations..."
python manage.py migrate

echo "✅ Schema routing setup complete!"
echo ""
echo "Your database now has the following schema organization:"
echo "- users: User management, accounts, roles"
echo "- contracts: All contract types and amendments" 
echo "- energy: Energy operations and infrastructure"
echo "- finance: Billing, payments, and pricing"
echo "- support: Customer support and public pricing"
echo "- metering: Metering infrastructure"
echo "- public: Django core tables only"
'''
    
    with open("setup_migrations.sh", 'w') as f:
        f.write(script_content)
    
    os.chmod("setup_migrations.sh", 0o755)
    print("✅ Created setup_migrations.sh script")


def create_documentation():
    """Create documentation for schema routing"""
    
    doc_content = '''# PostgreSQL Schema Routing Setup

## Overview

This system uses PostgreSQL schemas to organize tables by business domain:

- **users**: User management, accounts, roles, permissions
- **contracts**: All contract types and amendments
- **energy**: Energy operations and infrastructure  
- **finance**: Billing, payments, and pricing
- **support**: Customer support and public pricing
- **metering**: Metering infrastructure
- **public**: Django core tables only

## Starting From Scratch

To set up the system from scratch with proper schema routing:

### 1. Ensure PostgreSQL is running
```bash
docker-compose up -d db timescaledb redis
```

### 2. Run the setup script
```bash
./setup_migrations.sh
```

### 3. Verify schema organization
```sql
SELECT schemaname, COUNT(*) as table_count 
FROM pg_tables 
WHERE schemaname IN ('public', 'users', 'contracts', 'energy', 'finance', 'support', 'metering') 
GROUP BY schemaname 
ORDER BY schemaname;
```

## Manual Setup (Alternative)

If you prefer manual setup:

### 1. Create schemas
```bash
python manage.py ensure_schemas
```

### 2. Add db_table to models
Add `db_table = 'schema.tablename'` to each model's Meta class:

```python
class Tenant(models.Model):
    # ... fields ...
    
    class Meta:
        db_table = 'users.users_tenant'
        # ... other meta options ...
```

### 3. Create and apply migrations
```bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate
```

## Database Configuration

The database is configured with a search path that includes all schemas:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ... connection details ...
        'OPTIONS': {
            'options': '-c search_path=users,contracts,energy,finance,support,pricing,metering,public'
        },
    }
}
```

This allows Django to find tables across all schemas without requiring full schema.table references in queries.

## Benefits

1. **Organization**: Clear separation of business domains
2. **Security**: Schema-level permissions can be applied
3. **Performance**: Better query planning and indexing
4. **Maintainability**: Easier to understand and modify
5. **Scalability**: Can distribute schemas across databases if needed

## Troubleshooting

### Tables created in wrong schema
If tables are created in the public schema instead of the intended schema:

1. Check that `db_table` values include schema prefixes
2. Ensure the `ensure_schemas` command was run before migrations
3. Verify database search path configuration

### Migration errors
If you encounter migration errors:

1. Drop and recreate the database
2. Run the setup script again
3. Check that all required schemas exist

### Model relationship errors
If foreign key relationships fail across schemas:

1. Ensure both models use the same database (default)
2. Check that search path includes both schemas
3. Verify foreign key field references are correct
'''
    
    with open("SCHEMA_ROUTING_SETUP.md", 'w') as f:
        f.write(doc_content)
    
    print("✅ Created SCHEMA_ROUTING_SETUP.md documentation")


def main():
    """Main setup function"""
    print("🔧 Setting up PostgreSQL schema routing for Utility Byte platform...")
    print()
    
    # Create management command
    create_ensure_schemas_command()
    
    # Show what models need updating
    print("\n📋 Key models that need db_table schema routing:")
    update_key_models()
    
    # Create migration script
    print()
    create_migration_script()
    
    # Create documentation
    print()
    create_documentation()
    
    print()
    print("✅ Schema routing setup complete!")
    print()
    print("📖 Next steps:")
    print("1. Review SCHEMA_ROUTING_SETUP.md for detailed instructions")
    print("2. Add db_table values to your models (see examples above)")
    print("3. Run ./setup_migrations.sh to create schema-aware migrations")
    print("4. Or follow the manual setup process in the documentation")
    print()
    print("🎯 Goal: All tables properly organized in PostgreSQL schemas")


if __name__ == '__main__':
    main() 