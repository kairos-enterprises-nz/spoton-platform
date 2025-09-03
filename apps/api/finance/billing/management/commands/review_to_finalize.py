from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.invoices.models import Invoice


class Command(BaseCommand):
    help = 'Transition invoices from review to finalized and booked'

    def add_arguments(self, parser):
        parser.add_argument('--finalize', action='store_true')
        parser.add_argument('--book', action='store_true')

    def handle(self, *args, **options):
        finalize = options['finalize']
        book = options['book']

        updated = 0
        for inv in Invoice.objects.filter(status__in=['review', 'draft']):
            if finalize:
                inv.status = 'finalized'
                inv.finalized_at = timezone.now()
            if book and inv.status == 'finalized':
                inv.status = 'booked'
                inv.booked_at = timezone.now()
            inv.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} invoices'))

