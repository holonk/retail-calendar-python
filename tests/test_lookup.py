"""Port of the JS package's ``__tests__/gregorian_helpers.test.ts``, plus the retail-calendar-api style helpers."""

from __future__ import annotations

import datetime as dt

import pytest

from retail_calendar import (
    MAX_YEAR,
    MIN_YEAR,
    NRF_CALENDAR_OPTIONS,
    DateSegment,
    LastMonthOfYear,
    RetailCalendarOptions,
    calendar_of_gregorian_date,
    date_to_segment,
    is_leap_year,
    leap_years,
    segment_to_date,
    week_of_gregorian_date,
)


def test_week_of_gregorian_date() -> None:
    found = week_of_gregorian_date(dt.date(2020, 2, 5), NRF_CALENDAR_OPTIONS)
    assert found.week.week_of_year == 0
    assert found.calendar.year == 2020


def test_week_of_gregorian_date_in_a_different_retail_year() -> None:
    found = week_of_gregorian_date(dt.date(2020, 2, 1), NRF_CALENDAR_OPTIONS)
    assert found.week.week_of_year == 51
    assert found.calendar.year == 2019


def test_datetimes_are_accepted() -> None:
    assert date_to_segment(dt.datetime(2020, 2, 1, 23, 59, 59), NRF_CALENDAR_OPTIONS) == DateSegment(2019, 51)
    aware = dt.datetime(2020, 2, 2, 0, 30, tzinfo=dt.UTC)
    assert date_to_segment(aware, NRF_CALENDAR_OPTIONS) == DateSegment(2020, 0)


def test_date_to_segment_and_back() -> None:
    segment = date_to_segment(dt.date(2024, 2, 3), NRF_CALENDAR_OPTIONS)
    assert segment == DateSegment(year=2023, week=52)  # 2023 has 53 weeks
    assert segment_to_date(segment, NRF_CALENDAR_OPTIONS) == dt.date(2024, 1, 28)


def test_segment_to_date_of_a_missing_week() -> None:
    with pytest.raises(ValueError, match="Week 52 not found in year 2022"):
        segment_to_date(DateSegment(2022, 52), NRF_CALENDAR_OPTIONS)


def test_leap_years() -> None:
    assert leap_years(range(2010, 2030), NRF_CALENDAR_OPTIONS) == [2012, 2017, 2023, 2028]
    assert is_leap_year(2023, NRF_CALENDAR_OPTIONS)
    assert not is_leap_year(2024, NRF_CALENDAR_OPTIONS)


def test_dates_at_the_edge_of_the_supported_range() -> None:
    december = RetailCalendarOptions.from_dict({**NRF_CALENDAR_OPTIONS.to_dict(), "lastMonthOfYear": 11})
    assert december.last_month_of_year is LastMonthOfYear.DECEMBER
    assert calendar_of_gregorian_date(dt.date(MIN_YEAR, 6, 1), december).year == MIN_YEAR
    assert calendar_of_gregorian_date(dt.date(MAX_YEAR, 6, 1), december).year == MAX_YEAR
    with pytest.raises(ValueError, match="No retail calendar contains"):
        calendar_of_gregorian_date(dt.date(1, 6, 1), december)
