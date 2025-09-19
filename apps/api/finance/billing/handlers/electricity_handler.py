from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Tuple

from django.utils import timezone
from finance.billing.models import Bill, BillLineItem, BillingRun
from finance.pricing.models import ServicePlan, Tariff


def calculate_bill(contract_id: str, period_start: datetime, period_end: datetime) -> Tuple[Bill, list[BillLineItem]]:
    """
    Stub electricity billing calculation (weekly, postpaid)
    """
    # Placeholder deterministic values for UAT sample data
    subtotal = Decimal('42.00')
    tax_amount = Decimal('6.30')
    total = subtotal + tax_amount

    bill = Bill(
        bill_number=f"ELEC-{int(period_start.timestamp())}-{contract_id}",
        period_start=period_start,
        period_end=period_end,
        issue_date=timezone.now(),
        due_date=timezone.now(),
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total,
        amount_due=total,
    )

    line = BillLineItem(
        description="Electricity usage",
        service_type='electricity',
        quantity=Decimal('100.0000'),
        unit='kWh',
        unit_price=Decimal('0.420000'),
        amount=subtotal,
        is_taxable=True,
        tax_rate=Decimal('0.1500'),
        tax_amount=tax_amount,
        sort_order=1,
        service_period_start=period_start,
        service_period_end=period_end,
    )

    return bill, [line]

