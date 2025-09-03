from datetime import date, timedelta

def is_business_day(d, public_holidays):
    """
    Checks if a given date is a business day (not a weekend or public holiday).
    """
    if d.weekday() >= 5:  # Monday is 0 and Sunday is 6
        return False
    if d in public_holidays:
        return False
    return True

def calculate_business_day_delta(start_date, end_date, public_holidays):
    """
    Calculates the number of business days between two dates, excluding weekends
    and specified public holidays.
    """
    if start_date > end_date:
        return 0

    business_days = 0
    current_date = start_date.date() if hasattr(start_date, 'date') else start_date
    final_date = end_date.date() if hasattr(end_date, 'date') else end_date

    # Don't count the start day itself, count the days *between*
    current_date += timedelta(days=1)

    while current_date <= final_date:
        if is_business_day(current_date, public_holidays):
            business_days += 1
        current_date += timedelta(days=1)

    return business_days 