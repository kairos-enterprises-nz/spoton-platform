from django.core.management.base import BaseCommand
from django.db import connections
import subprocess


class Command(BaseCommand):
    help = 'Migrate energy tables from primary DB to TimescaleDB and set up hypertables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-data',
            action='store_true',
            help='Skip data migration, only create table structures',
        )

    def handle(self, *args, **options):
        skip_data = options['skip_data']
        
        self.stdout.write("🚀 Starting TimescaleDB migration and setup...")
        
        try:
            # Step 1: Migrate tables
            self.migrate_energy_tables(skip_data)
            
            # Step 2: Set up hypertables
            self.setup_hypertables()
            
            self.stdout.write(
                self.style.SUCCESS('🎉 TimescaleDB setup completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration failed: {str(e)}')
            )
            raise

    def migrate_energy_tables(self, skip_data=False):
        """Migrate energy tables from primary DB to TimescaleDB"""
        
        primary_db = connections['default']
        timescale_db = connections['timescale']
        
        # Energy tables to migrate
        energy_tables = [
            'metering_meterreading',
            'metering_meterreadingaggregate',
            'wholesale_prices_marketprice',
            'wholesale_prices_marketsummary',
            'wholesale_prices_priceforecast',
        ]
        
        self.stdout.write("🔄 Starting migration of key time-series tables to TimescaleDB...")
        
        with primary_db.cursor() as primary_cursor, timescale_db.cursor() as timescale_cursor:
            
            for table in energy_tables:
                self.stdout.write(f"📋 Processing table: {table}")
                
                try:
                    # Check if table exists in primary DB
                    primary_cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = '{table}'
                        );
                    """)
                    
                    if not primary_cursor.fetchone()[0]:
                        self.stdout.write(f"⚠️  Table {table} not found in primary DB, skipping...")
                        continue
                    
                    # Check if table already exists in TimescaleDB
                    timescale_cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = '{table}'
                        );
                    """)
                    
                    if timescale_cursor.fetchone()[0]:
                        self.stdout.write(f"✅ Table {table} already exists in TimescaleDB")
                        continue
                    
                    # Get table structure using pg_dump
                    self.stdout.write(f"🔨 Creating table {table} in TimescaleDB...")
                    
                    try:
                        # Use pg_dump to get table structure
                        dump_cmd = [
                            'docker-compose', 'exec', '-T', 'db', 
                            'pg_dump', '-U', 'postgres', '-d', 'spoton',
                            '--schema-only', '--no-owner', '--no-privileges',
                            '-t', table
                        ]
                        
                        result = subprocess.run(dump_cmd, capture_output=True, text=True, cwd='/home/arun-kumar/Dev')
                        
                        if result.returncode == 0:
                            # Extract CREATE TABLE statement
                            dump_output = result.stdout
                            lines = dump_output.split('\n')
                            create_lines = []
                            in_create = False
                            
                            for line in lines:
                                if line.startswith('CREATE TABLE'):
                                    in_create = True
                                    create_lines.append(line)
                                elif in_create:
                                    create_lines.append(line)
                                    if line.strip().endswith(');'):
                                        break
                            
                            if create_lines:
                                create_sql = '\n'.join(create_lines)
                                timescale_cursor.execute(create_sql)
                                self.stdout.write(f"✅ Created table structure for {table}")
                            else:
                                raise Exception("Could not extract CREATE TABLE statement")
                        else:
                            raise Exception(f"pg_dump failed: {result.stderr}")
                            
                    except Exception as dump_error:
                        # Fallback to manual approach
                        self.stdout.write(f"⚠️  pg_dump failed, using manual approach: {dump_error}")
                        
                        # Get column information
                        primary_cursor.execute(f"""
                            SELECT column_name, data_type, character_maximum_length, 
                                   numeric_precision, numeric_scale, is_nullable, column_default
                            FROM information_schema.columns
                            WHERE table_name = '{table}' AND table_schema = 'public'
                            ORDER BY ordinal_position;
                        """)
                        
                        columns = primary_cursor.fetchall()
                        
                        # Build CREATE TABLE statement manually
                        column_defs = []
                        for col in columns:
                            col_name, data_type, max_length, num_precision, num_scale, nullable, default = col
                            
                            # Handle data type
                            if data_type == 'character varying':
                                col_type = f"varchar({max_length})" if max_length else "varchar"
                            elif data_type == 'character':
                                col_type = f"char({max_length})" if max_length else "char"
                            elif data_type == 'numeric' and num_precision and num_scale:
                                col_type = f"numeric({num_precision},{num_scale})"
                            elif data_type == 'numeric' and num_precision:
                                col_type = f"numeric({num_precision})"
                            else:
                                col_type = data_type
                            
                            # Build column definition
                            col_def = f"{col_name} {col_type}"
                            
                            if nullable == 'NO':
                                col_def += " NOT NULL"
                            
                            if default and not str(default).startswith('nextval('):
                                col_def += f" DEFAULT {default}"
                            
                            column_defs.append(col_def)
                        
                        create_sql = f"CREATE TABLE {table} ({', '.join(column_defs)});"
                        timescale_cursor.execute(create_sql)
                        self.stdout.write(f"✅ Created table structure for {table} (manual)")
                        
                    # Copy data if not skipping
                    if not skip_data:
                        self.stdout.write(f"📊 Copying data for table {table}...")
                        
                        # Get row count first
                        primary_cursor.execute(f"SELECT COUNT(*) FROM {table};")
                        row_count = primary_cursor.fetchone()[0]
                        
                        if row_count > 0:
                            # Copy data in batches for large tables
                            batch_size = 1000
                            offset = 0
                            
                            # Get column names first
                            primary_cursor.execute(f"""
                                SELECT column_name FROM information_schema.columns
                                WHERE table_name = '{table}' AND table_schema = 'public'
                                ORDER BY ordinal_position;
                            """)
                            
                            column_names = [col[0] for col in primary_cursor.fetchall()]
                            columns_str = ', '.join(column_names)
                            placeholders = ', '.join(['%s'] * len(column_names))
                            
                            while offset < row_count:
                                # Try to order by id, fallback to no order
                                try:
                                    primary_cursor.execute(f"""
                                        SELECT {columns_str} FROM {table} 
                                        ORDER BY id 
                                        LIMIT {batch_size} OFFSET {offset};
                                    """)
                                except:
                                    primary_cursor.execute(f"""
                                        SELECT {columns_str} FROM {table} 
                                        LIMIT {batch_size} OFFSET {offset};
                                    """)
                                
                                rows = primary_cursor.fetchall()
                                if not rows:
                                    break
                                
                                # Insert batch into TimescaleDB
                                insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                                timescale_cursor.executemany(insert_sql, rows)
                                
                                offset += batch_size
                                self.stdout.write(f"  📦 Copied batch: {offset}/{row_count} rows")
                            
                            self.stdout.write(f"✅ Copied {row_count} rows for table {table}")
                        else:
                            self.stdout.write(f"ℹ️  No data to copy for table {table}")
                    else:
                        self.stdout.write(f"⏭️  Skipping data copy for table {table}")
                    
                except Exception as e:
                    self.stdout.write(f"❌ Error migrating table {table}: {str(e)}")
                    continue
        
        self.stdout.write("✅ Table migration completed!")

    def setup_hypertables(self):
        """Set up TimescaleDB hypertables for time-series tables"""
        
        timescale_db = connections['timescale']
        
        # Time-series tables and their time columns
        hypertables = {
            'metering_meterreading': 'timestamp',
            'metering_meterreadingaggregate': 'period_start', 
            'wholesale_prices_marketprice': 'timestamp',
        }
        
        self.stdout.write("🔧 Setting up TimescaleDB hypertables...")
        
        with timescale_db.cursor() as cursor:
            
            # Enable TimescaleDB extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            
            for table, time_column in hypertables.items():
                try:
                    self.stdout.write(f"⚙️  Creating hypertable for {table} on column {time_column}")
                    
                    # Check if table exists
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = '{table}'
                        );
                    """)
                    
                    if not cursor.fetchone()[0]:
                        self.stdout.write(f"⚠️  Table {table} not found, skipping hypertable creation")
                        continue
                    
                    # Create hypertable
                    cursor.execute(f"""
                        SELECT create_hypertable(
                            '{table}', 
                            '{time_column}',
                            chunk_time_interval => INTERVAL '1 day',
                            if_not_exists => TRUE
                        );
                    """)
                    
                    self.stdout.write(f"✅ Created hypertable for {table}")
                    
                except Exception as e:
                    self.stdout.write(f"❌ Error setting up hypertable for {table}: {str(e)}")
                    continue
        
        self.stdout.write("✅ Hypertable setup completed!") 