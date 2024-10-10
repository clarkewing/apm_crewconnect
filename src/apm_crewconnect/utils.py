from datetime import date, timedelta


def date_in_range(date: date, start: date, end: date) -> bool:
    if date >= start and date <= end:
        return True

    return False


def dates_in_range(dates: list[date], start: date, end: date) -> bool:
    return any(date_in_range(date, start, end) for date in dates)


def date_range(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("End date must come after start date")
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]
