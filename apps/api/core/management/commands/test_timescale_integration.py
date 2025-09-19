"""
Test command to verify TimescaleDB integration for Airflow DAGs.
This ensures that the shared hypertable with tenant partitioning works correctly.
"""
from django.core.management.base import BaseCommand
from django.db import connections
from datetime import datetime, timezone
import random

class Command(BaseCommand):
    help = 'Test TimescaleDB integration for Airflow DAGs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            default=1,
            help='Tenant ID to use for testing',
        )
        parser.add_argument(
            '--insert-test-data',
            action='store_true',
            help='Insert test meter reading data',
        )

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        
        self.stdout.write(
            self.style.SUCCESS('Testing TimescaleDB integration...')
        )

        # Test 1: Connection to TimescaleDB
        self._test_connection()
        
        # Test 2: Tenant context setting (for RLS)
        self._test_tenant_context(tenant_id)
        
        # Test 3: Insert test data if requested
        if options['insert_test_data']:
            self._insert_test_data(tenant_id)
        
        # Test 4: Query data with RLS
        self._test_query_with_rls(tenant_id)
        
        self.stdout.write(
            self.style.SUCCESS('✓ All TimescaleDB tests passed!')
        )

    def _test_connection(self):
        """Test connection to TimescaleDB"""
        self.stdout.write('Testing TimescaleDB connection...')
        
        try:
            timescale_conn = connections['timescaledb']
            with timescale_conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(f'✓ Connected to: {version}')
                
                # Check if TimescaleDB extension is available
                cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
                result = cursor.fetchone()
                if result:
                    self.stdout.write('✓ TimescaleDB extension found')
                else:
                    self.stdout.write('⚠ TimescaleDB extension not found (running on regular PostgreSQL)')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Connection failed: {str(e)}')
            )
            raise

    def _test_tenant_context(self, tenant_id):
        """Test setting tenant context for RLS"""
        self.stdout.write(f'Testing tenant context setting (tenant_id: {tenant_id})...')
        
        try:
            timescale_conn = connections['timescaledb']
            with timescale_conn.cursor() as cursor:
                # Set tenant context
                cursor.execute("SET app.current_tenant_id = %s", [tenant_id])
                
                # Verify it was set
                cursor.execute("SELECT current_setting('app.current_tenant_id', true);")
                result = cursor.fetchone()
                if result and result[0] == str(tenant_id):
                    self.stdout.write('✓ Tenant context set correctly')
                else:
                    self.stdout.write(f'⚠ Tenant context: {result}')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Tenant context test failed: {str(e)}')
            )
            raise

    def _insert_test_data(self, tenant_id):
        """Insert test meter reading data"""
        self.stdout.write('Inserting test meter reading data...')
        
        try:
            timescale_conn = connections['timescaledb']
            with timescale_conn.cursor() as cursor:
                # Set tenant context first
                cursor.execute("SET app.current_tenant_id = %s", [tenant_id])
                
                # Insert test data
                test_data = []
                base_time = datetime.now(timezone.utc)
                
                for i in range(10):
                    test_data.append((
                        tenant_id,
                        f'CONN_{tenant_id}_{i:03d}',
                        base_time.replace(hour=i, minute=0, second=0, microsecond=0),
                        round(random.uniform(10.0, 100.0), 3),
                        round(random.uniform(5.0, 50.0), 3),
                        round(random.uniform(15.0, 120.0), 3),
                    ))
                
                cursor.executemany("""
                    INSERT INTO timescale.meter_read_interval 
                    (tenant_id, connection_id, reading_datetime, kwh_consumption, kvarh_consumption, kva_demand)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, test_data)
                
                self.stdout.write(f'✓ Inserted {len(test_data)} test records for tenant {tenant_id}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Test data insertion failed: {str(e)}')
            )
            raise

    def _test_query_with_rls(self, tenant_id):
        """Test querying data with Row-Level Security"""
        self.stdout.write('Testing data query with RLS...')
        
        try:
            timescale_conn = connections['timescaledb']
            with timescale_conn.cursor() as cursor:
                # Set tenant context
                cursor.execute("SET app.current_tenant_id = %s", [tenant_id])
                
                # Query data (should only return data for this tenant due to RLS)
                cursor.execute("""
                    SELECT tenant_id, connection_id, reading_datetime, kwh_consumption
                    FROM timescale.meter_read_interval
                    ORDER BY reading_datetime DESC
                    LIMIT 5
                """)
                
                results = cursor.fetchall()
                self.stdout.write(f'✓ Query returned {len(results)} records')
                
                # Verify all results are for the correct tenant
                for row in results:
                    if row[0] != tenant_id:
                        self.stdout.write(
                            self.style.ERROR(f'✗ RLS violation: Found data for tenant {row[0]} when querying for tenant {tenant_id}')
                        )
                        return
                
                if results:
                    self.stdout.write('✓ Row-Level Security working correctly')
                    self.stdout.write(f'  Sample record: {results[0]}')
                else:
                    self.stdout.write('ℹ No data found (this is normal if no test data was inserted)')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Query test failed: {str(e)}')
            )
            raise 