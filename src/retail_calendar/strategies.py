"""Strategies that pick the last day of a retail year.

Each strategy receives the last day of the Gregorian month the retail year ends in, the ISO weekday weeks end on and
the retail year, and returns the last day of that retail year. They mirror the JS package's ``LastDayStrategy``
implementations one to one.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import assert_never

from retail_calendar._dates import ONE_DAY, ONE_WEEK, weeks_between, with_iso_weekday
from retail_calendar.enums import WeekCalculation
from retail_calendar.options import RetailCalendarOptions

LastDayStrategy = Callable[[dt.date, int, int], dt.date]
"""``(last_day_of_gregorian_year, last_iso_weekday, retail_year) -> last_day_of_retail_year``."""


def last_day_before_eom(last_day_of_gregorian_year: dt.date, last_iso_weekday: int, _retail_year: int) -> dt.date:
    """The last ``last_iso_weekday`` on or before the end of the month."""
    candidate = with_iso_weekday(last_day_of_gregorian_year, last_iso_weekday)
    if candidate.month != last_day_of_gregorian_year.month:
        candidate -= ONE_WEEK
    return candidate


def last_day_before_eom_except_leap_year(
    last_day_of_gregorian_year: dt.date, last_iso_weekday: int, retail_year: int
) -> dt.date:
    """Like :func:`last_day_before_eom`, but a 53-week next year moves its extra week into this year.

    The next year's end is taken as December 31st of the following Gregorian year, exactly as the JS package does.
    For years that do not end in December that is not a retail year end, the 53-week check never matches, and this
    behaves like :func:`last_day_before_eom`.
    """
    last_day_of_next_gregorian_year = dt.date((last_day_of_gregorian_year + ONE_DAY).year, 12, 31)
    last_day_of_this_year = last_day_before_eom(last_day_of_gregorian_year, last_iso_weekday, retail_year)
    last_day_of_next_year = last_day_before_eom(last_day_of_next_gregorian_year, last_iso_weekday, retail_year + 1)
    if weeks_between(last_day_of_next_year, last_day_of_this_year) == 53:
        return last_day_of_this_year + ONE_WEEK
    return last_day_of_this_year


def last_day_nearest_eom(last_day_of_gregorian_year: dt.date, last_iso_weekday: int, _retail_year: int) -> dt.date:
    """The ``last_iso_weekday`` nearest to the end of the month."""
    current_week = with_iso_weekday(last_day_of_gregorian_year, last_iso_weekday)
    # Candidates in the JS package's tie-break order: next week, last week, current week.
    candidates = (current_week + ONE_WEEK, current_week - ONE_WEEK, current_week)
    return min(candidates, key=lambda candidate: abs((last_day_of_gregorian_year - candidate).days))


def first_bow_of_first_month(last_day_of_gregorian_year: dt.date, last_iso_weekday: int, _retail_year: int) -> dt.date:
    """The day before the first beginning of week on or after the first day of the next month."""
    first_iso_weekday = last_iso_weekday % 7 + 1
    start_of_next_year = last_day_of_gregorian_year + ONE_DAY
    start_of_next_year += dt.timedelta(days=(first_iso_weekday - start_of_next_year.isoweekday()) % 7)
    return start_of_next_year - ONE_DAY


def penultimate_day_of_week_nearest_eom(
    last_day_of_gregorian_year: dt.date, last_iso_weekday: int, retail_year: int
) -> dt.date:
    """The day after the penultimate weekday of the week nearest to the end of the month."""
    penultimate_iso_weekday = (last_iso_weekday - 2) % 7 + 1
    return last_day_nearest_eom(last_day_of_gregorian_year, penultimate_iso_weekday, retail_year) + ONE_DAY


def custom_leap_year(leap_year: int, leap_year_end_date: dt.date, leap_year_frequency: int) -> LastDayStrategy:
    """A strategy with a known year end and a fixed leap year frequency.

    ``leap_year`` ends on ``leap_year_end_date``, and every ``leap_year_frequency``-th year from it (in both
    directions) has 53 weeks. The Gregorian month end and the week end day are ignored.
    """

    def is_leap_year(year: int) -> bool:
        return abs(year - leap_year) % leap_year_frequency == 0

    def weeks_in_year(year: int) -> int:
        return 53 if is_leap_year(year) else 52

    def strategy(_last_day_of_gregorian_year: dt.date, _last_iso_weekday: int, retail_year: int) -> dt.date:
        if retail_year >= leap_year:
            weeks = sum(weeks_in_year(year) for year in range(leap_year + 1, retail_year + 1))
        else:
            weeks = -sum(weeks_in_year(year) for year in range(retail_year + 1, leap_year + 1))
        return leap_year_end_date + dt.timedelta(weeks=weeks)

    return strategy


def strategy_for(options: RetailCalendarOptions) -> LastDayStrategy:
    """The strategy configured by ``options.week_calculation``."""
    match options.week_calculation:
        case WeekCalculation.LAST_DAY_BEFORE_EOM:
            return last_day_before_eom
        case WeekCalculation.LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR:
            return last_day_before_eom_except_leap_year
        case WeekCalculation.LAST_DAY_NEAREST_EOM:
            return last_day_nearest_eom
        case WeekCalculation.FIRST_BOW_OF_FIRST_MONTH:
            return first_bow_of_first_month
        case WeekCalculation.PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM:
            return penultimate_day_of_week_nearest_eom
        case WeekCalculation.CUSTOM_LEAP_YEAR:
            # Presence is guaranteed by RetailCalendarOptions validation.
            assert options.leap_year is not None
            assert options.leap_year_end_date is not None
            assert options.leap_year_frequency is not None
            return custom_leap_year(options.leap_year, options.leap_year_end_date, options.leap_year_frequency)
        case _:
            assert_never(options.week_calculation)
