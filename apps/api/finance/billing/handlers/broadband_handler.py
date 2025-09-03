from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Tuple

from django.utils import timezone
from finance.billing.models import Bill, BillLineItem


def calculate_bill(contract_id: str, period_start: datetime, period_end: datetime) -> Tuple[Bill, list[BillLineItem]]:
    """
    Stub broadband billing calculation (monthly, prepaid)
    """
    subtotal = Decimal('59.00')
    tax_amount = Decimal('8.85')
    total = subtotal + tax_amount

    bill = Bill(
        bill_number=f"BB-{int(period_start.timestamp())}-{contract_id}",
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
        description="Broadband monthly plan",
        service_type='broadband',
        quantity=Decimal('1.0000'),
        unit='month',
        unit_price=subtotal,
        amount=subtotal,
        is_taxable=True,
        tax_rate=Decimal('0.1500'),
        tax_amount=tax_amount,
        sort_order=1,
        service_period_start=period_start,
        service_period_end=period_end,
    )

    return bill, [line]

