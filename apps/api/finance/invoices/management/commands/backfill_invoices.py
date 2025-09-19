from __future__ import annotations

from datetime import datetime
from django.core.management.base import BaseCommand

from finance.invoices.models import Invoice


class Command(BaseCommand):
    help = 'Backfill invoices in dry-run mode to preview outputs'

    def add_arguments(self, parser):
        parser.add_argument('--service', required=True)
        parser.add_argument('--from', dest='from_date', required=True)
        parser.add_argument('--to', dest='to_date', required=True)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        from_date = datetime.fromisoformat(options['from_date']).date()
        to_date = datetime.fromisoformat(options['to_date']).date()
        dry_run = options['dry_run']
        service = options['service']

        self.stdout.write(f"Backfill window {from_date} -> {to_date} for {service}")
        # Placeholder: just report existing counts
        count = Invoice.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Existing invoices: {count}; dry-run only in this stub"))

