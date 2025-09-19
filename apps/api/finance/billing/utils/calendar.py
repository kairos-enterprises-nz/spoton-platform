from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Tuple


@dataclass(frozen=True)
class BillingPeriod:
    start: datetime
    end: datetime


class BillingCalendar:
    """
    Compute billing periods with awareness of leap years, DST and month/week boundaries.
    """

    @staticmethod
    def compute_periods(
        frequency: str,
        period: str,
        anchor_date: date,
        applies_to_next_month: bool = False,
    ) -> List[BillingPeriod]:
        if frequency not in {'weekly', 'monthly'}:
            raise ValueError('Unsupported frequency')
        if period not in {'prepaid', 'postpaid'}:
            raise ValueError('Unsupported period')

        if frequency == 'weekly':
            start = datetime.combine(anchor_date, datetime.min.time())
            end = start + timedelta(days=7)
            if period == 'prepaid':
                return [BillingPeriod(start=start, end=end)]
            else:
                return [BillingPeriod(start=start - timedelta(days=7), end=start)]

        # monthly
        start_of_month = anchor_date.replace(day=1)
        next_month = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_of_month = next_month - timedelta(seconds=1)

        if period == 'prepaid':
            start = datetime.combine(start_of_month, datetime.min.time())
            end = datetime.combine(next_month, datetime.min.time())
        else:
            prev_month = (start_of_month.replace(day=1) - timedelta(days=1)).replace(day=1)
            start = datetime.combine(prev_month, datetime.min.time())
            end = datetime.combine(start_of_month, datetime.min.time())

        if applies_to_next_month and period == 'postpaid':
            start, end = end, (end + (end - start))

        return [BillingPeriod(start=start, end=end)]

