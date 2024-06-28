from datetime import date


def date_in_range(date: date, start: date, end: date) -> bool:
    if date >= start and date <= end:
        return True

    return False


def dates_in_range(dates: list[date], start: date, end: date) -> bool:
    return any(date_in_range(date, start, end) for date in dates)
