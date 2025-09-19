"""
Management command to ensure all required PostgreSQL schemas exist
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Ensure all required PostgreSQL schemas exist'
    
    def handle(self, *args, **options):
        schemas = [
            'users',
            'contracts', 
            'energy',
            'finance',
            'support',
            'metering',
        ]
        
        with connection.cursor() as cursor:
            for schema in schemas:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Schema "{schema}" ensured')
                )
        
        self.stdout.write(
            self.style.SUCCESS('All schemas created successfully!')
        )
