"""
Database Schema Cleanup Management Command
==========================================

This command cleans up the database by:
1. Moving tables to their correct schemas
2. Dropping legacy/unused tables
3. Ensuring proper schema organization
4. Removing Airflow tables from main database

Usage: python manage.py cleanup_database_schemas
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clean up database schemas and move tables to proper locations'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor = connection.cursor()
        
        # Define proper schema organization
        self.schema_mappings = {
            # Users schema - should contain all user-related tables
            'users': [
                'users_tenant',
                'users_user', 
                'users_user_groups',
                'users_user_user_permissions',
                'users_otp',
                'users_userchangelog',
                'users_service_contract',  # Legacy - will be moved/dropped
                'user_details_useronboardingconfirmation',
                'user_details_userpreferences',
            ],
            
            # Contracts schema - all contract-related tables
            'contracts': [
                'contracts_servicecontract',
                'contracts_contractservice', 
                'contracts_contractamendment',
                'contracts_contractdocument',
            ],
            
            # Finance schema - billing and pricing
            'finance': [
                'billing_billingcycle',
                'billing_bill',
                'billing_billlineitem', 
                'billing_billadjustment',
                'billing_payment',
                'billing_paymentallocation',
                'billing_billingrun',
                'pricing_serviceplan',
                'pricing_pricingrule',
                'pricing_customerpricing',
                'pricing_pricecalculation',
            ],
            
            # Support schema - web support tables
            'support': [
                'address_plans_address',
                'public_pricing_electricityplan',
                'public_pricing_broadbandplan',
                'public_pricing_pricingregion',
                'public_pricing_mobileplan',
                'callback_request',  # Support related
            ],
            
            # Public schema - only Django core and auth tables
            'public': [
                'django_migrations',
                'django_admin_log',
                'django_content_type',
                'django_session',
                'auth_group',
                'auth_group_permissions', 
                'auth_permission',
                'token_blacklist_outstandingtoken',
                'token_blacklist_blacklistedtoken',
            ]
        }
        
        # Tables to drop completely (legacy/unused)
        self.tables_to_drop = [
            # Legacy Airflow tables (should be in separate DB)
            'dag', 'dag_code', 'dag_owner_attributes', 'dag_pickle',
            'dag_priority_parsing_request', 'dag_run', 'dag_run_note',
            'dag_schedule_dataset_alias_reference', 'dag_schedule_dataset_reference',
            'dag_tag', 'dag_warning', 'dagrun_dataset_event', 'dataset',
            'dataset_alias', 'dataset_alias_dataset', 'dataset_alias_dataset_event',
            'dataset_dag_run_queue', 'dataset_event', 'import_error', 'job',
            'log', 'log_template', 'rendered_task_instance_fields',
            'serialized_dag', 'session', 'sla_miss', 'slot_pool',
            'task_fail', 'task_instance', 'task_instance_history',
            'task_instance_note', 'task_map', 'task_outlet_dataset_reference',
            'task_reschedule', 'trigger', 'variable', 'xcom',
            
            # Legacy Flask-AppBuilder tables
            'ab_permission', 'ab_permission_view', 'ab_permission_view_role',
            'ab_register_user', 'ab_role', 'ab_user', 'ab_user_role',
            'ab_view_menu', 'alembic_version',
            
            # Legacy connection table (replaced by energy.connection)
            'connection',
        ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation',
        )

    def get_existing_tables(self, schema='public'):
        """Get list of existing tables in a schema"""
        self.cursor.execute(f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = '{schema}' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """)
        return [row[0] for row in self.cursor.fetchall()]

    def table_exists(self, table_name, schema='public'):
        """Check if table exists"""
        self.cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = '{schema}' 
            AND table_name = '{table_name}'
        );
        """)
        return self.cursor.fetchone()[0]

    def schema_exists(self, schema_name):
        """Check if schema exists"""
        self.cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.schemata 
            WHERE schema_name = '{schema_name}'
        );
        """)
        return self.cursor.fetchone()[0]

    def create_schema_if_not_exists(self, schema_name, dry_run=False):
        """Create schema if it doesn't exist"""
        if not self.schema_exists(schema_name):
            self.stdout.write(f"📁 Creating schema: {schema_name}")
            if not dry_run:
                self.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")

    def move_table_to_schema(self, table_name, target_schema, source_schema='public', dry_run=False):
        """Move table from one schema to another"""
        if self.table_exists(table_name, source_schema):
            if self.table_exists(table_name, target_schema):
                self.stdout.write(f"⚠️  Table {table_name} already exists in {target_schema}, skipping move")
                return False
            
            self.stdout.write(f"📦 Moving {source_schema}.{table_name} -> {target_schema}.{table_name}")
            if not dry_run:
                self.cursor.execute(f'ALTER TABLE "{source_schema}"."{table_name}" SET SCHEMA "{target_schema}";')
            return True
        return False

    def drop_table_if_exists(self, table_name, schema='public', dry_run=False):
        """Drop table if it exists"""
        if self.table_exists(table_name, schema):
            self.stdout.write(f"🗑️  Dropping {schema}.{table_name}")
            if not dry_run:
                self.cursor.execute(f'DROP TABLE IF EXISTS "{schema}"."{table_name}" CASCADE;')
            return True
        return False

    def cleanup_public_schema(self, dry_run=False):
        """Remove legacy tables from public schema"""
        self.stdout.write("\n=== CLEANING UP PUBLIC SCHEMA ===")
        
        public_tables = self.get_existing_tables('public')
        
        # Drop legacy tables
        for table in self.tables_to_drop:
            self.drop_table_if_exists(table, 'public', dry_run)
        
        # Move tables to proper schemas
        for target_schema, tables in self.schema_mappings.items():
            if target_schema == 'public':
                continue
                
            self.create_schema_if_not_exists(target_schema, dry_run)
            
            for table in tables:
                if table in public_tables:
                    self.move_table_to_schema(table, target_schema, 'public', dry_run)

    def verify_schema_organization(self):
        """Verify the final schema organization"""
        self.stdout.write("\n=== FINAL SCHEMA ORGANIZATION ===")
        
        schemas = ['public', 'users', 'contracts', 'energy', 'finance', 'support', 'pricing', 'metering']
        
        for schema in schemas:
            if self.schema_exists(schema):
                tables = self.get_existing_tables(schema)
                self.stdout.write(f"\n📁 Schema: {schema}")
                if tables:
                    for table in sorted(tables):
                        self.stdout.write(f"  📋 {table}")
                else:
                    self.stdout.write("  (empty)")

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write("🔍 DRY RUN MODE - No changes will be made")
        
        self.stdout.write("🧹 Starting Database Schema Cleanup...")
        
        if not force and not dry_run:
            confirm = input("\nThis will modify your database structure. Continue? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("❌ Cleanup cancelled")
                return
        
        try:
            if not dry_run:
                # Start transaction
                self.cursor.execute("BEGIN;")
            
            # Cleanup public schema
            self.cleanup_public_schema(dry_run)
            
            if not dry_run:
                # Commit changes
                self.cursor.execute("COMMIT;")
            
            self.stdout.write(self.style.SUCCESS("\n✅ Database schema cleanup completed successfully!"))
            
            # Verify results
            self.verify_schema_organization()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error during cleanup: {e}"))
            if not dry_run:
                self.cursor.execute("ROLLBACK;")
            raise 