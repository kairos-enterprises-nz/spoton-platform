"""
Management command to clean up TimescaleDB and fix database separation.
"""

from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Clean up TimescaleDB and fix database separation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-timescaledb',
            action='store_true',
            help='Reset TimescaleDB completely (drops all data)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Cleaning up TimescaleDB...'))
        
        if options['reset_timescaledb']:
            self.reset_timescaledb()
        
        self.clean_incorrect_tables()
        self.verify_separation()
        
        self.stdout.write(
            self.style.SUCCESS('TimescaleDB cleanup completed!')
        )

    def reset_timescaledb(self):
        """Reset TimescaleDB completely"""
        self.stdout.write(self.style.WARNING('Resetting TimescaleDB (this will drop all data)...'))
        
        timescale_db = connections['timescaledb']
        with timescale_db.cursor() as cursor:
            # Drop all schemas except system ones
            schemas_to_drop = ['metering', 'validation', 'energy', 'finance', 'support', 'pricing', 'users', 'contracts']
            
            for schema in schemas_to_drop:
                try:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                    self.stdout.write(f'Dropped schema: {schema}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error dropping schema {schema}: {e}'))

    def clean_incorrect_tables(self):
        """Remove tables that shouldn't be in TimescaleDB"""
        self.stdout.write('Cleaning incorrect tables from TimescaleDB...')
        
        # Tables that should NOT be in TimescaleDB (have foreign keys or are operational data)
        incorrect_tables = [
            'validation.validation_result',
            'validation.import_log', 
            'validation.change_log',
            'energy.export_log',
            'energy.reconciliation_submission',
            'energy.market_submission',
            'users.user',
            'users.tenant',
            'contracts.contract',
        ]
        
        timescale_db = connections['timescaledb']
        with timescale_db.cursor() as cursor:
            for table in incorrect_tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                    self.stdout.write(f'Dropped incorrect table: {table}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Table {table} not found or error: {e}'))

    def verify_separation(self):
        """Verify correct database separation"""
        self.stdout.write('Verifying database separation...')
        
        # Check TimescaleDB - should only have metering time-series tables
        timescale_db = connections['timescaledb']
        with timescale_db.cursor() as cursor:
            cursor.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'timescaledb_information', 'timescaledb_internal', '_timescaledb_internal', '_timescaledb_cache', '_timescaledb_catalog')
                ORDER BY schemaname, tablename
            """)
            
            timescale_tables = cursor.fetchall()
            
            self.stdout.write('\n=== TimescaleDB Tables ===')
            if timescale_tables:
                for schema, table in timescale_tables:
                    self.stdout.write(f'  {schema}.{table}')
            else:
                self.stdout.write('  No user tables found')
        
        # Check primary DB
        default_db = connections['default']
        with default_db.cursor() as cursor:
            cursor.execute("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'public')
                ORDER BY schemaname, tablename
            """)
            
            primary_tables = cursor.fetchall()
            
            self.stdout.write('\n=== Primary Database Tables ===')
            if primary_tables:
                for schema, table in primary_tables:
                    self.stdout.write(f'  {schema}.{table}')
            else:
                self.stdout.write('  No schema-organized tables found')
        
        # Expected separation
        self.stdout.write('\n=== Expected Separation ===')
        self.stdout.write('TimescaleDB should contain ONLY:')
        self.stdout.write('  - metering.interval_reads_raw')
        self.stdout.write('  - metering.interval_reads_derived')
        self.stdout.write('  - metering.interval_reads_final')
        self.stdout.write('  - metering.daily_register_reads')
        self.stdout.write('  - metering.estimated_interval_reads')
        self.stdout.write('  - metering.derived_read_calculation_log')
        
        self.stdout.write('\nPrimary DB should contain:')
        self.stdout.write('  - users.* (all user/tenant models)')
        self.stdout.write('  - contracts.* (all contract models)')
        self.stdout.write('  - energy.* (validation, export, submission models)')
        self.stdout.write('  - finance.* (billing, pricing models)')
        self.stdout.write('  - support.* (tickets, knowledge base)')

    def show_migration_cleanup_commands(self):
        """Show commands to clean up migrations"""
        self.stdout.write('\n=== Migration Cleanup Commands ===')
        self.stdout.write('Run these commands to clean up incorrect migrations:')
        self.stdout.write('')
        self.stdout.write('# Remove TimescaleDB migrations for non-time-series models:')
        self.stdout.write('rm -f energy/validation/migrations/0002_add_timescale_models.py')
        self.stdout.write('rm -f energy/export_core/migrations/0001_add_timescale_models.py')
        self.stdout.write('')
        self.stdout.write('# Recreate correct migrations:')
        self.stdout.write('python manage.py makemigrations validation')
        self.stdout.write('python manage.py makemigrations export_core')
        self.stdout.write('')
        self.stdout.write('# Apply to primary database:')
        self.stdout.write('python manage.py migrate validation')
        self.stdout.write('python manage.py migrate export_core') 