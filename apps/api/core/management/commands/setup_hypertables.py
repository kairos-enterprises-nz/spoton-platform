"""
Django management command to set up and manage TimescaleDB hypertables
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.conf import settings
from django.apps import apps
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Set up and manage TimescaleDB hypertables for time-series data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            default='timescale',
            help='Database alias to use (default: timescale)',
        )
        parser.add_argument(
            '--table',
            help='Specific table to convert to hypertable',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List existing hypertables and their configuration',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show detailed status of all hypertables',
        )
        parser.add_argument(
            '--setup-policies',
            action='store_true',
            help='Set up compression and retention policies',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if table has data',
        )

    def handle(self, *args, **options):
        self.database = options['database']
        self.dry_run = options['dry_run']
        self.force = options['force']
        
        if self.database not in settings.DATABASES:
            raise CommandError(f'Database "{self.database}" not found in settings')
        
        self.connection = connections[self.database]
        
        # Check if TimescaleDB is available
        if not self._is_timescaledb():
            raise CommandError(f'Database "{self.database}" is not TimescaleDB')
        
        if options['list']:
            self._list_hypertables()
        elif options['status']:
            self._show_status()
        elif options['setup_policies']:
            self._setup_policies()
        elif options['table']:
            self._setup_single_table(options['table'])
        else:
            self._setup_all_hypertables()

    def _is_timescaledb(self) -> bool:
        """Check if database has TimescaleDB extension"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
                return cursor.fetchone() is not None
        except Exception:
            return False

    def _get_hypertable_configs(self) -> dict:
        """Get configuration for all potential hypertables"""
        return {
            'wits.nodal_price': {
                'time_column': 'trading_date',
                'chunk_interval': 'INTERVAL \'1 month\'',
                'compress_after': 'INTERVAL \'7 days\'',
                'retain_for': 'INTERVAL \'2 years\'',
                'description': 'WITS nodal electricity prices from NZX',
                'partition_column': 'gip_gxp',  # Optional space partitioning
                'compression_segments': ['gip_gxp', 'price_type']
            },
            'wits.import_log': {
                'time_column': 'imported_at',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'3 days\'',
                'retain_for': 'INTERVAL \'6 months\'',
                'description': 'WITS data import logs and status'
            },
            'energy_meter_reading': {
                'time_column': 'reading_datetime',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'7 days\'',
                'retain_for': 'INTERVAL \'7 years\'',
                'description': 'Electricity meter readings',
                'partition_column': 'connection_id',
                'compression_segments': ['connection_id', 'meter_type']
            },
            'energy_meter_reading_aggregate': {
                'time_column': 'period_start',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'30 days\'',
                'retain_for': 'INTERVAL \'10 years\'',
                'description': 'Pre-calculated meter reading aggregates'
            },
            'energy_audit_log': {
                'time_column': 'timestamp',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'30 days\'',
                'retain_for': 'INTERVAL \'7 years\'',
                'description': 'System audit logs'
            },
            'energy_audit_data_change': {
                'time_column': 'timestamp',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'30 days\'',
                'retain_for': 'INTERVAL \'7 years\'',
                'description': 'Data change audit trail'
            },
            'energy_data_import_log': {
                'time_column': 'started_at',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'7 days\'',
                'retain_for': 'INTERVAL \'1 year\'',
                'description': 'Data import operation logs'
            },
            'energy_reconciliation_run': {
                'time_column': 'created_at',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'30 days\'',
                'retain_for': 'INTERVAL \'3 years\'',
                'description': 'Energy reconciliation run records'
            },
            'users_activity_log': {
                'time_column': 'timestamp',
                'chunk_interval': 'INTERVAL \'1 day\'',
                'compress_after': 'INTERVAL \'7 days\'',
                'retain_for': 'INTERVAL \'2 years\'',
                'description': 'User activity and access logs'
            }
        }

    def _list_hypertables(self):
        """List existing hypertables"""
        self.stdout.write("📊 TimescaleDB Hypertables Status")
        self.stdout.write("=" * 50)
        
        with self.connection.cursor() as cursor:
            # Get existing hypertables
            cursor.execute("""
                SELECT 
                    hypertable_name,
                    num_chunks,
                    compression_enabled
                FROM timescaledb_information.hypertables
                ORDER BY hypertable_name
            """)
            
            hypertables = cursor.fetchall()
            
            if not hypertables:
                self.stdout.write("No hypertables found")
                return
            
            for row in hypertables:
                name, chunks, compressed = row
                
                self.stdout.write(f"\n🕐 {name}")
                self.stdout.write(f"   Chunks: {chunks or 'N/A'}")
                self.stdout.write(f"   Compression: {'✅ Enabled' if compressed else '❌ Disabled'}")
                
                # Get size information using TimescaleDB functions
                try:
                    cursor.execute("SELECT hypertable_size(%s)", [name])
                    total_size = cursor.fetchone()[0]
                    if total_size:
                        self.stdout.write(f"   Total Size: {self._format_bytes(total_size)}")
                except Exception:

    def _show_status(self):
        """Show detailed status of hypertables"""
        self.stdout.write("📈 Detailed Hypertable Status")
        self.stdout.write("=" * 50)
        
        configs = self._get_hypertable_configs()
        
        with self.connection.cursor() as cursor:
            # Get existing hypertables with details
            cursor.execute("""
                SELECT 
                    h.hypertable_name,
                    h.num_dimensions,
                    d.column_name as time_column,
                    d.time_interval,
                    h.compression_enabled,
                    h.num_chunks
                FROM timescaledb_information.hypertables h
                LEFT JOIN timescaledb_information.dimensions d 
                    ON h.hypertable_name = d.hypertable_name AND d.dimension_type = 'Time'
                ORDER BY h.hypertable_name
            """)
            
            existing_hypertables = {row[0]: row for row in cursor.fetchall()}
            
            # Show status for each configured table
            for table_name, config in configs.items():
                self.stdout.write(f"\n📋 {table_name}")
                self.stdout.write(f"   Description: {config['description']}")
                
                if table_name in existing_hypertables:
                    row = existing_hypertables[table_name]
                    _, dims, time_col, interval, compressed, chunks = row
                    
                    self.stdout.write("   Status: ✅ Hypertable")
                    self.stdout.write(f"   Time Column: {time_col}")
                    self.stdout.write(f"   Chunk Interval: {interval}")
                    self.stdout.write(f"   Dimensions: {dims}")
                    self.stdout.write(f"   Compression: {'✅ Enabled' if compressed else '❌ Disabled'}")
                    self.stdout.write(f"   Chunks: {chunks or 0}")
                    
                    # Get size using TimescaleDB function
                    try:
                        cursor.execute("SELECT hypertable_size(%s)", [table_name])
                        size = cursor.fetchone()[0]
                        if size:
                            self.stdout.write(f"   Size: {self._format_bytes(size)}")
                    except Exception:
                    
                    # Check for policies
                    self._check_policies(cursor, table_name)
                else:
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, [table_name])
                    
                    if cursor.fetchone()[0]:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        self.stdout.write("   Status: ⚠️ Regular table (not hypertable)")
                        self.stdout.write(f"   Rows: {row_count:,}")
                    else:
                        self.stdout.write("   Status: ❌ Table does not exist")

    def _check_policies(self, cursor, table_name):
        """Check compression and retention policies for a table"""
        try:
            # Check compression policy
            cursor.execute("""
                SELECT config
                FROM timescaledb_information.jobs
                WHERE hypertable_name = %s 
                AND proc_name LIKE '%compression%'
            """, [table_name])
            
            compress_result = cursor.fetchone()
            if compress_result and compress_result[0]:
                try:
                    import json
                    config = json.loads(compress_result[0])
                    compress_after = config.get('compress_after', 'Unknown')
                    self.stdout.write(f"   Compression Policy: ✅ After {compress_after}")
                except Exception as e:
                    self.stdout.write("   Compression Policy: ✅ Enabled")
            else:
                self.stdout.write("   Compression Policy: ❌ None")
            
            # Check retention policy
            cursor.execute("""
                SELECT config
                FROM timescaledb_information.jobs
                WHERE hypertable_name = %s 
                AND (proc_name LIKE '%retention%' OR proc_name LIKE '%drop_chunks%')
            """, [table_name])
            
            retention_result = cursor.fetchone()
            if retention_result and retention_result[0]:
                try:
                    import json
                    config = json.loads(retention_result[0])
                    drop_after = config.get('drop_after', 'Unknown')
                    self.stdout.write(f"   Retention Policy: ✅ Drop after {drop_after}")
                except Exception as e:
                    self.stdout.write("   Retention Policy: ✅ Enabled")
            else:
                self.stdout.write("   Retention Policy: ❌ None")
        except Exception as e:
            self.stdout.write(f"   Policy Check: ⚠️ Error checking policies: {e}")

    def _setup_single_table(self, table_name: str):
        """Set up a single table as hypertable"""
        configs = self._get_hypertable_configs()
        
        if table_name not in configs:
            raise CommandError(f"No configuration found for table '{table_name}'")
        
        config = configs[table_name]
        self._create_hypertable(table_name, config)

    def _setup_all_hypertables(self):
        """Set up all configured hypertables"""
        self.stdout.write("🕐 Setting up TimescaleDB hypertables...")
        
        configs = self._get_hypertable_configs()
        
        with self.connection.cursor() as cursor:
            # Ensure TimescaleDB extension is enabled
            if not self.dry_run:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            # Get existing hypertables
            cursor.execute("SELECT hypertable_name FROM timescaledb_information.hypertables")
            existing_hypertables = {row[0] for row in cursor.fetchall()}
            
            for table_name, config in configs.items():
                if table_name in existing_hypertables:
                    self.stdout.write(f"  ✅ {table_name} already a hypertable")
                    continue
                
                self._create_hypertable(table_name, config)

    def _create_hypertable(self, table_name: str, config: dict):
        """Create a hypertable from configuration"""
        with self.connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, [table_name])
            
            if not cursor.fetchone()[0]:
                self.stdout.write(f"  ⚠️ Table {table_name} does not exist, skipping")
                return
            
            # Check if time column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                )
            """, [table_name, config['time_column']])
            
            if not cursor.fetchone()[0]:
                self.stdout.write(f"  ⚠️ Time column {config['time_column']} not found in {table_name}")
                return
            
            # Check for existing data
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            if row_count > 0 and not self.force:
                self.stdout.write(f"  ⚠️ {table_name} has {row_count:,} rows. Use --force to convert")
                return
            
            if self.dry_run:
                self.stdout.write(f"  📋 Would create hypertable for {table_name}")
                return
            
            try:
                # Create hypertable
                create_sql = f"""
                    SELECT create_hypertable(
                        '{table_name}', 
                        '{config['time_column']}',
                        chunk_time_interval => {config['chunk_interval']},
                        if_not_exists => TRUE
                """
                
                # Add space partitioning if configured
                if 'partition_column' in config:
                    create_sql += f", partitioning_column => '{config['partition_column']}'"
                
                create_sql += ")"
                
                cursor.execute(create_sql)
                self.stdout.write(f"  ✅ Created hypertable for {table_name} ({config['description']})")
                
                if row_count > 0:
                    self.stdout.write(f"     Converted {row_count:,} existing rows")
                
            except Exception as e:
                self.stdout.write(f"  ❌ Failed to create hypertable for {table_name}: {e}")

    def _setup_policies(self):
        """Set up compression and retention policies"""
        self.stdout.write("🗜️ Setting up compression and retention policies...")
        
        configs = self._get_hypertable_configs()
        
        with self.connection.cursor() as cursor:
            # Get existing hypertables
            cursor.execute("SELECT hypertable_name FROM timescaledb_information.hypertables")
            existing_hypertables = {row[0] for row in cursor.fetchall()}
            
            for table_name, config in configs.items():
                if table_name not in existing_hypertables:
                    self.stdout.write(f"  ⚠️ {table_name} is not a hypertable, skipping policies")
                    continue
                
                self._setup_table_policies(cursor, table_name, config)

    def _setup_table_policies(self, cursor, table_name: str, config: dict):
        """Set up policies for a specific table"""
        if self.dry_run:
            self.stdout.write(f"  📋 Would set up policies for {table_name}")
            return
        
        try:
            # Set up compression policy
            if 'compress_after' in config:
                # Enable compression first
                compress_sql = f"ALTER TABLE {table_name} SET (timescaledb.compress = TRUE"
                
                if 'compression_segments' in config:
                    segments = "', '".join(config['compression_segments'])
                    compress_sql += f", timescaledb.compress_segmentby = '{segments}'"
                
                compress_sql += ")"
                cursor.execute(compress_sql)
                
                # Add compression policy
                cursor.execute(f"""
                    SELECT add_compression_policy(
                        '{table_name}', 
                        {config['compress_after']},
                        if_not_exists => TRUE
                    )
                """)
                self.stdout.write(f"  ✅ Compression policy for {table_name} (after {config['compress_after']})")
            
            # Set up retention policy
            if 'retain_for' in config:
                cursor.execute(f"""
                    SELECT add_retention_policy(
                        '{table_name}', 
                        {config['retain_for']},
                        if_not_exists => TRUE
                    )
                """)
                self.stdout.write(f"  ✅ Retention policy for {table_name} (keep {config['retain_for']})")
                
        except Exception as e:
            self.stdout.write(f"  ⚠️ Policy setup failed for {table_name}: {e}")

    def _format_bytes(self, bytes_val) -> str:
        """Format bytes into human readable string"""
        if bytes_val is None:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB" 