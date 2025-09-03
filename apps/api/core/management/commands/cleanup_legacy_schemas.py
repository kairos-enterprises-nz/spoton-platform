"""
Cleanup legacy schemas and move all ORM data to public schema.
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Cleanup legacy schemas and move ORM data to public schema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Cleaning up legacy schemas...')
        )

        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            self._analyze_schemas()
            self._move_tables_to_public()
            self._drop_empty_schemas()
            self._verify_cleanup()
            
            self.stdout.write(
                self.style.SUCCESS('Schema cleanup completed!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Cleanup failed: {str(e)}')
            )
            raise

    def _analyze_schemas(self):
        """Analyze current schema state"""
        self.stdout.write('Analyzing current schemas...')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name;
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            
            for schema in schemas:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s;
                """, [schema])
                table_count = cursor.fetchone()[0]
                self.stdout.write(f'  - {schema}: {table_count} tables')

    def _move_tables_to_public(self):
        """Move tables from legacy schemas to public"""
        self.stdout.write('Moving tables to public schema...')
        
        legacy_schemas = ['contracts', 'energy', 'finance', 'users']
        
        with connection.cursor() as cursor:
            for schema in legacy_schemas:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """, [schema])
                
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    self._move_table(cursor, schema, table)

    def _move_table(self, cursor, schema, table):
        """Move a single table to public schema"""
        source_table = f'"{schema}"."{table}"'
        
        try:
            # Check if table exists in public
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, [table])
            
            exists_in_public = cursor.fetchone()[0]
            
            if exists_in_public:
                self.stdout.write(f'    ✓ {table}: Already in public schema')
            else:
                if not self.dry_run:
                    cursor.execute(f'ALTER TABLE {source_table} SET SCHEMA public')
                    self.stdout.write(f'    ✓ {table}: Moved to public')
                else:
                    self.stdout.write(f'    → Would move {table} to public')
                    
        except Exception as e:
            self.stdout.write(f'    ✗ {table}: Error: {e}')

    def _drop_empty_schemas(self):
        """Drop empty legacy schemas"""
        self.stdout.write('Dropping empty legacy schemas...')
        
        legacy_schemas = ['contracts', 'energy', 'finance', 'pricing', 'support', 'users']
        
        with connection.cursor() as cursor:
            for schema in legacy_schemas:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s;
                """, [schema])
                
                table_count = cursor.fetchone()[0]
                
                if table_count == 0:
                    if not self.dry_run:
                        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                        self.stdout.write(f'  ✓ Dropped schema: {schema}')
                    else:
                        self.stdout.write(f'  → Would drop schema: {schema}')
                else:
                    self.stdout.write(f'  ⚠ Schema {schema} has {table_count} tables')

    def _verify_cleanup(self):
        """Verify the cleanup was successful"""
        self.stdout.write('Final schema state:')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name, COUNT(table_name) as table_count
                FROM information_schema.schemata s
                LEFT JOIN information_schema.tables t ON s.schema_name = t.table_schema
                WHERE s.schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                GROUP BY schema_name
                ORDER BY schema_name;
            """)
            
            results = cursor.fetchall()
            
            for schema, table_count in results:
                self.stdout.write(f'  - {schema}: {table_count or 0} tables')
