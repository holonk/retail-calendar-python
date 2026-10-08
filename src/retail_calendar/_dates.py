"""Small date helpers. All arithmetic is on naive ``datetime.date`` values, so there is no timezone or DST effect."""

import calendar
import datetime as dt

ONE_DAY = dt.timedelta(days=1)
ONE_WEEK = dt.timedelta(weeks=1)


def to_date(value: dt.date) -> dt.date:
    """Drop the time part of a ``datetime`` (including ``pandas.Timestamp``) so it compares with ``date``."""
    return value.date() if isinstance(value, dt.datetime) else value


def end_of_month(year: int, month: int) -> dt.date:
    """Last day of the given 1-based month."""
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def with_iso_weekday(date: dt.date, iso_weekday: int) -> dt.date:
    """The day with the given ISO weekday (Monday is 1) in the same Monday-to-Sunday week as ``date``."""
    return date + dt.timedelta(days=iso_weekday - date.isoweekday())


def weeks_between(later: dt.date, earlier: dt.date) -> int:
    """Whole weeks from ``earlier`` to ``later``, rounded down like the JS package does."""
    return (later - earlier).days // 7
