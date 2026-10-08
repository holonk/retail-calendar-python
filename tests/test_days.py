"""Port of the JS package's ``__tests__/days.test.ts``."""

import datetime as dt

import pytest

from retail_calendar import NRF_CALENDAR_OPTIONS, RetailCalendar, RetailDay


def assert_day(
    day: RetailDay,
    *,
    date: dt.date,
    day_of_year: int,
    day_of_week: int,
    day_of_month: int | None,
    week_of_year: int,
    month_of_year: int | None,
    gregorian_day_of_year: int,
) -> None:
    assert day == RetailDay(
        date=date,
        day_of_year=day_of_year,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        week_of_year=week_of_year,
        month_of_year=month_of_year,
    )
    assert day.gregorian_day_of_year == gregorian_day_of_year
    assert day.gregorian_month_of_year == date.month
    assert day.gregorian_day_of_month == date.day


class TestNrfNonLeapYear:
    @pytest.fixture
    def calendar(self) -> RetailCalendar:
        return RetailCalendar(NRF_CALENDAR_OPTIONS, 2022)

    def test_has_52_weeks_of_days(self, calendar: RetailCalendar) -> None:
        assert len(calendar.days) == 52 * 7

    @pytest.mark.parametrize(
        ("index", "date", "day_of_month", "day_of_week", "month_of_year", "week_of_year", "gregorian_day_of_year"),
        [
            (0, dt.date(2022, 1, 30), 1, 1, 1, 0, 30),
            (1, dt.date(2022, 1, 31), 2, 2, 1, 0, 31),
            (2, dt.date(2022, 2, 1), 3, 3, 1, 0, 32),
            (52 * 7 - 1, dt.date(2023, 1, 28), 28, 7, 12, 51, 28),
            (31 * 7 + 1, dt.date(2022, 9, 5), 9, 2, 8, 31, 248),
        ],
        ids=["first", "second", "third", "last", "random"],
    )
    def test_day(
        self,
        calendar: RetailCalendar,
        index: int,
        date: dt.date,
        day_of_month: int,
        day_of_week: int,
        month_of_year: int,
        week_of_year: int,
        gregorian_day_of_year: int,
    ) -> None:
        assert_day(
            calendar.days[index],
            date=date,
            day_of_year=index + 1,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            week_of_year=week_of_year,
            month_of_year=month_of_year,
            gregorian_day_of_year=gregorian_day_of_year,
        )
        assert calendar.day_of(date) == calendar.days[index]


class TestNrfLeapYear:
    @pytest.fixture
    def calendar(self) -> RetailCalendar:
        return RetailCalendar(NRF_CALENDAR_OPTIONS, 2023)

    def test_has_53_weeks_of_days(self, calendar: RetailCalendar) -> None:
        assert len(calendar.days) == 53 * 7

    @pytest.mark.parametrize(
        ("index", "date", "day_of_month", "day_of_week", "month_of_year", "week_of_year", "gregorian_day_of_year"),
        [
            (0, dt.date(2023, 1, 29), 1, 1, 1, 0, 29),
            (1, dt.date(2023, 1, 30), 2, 2, 1, 0, 30),
            (2, dt.date(2023, 1, 31), 3, 3, 1, 0, 31),
            # The 53rd week belongs to no month.
            (53 * 7 - 1, dt.date(2024, 2, 3), None, 7, None, 52, 34),
            (31 * 7 + 1, dt.date(2023, 9, 4), 9, 2, 8, 31, 247),
        ],
        ids=["first", "second", "third", "last", "random"],
    )
    def test_day(
        self,
        calendar: RetailCalendar,
        index: int,
        date: dt.date,
        day_of_month: int | None,
        day_of_week: int,
        month_of_year: int | None,
        week_of_year: int,
        gregorian_day_of_year: int,
    ) -> None:
        assert_day(
            calendar.days[index],
            date=date,
            day_of_year=index + 1,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            week_of_year=week_of_year,
            month_of_year=month_of_year,
            gregorian_day_of_year=gregorian_day_of_year,
        )
        assert calendar.day_of(date) == calendar.days[index]
