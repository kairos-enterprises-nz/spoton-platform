from __future__ import annotations

from django.core.management.base import BaseCommand

from finance.invoices.models import Invoice
from finance.invoices.pdf.generate_invoice_runtime import render_from_invoice


class Command(BaseCommand):
    help = 'Stub PDF generation for invoices (marks flag and sets path)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        changed = 0
        for inv in Invoice.objects.filter(is_pdf_generated=False):
            if dry_run:
                self.stdout.write(f'DRY-RUN would generate PDF for {inv.invoice_number}')
                continue
            # Phase A: broadband-only renderer; fall back to simple path for others
            try:
                if inv.lines.filter(service_type='broadband').exists():
                    # Strictly use the generate_invoice.py design
                    pdf_path = render_from_invoice(str(inv.id))
                else:
                    pdf_path = f"/app/media/invoices/{inv.invoice_number}.pdf"
                inv.pdf_file_path = pdf_path
                inv.is_pdf_generated = True
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'PDF generation failed for {inv.invoice_number}: {exc}'))
                continue
            inv.save(update_fields=['pdf_file_path', 'is_pdf_generated'])
            changed += 1
        self.stdout.write(self.style.SUCCESS(f'Generated PDFs for {changed} invoices'))

