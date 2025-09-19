from __future__ import annotations

from django.core.management.base import BaseCommand
from finance.billing.models import Bill
from finance.invoices.models import Invoice, InvoiceLine


class Command(BaseCommand):
    help = 'Generate draft invoices for Bills without an Invoice'

    def add_arguments(self, parser):
        parser.add_argument('--service', choices=['electricity', 'broadband', 'mobile'])
        parser.add_argument('--date')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        qs = Bill.objects.all()
        dry_run = options['dry_run']

        count = 0
        for bill in qs:
            if hasattr(bill, 'invoice'):
                continue
            if dry_run:
                self.stdout.write(f'DRY-RUN would create invoice for {bill.bill_number}')
                continue

            invoice = Invoice.objects.create(
                tenant=bill.tenant,
                bill=bill,
                customer=bill.customer,
                invoice_number=f'INV-{bill.bill_number}',
                status='draft',
                payment_status='unpaid',
                issue_date=bill.issue_date,
                due_date=bill.due_date,
                subtotal=bill.subtotal,
                tax_amount=bill.tax_amount,
                total_amount=bill.total_amount,
                amount_paid=bill.amount_paid,
                amount_due=bill.amount_due,
            )

            for li in bill.line_items.all():
                InvoiceLine.objects.create(
                    tenant=bill.tenant,
                    invoice=invoice,
                    description=li.description,
                    service_type=li.service_type,
                    quantity=li.quantity,
                    unit=li.unit,
                    unit_price=li.unit_price,
                    amount=li.amount,
                    service_period_start=li.service_period_start,
                    service_period_end=li.service_period_end,
                    is_taxable=li.is_taxable,
                    tax_rate=li.tax_rate,
                    tax_amount=li.tax_amount,
                    sort_order=li.sort_order,
                    section_header=li.section_header,
                )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {count} draft invoices'))

