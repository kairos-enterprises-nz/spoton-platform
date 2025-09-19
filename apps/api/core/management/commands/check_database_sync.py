"""
Management command to check primary and secondary database synchronization
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, connection
from django.apps import apps
from django.conf import settings
from django.core.management.color import make_style
import sys
from collections import defaultdict


class Command(BaseCommand):
    help = 'Check primary and secondary database tables and model synchronization'
    
    def __init__(self):
        super().__init__()
        self.style = make_style()
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            help='Specific database to check (default: all configured databases)',
        )
        parser.add_argument(
            '--models-only',
            action='store_true',
            help='Only check Django models synchronization',
        )
        parser.add_argument(
            '--tables-only',
            action='store_true',
            help='Only check database tables',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        database_name = options.get('database')
        models_only = options.get('models_only', False)
        tables_only = options.get('tables_only', False)
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Database Synchronization Check')
        )
        self.stdout.write('=' * 50)
        
        # Get all configured databases
        databases = [database_name] if database_name else list(connections.databases.keys())
        
        for db_name in databases:
            self.check_database(db_name, models_only, tables_only)
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Database synchronization check completed!')
        )

    def check_database(self, db_name, models_only=False, tables_only=False):
        """Check a specific database"""
        try:
            self.stdout.write(f'\n📊 Checking Database: {db_name.upper()}')
            self.stdout.write('-' * 30)
            
            # Test database connection
            db_connection = connections[db_name]
            
            with db_connection.cursor() as cursor:
                # Check database connection
                if not self.check_connection(cursor, db_name):
                    return
                
                # Get database info
                db_info = self.get_database_info(cursor, db_name)
                self.display_database_info(db_info, db_name)
                
                if not tables_only:
                    # Check Django models
                    self.check_django_models(db_name)
                
                if not models_only:
                    # Check database tables
                    self.check_database_tables(cursor, db_name)
                
                # Check for missing migrations
                self.check_migrations(db_name)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error checking database {db_name}: {str(e)}')
            )

    def check_connection(self, cursor, db_name):
        """Test database connection"""
        try:
            cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS(f'✅ Connection: OK')
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Connection: FAILED - {str(e)}')
            )
            return False

    def get_database_info(self, cursor, db_name):
        """Get database information"""
        info = {}
        
        try:
            # PostgreSQL specific queries
            if 'postgresql' in connections[db_name].settings_dict['ENGINE']:
                cursor.execute("SELECT version()")
                info['version'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT current_database()")
                info['database_name'] = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY schemaname, tablename
                """)
                info['tables'] = cursor.fetchall()
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                """)
                info['table_count'] = cursor.fetchone()[0]
                
            # SQLite specific queries
            elif 'sqlite' in connections[db_name].settings_dict['ENGINE']:
                cursor.execute("SELECT sqlite_version()")
                info['version'] = f"SQLite {cursor.fetchone()[0]}"
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                info['tables'] = [(None, table[0]) for table in tables]
                info['table_count'] = len(tables)
                info['database_name'] = connections[db_name].settings_dict['NAME']
                
        except Exception as e:
            info['error'] = str(e)
            
        return info

    def display_database_info(self, info, db_name):
        """Display database information"""
        if 'error' in info:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting database info: {info["error"]}')
            )
            return
            
        self.stdout.write(f'📋 Database: {info.get("database_name", "Unknown")}')
        self.stdout.write(f'🔧 Version: {info.get("version", "Unknown")}')
        self.stdout.write(f'📊 Tables: {info.get("table_count", 0)}')
        
        if self.verbose and info.get('tables'):
            self.stdout.write('\n📝 Table List:')
            for schema, table in info['tables']:
                if schema:
                    self.stdout.write(f'  • {schema}.{table}')
                else:
                    self.stdout.write(f'  • {table}')

    def check_django_models(self, db_name):
        """Check Django models for the database"""
        self.stdout.write(f'\n🏗️  Django Models Check ({db_name})')
        
        try:
            # Get all Django apps and their models
            app_models = defaultdict(list)
            
            for app_config in apps.get_app_configs():
                for model in app_config.get_models():
                    # Check if model uses this database
                    if self.model_uses_database(model, db_name):
                        app_models[app_config.label].append(model)
            
            if not app_models:
                self.stdout.write('  ℹ️  No Django models configured for this database')
                return
            
            total_models = sum(len(models) for models in app_models.values())
            self.stdout.write(f'  📊 Total Models: {total_models}')
            
            for app_label, models in app_models.items():
                self.stdout.write(f'\n  📱 App: {app_label} ({len(models)} models)')
                
                if self.verbose:
                    for model in models:
                        table_name = model._meta.db_table
                        self.stdout.write(f'    • {model.__name__} → {table_name}')
                        
                        # Check if table exists in database
                        if self.table_exists(table_name, db_name):
                            self.stdout.write(
                                self.style.SUCCESS(f'      ✅ Table exists')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'      ❌ Table missing')
                            )
                            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error checking Django models: {str(e)}')
            )

    def check_database_tables(self, cursor, db_name):
        """Check database tables"""
        self.stdout.write(f'\n🗄️  Database Tables Check ({db_name})')
        
        try:
            # Get Django model table names
            django_tables = set()
            for app_config in apps.get_app_configs():
                for model in app_config.get_models():
                    if self.model_uses_database(model, db_name):
                        django_tables.add(model._meta.db_table)
            
            # Get actual database tables
            if 'postgresql' in connections[db_name].settings_dict['ENGINE']:
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
                db_tables = set(row[0] for row in cursor.fetchall())
                
            elif 'sqlite' in connections[db_name].settings_dict['ENGINE']:
                cursor.execute("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                db_tables = set(row[0] for row in cursor.fetchall())
            else:
                db_tables = set()
            
            # Compare tables
            missing_tables = django_tables - db_tables
            extra_tables = db_tables - django_tables
            matching_tables = django_tables & db_tables
            
            self.stdout.write(f'  ✅ Matching Tables: {len(matching_tables)}')
            self.stdout.write(f'  ❌ Missing Tables: {len(missing_tables)}')
            self.stdout.write(f'  ➕ Extra Tables: {len(extra_tables)}')
            
            if self.verbose:
                if missing_tables:
                    self.stdout.write('\n  ❌ Missing Tables:')
                    for table in sorted(missing_tables):
                        self.stdout.write(f'    • {table}')
                
                if extra_tables:
                    self.stdout.write('\n  ➕ Extra Tables (not in Django models):')
                    for table in sorted(extra_tables):
                        self.stdout.write(f'    • {table}')
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error checking database tables: {str(e)}')
            )

    def check_migrations(self, db_name):
        """Check migration status"""
        self.stdout.write(f'\n🔄 Migration Status Check ({db_name})')
        
        try:
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connections[db_name])
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Unapplied Migrations: {len(plan)}')
                )
                if self.verbose:
                    for migration, backwards in plan:
                        direction = "REVERSE" if backwards else "APPLY"
                        self.stdout.write(f'    • {direction}: {migration}')
            else:
                self.stdout.write(
                    self.style.SUCCESS('  ✅ All migrations applied')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error checking migrations: {str(e)}')
            )

    def model_uses_database(self, model, db_name):
        """Check if a model uses a specific database"""
        # Check database routing
        from django.db import router
        return router.db_for_read(model) == db_name or db_name == 'default'

    def table_exists(self, table_name, db_name):
        """Check if a table exists in the database"""
        try:
            with connections[db_name].cursor() as cursor:
                if 'postgresql' in connections[db_name].settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, [table_name])
                elif 'sqlite' in connections[db_name].settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, [table_name])
                    return bool(cursor.fetchone())
                
                return cursor.fetchone()[0] if cursor.fetchone() else False
                
        except Exception:
            return False 