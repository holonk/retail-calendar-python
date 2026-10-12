"""Invariants that hold for every configuration and year."""

from __future__ import annotations

import datetime as dt

from hypothesis import given
from hypothesis import strategies as st

from retail_calendar import (
    LastDayOfWeek,
    LastMonthOfYear,
    RetailCalendarOptions,
    WeekCalculation,
    WeekGrouping,
    date_to_segment,
    get_retail_calendar,
    segment_to_date,
)


@st.composite
def calendar_options(draw: st.DrawFn) -> RetailCalendarOptions:
    week_calculation = draw(st.sampled_from(WeekCalculation))
    last_day_of_week = draw(st.sampled_from(LastDayOfWeek))
    custom = {}
    if week_calculation is WeekCalculation.CUSTOM_LEAP_YEAR:
        leap_year = draw(st.integers(1990, 2030))
        end = draw(st.dates(dt.date(leap_year, 1, 1), dt.date(leap_year + 1, 12, 31)))
        custom = {
            "leap_year": leap_year,
            # Year ends on the configured week end day, as real configurations do.
            "leap_year_end_date": end + dt.timedelta(days=(last_day_of_week - end.isoweekday()) % 7),
            "leap_year_frequency": draw(st.integers(5, 7)),
        }
    return RetailCalendarOptions(
        week_grouping=draw(st.sampled_from(WeekGrouping)),
        last_day_of_week=last_day_of_week,
        last_month_of_year=draw(st.sampled_from(LastMonthOfYear)),
        week_calculation=week_calculation,
        add_leap_week_to_month=draw(st.none() | st.integers(0, 11)),
        beginning_month_index=draw(st.sampled_from([0, 1])),
        **custom,  # type: ignore[arg-type]
    )


years = st.integers(1900, 2100)


@given(calendar_options(), years)
def test_consecutive_years_touch(options: RetailCalendarOptions, year: int) -> None:
    calendar = get_retail_calendar(options, year)
    assert get_retail_calendar(options, year + 1).first_day == calendar.last_day + dt.timedelta(days=1)


@given(calendar_options(), years)
def test_weeks(options: RetailCalendarOptions, year: int) -> None:
    calendar = get_retail_calendar(options, year)
    assert calendar.number_of_weeks in (52, 53)
    assert len(calendar.weeks) == calendar.number_of_weeks
    assert calendar.weeks[0].start_date == calendar.first_day
    assert calendar.weeks[-1].end_date == calendar.last_day
    for index, week in enumerate(calendar.weeks):
        assert week.week_of_year == index
        assert week.end_date - week.start_date == dt.timedelta(days=6)
        assert week.end_date.isoweekday() == options.last_day_of_week
        if index:
            assert week.start_date == calendar.weeks[index - 1].end_date + dt.timedelta(days=1)
    leap_weeks = [week for week in calendar.weeks if week.is_leap_week]
    expected_leap_weeks = 1 if calendar.is_leap_year and options.add_leap_week_to_month is None else 0
    assert len(leap_weeks) == expected_leap_weeks


@given(calendar_options(), years)
def test_months(options: RetailCalendarOptions, year: int) -> None:
    calendar = get_retail_calendar(options, year)
    assert len(calendar.months) == 12
    assert sum(month.number_of_weeks for month in calendar.months) == sum(
        not week.is_leap_week for week in calendar.weeks
    )
    for index, month in enumerate(calendar.months):
        assert month.month_of_year == index + options.beginning_month_index
        assert month.quarter_of_year == index // 3 + 1
        assert len(month.weeks) == month.number_of_weeks
        assert month.start_date == month.weeks[0].start_date
        assert month.end_date == month.weeks[-1].end_date
        assert all(week.month_of_year == month.month_of_year for week in month.weeks)
        assert [week.week_of_month for week in month.weeks] == list(range(month.number_of_weeks))


@given(calendar_options(), st.dates(dt.date(1900, 1, 1), dt.date(2100, 12, 31)))
def test_date_to_segment_round_trips(options: RetailCalendarOptions, date: dt.date) -> None:
    segment = date_to_segment(date, options)
    week_start = segment_to_date(segment, options)
    assert week_start <= date < week_start + dt.timedelta(days=7)
    calendar = get_retail_calendar(options, segment.year)
    assert date in calendar
    day = calendar.day_of(date)
    assert day == calendar.days[(date - calendar.first_day).days]
    assert day.week_of_year == segment.week
