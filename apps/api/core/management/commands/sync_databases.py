"""
Management command to synchronize data between primary and secondary databases
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.apps import apps
from django.core.management.color import make_style
from django.core.management import call_command
from collections import defaultdict
import sys
import os
from typing import Dict, List, Set, Optional, Tuple
from django.conf import settings
from django.db.models import Model
from django.db.utils import OperationalError, ProgrammingError
import time
from decimal import Decimal


class Command(BaseCommand):
    help = 'Synchronize data between primary and secondary databases with TimescaleDB hypertable support'
    
    def __init__(self):
        super().__init__()
        self.style = make_style()
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='default',
            help='Source database name (default: default)',
        )
        parser.add_argument(
            '--target',
            type=str,
            default='timescale',
            help='Target database name (default: timescale)',
        )
        parser.add_argument(
            '--models',
            type=str,
            nargs='+',
            help='Specific models to sync (app.Model format)',
        )
        parser.add_argument(
            '--apps',
            type=str,
            nargs='+',
            help='Specific apps to sync',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if target tables exist',
        )
        parser.add_argument(
            '--migrate',
            action='store_true',
            help='Run migrations on target database first',
        )
        parser.add_argument(
            '--setup-hypertables',
            action='store_true',
            help='Set up TimescaleDB hypertables for time-series data',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for data transfer (default: 1000)',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.batch_size = options['batch_size']
        
        source_db = options['source']
        target_db = options['target']
        
        if not target_db:
            raise CommandError('Target database is required. Use --target option.')
        
        if source_db == target_db:
            raise CommandError('Source and target databases cannot be the same.')
        
        self.stdout.write(
            self.style.SUCCESS('🔄 Database Synchronization')
        )
        self.stdout.write('=' * 40)
        self.stdout.write(f'Source: {source_db}')
        self.stdout.write(f'Target: {target_db}')
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )
        
        # Validate databases exist
        if not self.validate_databases(source_db, target_db):
            return
        
        # Run migrations on target if requested
        if options['migrate'] and not self.dry_run:
            self.run_migrations(target_db)
        
        # Set up hypertables if requested or if target is TimescaleDB
        if options['setup_hypertables'] or self._is_timescaledb(target_db):
            self._setup_hypertables(target_db)
        
        # Get models to sync
        models_to_sync = self.get_models_to_sync(options)
        
        if not models_to_sync:
            self.stdout.write(
                self.style.WARNING('No models found to sync.')
            )
            return
        
        # Perform synchronization
        self.sync_models(models_to_sync, source_db, target_db, self.dry_run, self.force)
        
        if not self.dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Database synchronization completed!')
            )

    def validate_databases(self, source_db, target_db):
        """Validate that both databases exist and are accessible"""
        try:
            # Test source database
            with connections[source_db].cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS(f'✅ Source database ({source_db}): Connected')
            )
            
            # Test target database
            with connections[target_db].cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(
                self.style.SUCCESS(f'✅ Target database ({target_db}): Connected')
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection error: {str(e)}')
            )
            return False

    def run_migrations(self, target_db):
        """Run migrations on target database"""
        self.stdout.write(f'\n🔄 Running migrations on {target_db}...')
        try:
            call_command('migrate', database=target_db, verbosity=1)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Migrations completed on {target_db}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration error: {str(e)}')
            )

    def get_models_to_sync(self, options):
        """Get list of models to synchronize"""
        models_to_sync = []
        
        if options['models']:
            # Sync specific models
            for model_path in options['models']:
                try:
                    app_label, model_name = model_path.split('.')
                    model = apps.get_model(app_label, model_name)
                    models_to_sync.append(model)
                except (ValueError, LookupError) as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Invalid model: {model_path} - {str(e)}')
                    )
        
        elif options['apps']:
            # Sync specific apps
            for app_label in options['apps']:
                try:
                    app_config = apps.get_app_config(app_label)
                    models_to_sync.extend(app_config.get_models())
                except LookupError as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Invalid app: {app_label} - {str(e)}')
                    )
        
        else:
            # Default: sync time-series models for TimescaleDB
            time_series_models = [
                'energy.wits.WitsNodalPrice',
                'energy.wits.WitsImportLog',
                'energy.metering.MeterReading',
                'energy.metering.MeterReadingAggregate',
                'energy.audit.AuditLog',
                'energy.audit.DataChangeAudit',
                'users.ActivityLog'
            ]
            
            for model_name in time_series_models:
                try:
                    parts = model_name.split('.')
                    if len(parts) >= 2:
                        app_label = parts[0]
                        model_label = parts[-1]  # Take the last part as model name
                        model = apps.get_model(app_label, model_label)
                        models_to_sync.append(model)
                except LookupError:
                    # Model doesn't exist, skip
                    continue
        
        return models_to_sync

    def sync_models(self, models, source_db, target_db, dry_run, force):
        """Synchronize models between databases"""
        self.stdout.write(f'\n📊 Models to sync: {len(models)}')
        
        for model in models:
            self.sync_model(model, source_db, target_db, dry_run, force)

    def sync_model(self, model, source_db, target_db, dry_run, force):
        """Synchronize a single model"""
        model_name = f'{model._meta.app_label}.{model.__name__}'
        table_name = model._meta.db_table
        
        self.stdout.write(f'\n🔄 Syncing {model_name} ({table_name})')
        
        try:
            # Check if target table exists
            if not force and self.table_exists(table_name, target_db):
                target_count = self.get_record_count(model, target_db)
                if target_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Target table has {target_count} records. Use --force to overwrite.')
                    )
                    return
            
            # Get source data count
            source_count = self.get_record_count(model, source_db)
            self.stdout.write(f'  📊 Source records: {source_count}')
            
            if source_count == 0:
                self.stdout.write('  ℹ️  No data to sync')
                return
            
            if dry_run:
                self.stdout.write(f'  🔍 Would sync {source_count} records')
                return
            
            # Perform actual sync
            self.copy_model_data(model, source_db, target_db, force)
            
            # Verify sync
            target_count = self.get_record_count(model, target_db)
            if target_count == source_count:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Synced {target_count} records')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Partial sync: {target_count}/{source_count} records')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Sync error: {str(e)}')
            )

    def copy_model_data(self, model, source_db, target_db, force):
        """Copy data from source to target database"""
        # Clear target table if force is enabled
        if force:
            with connections[target_db].cursor() as cursor:
                cursor.execute(f'DELETE FROM {model._meta.db_table}')
        
        # Get all records from source
        source_records = model.objects.using(source_db).all()
        
        # Batch insert to target
        batch_size = 1000
        records_batch = []
        
        for record in source_records:
            # Reset primary key to allow insertion
            record.pk = None
            records_batch.append(record)
            
            if len(records_batch) >= batch_size:
                model.objects.using(target_db).bulk_create(records_batch)
                records_batch = []
        
        # Insert remaining records
        if records_batch:
            model.objects.using(target_db).bulk_create(records_batch)

    def get_record_count(self, model, db_name):
        """Get number of records in a model table"""
        try:
            return model.objects.using(db_name).count()
        except Exception:
            return 0

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
                    return cursor.fetchone()[0]
                elif 'sqlite' in connections[db_name].settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, [table_name])
                    return bool(cursor.fetchone())
                
        except Exception:
            return False

    def _is_timescaledb(self, db_alias: str) -> bool:
        """Check if database is TimescaleDB"""
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
                return cursor.fetchone() is not None
        except:
            return False

    def _setup_hypertables(self, target_db: str):
        """Set up TimescaleDB hypertables for time-series data"""
        if not self._is_timescaledb(target_db):
            self.stdout.write("  ⚠️ Target database is not TimescaleDB, skipping hypertable setup")
            return
        
        self.stdout.write("🕐 Setting up TimescaleDB hypertables...")
        
        # Define time-series tables and their time columns
        hypertable_configs = {
            'wits.nodal_price': {
                'time_column': 'trading_date',
                'chunk_interval': 'INTERVAL \'1 month\'',
                'description': 'WITS nodal prices'
            },
            'wits.import_log': {
                'time_column': 'imported_at',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'WITS import logs'
            },
            'energy_meter_reading': {
                'time_column': 'reading_datetime',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'Meter readings'
            },
            'energy_meter_reading_aggregate': {
                'time_column': 'period_start',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'Meter reading aggregates'
            },
            'energy_audit_log': {
                'time_column': 'timestamp',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'Audit logs'
            },
            'energy_audit_data_change': {
                'time_column': 'timestamp',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'Data change audit'
            },
            'energy_data_import_log': {
                'time_column': 'started_at',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'Data import logs'
            },
            'energy_reconciliation_run': {
                'time_column': 'created_at',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'Reconciliation runs'
            },
            'users_activity_log': {
                'time_column': 'timestamp',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'description': 'User activity logs'
            }
        }
        
        if not self.dry_run:
            with connections[target_db].cursor() as cursor:
                # Ensure TimescaleDB extension is enabled
                cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                
                # Get existing hypertables
                cursor.execute("""
                    SELECT hypertable_name 
                    FROM timescaledb_information.hypertables
                """)
                existing_hypertables = {row[0] for row in cursor.fetchall()}
                
                for table_name, config in hypertable_configs.items():
                    if table_name in existing_hypertables:
                        self.stdout.write(f"  ✅ {table_name} already a hypertable")
                        continue
                    
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, [table_name])
                    
                    if not cursor.fetchone()[0]:
                        self.stdout.write(f"  ⚠️ Table {table_name} does not exist, skipping")
                        continue
                    
                    # Check if time column exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = %s AND column_name = %s
                        )
                    """, [table_name, config['time_column']])
                    
                    if not cursor.fetchone()[0]:
                        self.stdout.write(f"  ⚠️ Time column {config['time_column']} not found in {table_name}, skipping")
                        continue
                    
                    try:
                        # Create hypertable
                        cursor.execute(f"""
                            SELECT create_hypertable(
                                '{table_name}', 
                                '{config['time_column']}',
                                chunk_time_interval => {config['chunk_interval']},
                                if_not_exists => TRUE
                            )
                        """)
                        self.stdout.write(f"  ✅ Created hypertable for {table_name} ({config['description']})")
                        
                        # Add compression policy for older data (optional)
                        if table_name in ['wits.nodal_price', 'energy_meter_reading']:
                            cursor.execute(f"""
                                SELECT add_compression_policy(
                                    '{table_name}', 
                                    INTERVAL '7 days',
                                    if_not_exists => TRUE
                                )
                            """)
                            self.stdout.write(f"  ✅ Added compression policy for {table_name}")
                        
                    except Exception as e:
                        self.stdout.write(f"  ⚠️ Could not create hypertable for {table_name}: {e}")
        else:
            self.stdout.write("  📋 Dry run: Would set up hypertables for time-series tables")

    def _get_table_info(self, db_alias: str, table_name: str) -> Optional[Dict]:
        """Get table information including row count and last modified"""
        try:
            with connections[db_alias].cursor() as cursor:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                # Try to get last modified (if table has timestamp columns)
                last_modified = None
                timestamp_columns = ['updated_at', 'created_at', 'timestamp', 'modified_at']
                
                for col in timestamp_columns:
                    try:
                        cursor.execute(f"SELECT MAX({col}) FROM {table_name}")
                        result = cursor.fetchone()
                        if result and result[0]:
                            last_modified = result[0]
                            break
                    except:
                        continue
                
                return {
                    'row_count': row_count,
                    'last_modified': last_modified
                }
        except Exception:
            return None 