from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.invoices.models import Invoice


class Command(BaseCommand):
    help = 'Book finalized invoices (immutable)'

    def handle(self, *args, **options):
        updated = 0
        for inv in Invoice.objects.filter(status='finalized'):
            inv.status = 'booked'
            inv.booked_at = timezone.now()
            inv.save(update_fields=['status', 'booked_at'])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Booked {updated} invoices'))

