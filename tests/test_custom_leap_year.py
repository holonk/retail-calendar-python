"""Port of the JS package's ``__tests__/custom_leap_year.test.ts``."""

import datetime as dt

import pytest

from retail_calendar import (
    LastDayOfWeek,
    LastMonthOfYear,
    RetailCalendarOptions,
    WeekCalculation,
    WeekGrouping,
    get_retail_calendar,
)

# 2005, 2011, 2017, 2023, ... have 53 weeks.
OPTIONS = RetailCalendarOptions(
    week_calculation=WeekCalculation.CUSTOM_LEAP_YEAR,
    last_day_of_week=LastDayOfWeek.SATURDAY,
    last_month_of_year=LastMonthOfYear.FEBRUARY,
    week_grouping=WeekGrouping.GROUP_454,
    leap_year=2005,
    leap_year_end_date=dt.date(2006, 3, 11),  # a Saturday
    leap_year_frequency=6,
)


def test_first_given_leap_year_has_53_weeks() -> None:
    calendar = get_retail_calendar(OPTIONS, 2005)
    assert len(calendar.weeks) == 53
    assert calendar.weeks[0].start_date == dt.date(2005, 3, 6)
    assert calendar.weeks[52].end_date == dt.date(2006, 3, 11)


@pytest.mark.parametrize("year", [2023, 1999])
def test_later_and_earlier_leap_years_have_53_weeks(year: int) -> None:
    assert len(get_retail_calendar(OPTIONS, year).weeks) == 53


def test_year_end_dates_of_retail_years_2005_to_2029() -> None:
    expected = [
        "2006-03-11", "2007-03-10", "2008-03-08", "2009-03-07", "2010-03-06",
        "2011-03-05", "2012-03-10", "2013-03-09", "2014-03-08", "2015-03-07",
        "2016-03-05", "2017-03-04", "2018-03-10", "2019-03-09", "2020-03-07",
        "2021-03-06", "2022-03-05", "2023-03-04", "2024-03-09", "2025-03-08",
        "2026-03-07", "2027-03-06", "2028-03-04", "2029-03-03", "2030-03-09",
    ]  # fmt: skip
    actual = [get_retail_calendar(OPTIONS, year).weeks[-1].end_date.isoformat() for year in range(2005, 2030)]
    assert actual == expected
