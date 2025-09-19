"""
Custom PostgreSQL backend with schema routing support
"""
from django.db.backends.postgresql import base
from django.db.backends.postgresql.schema import DatabaseSchemaEditor


class DatabaseSchemaEditor(DatabaseSchemaEditor):
    """
    Custom schema editor that creates tables in appropriate schemas
    """
    
    def _get_schema_for_model(self, model):
        """
        Determine which schema a model should be created in based on its app
        """
        app_label = model._meta.app_label
        
        schema_mapping = {
            'users': 'users',
            'user_details': 'users',
            'contracts': 'contracts',
            'billing': 'finance',
            'pricing': 'finance',
            'connections': 'energy',
            'tariffs': 'energy',
            'tariff_profile': 'energy',
            'validation': 'energy',
            'export_core': 'energy',
            'metering': 'metering',
            'address_plans': 'support',
            'public_pricing': 'support',
        }
        
        return schema_mapping.get(app_label, 'public')
    
    def _create_table_sql(self, model):
        """
        Override table creation to use proper schema
        """
        schema = self._get_schema_for_model(model)
        table_name = model._meta.db_table
        
        # If schema is not public, prefix the table name with schema
        if schema != 'public':
            # Remove any existing schema prefix from table name
            if '.' in table_name:
                table_name = table_name.split('.')[-1]
            model._meta.db_table = f'{schema}.{table_name}'
        
        return super()._create_table_sql(model)


class DatabaseWrapper(base.DatabaseWrapper):
    """
    Custom PostgreSQL database wrapper with schema support
    """
    SchemaEditorClass = DatabaseSchemaEditor
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure schemas exist
        self._ensure_schemas_exist()
    
    def _ensure_schemas_exist(self):
        """
        Ensure all required schemas exist
        """
        schemas = ['users', 'contracts', 'energy', 'finance', 'support', 'metering']
        
        with self.cursor() as cursor:
            for schema in schemas:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}") 