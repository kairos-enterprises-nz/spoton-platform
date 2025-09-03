from __future__ import annotations

from datetime import datetime, timedelta
from importlib import import_module
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finance.billing.models import Bill, BillLineItem, BillingRun
from finance.billing.models_registry import ServiceRegistry


class Command(BaseCommand):
    help = 'Calculate bills for a given service and date'

    def add_arguments(self, parser):
        parser.add_argument('--service', required=True, choices=['electricity', 'broadband', 'mobile'])
        parser.add_argument('--date', required=True, help='Anchor date YYYY-MM-DD')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        service = options['service']
        anchor_date = datetime.fromisoformat(options['date']).date()
        dry_run: bool = options['dry_run']

        registry: Optional[ServiceRegistry] = ServiceRegistry.objects.filter(service_code=service, is_active=True).first()
        if not registry:
            raise CommandError(f'No active ServiceRegistry entry for {service}')

        module_path, func_name = registry.billing_handler.rsplit('.', 1)
        handler_module = import_module(module_path)
        handler_func = getattr(handler_module, func_name)

        # Simple period window for stub: one week/month anchored on given date
        if registry.frequency == 'weekly':
            period_start = datetime.combine(anchor_date, datetime.min.time())
            period_end = period_start + timedelta(days=7)
        else:
            start_of_month = anchor_date.replace(day=1)
            next_month = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_start = datetime.combine(start_of_month, datetime.min.time())
            period_end = datetime.combine(next_month, datetime.min.time())

        self.stdout.write(self.style.SUCCESS(f'Calculating {service} bills for {period_start.date()} to {period_end.date()}'))

        # For UAT sample: use fake contract_ids 1..3
        for contract_id in ['C1', 'C2', 'C3']:
            bill, items = handler_func(contract_id, period_start, period_end)
            if dry_run:
                self.stdout.write(f'DRY-RUN would create bill {bill.bill_number} with {len(items)} item(s)')
                continue

            bill.save()
            for item in items:
                item.bill = bill
                item.save()

        self.stdout.write(self.style.SUCCESS('Billing calculation complete'))

