"""A configurable retail calendar: NRF 4-5-4, 4-4-5, 5-4-4 and custom leap year calendars.

Python port of the ``retail-calendar`` npm package.
"""

from __future__ import annotations

from retail_calendar.calendar import MAX_YEAR, MIN_YEAR, RetailCalendar, get_retail_calendar
from retail_calendar.enums import LastDayOfWeek, LastMonthOfYear, WeekCalculation, WeekGrouping
from retail_calendar.lookup import (
    WeekOfCalendar,
    calendar_of_gregorian_date,
    date_to_segment,
    is_leap_year,
    leap_years,
    segment_to_date,
    week_of_gregorian_date,
)
from retail_calendar.models import DateSegment, RetailDay, RetailMonth, RetailWeek
from retail_calendar.options import NRF_CALENDAR_OPTIONS, RetailCalendarOptions

__all__ = [
    "MAX_YEAR",
    "MIN_YEAR",
    "NRF_CALENDAR_OPTIONS",
    "DateSegment",
    "LastDayOfWeek",
    "LastMonthOfYear",
    "RetailCalendar",
    "RetailCalendarOptions",
    "RetailDay",
    "RetailMonth",
    "RetailWeek",
    "WeekCalculation",
    "WeekGrouping",
    "WeekOfCalendar",
    "calendar_of_gregorian_date",
    "date_to_segment",
    "get_retail_calendar",
    "is_leap_year",
    "leap_years",
    "segment_to_date",
    "week_of_gregorian_date",
]
