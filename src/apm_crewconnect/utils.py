from datetime import date, timedelta, timezone


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


def timedelta_to_str(timedelta: timedelta, format: str = "{}:{:02}") -> str:
    total_seconds = timedelta.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return format.format(int(hours), int(minutes))


def timezone_to_offset_str(tz: timezone) -> str:
    total_seconds = tz.utcoffset(None).total_seconds()
    sign = "+" if total_seconds >= 0 else "-"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return sign + "{:02}{:02}".format(int(hours), int(minutes))
