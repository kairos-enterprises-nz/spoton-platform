"""
Simplified database router for django-tenants + TimescaleDB architecture.
All ORM models are in public schema (managed by django-tenants).
Only TimescaleDB routing is needed for time-series data.
"""

class DatabaseRouter:
    """
    Database router for django-tenants + TimescaleDB setup.
    
    - All ORM models: public schema (django-tenants managed)
    - Time-series data: TimescaleDB (non-ORM)
    """
    
    def db_for_read(self, model, **hints):
        """All ORM reads go to default database."""
        return 'default'
    
    def db_for_write(self, model, **hints):
        """All ORM writes go to default database."""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow all relations since everything is in the same database."""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All Django migrations go to default database.
        TimescaleDB is managed separately.
        """
        if db == 'default':
            return True
        elif db == 'timescaledb':
            # No Django migrations for TimescaleDB
            return False
        return None