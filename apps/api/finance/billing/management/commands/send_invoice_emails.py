from __future__ import annotations

from django.core.management.base import BaseCommand

from finance.invoices.management.commands.send_invoice_emails import Command as InvoiceEmailCommand


class Command(BaseCommand):
    help = 'Proxy to invoice email sending for convenience'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        return InvoiceEmailCommand().handle(*args, **options)

