from __future__ import annotations

from django.core.management.base import BaseCommand

from finance.invoices.management.commands.generate_draft_invoices import Command as InvoiceDraftCommand


class Command(BaseCommand):
    help = 'Proxy to invoice draft generation for convenience'

    def add_arguments(self, parser):
        parser.add_argument('--service', choices=['electricity', 'broadband', 'mobile'])
        parser.add_argument('--date')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        return InvoiceDraftCommand().handle(*args, **options)

