"""
Django management command to validate database schema consistency.
Used in CI/CD pipeline to ensure UAT and Live databases have matching schemas.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Validate database schema consistency for CI/CD deployments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--compare-with',
            type=str,
            help='Database connection string to compare with (e.g., "postgresql://user:pass@host:port/db")'
        )
        parser.add_argument(
            '--export-schema',
            action='store_true',
            help='Export current schema to JSON file for comparison'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            default='schema_export.json',
            help='Output file for schema export (default: schema_export.json)'
        )
        parser.add_argument(
            '--check-migrations',
            action='store_true',
            help='Check if all migrations are applied'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 SpotOn Schema Validation Tool')
        )
        
        if options['export_schema']:
            self.export_schema(options['output_file'])
        elif options['check_migrations']:
            self.check_migrations()
        elif options['compare_with']:
            self.compare_schemas(options['compare_with'])
        else:
            self.show_current_schema()

    def get_schema_info(self):
        """Extract comprehensive schema information from current database"""
        with connection.cursor() as cursor:
            schema_info = {
                'timestamp': datetime.now().isoformat(),
                'database': settings.DATABASES['default']['NAME'],
                'tables': {},
                'indexes': {},
                'constraints': {},
                'migrations': {}
            }
            
            # Get table information
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'users_%' OR table_name LIKE 'energy_%' OR table_name LIKE 'finance_%'
                ORDER BY table_name, ordinal_position
            """)
            
            for row in cursor.fetchall():
                table_name, column_name, data_type, is_nullable, column_default = row
                if table_name not in schema_info['tables']:
                    schema_info['tables'][table_name] = []
                
                schema_info['tables'][table_name].append({
                    'column': column_name,
                    'type': data_type,
                    'nullable': is_nullable == 'YES',
                    'default': column_default
                })
            
            # Get index information
            cursor.execute("""
                SELECT schemaname, tablename, indexname, indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND (tablename LIKE 'users_%' OR tablename LIKE 'energy_%' OR tablename LIKE 'finance_%')
                ORDER BY tablename, indexname
            """)
            
            for row in cursor.fetchall():
                schema, table, index_name, index_def = row
                if table not in schema_info['indexes']:
                    schema_info['indexes'][table] = []
                
                schema_info['indexes'][table].append({
                    'name': index_name,
                    'definition': index_def
                })
            
            # Get migration status
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app IN ('users', 'energy', 'finance', 'core')
                ORDER BY app, name
            """)
            
            for row in cursor.fetchall():
                app, name, applied = row
                if app not in schema_info['migrations']:
                    schema_info['migrations'][app] = []
                
                schema_info['migrations'][app].append({
                    'name': name,
                    'applied': applied.isoformat() if applied else None
                })
            
            return schema_info

    def export_schema(self, output_file):
        """Export current schema to JSON file"""
        self.stdout.write('📤 Exporting current schema...')
        
        schema_info = self.get_schema_info()
        
        with open(output_file, 'w') as f:
            json.dump(schema_info, f, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Schema exported to {output_file}')
        )
        
        # Print summary
        table_count = len(schema_info['tables'])
        migration_count = sum(len(migrations) for migrations in schema_info['migrations'].values())
        
        self.stdout.write(f'📊 Summary: {table_count} tables, {migration_count} migrations')

    def show_current_schema(self):
        """Display current schema information"""
        self.stdout.write('📋 Current Database Schema:')
        
        schema_info = self.get_schema_info()
        
        self.stdout.write(f"🗄️  Database: {schema_info['database']}")
        self.stdout.write(f"📅 Timestamp: {schema_info['timestamp']}")
        
        # Show tables
        self.stdout.write('\n📊 Tables:')
        for table_name, columns in schema_info['tables'].items():
            self.stdout.write(f"  • {table_name} ({len(columns)} columns)")
        
        # Show migration status  
        self.stdout.write('\n🔄 Migration Status:')
        for app, migrations in schema_info['migrations'].items():
            applied_count = len([m for m in migrations if m['applied']])
            self.stdout.write(f"  • {app}: {applied_count}/{len(migrations)} applied")

    def check_migrations(self):
        """Check if all migrations are applied"""
        from django.core.management import call_command
        from io import StringIO
        
        self.stdout.write('🔍 Checking migration status...')
        
        # Capture showmigrations output
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out)
        migration_output = out.getvalue()
        
        unapplied_migrations = []
        for line in migration_output.split('\n'):
            if line.strip() and not line.startswith('[X]') and line.startswith('[ ]'):
                unapplied_migrations.append(line.strip())
        
        if unapplied_migrations:
            self.stdout.write(
                self.style.ERROR(f'❌ {len(unapplied_migrations)} unapplied migrations found:')
            )
            for migration in unapplied_migrations:
                self.stdout.write(f'  {migration}')
            raise CommandError('Unapplied migrations detected')
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ All migrations are applied')
            )

    def compare_schemas(self, compare_db):
        """Compare current schema with another database"""
        self.stdout.write(f'🔄 Comparing schemas with {compare_db}')
        # This would require additional database connection setup
        # For now, we'll implement the export/compare workflow
        self.stdout.write(
            self.style.WARNING('Schema comparison requires exported schema files. Use --export-schema first.')
        )