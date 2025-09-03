from __future__ import annotations

from django.core.management.base import BaseCommand

from finance.invoices.models import Invoice
from finance.invoices.accounting_sync import XeroSandboxProvider


class Command(BaseCommand):
    help = 'Stub sync of accounting status for invoices'

    def add_arguments(self, parser):
        parser.add_argument('--since')

    def handle(self, *args, **options):
        provider = XeroSandboxProvider()
        changed = 0
        for inv in Invoice.objects.filter(external_accounting_id=''):
            result = provider.push_invoice(inv)
            if result.success and result.external_id:
                inv.external_accounting_id = result.external_id
                inv.save(update_fields=['external_accounting_id'])
                changed += 1
        self.stdout.write(self.style.SUCCESS(f'Updated accounting IDs for {changed} invoices'))

