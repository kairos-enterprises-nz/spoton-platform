from __future__ import annotations

from django.core.management.base import BaseCommand

from finance.invoices.management.commands.generate_pdfs import Command as InvoicePdfCommand


class Command(BaseCommand):
    help = 'Proxy to invoice PDF generation for convenience'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        return InvoicePdfCommand().handle(*args, **options)

