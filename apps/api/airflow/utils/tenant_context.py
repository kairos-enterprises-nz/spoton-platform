"""
Tenant Context Utility for Airflow DAGs

Provides tenant-aware database connections and context management for multi-tenant DAGs.
Integrates with django-tenants and TimescaleDB Row-Level Security (RLS).

Author: SpotOn Data Team
"""

import os
import logging
import psycopg2
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TenantContextManager:
    """
    Manages tenant context for Airflow DAGs in a multi-tenant environment.
    
    Features:
    - Automatic tenant detection from environment variables
    - Row-Level Security (RLS) support for TimescaleDB
    - Backward compatibility for single-tenant setups
    - Connection pooling and management
    """
    
    def __init__(self):
        self.current_tenant_id = None
        self.current_tenant_slug = None
        self._connection_cache = {}
    
    def get_tenant_context(self) -> Dict[str, Any]:
        """
        Get current tenant context from environment variables or configuration.
        
        Environment Variables:
        - TENANT_ID: Explicit tenant ID (highest priority)
        - TENANT_SLUG: Tenant slug for lookup
        - UTILITY_NAME: Legacy utility name mapping
        
        Returns:
            Dict containing tenant information
        """
        # Method 1: Direct tenant ID from environment
        tenant_id = os.getenv('TENANT_ID')
        if tenant_id:
            try:
                tenant_id = int(tenant_id)
                self.current_tenant_id = tenant_id
                return self._get_tenant_info_by_id(tenant_id)
            except ValueError:
                logger.warning(f"Invalid TENANT_ID environment variable: {tenant_id}")
        
        # Method 2: Tenant slug from environment
        tenant_slug = os.getenv('TENANT_SLUG')
        if tenant_slug:
            self.current_tenant_slug = tenant_slug
            return self._get_tenant_info_by_slug(tenant_slug)
        
        # Method 3: Legacy UTILITY_NAME mapping
        utility_name = os.getenv('UTILITY_NAME')
        if utility_name:
            return self._get_tenant_info_by_utility_name(utility_name)
        
        # Method 4: Default tenant for backward compatibility
        logger.info("No tenant context found, using default tenant")
        return self._get_default_tenant_context()
    
    def _get_tenant_info_by_id(self, tenant_id: int) -> Dict[str, Any]:
        """Get tenant information by ID from database."""
        try:
            from .connection import get_connection
            
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, slug, contact_email, timezone, currency, is_active
                        FROM users_tenant 
                        WHERE id = %s AND is_active = true
                    """, [tenant_id])
                    
                    result = cursor.fetchone()
                    if result:
                        return {
                            'tenant_id': result[0],
                            'tenant_name': result[1],
                            'tenant_slug': result[2],
                            'contact_email': result[3],
                            'timezone': result[4],
                            'currency': result[5],
                            'is_active': result[6],
                            'schema_name': f"tenant_{result[2]}",
                        }
                    else:
                        logger.warning(f"Tenant ID {tenant_id} not found or inactive")
                        return self._get_default_tenant_context()
                        
        except Exception as e:
            logger.error(f"Failed to get tenant info by ID {tenant_id}: {e}")
            return self._get_default_tenant_context()
    
    def _get_tenant_info_by_slug(self, tenant_slug: str) -> Dict[str, Any]:
        """Get tenant information by slug from database."""
        try:
            from .connection import get_connection
            
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, slug, contact_email, timezone, currency, is_active
                        FROM users_tenant 
                        WHERE slug = %s AND is_active = true
                    """, [tenant_slug])
                    
                    result = cursor.fetchone()
                    if result:
                        self.current_tenant_id = result[0]
                        return {
                            'tenant_id': result[0],
                            'tenant_name': result[1],
                            'tenant_slug': result[2],
                            'contact_email': result[3],
                            'timezone': result[4],
                            'currency': result[5],
                            'is_active': result[6],
                            'schema_name': f"tenant_{result[2]}",
                        }
                    else:
                        logger.warning(f"Tenant slug '{tenant_slug}' not found or inactive")
                        return self._get_default_tenant_context()
                        
        except Exception as e:
            logger.error(f"Failed to get tenant info by slug {tenant_slug}: {e}")
            return self._get_default_tenant_context()
    
    def _get_tenant_info_by_utility_name(self, utility_name: str) -> Dict[str, Any]:
        """Get tenant information by legacy utility name mapping."""
        # Legacy mapping for backward compatibility
        utility_mappings = {
            'spotone': 'spoton-energy',
            'utility-byte': 'utility-byte-default',
            'test': 'test-utility',
            # Add more mappings as needed
        }
        
        tenant_slug = utility_mappings.get(utility_name.lower(), utility_name.lower())
        logger.info(f"Mapping utility name '{utility_name}' to tenant slug '{tenant_slug}'")
        
        return self._get_tenant_info_by_slug(tenant_slug)
    
    def _get_default_tenant_context(self) -> Dict[str, Any]:
        """Get default tenant context for backward compatibility."""
        return {
            'tenant_id': 1,
            'tenant_name': 'Default Utility',
            'tenant_slug': 'default',
            'contact_email': '',
            'timezone': 'Pacific/Auckland',
            'currency': 'NZD',
            'is_active': True,
            'schema_name': 'public',
        }
    
    @contextmanager
    def tenant_connection(self, tenant_context: Optional[Dict[str, Any]] = None):
        """
        Get a database connection with tenant context set for RLS.
        
        Args:
            tenant_context: Optional tenant context. If None, will auto-detect.
            
        Yields:
            psycopg2 connection with tenant context set
        """
        if tenant_context is None:
            tenant_context = self.get_tenant_context()
        
        from .connection import get_connection
        
        conn = get_connection()
        try:
            # Set tenant context for Row-Level Security
            tenant_id = tenant_context['tenant_id']
            with conn.cursor() as cursor:
                cursor.execute("SET app.current_tenant_id = %s", [tenant_id])
                logger.debug(f"Set tenant context: tenant_id={tenant_id}")
            
            yield conn
            
        except Exception as e:
            logger.error(f"Error in tenant connection: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def set_tenant_context_for_connection(self, conn, tenant_context: Optional[Dict[str, Any]] = None):
        """
        Set tenant context on an existing connection.
        
        Args:
            conn: psycopg2 connection
            tenant_context: Optional tenant context. If None, will auto-detect.
        """
        if tenant_context is None:
            tenant_context = self.get_tenant_context()
        
        tenant_id = tenant_context['tenant_id']
        with conn.cursor() as cursor:
            cursor.execute("SET app.current_tenant_id = %s", [tenant_id])
            logger.debug(f"Set tenant context on existing connection: tenant_id={tenant_id}")
    
    def get_tenant_data_path(self, tenant_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get tenant-specific data path for file operations.
        
        Args:
            tenant_context: Optional tenant context. If None, will auto-detect.
            
        Returns:
            Path string for tenant data directory
        """
        if tenant_context is None:
            tenant_context = self.get_tenant_context()
        
        tenant_slug = tenant_context['tenant_slug']
        base_path = os.getenv('DATA_PATH', '/data')
        
        return f"{base_path}/tenants/{tenant_slug}"
    
    def log_tenant_activity(self, activity: str, details: Dict[str, Any] = None, 
                           tenant_context: Optional[Dict[str, Any]] = None):
        """
        Log tenant-specific activity for auditing.
        
        Args:
            activity: Description of the activity
            details: Additional details to log
            tenant_context: Optional tenant context. If None, will auto-detect.
        """
        if tenant_context is None:
            tenant_context = self.get_tenant_context()
        
        log_entry = {
            'tenant_id': tenant_context['tenant_id'],
            'tenant_slug': tenant_context['tenant_slug'],
            'activity': activity,
            'details': details or {},
            'timestamp': logger.handlers[0].format(logger.makeRecord(
                logger.name, logging.INFO, __file__, 0, "", (), None
            )) if logger.handlers else None
        }
        
        logger.info(f"[Tenant: {tenant_context['tenant_slug']}] {activity}", extra=log_entry)


# Global instance for easy access
tenant_manager = TenantContextManager()


# Convenience functions for DAGs
def get_tenant_context() -> Dict[str, Any]:
    """Get current tenant context."""
    return tenant_manager.get_tenant_context()


def get_tenant_connection(tenant_context: Optional[Dict[str, Any]] = None):
    """Get a tenant-aware database connection."""
    return tenant_manager.tenant_connection(tenant_context)


def set_tenant_context(conn, tenant_context: Optional[Dict[str, Any]] = None):
    """Set tenant context on an existing connection."""
    return tenant_manager.set_tenant_context_for_connection(conn, tenant_context)


def get_tenant_data_path(tenant_context: Optional[Dict[str, Any]] = None) -> str:
    """Get tenant-specific data path."""
    return tenant_manager.get_tenant_data_path(tenant_context)


def log_tenant_activity(activity: str, details: Dict[str, Any] = None, 
                       tenant_context: Optional[Dict[str, Any]] = None):
    """Log tenant-specific activity."""
    return tenant_manager.log_tenant_activity(activity, details, tenant_context)


# Backward compatibility functions
def get_legacy_connection():
    """
    DEPRECATED: Use get_tenant_connection() instead.
    Provides backward compatibility for existing DAGs.
    """
    logger.warning("get_legacy_connection() is deprecated. Use get_tenant_connection() instead.")
    return get_tenant_connection()


def ensure_tenant_schemas(tenant_context: Optional[Dict[str, Any]] = None):
    """
    Ensure tenant-specific schemas exist.
    
    Args:
        tenant_context: Optional tenant context. If None, will auto-detect.
    """
    if tenant_context is None:
        tenant_context = get_tenant_context()
    
    schemas = ['metering_processed', 'wits', 'metering_raw']
    
    with get_tenant_connection(tenant_context) as conn:
        try:
            with conn.cursor() as cursor:
                for schema in schemas:
                    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                    logger.info(f"✅ Schema '{schema}' ensured for tenant {tenant_context['tenant_slug']}")
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to ensure schemas for tenant {tenant_context['tenant_slug']}: {e}")
            conn.rollback()
            raise


def get_all_active_tenants() -> List[Dict[str, Any]]:
    """
    Get list of all active tenants for multi-tenant DAG processing.
    
    Returns:
        List of tenant context dictionaries
    """
    try:
        from .connection import get_connection
        
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, slug, contact_email, timezone, currency, is_active
                    FROM users_tenant 
                    WHERE is_active = true
                    ORDER BY name
                """)
                
                tenants = []
                for result in cursor.fetchall():
                    tenants.append({
                        'tenant_id': result[0],
                        'tenant_name': result[1],
                        'tenant_slug': result[2],
                        'contact_email': result[3],
                        'timezone': result[4],
                        'currency': result[5],
                        'is_active': result[6],
                        'schema_name': f"tenant_{result[2]}",
                    })
                
                return tenants
                
    except Exception as e:
        logger.error(f"Failed to get active tenants: {e}")
        return [tenant_manager._get_default_tenant_context()] 