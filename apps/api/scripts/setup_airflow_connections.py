#!/usr/bin/env python3
"""
Setup Airflow Database Connections

This script configures the Airflow connections needed for the BCMM ETL pipeline
to connect to the PostgreSQL database using the same configuration as Django.
"""

import os
import django
from django.conf import settings

# Setup Django to get database configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

def setup_airflow_postgres_connection():
    """
    Set up the postgres_default connection in Airflow using Django's database configuration
    """
    try:
        from airflow.models import Connection
        from airflow.utils.db import create_session
        
        # Get Django's database configuration
        db_config = settings.DATABASES['default']
        
        # Create the connection object
        conn_id = 'postgres_default'
        conn = Connection(
            conn_id=conn_id,
            conn_type='postgres',
            host=db_config['HOST'],
            port=db_config['PORT'],
            schema=db_config['NAME'],
            login=db_config['USER'],
            password=db_config['PASSWORD']
        )
        
        # Add or update the connection
        with create_session() as session:
            # Check if connection already exists
            existing_conn = session.query(Connection).filter(Connection.conn_id == conn_id).first()
            
            if existing_conn:
                # Update existing connection
                existing_conn.host = conn.host
                existing_conn.port = conn.port
                existing_conn.schema = conn.schema
                existing_conn.login = conn.login
                existing_conn.password = conn.password
                print(f"✓ Updated existing Airflow connection: {conn_id}")
            else:
                # Add new connection
                session.add(conn)
                print(f"✓ Created new Airflow connection: {conn_id}")
            
            session.commit()
            
        # Test the connection
        test_connection(conn_id)
        
    except ImportError:
        print("⚠ Airflow not available - using environment variable method")
        setup_airflow_connection_via_env()
    except Exception as e:
        print(f"✗ Error setting up Airflow connection: {e}")
        print("⚠ Trying environment variable method as fallback")
        setup_airflow_connection_via_env()

def setup_airflow_connection_via_env():
    """
    Set up Airflow connection using environment variables as fallback
    """
    try:
        # Get Django's database configuration
        db_config = settings.DATABASES['default']
        
        # Create connection URI
        password = db_config.get('PASSWORD', '')
        password_part = f":{password}" if password else ""
        
        connection_uri = (
            f"postgresql://{db_config['USER']}{password_part}@"
            f"{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        )
        
        # Set environment variable
        os.environ['AIRFLOW_CONN_POSTGRES_DEFAULT'] = connection_uri
        
        print(f"✓ Set AIRFLOW_CONN_POSTGRES_DEFAULT environment variable")
        print(f"  Connection URI: postgresql://{db_config['USER']}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}")
        
    except Exception as e:
        print(f"✗ Error setting up environment variable: {e}")

def test_connection(conn_id='postgres_default'):
    """
    Test the Airflow database connection
    """
    try:
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        
        pg_hook = PostgresHook(postgres_conn_id=conn_id)
        
        # Test query
        result = pg_hook.get_first("SELECT 1 as test")
        
        if result and result[0] == 1:
            print(f"✓ Airflow connection test successful: {conn_id}")
            
            # Test BCMM data access
            bcmm_count = pg_hook.get_first("SELECT COUNT(*) FROM metering_raw.bcmm_hhr")
            print(f"✓ BCMM HHR data accessible: {bcmm_count[0]} records")
            
            return True
        else:
            print(f"✗ Airflow connection test failed: {conn_id}")
            return False
            
    except Exception as e:
        print(f"✗ Airflow connection test error: {e}")
        return False

def create_airflow_connection_cli():
    """
    Generate CLI command to create the connection manually
    """
    try:
        db_config = settings.DATABASES['default']
        
        password = db_config.get('PASSWORD', '')
        password_part = f" --conn-password '{password}'" if password else ""
        
        cli_command = (
            f"airflow connections add postgres_default "
            f"--conn-type postgres "
            f"--conn-host {db_config['HOST']} "
            f"--conn-port {db_config['PORT']} "
            f"--conn-schema {db_config['NAME']} "
            f"--conn-login {db_config['USER']}"
            f"{password_part}"
        )
        
        print(f"\nManual CLI command to create connection:")
        print(f"  {cli_command}")
        
    except Exception as e:
        print(f"✗ Error generating CLI command: {e}")

def main():
    """
    Main function to set up Airflow connections
    """
    print("Setting up Airflow Database Connections...")
    print("=" * 50)
    
    # Method 1: Try to set up connection directly in Airflow
    setup_airflow_postgres_connection()
    
    # Method 2: Generate CLI command for manual setup
    create_airflow_connection_cli()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("\nIf the automatic setup didn't work, you can:")
    print("1. Use the CLI command shown above")
    print("2. Set the environment variable in your Docker compose")
    print("3. Use the Airflow web UI to create the connection manually")

if __name__ == "__main__":
    main() 