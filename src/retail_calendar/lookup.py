"""Conversions between Gregorian dates and retail weeks.

These mirror the retail-calendar-api endpoints:

* ``get-date-segments-from-dates``  -> :func:`date_to_segment`
* ``get-dates-from-date-segments``  -> :func:`segment_to_date`
* ``get-leap-years``                -> :func:`leap_years`
"""

import datetime as dt
from collections.abc import Iterable
from typing import NamedTuple

from retail_calendar._dates import to_date
from retail_calendar.calendar import MAX_YEAR, MIN_YEAR, RetailCalendar, get_retail_calendar
from retail_calendar.models import DateSegment, RetailWeek
from retail_calendar.options import RetailCalendarOptions


class WeekOfCalendar(NamedTuple):
    """A retail week together with the calendar it belongs to."""

    calendar: RetailCalendar
    week: RetailWeek


def calendar_of_gregorian_date(date: dt.date, options: RetailCalendarOptions) -> RetailCalendar:
    """The retail calendar whose year contains ``date``."""
    date = to_date(date)
    # A retail year starts at most a few weeks before or after its Gregorian counterpart, so one of these matches.
    for year in (date.year - 1, date.year, date.year + 1):
        if MIN_YEAR <= year <= MAX_YEAR:
            calendar = get_retail_calendar(options, year)
            if date in calendar:
                return calendar
    raise ValueError(f"No retail calendar contains {date}; supported retail years are {MIN_YEAR} to {MAX_YEAR}")


def week_of_gregorian_date(date: dt.date, options: RetailCalendarOptions) -> WeekOfCalendar:
    """The retail week containing ``date``, and its calendar."""
    calendar = calendar_of_gregorian_date(date, options)
    return WeekOfCalendar(calendar=calendar, week=calendar.week_of(date))


def date_to_segment(date: dt.date, options: RetailCalendarOptions) -> DateSegment:
    """The (retail year, 0-based week of year) containing ``date``."""
    return calendar_of_gregorian_date(date, options).segment_of(date)


def segment_to_date(segment: DateSegment, options: RetailCalendarOptions) -> dt.date:
    """The first day of the retail week ``segment``. Raises ``ValueError`` if the year has no such week."""
    return get_retail_calendar(options, segment.year).week(segment.week).start_date


def is_leap_year(year: int, options: RetailCalendarOptions) -> bool:
    """Whether retail year ``year`` has 53 weeks."""
    return get_retail_calendar(options, year).is_leap_year


def leap_years(years: Iterable[int], options: RetailCalendarOptions) -> list[int]:
    """The years among ``years`` that have 53 weeks, in the given order."""
    return [year for year in years if is_leap_year(year, options)]
