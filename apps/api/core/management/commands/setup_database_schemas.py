"""
Management command to set up database schemas for the Utility Byte platform.
"""

import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Sets up database schemas and TimescaleDB for the Utility Byte platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force schema creation even if schemas already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Check if TimescaleDB extension is installed
        self.stdout.write(self.style.NOTICE('Checking TimescaleDB extension...'))
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb';")
            has_timescale = cursor.fetchone()[0] > 0
            
            if not has_timescale:
                self.stdout.write(self.style.ERROR(
                    'TimescaleDB extension not found. Please install TimescaleDB and create the extension.'
                ))
                self.stdout.write(self.style.NOTICE(
                    'You can create the extension with: CREATE EXTENSION IF NOT EXISTS timescaledb;'
                ))
                return
        
        self.stdout.write(self.style.SUCCESS('TimescaleDB extension found.'))
        
        # Check if schemas already exist
        schemas = ['users', 'contracts', 'energy', 'finance', 'support', 'pricing', 'metering']
        existing_schemas = []
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT schema_name FROM information_schema.schemata;")
            existing_schemas = [row[0] for row in cursor.fetchall()]
        
        # Create schemas
        self.stdout.write(self.style.NOTICE('Creating schemas...'))
        for schema in schemas:
            if schema in existing_schemas and not force:
                self.stdout.write(f'Schema "{schema}" already exists. Skipping.')
                continue
                
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
                self.stdout.write(self.style.SUCCESS(f'Created schema "{schema}".'))
        
        # Run TimescaleDB setup script if it exists
        script_path = os.path.join(settings.BASE_DIR, 'scripts', 'setup_timescaledb.sql')
        if os.path.exists(script_path):
            self.stdout.write(self.style.NOTICE('Running TimescaleDB setup script...'))
            
            # Get database connection details from settings
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings.get('PASSWORD', '')
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '5432')
            
            # Set environment variables for psql
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            # Run the script using psql
            try:
                cmd = [
                    'psql',
                    '-h', db_host,
                    '-p', db_port,
                    '-U', db_user,
                    '-d', db_name,
                    '-f', script_path
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    self.stdout.write(self.style.SUCCESS('TimescaleDB setup script executed successfully.'))
                else:
                    self.stdout.write(self.style.ERROR(f'Error executing TimescaleDB setup script: {stderr.decode()}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to run TimescaleDB setup script: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'TimescaleDB setup script not found at {script_path}. Skipping hypertable creation.'
            ))
        
        # Update settings.py to include the database router
        self.stdout.write(self.style.NOTICE('Database schemas setup complete.'))
        self.stdout.write(self.style.NOTICE(
            'Make sure to add SchemaRouter to DATABASE_ROUTERS in settings.py:\n'
            'DATABASE_ROUTERS = ["utilitybyte.db_router.SchemaRouter"]'
        ))
        
        # Final message
        self.stdout.write(self.style.SUCCESS(
            'Database schema setup complete. You can now run migrations with:\n'
            'python manage.py migrate'
        )) 