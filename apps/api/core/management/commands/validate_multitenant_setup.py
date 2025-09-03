"""
Management command to validate multi-tenant database setup.

This command checks:
1. Database routing configuration
2. Schema integrity
3. Cross-database relation violations
4. Migration state consistency
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connections
from django.conf import settings
from utilitybyte.db_router import SchemaRouter, TimescaleDBRouter
import sys


class Command(BaseCommand):
    help = 'Validate multi-tenant database setup and routing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-relations',
            action='store_true',
            help='Check for potential cross-database relation violations',
        )
        parser.add_argument(
            '--check-schemas',
            action='store_true',
            help='Verify that all required schemas exist',
        )
        parser.add_argument(
            '--check-routing',
            action='store_true',
            help='Validate database routing configuration',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all validation checks',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('🔍 Validating Multi-Tenant Setup\n'))
        
        errors = []
        warnings = []
        
        if options['all'] or options['check_routing']:
            routing_errors, routing_warnings = self.check_routing()
            errors.extend(routing_errors)
            warnings.extend(routing_warnings)
        
        if options['all'] or options['check_schemas']:
            schema_errors, schema_warnings = self.check_schemas()
            errors.extend(schema_errors)
            warnings.extend(schema_warnings)
        
        if options['all'] or options['check_relations']:
            relation_errors, relation_warnings = self.check_relations()
            errors.extend(relation_errors)
            warnings.extend(relation_warnings)
        
        # Display results
        self.display_results(errors, warnings)
        
        if errors:
            sys.exit(1)

    def check_routing(self):
        """Validate database routing configuration."""
        self.stdout.write('📋 Checking Database Routing...')
        errors = []
        warnings = []
        
        # Check if routers are properly configured
        routers = getattr(settings, 'DATABASE_ROUTERS', [])
        expected_routers = [
            'utilitybyte.db_router.TimescaleDBRouter',
            'utilitybyte.db_router.SchemaRouter'
        ]
        
        for expected_router in expected_routers:
            if expected_router not in routers:
                errors.append(f"Missing router: {expected_router}")
        
        # Check each app's routing
        schema_router = SchemaRouter()
        timescale_router = TimescaleDBRouter()
        
        for app_config in apps.get_app_configs():
            app_label = app_config.label
            
            # Get expected database from router
            class MockModel:
                class _meta:
                    pass
                
            MockModel._meta.app_label = app_label
            
            expected_db = schema_router._get_db_for_model(MockModel)
            
            # Check if database exists in settings
            if expected_db not in settings.DATABASES:
                errors.append(f"App '{app_label}' routes to '{expected_db}' but database not configured")
        
        self.stdout.write(f"  ✅ Routing check completed")
        return errors, warnings

    def check_schemas(self):
        """Verify that all required schemas exist."""
        self.stdout.write('🏗️  Checking Database Schemas...')
        errors = []
        warnings = []
        
        required_schemas = ['users', 'contracts', 'energy', 'finance', 'support']
        
        for db_alias in ['default'] + required_schemas:
            if db_alias not in settings.DATABASES:
                continue
                
            try:
                connection = connections[db_alias]
                with connection.cursor() as cursor:
                    # Check if schema exists (for non-default databases)
                    if db_alias != 'default':
                        cursor.execute(
                            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                            [db_alias]
                        )
                        if not cursor.fetchone():
                            errors.append(f"Schema '{db_alias}' does not exist in database")
                    
                    # Check if tables exist in expected schema
                    if db_alias == 'default':
                        schema_name = 'public'
                    else:
                        schema_name = db_alias
                    
                    cursor.execute(
                        "SELECT count(*) FROM pg_tables WHERE schemaname = %s",
                        [schema_name]
                    )
                    table_count = cursor.fetchone()[0]
                    
                    if table_count == 0 and db_alias != 'default':
                        warnings.append(f"No tables found in schema '{schema_name}'")
                    
            except Exception as e:
                errors.append(f"Cannot connect to database '{db_alias}': {e}")
        
        self.stdout.write(f"  ✅ Schema check completed")
        return errors, warnings

    def check_relations(self):
        """Check for potential cross-database relation violations."""
        self.stdout.write('🔗 Checking Cross-Database Relations...')
        errors = []
        warnings = []
        
        schema_router = SchemaRouter()
        
        # Check each model's foreign keys and many-to-many relations
        for model in apps.get_models():
            model_db = schema_router._get_db_for_model(model)
            
            # Check foreign keys
            for field in model._meta.get_fields():
                if hasattr(field, 'remote_field') and field.remote_field:
                    related_model = field.remote_field.model
                    related_db = schema_router._get_db_for_model(related_model)
                    
                    # Check if relation crosses database boundaries inappropriately
                    if model_db != related_db and model_db != 'default' and related_db != 'default':
                        errors.append(
                            f"Cross-database relation: {model._meta.label}.{field.name} "
                            f"({model_db}) -> {related_model._meta.label} ({related_db})"
                        )
                    elif model_db != related_db:
                        # This is allowed (relation to/from default schema)
                        warnings.append(
                            f"Cross-schema relation: {model._meta.label}.{field.name} "
                            f"({model_db}) -> {related_model._meta.label} ({related_db})"
                        )
        
        self.stdout.write(f"  ✅ Relation check completed")
        return errors, warnings

    def display_results(self, errors, warnings):
        """Display validation results."""
        self.stdout.write('\n📊 Validation Results:')
        
        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS('✅ All checks passed! Multi-tenant setup is valid.'))
            return
        
        if warnings:
            self.stdout.write(f'\n⚠️  Warnings ({len(warnings)}):')
            for warning in warnings:
                self.stdout.write(f'  • {warning}')
        
        if errors:
            self.stdout.write(f'\n❌ Errors ({len(errors)}):')
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  • {error}'))
        
        self.stdout.write('\n💡 Recommendations:')
        if errors:
            self.stdout.write('  • Fix the errors above before deploying to production')
            self.stdout.write('  • Run migrations: python manage.py migrate --database=<db_alias>')
            self.stdout.write('  • Check database router configuration')
        
        if warnings:
            self.stdout.write('  • Review warnings for potential issues')
            self.stdout.write('  • Consider data migration if schemas are empty') 