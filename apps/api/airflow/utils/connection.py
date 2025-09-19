"""
Database connection utility for Airflow DAGs.
Provides connection management for the utilitybyte database.
"""

import os
import psycopg2
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_connection():
    """
    Get database connection to utilitybyte database.
    Provides consistent connection management across all DAGs.
    """
    try:
        # Try to use Airflow connection first
        from airflow.hooks.base import BaseHook
        conn = BaseHook.get_connection('utilitybyte_default')
        return psycopg2.connect(
            host=conn.host,
            port=conn.port,
            database=conn.schema,
            user=conn.login,
            password=conn.password
        )
    except Exception as e:
        logger.warning(f"Airflow connection failed, using environment variables: {e}")
        # Fallback to environment variables
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'db'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'utilitybyte'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'pick.pock')
        )


def get_connection_config() -> dict:
    """Get database connection configuration as dictionary."""
    try:
        from airflow.hooks.base import BaseHook
        conn = BaseHook.get_connection('utilitybyte_default')
        return {
            'host': conn.host,
            'port': conn.port,
            'database': conn.schema,
            'user': conn.login,
            'password': conn.password
        }
    except:
        return {
            'host': os.getenv('DB_HOST', 'db'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'utilitybyte'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'pick.pock')
        }


def test_connection() -> bool:
    """Test database connection."""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        conn.close()
        return result[0] == 1
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def ensure_schemas():
    """Ensure all required schemas exist in the unified database."""
    schemas = ['metering_processed', 'wits', 'metering_raw']
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for schema in schemas:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                logger.info(f"✅ Schema '{schema}' ensured")
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to ensure schemas: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_schema_table_count(schema: str) -> int:
    """Get number of tables in a specific schema."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, [schema])
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"❌ Failed to get table count for schema {schema}: {e}")
        return 0
    finally:
        conn.close()


def verify_timescaledb_extension() -> bool:
    """Verify TimescaleDB extension is installed and available."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
                )
            """)
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"❌ Failed to verify TimescaleDB extension: {e}")
        return False
    finally:
        conn.close()


def get_hypertable_info() -> list:
    """Get information about existing hypertables."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    num_chunks,
                    compression_enabled
                FROM timescaledb_information.hypertables
                ORDER BY schemaname, tablename
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"❌ Failed to get hypertable info: {e}")
        return []
    finally:
        conn.close()


# Legacy compatibility - deprecated functions for migration
def get_timescale_connection():
    """
    DEPRECATED: Use get_connection() instead.
    Kept for backward compatibility during migration.
    """
    logger.warning("get_timescale_connection() is deprecated. Use get_connection() instead.")
    return get_connection()

# Legacy alias for backward compatibility
def get_unified_connection():
    """
    DEPRECATED: Use get_connection() instead.
    Legacy alias maintained for backward compatibility.
    """
    logger.warning("get_unified_connection() is deprecated. Use get_connection() instead.")
    return get_connection() 