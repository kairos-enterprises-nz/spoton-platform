from __future__ import annotations

from django.core.management.base import BaseCommand

from finance.billing.models_registry import ServiceRegistry


class Command(BaseCommand):
    help = 'Seed ServiceRegistry with default P/I/M services and handler paths'

    def handle(self, *args, **options):
        entries = [
            {
                'service_code': 'electricity',
                'name': 'Electricity',
                'billing_type': 'postpaid',
                'frequency': 'weekly',
                'period': 'postpaid',
                'applies_to_next_month': False,
                'billing_handler': 'finance.billing.handlers.electricity_handler.calculate_bill',
                'tariff_handler': '',
            },
            {
                'service_code': 'broadband',
                'name': 'Broadband',
                'billing_type': 'prepaid',
                'frequency': 'monthly',
                'period': 'prepaid',
                'applies_to_next_month': False,
                'billing_handler': 'finance.billing.handlers.broadband_handler.calculate_bill',
                'tariff_handler': '',
            },
            {
                'service_code': 'mobile',
                'name': 'Mobile',
                'billing_type': 'prepaid',
                'frequency': 'monthly',
                'period': 'prepaid',
                'applies_to_next_month': False,
                'billing_handler': 'finance.billing.handlers.mobile_handler.calculate_bill',
                'tariff_handler': '',
            },
        ]

        created = 0
        for e in entries:
            obj, was_created = ServiceRegistry.objects.update_or_create(
                tenant=None,
                service_code=e['service_code'],
                defaults=e,
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} new registry entries'))

