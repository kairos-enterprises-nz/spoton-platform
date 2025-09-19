"""
Management command to set up TimescaleDB database and schemas.
"""

from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up TimescaleDB database with required schemas and hypertables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-database',
            action='store_true',
            help='Create the TimescaleDB database if it does not exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up TimescaleDB...'))
        
        # Get TimescaleDB connection
        try:
            timescale_db = connections['timescaledb']
        except KeyError:
            self.stdout.write(
                self.style.ERROR('TimescaleDB database not configured in settings')
            )
            return
        
        if options['create_database']:
            self.create_database()
        
        self.create_schemas()
        self.create_hypertables()
        
        self.stdout.write(
            self.style.SUCCESS('TimescaleDB setup completed successfully!')
        )

    def create_database(self):
        """Create the TimescaleDB database if it doesn't exist"""
        self.stdout.write('Creating TimescaleDB database...')
        
        # Get default connection to create database
        default_db = connections['default']
        db_name = settings.DATABASES['timescaledb']['NAME']
        
        with default_db.cursor() as cursor:
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                [db_name]
            )
            
            if not cursor.fetchone():
                # Create database
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                self.stdout.write(f'Database "{db_name}" created successfully')
            else:
                self.stdout.write(f'Database "{db_name}" already exists')

    def create_schemas(self):
        """Create required schemas in TimescaleDB"""
        self.stdout.write('Creating schemas...')
        
        schemas = [
            'users',
            'contracts', 
            'energy',
            'finance',
            'support',
            'pricing',
            'metering',
            'validation'
        ]
        
        timescale_db = connections['timescaledb']
        with timescale_db.cursor() as cursor:
            # Create TimescaleDB extension
            cursor.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
            
            # Create schemas
            for schema in schemas:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                self.stdout.write(f'Schema "{schema}" created')
            
            # Set search path
            search_path = ', '.join([f'"{s}"' for s in schemas] + ['public'])
            cursor.execute(f'SET search_path TO {search_path}')

    def create_hypertables(self):
        """Create hypertables for time-series data"""
        self.stdout.write('Creating hypertables...')
        
        # Hypertable definitions (ONLY for pure time-series data in TimescaleDB)
        hypertables = [
            {
                'table': 'metering.interval_reads_raw',
                'time_column': 'timestamp',
                'chunk_interval': '1 day'
            },
            {
                'table': 'metering.interval_reads_derived',
                'time_column': 'timestamp', 
                'chunk_interval': '1 day'
            },
            {
                'table': 'metering.interval_reads_final',
                'time_column': 'timestamp',
                'chunk_interval': '1 day'
            },
            {
                'table': 'metering.daily_register_reads',
                'time_column': 'reading_date',
                'chunk_interval': '30 days'
            },
            {
                'table': 'metering.estimated_interval_reads',
                'time_column': 'timestamp',
                'chunk_interval': '1 day'
            }
        ]
        
        timescale_db = connections['timescaledb']
        with timescale_db.cursor() as cursor:
            for hypertable in hypertables:
                try:
                    # Check if table exists before creating hypertable
                    table_parts = hypertable['table'].split('.')
                    schema_name = table_parts[0]
                    table_name = table_parts[1]
                    
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        )
                    """, [schema_name, table_name])
                    
                    table_exists = cursor.fetchone()[0]
                    
                    if table_exists:
                        # Create hypertable
                        cursor.execute(f"""
                            SELECT create_hypertable(
                                '{hypertable['table']}', 
                                '{hypertable['time_column']}',
                                chunk_time_interval => INTERVAL '{hypertable['chunk_interval']}',
                                if_not_exists => TRUE
                            )
                        """)
                        
                        self.stdout.write(
                            f'Hypertable created for {hypertable["table"]}'
                        )
                        
                        # Add compression policy for interval reads
                        if 'interval_reads' in hypertable['table']:
                            cursor.execute(f"""
                                ALTER TABLE {hypertable['table']} SET (
                                    timescaledb.compress,
                                    timescaledb.compress_segmentby = 'tenant_id,connection_id,register_code'
                                )
                            """)
                            
                            cursor.execute(f"""
                                SELECT add_compression_policy(
                                    '{hypertable['table']}', 
                                    INTERVAL '7 days',
                                    if_not_exists => TRUE
                                )
                            """)
                            
                            self.stdout.write(
                                f'Compression policy added for {hypertable["table"]}'
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Table {hypertable["table"]} does not exist, skipping hypertable creation'
                            )
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error creating hypertable for {hypertable["table"]}: {e}'
                        )
                    ) 