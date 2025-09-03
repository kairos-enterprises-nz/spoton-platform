"""
Management command to safely clean up irrelevant database tables
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.apps import apps
from django.conf import settings
from django.core.management.color import make_style
from django.core.management import call_command
import sys
import re
from datetime import datetime


class Command(BaseCommand):
    help = 'Safely clean up irrelevant database tables with comprehensive safety checks'
    
    def __init__(self):
        super().__init__()
        self.style = make_style()
        
        # Protected tables that should NEVER be deleted
        self.PROTECTED_TABLES = {
            # Django system tables
            'django_migrations',
            'django_content_type',
            'django_admin_log',
            'django_session',
            'auth_permission',
            'auth_group',
            'auth_group_permissions',
            'auth_user',
            'auth_user_groups',
            'auth_user_user_permissions',
            
            # TimescaleDB system tables (patterns)
            '_timescaledb_cache.*',
            '_timescaledb_catalog.*',
            '_timescaledb_config.*',
            '_timescaledb_internal.*',
            
            # PostgreSQL system tables
            'pg_*',
            'information_schema.*',
            
            # Common system tables
            'sqlite_master',
            'sqlite_sequence',
        }
        
        # Airflow system tables (automatically excluded)
        self.AIRFLOW_SYSTEM_TABLES = {
            # Core Airflow tables
            'alembic_version',
            'dag',
            'dag_run',
            'dag_code',
            'dag_tag',
            'dag_pickle',
            'dag_warning',
            'dag_owner_attributes',
            'dag_priority_parsing_request',
            'dag_run_note',
            'dag_schedule_dataset_reference',
            'dag_schedule_dataset_alias_reference',
            'serialized_dag',
            
            # Task management
            'task_instance',
            'task_instance_history',
            'task_instance_note',
            'task_fail',
            'task_reschedule',
            'task_map',
            'task_outlet_dataset_reference',
            'rendered_task_instance_fields',
            
            # Job and execution
            'job',
            'slot_pool',
            'trigger',
            'callback_request',
            'sla_miss',
            
            # Data and communication
            'xcom',
            'variable',
            'connection',
            'import_error',
            
            # Logging
            'log',
            'log_template',
            
            # Dataset management
            'dataset',
            'dataset_event',
            'dataset_alias',
            'dataset_alias_dataset',
            'dataset_alias_dataset_event',
            'dataset_dag_run_queue',
            'dagrun_dataset_event',
            
            # Airflow web UI tables
            'ab_permission',
            'ab_permission_view',
            'ab_permission_view_role',
            'ab_register_user',
            'ab_role',
            'ab_user',
            'ab_user_role',
            'ab_view_menu',
            
            # Session management
            'session',
            
            # User management (Django-style but for Airflow)
            'users_user_groups',
            'users_user_user_permissions',
        }
        
        # Tables that are commonly safe to remove (still requires confirmation)
        self.COMMON_CLEANUP_PATTERNS = [
            r'.*_old$',
            r'.*_backup$',
            r'.*_temp$',
            r'.*_tmp$',
            r'test_.*',
            r'temp_.*',
            r'backup_.*',
        ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database to clean up (default: default)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually doing it',
        )
        parser.add_argument(
            '--auto-confirm',
            action='store_true',
            help='Automatically confirm common cleanup patterns (still shows dry-run first)',
        )
        parser.add_argument(
            '--include-pattern',
            type=str,
            nargs='+',
            help='Additional regex patterns for tables to include in cleanup',
        )
        parser.add_argument(
            '--exclude-pattern',
            type=str,
            nargs='+',
            help='Additional regex patterns for tables to exclude from cleanup',
        )
        parser.add_argument(
            '--backup-first',
            action='store_true',
            help='Create backup before deletion (PostgreSQL only)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip some safety checks (USE WITH EXTREME CAUTION)',
        )
        parser.add_argument(
            '--show-airflow',
            action='store_true',
            help='Show Airflow system tables in cleanup candidates (normally hidden)',
        )

    def handle(self, *args, **options):
        database = options['database']
        dry_run = options.get('dry_run', False)
        auto_confirm = options.get('auto_confirm', False)
        include_patterns = options.get('include_pattern', [])
        exclude_patterns = options.get('exclude_pattern', [])
        backup_first = options.get('backup_first', False)
        force = options.get('force', False)
        show_airflow = options.get('show_airflow', False)
        
        self.stdout.write(
            self.style.SUCCESS('🧹 Database Table Cleanup')
        )
        self.stdout.write('=' * 40)
        self.stdout.write(f'Database: {database}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )
        
        if force:
            self.stdout.write(
                self.style.ERROR('⚠️  FORCE MODE ENABLED - Some safety checks disabled')
            )
        
        # Validate database
        if not self.validate_database(database):
            return
        
        # Get tables to potentially clean up
        cleanup_candidates = self.get_cleanup_candidates(
            database, include_patterns, exclude_patterns, show_airflow
        )
        
        if not cleanup_candidates:
            self.stdout.write(
                self.style.SUCCESS('✅ No tables found for cleanup')
            )
            return
        
        # Display cleanup plan
        self.display_cleanup_plan(cleanup_candidates)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n🔍 This was a dry run. Use without --dry-run to execute.')
            )
            return
        
        # Safety confirmation
        if not force and not self.confirm_cleanup(cleanup_candidates, auto_confirm):
            self.stdout.write(
                self.style.WARNING('❌ Cleanup cancelled by user')
            )
            return
        
        # Create backup if requested
        if backup_first and not self.create_backup(database):
            self.stdout.write(
                self.style.ERROR('❌ Backup failed. Cleanup cancelled.')
            )
            return
        
        # Execute cleanup
        self.execute_cleanup(cleanup_candidates, database)
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Database cleanup completed!')
        )

    def validate_database(self, database):
        """Validate database connection and safety"""
        try:
            with connections[database].cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS(f'✅ Database connection: OK')
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {str(e)}')
            )
            return False

    def get_cleanup_candidates(self, database, include_patterns, exclude_patterns, show_airflow=False):
        """Get list of tables that are candidates for cleanup"""
        try:
            # Get Django model tables
            django_tables = set()
            try:
                for app_config in apps.get_app_configs():
                    for model in app_config.get_models():
                        django_tables.add(model._meta.db_table)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Warning getting Django models: {str(e)}')
                )
            
            # Get actual database tables
            with connections[database].cursor() as cursor:
                if 'postgresql' in connections[database].settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT schemaname, tablename 
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """)
                    results = cursor.fetchall()
                    db_tables = set(row[1] for row in results) if results else set()
                    
                elif 'sqlite' in connections[database].settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """)
                    results = cursor.fetchall()
                    db_tables = set(row[0] for row in results) if results else set()
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Unsupported database engine')
                    )
                    return []
            
            # Find extra tables (in DB but not in Django models)
            extra_tables = db_tables - django_tables
            
            # Filter out protected tables
            cleanup_candidates = []
            airflow_tables_hidden = 0
            
            for table in extra_tables:
                # Check if it's an Airflow table and should be hidden
                if not show_airflow and table in self.AIRFLOW_SYSTEM_TABLES:
                    airflow_tables_hidden += 1
                    continue
                    
                # When showing Airflow tables, don't protect them so they can be reviewed
                if not self.is_protected_table(table, include_airflow_protection=not show_airflow):
                    category = self.categorize_table(table, include_patterns, exclude_patterns)
                    if category != 'excluded':
                        # Special category for Airflow tables when shown
                        if show_airflow and table in self.AIRFLOW_SYSTEM_TABLES:
                            category = 'airflow_system'
                        
                        cleanup_candidates.append({
                            'name': table,
                            'category': category,
                            'reason': self.get_cleanup_reason(table, category)
                        })
            
            # Show summary of hidden Airflow tables
            if airflow_tables_hidden > 0 and not show_airflow:
                self.stdout.write(
                    self.style.SUCCESS(f'ℹ️  {airflow_tables_hidden} Airflow system tables hidden (use --show-airflow to display)')
                )
            
            return cleanup_candidates
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting cleanup candidates: {str(e)}')
            )
            return []

    def is_protected_table(self, table_name, include_airflow_protection=True):
        """Check if table is protected from deletion"""
        # Check standard protected tables
        for pattern in self.PROTECTED_TABLES:
            if '*' in pattern:
                # Convert to regex
                regex_pattern = pattern.replace('*', '.*')
                if re.match(regex_pattern, table_name):
                    return True
            else:
                if table_name == pattern:
                    return True
        
        # Check Airflow system tables (only if protection is enabled)
        if include_airflow_protection and table_name in self.AIRFLOW_SYSTEM_TABLES:
            return True
            
        return False

    def categorize_table(self, table_name, include_patterns, exclude_patterns):
        """Categorize table for cleanup decision"""
        # Handle None patterns
        if exclude_patterns is None:
            exclude_patterns = []
        if include_patterns is None:
            include_patterns = []
            
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if re.search(pattern, table_name):
                return 'excluded'
        
        # Check include patterns
        for pattern in include_patterns:
            if re.search(pattern, table_name):
                return 'included'
        
        # Check common cleanup patterns
        for pattern in self.COMMON_CLEANUP_PATTERNS:
            if re.search(pattern, table_name):
                return 'common_cleanup'
        
        # Default: manual review required
        return 'manual_review'

    def get_cleanup_reason(self, table_name, category):
        """Get human-readable reason for cleanup"""
        if category == 'included':
            return 'Matches include pattern'
        elif category == 'common_cleanup':
            return 'Matches common cleanup pattern'
        elif category == 'airflow_system':
            return 'Airflow system table (NOT RECOMMENDED to delete)'
        elif category == 'manual_review':
            return 'Not in Django models (manual review needed)'
        else:
            return 'Unknown'

    def display_cleanup_plan(self, cleanup_candidates):
        """Display the cleanup plan to user"""
        self.stdout.write(f'\n📋 Cleanup Plan ({len(cleanup_candidates)} tables)')
        self.stdout.write('-' * 50)
        
        # Group by category
        categories = {}
        for candidate in cleanup_candidates:
            cat = candidate['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(candidate)
        
        for category, tables in categories.items():
            if category == 'common_cleanup':
                icon = '🟢'
                desc = 'Safe to clean up'
            elif category == 'included':
                icon = '🔵'
                desc = 'Explicitly included'
            elif category == 'airflow_system':
                icon = '🔴'
                desc = 'Airflow system tables (NOT RECOMMENDED)'
            else:
                icon = '🟡'
                desc = 'Requires manual review'
            
            self.stdout.write(f'\n{icon} {category.upper()} ({len(tables)} tables) - {desc}')
            for table in tables:
                self.stdout.write(f'  • {table["name"]} - {table["reason"]}')

    def confirm_cleanup(self, cleanup_candidates, auto_confirm):
        """Get user confirmation for cleanup"""
        # Separate auto-confirmable vs manual review
        auto_tables = [t for t in cleanup_candidates if t['category'] in ['common_cleanup', 'included']]
        manual_tables = [t for t in cleanup_candidates if t['category'] == 'manual_review']
        
        confirmed_tables = []
        
        # Auto-confirm safe tables if requested
        if auto_confirm and auto_tables:
            self.stdout.write(f'\n🟢 Auto-confirming {len(auto_tables)} safe tables...')
            confirmed_tables.extend(auto_tables)
        
        # Manual confirmation for review tables
        if manual_tables:
            self.stdout.write(f'\n🟡 {len(manual_tables)} tables require manual confirmation:')
            for table in manual_tables:
                response = input(f'Delete "{table["name"]}"? [y/N]: ').lower().strip()
                if response in ['y', 'yes']:
                    confirmed_tables.append(table)
                    self.stdout.write(f'  ✅ {table["name"]} - confirmed for deletion')
                else:
                    self.stdout.write(f'  ❌ {table["name"]} - skipped')
        
        if not auto_confirm and auto_tables:
            self.stdout.write(f'\n🟢 {len(auto_tables)} safe tables found. Confirm all? [Y/n]: ')
            response = input().lower().strip()
            if response in ['', 'y', 'yes']:
                confirmed_tables.extend(auto_tables)
        
        # Final confirmation
        if confirmed_tables:
            self.stdout.write(f'\n⚠️  FINAL CONFIRMATION: Delete {len(confirmed_tables)} tables?')
            for table in confirmed_tables:
                self.stdout.write(f'  • {table["name"]}')
            
            response = input('\nType "DELETE" to confirm: ').strip()
            if response == 'DELETE':
                # Store confirmed tables for cleanup
                self.confirmed_tables = confirmed_tables
                return True
        
        return False

    def create_backup(self, database):
        """Create database backup before cleanup"""
        if 'postgresql' not in connections[database].settings_dict['ENGINE']:
            self.stdout.write(
                self.style.WARNING('⚠️  Backup only supported for PostgreSQL')
            )
            return True
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'backup_before_cleanup_{timestamp}.sql'
            
            self.stdout.write(f'📦 Creating backup: {backup_file}')
            
            # This would need to be implemented based on your backup strategy
            self.stdout.write(
                self.style.WARNING('💡 Manual backup recommended before proceeding')
            )
            
            response = input('Continue without automatic backup? [y/N]: ').lower().strip()
            return response in ['y', 'yes']
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Backup failed: {str(e)}')
            )
            return False

    def execute_cleanup(self, cleanup_candidates, database):
        """Execute the actual cleanup"""
        if not hasattr(self, 'confirmed_tables'):
            self.stdout.write(
                self.style.ERROR('❌ No confirmed tables for cleanup')
            )
            return
        
        self.stdout.write(f'\n🗑️  Executing cleanup of {len(self.confirmed_tables)} tables...')
        
        success_count = 0
        error_count = 0
        
        with connections[database].cursor() as cursor:
            for table in self.confirmed_tables:
                try:
                    table_name = table['name']
                    self.stdout.write(f'  🗑️  Dropping {table_name}...', ending='')
                    
                    # Use transaction for safety
                    with transaction.atomic(using=database):
                        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                    
                    self.stdout.write(
                        self.style.SUCCESS(' ✅ Success')
                    )
                    success_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f' ❌ Failed: {str(e)}')
                    )
                    error_count += 1
        
        # Summary
        self.stdout.write(f'\n📊 Cleanup Summary:')
        self.stdout.write(f'  ✅ Successfully deleted: {success_count} tables')
        if error_count > 0:
            self.stdout.write(f'  ❌ Failed to delete: {error_count} tables')
        
        # Recommend verification
        self.stdout.write(f'\n💡 Recommended: Run check_database_sync to verify cleanup')