from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.invoices.models import Invoice


class Command(BaseCommand):
    help = 'Stub email sending for invoices (marks emailed)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        changed = 0
        for inv in Invoice.objects.filter(is_pdf_generated=True, is_emailed=False):
            if dry_run:
                self.stdout.write(f'DRY-RUN would email {inv.invoice_number}')
                continue
            inv.is_emailed = True
            inv.emailed_at = timezone.now()
            inv.save(update_fields=['is_emailed', 'emailed_at'])
            changed += 1
        self.stdout.write(self.style.SUCCESS(f'Emailed {changed} invoices'))

