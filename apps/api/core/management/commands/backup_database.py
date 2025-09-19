"""
Django management command for database backup and rollback in CI/CD deployments.
Provides safe database operations for production deployments.
"""
import os
import subprocess
import json
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Backup and rollback database for safe CI/CD deployments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Create a database backup'
        )
        parser.add_argument(
            '--restore',
            type=str,
            help='Restore from backup file'
        )
        parser.add_argument(
            '--list-backups',
            action='store_true',
            help='List available backups'
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='./backups',
            help='Directory to store backups (default: ./backups)'
        )
        parser.add_argument(
            '--schema-only',
            action='store_true',
            help='Backup/restore schema only (no data)'
        )
        parser.add_argument(
            '--pre-migration',
            action='store_true',
            help='Create pre-migration backup with timestamp'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🗄️  SpotOn Database Backup Tool')
        )
        
        # Ensure backup directory exists
        backup_dir = options['backup_dir']
        os.makedirs(backup_dir, exist_ok=True)
        
        if options['backup'] or options['pre_migration']:
            self.create_backup(backup_dir, options['schema_only'], options['pre_migration'])
        elif options['restore']:
            self.restore_backup(options['restore'])
        elif options['list_backups']:
            self.list_backups(backup_dir)
        else:
            self.show_status()

    def get_db_config(self):
        """Get database configuration from Django settings"""
        db_config = settings.DATABASES['default']
        return {
            'host': db_config.get('HOST', 'localhost'),
            'port': db_config.get('PORT', '5432'),
            'name': db_config['NAME'],
            'user': db_config['USER'],
            'password': db_config['PASSWORD']
        }

    def create_backup(self, backup_dir, schema_only=False, pre_migration=False):
        """Create database backup using pg_dump"""
        db_config = self.get_db_config()
        
        # Generate backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_type = 'schema' if schema_only else 'full'
        prefix = 'pre_migration' if pre_migration else 'backup'
        
        backup_filename = f"{prefix}_{backup_type}_{db_config['name']}_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        self.stdout.write(f'📤 Creating {"schema-only" if schema_only else "full"} backup...')
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', db_config['host'],
            '-p', str(db_config['port']),
            '-U', db_config['user'],
            '-d', db_config['name'],
            '--verbose',
            '--clean',
            '--if-exists',
        ]
        
        if schema_only:
            cmd.append('--schema-only')
        
        cmd.extend(['-f', backup_path])
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            # Create metadata file
            metadata = {
                'backup_file': backup_filename,
                'timestamp': timestamp,
                'database': db_config['name'],
                'schema_only': schema_only,
                'pre_migration': pre_migration,
                'size_bytes': os.path.getsize(backup_path),
                'django_migrations': self.get_migration_status()
            }
            
            metadata_path = backup_path.replace('.sql', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Backup created: {backup_filename}')
            )
            self.stdout.write(f'📊 Size: {metadata["size_bytes"] / 1024 / 1024:.1f} MB')
            
            return backup_path
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Backup failed: {e.stderr}')
            )
            raise CommandError('Backup operation failed')

    def restore_backup(self, backup_file):
        """Restore database from backup file"""
        if not os.path.exists(backup_file):
            raise CommandError(f'Backup file not found: {backup_file}')
        
        db_config = self.get_db_config()
        
        self.stdout.write(f'🔄 Restoring from backup: {backup_file}')
        
        # Warning for production
        if 'live' in db_config['name'].lower() or 'prod' in db_config['name'].lower():
            confirm = input('⚠️  WARNING: Restoring to PRODUCTION database. Type "CONFIRM" to proceed: ')
            if confirm != 'CONFIRM':
                self.stdout.write('❌ Restore cancelled')
                return
        
        # Build psql command
        cmd = [
            'psql',
            '-h', db_config['host'],
            '-p', str(db_config['port']),
            '-U', db_config['user'],
            '-d', db_config['name'],
            '-f', backup_file,
            '--verbose'
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Database restored successfully')
            )
            
            # Check migration status after restore
            self.stdout.write('🔍 Checking migration status after restore...')
            self.check_migration_status()
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Restore failed: {e.stderr}')
            )
            raise CommandError('Restore operation failed')

    def list_backups(self, backup_dir):
        """List available backup files"""
        self.stdout.write(f'📋 Available backups in {backup_dir}:')
        
        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.sql'):
                backup_path = os.path.join(backup_dir, filename)
                metadata_path = backup_path.replace('.sql', '_metadata.json')
                
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                backup_files.append({
                    'filename': filename,
                    'path': backup_path,
                    'size': os.path.getsize(backup_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(backup_path)),
                    'metadata': metadata
                })
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x['modified'], reverse=True)
        
        if not backup_files:
            self.stdout.write('  No backups found')
            return
        
        for backup in backup_files:
            size_mb = backup['size'] / 1024 / 1024
            backup_type = 'schema' if backup['metadata'].get('schema_only') else 'full'
            
            self.stdout.write(
                f"  • {backup['filename']} ({size_mb:.1f} MB, {backup_type})"
            )
            self.stdout.write(
                f"    Created: {backup['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
            )

    def get_migration_status(self):
        """Get current migration status"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                ORDER BY app, name
            """)
            
            migrations = {}
            for app, name, applied in cursor.fetchall():
                if app not in migrations:
                    migrations[app] = []
                migrations[app].append({
                    'name': name,
                    'applied': applied.isoformat() if applied else None
                })
            
            return migrations

    def check_migration_status(self):
        """Check and display migration status"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', stdout=out)
        migration_output = out.getvalue()
        
        self.stdout.write('📊 Migration Status:')
        for line in migration_output.split('\n'):
            if line.strip():
                self.stdout.write(f'  {line}')

    def show_status(self):
        """Show current database status"""
        db_config = self.get_db_config()
        
        self.stdout.write(f"🗄️  Database: {db_config['name']}")
        self.stdout.write(f"🌐 Host: {db_config['host']}:{db_config['port']}")
        
        # Check connection
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT version()')
                version = cursor.fetchone()[0]
                self.stdout.write(f"✅ Connection: {version.split()[0]} {version.split()[1]}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Connection failed: {e}')
            )
            return
        
        # Show migration status
        self.check_migration_status()