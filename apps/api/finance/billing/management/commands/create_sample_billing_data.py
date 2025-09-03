from __future__ import annotations

from datetime import date
from django.core.management.base import BaseCommand

from finance.billing.models import Bill
from finance.billing.models_registry import ServiceRegistry
from finance.invoices.models import Invoice


class Command(BaseCommand):
    help = 'Create sample data: seed registry, calculate bills, generate invoices and PDFs (UAT)'

    def add_arguments(self, parser):
        parser.add_argument('--anchor', default=date.today().isoformat())
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        anchor = options['anchor']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('Seeding service registry'))
        self.call_command('seed_service_registry')

        for service in ['electricity', 'broadband', 'mobile']:
            self.stdout.write(self.style.SUCCESS(f'Calculating bills for {service}'))
            self.call_command('calculate_bills', f'--service={service}', f'--date={anchor}', *(['--dry-run'] if dry_run else []))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Generating draft invoices'))
            self.call_command('generate_draft_invoices')
            self.stdout.write(self.style.SUCCESS('Generating PDFs'))
            self.call_command('generate_pdfs')

        self.stdout.write(self.style.SUCCESS('Sample data setup complete'))

    def call_command(self, name: str, *args):
        from django.core.management import call_command
        call_command(name, *args)

