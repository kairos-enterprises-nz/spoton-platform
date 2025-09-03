from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up TimescaleDB hypertables and optimizations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            default='timescale',
            help='Database alias to use (default: timescale)',
        )

    def handle(self, *args, **options):
        database = options['database']
        
        if database not in settings.DATABASES:
            self.stdout.write(
                self.style.ERROR(f'Database "{database}" not found in settings')
            )
            return

        connection = connections[database]
        
        try:
            with connection.cursor() as cursor:
                self.stdout.write('Setting up TimescaleDB hypertables...')
                
                # Call the setup function created in init script
                cursor.execute("SELECT setup_hypertables();")
                
                # Create additional indexes for performance
                self.stdout.write('Creating performance indexes...')
                
                # Indexes for meter readings
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meterreading_connection_date 
                    ON energy_meterreading (connection_id, reading_date DESC);
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meterreading_meter_date 
                    ON energy_meterreading (meter_serial, reading_date DESC);
                """)
                
                # Indexes for market prices
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_marketprice_node_date 
                    ON energy_marketprice (market_node, trading_date DESC);
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_marketprice_type_date 
                    ON energy_marketprice (price_type, trading_date DESC);
                """)
                
                # Create continuous aggregates for better performance
                self.stdout.write('Creating continuous aggregates...')
                
                # Daily energy consumption aggregate
                cursor.execute("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS daily_energy_consumption
                    WITH (timescaledb.continuous) AS
                    SELECT 
                        time_bucket('1 day', reading_date) AS day,
                        connection_id,
                        AVG(consumption_kwh) AS avg_consumption,
                        MAX(consumption_kwh) AS max_consumption,
                        MIN(consumption_kwh) AS min_consumption,
                        SUM(consumption_kwh) AS total_consumption,
                        COUNT(*) AS reading_count
                    FROM energy_meterreading
                    GROUP BY day, connection_id;
                """)
                
                # Add refresh policy for continuous aggregate
                cursor.execute("""
                    SELECT add_continuous_aggregate_policy('daily_energy_consumption',
                        start_offset => INTERVAL '1 month',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '1 hour',
                        if_not_exists => TRUE);
                """)
                
                # Monthly market price aggregate
                cursor.execute("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_market_prices
                    WITH (timescaledb.continuous) AS
                    SELECT 
                        time_bucket('1 month', trading_date) AS month,
                        market_node,
                        price_type,
                        AVG(price) AS avg_price,
                        MAX(price) AS max_price,
                        MIN(price) AS min_price,
                        COUNT(*) AS price_count
                    FROM energy_marketprice
                    GROUP BY month, market_node, price_type;
                """)
                
                # Add refresh policy for monthly aggregate
                cursor.execute("""
                    SELECT add_continuous_aggregate_policy('monthly_market_prices',
                        start_offset => INTERVAL '6 months',
                        end_offset => INTERVAL '1 day',
                        schedule_interval => INTERVAL '1 day',
                        if_not_exists => TRUE);
                """)
                
                self.stdout.write(
                    self.style.SUCCESS('TimescaleDB setup completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up TimescaleDB: {str(e)}')
            )
            raise 