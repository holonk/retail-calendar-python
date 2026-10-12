"""Port of the JS package's ``__tests__/retail_calendar.test.ts``."""

from __future__ import annotations

import dataclasses
import datetime as dt

import pytest

from retail_calendar import (
    NRF_CALENDAR_OPTIONS,
    LastDayOfWeek,
    LastMonthOfYear,
    RetailCalendar,
    RetailCalendarOptions,
    WeekCalculation,
    WeekGrouping,
    get_retail_calendar,
)
from tests.helpers import assert_same_week, load_fixture

D = dt.date.fromisoformat


def options(**changes: object) -> RetailCalendarOptions:
    return dataclasses.replace(NRF_CALENDAR_OPTIONS, **changes)  # type: ignore[arg-type]


class TestAddLeapWeekToMonthOption:
    def test_defaults_to_none(self) -> None:
        assert RetailCalendar(NRF_CALENDAR_OPTIONS, 2022).options.add_leap_week_to_month is None

    def test_given_value_is_kept(self) -> None:
        assert RetailCalendar(options(add_leap_week_to_month=10), 2022).options.add_leap_week_to_month == 10


class TestLastDayNearestEom445:
    def test_penultimate_leap_year_returns_the_right_data_for_each_week_of_2022(self) -> None:
        calendar = RetailCalendar(
            RetailCalendarOptions(
                week_calculation=WeekCalculation.LAST_DAY_NEAREST_EOM,
                week_grouping=WeekGrouping.GROUP_445,
                last_day_of_week=LastDayOfWeek.FRIDAY,
                last_month_of_year=LastMonthOfYear.JANUARY,
                add_leap_week_to_month=10,
            ),
            2022,
        )
        expected_weeks = load_fixture("last_day_nearest_eom_445_penultimate_weeks")[
            "lastDayNearestEOM445PenultimateWeeks"
        ]
        for actual, expected in zip(calendar.weeks, expected_weeks, strict=True):
            assert_same_week(actual, expected)

    arbitrary_leap_year_options = RetailCalendarOptions(
        week_calculation=WeekCalculation.LAST_DAY_NEAREST_EOM,
        week_grouping=WeekGrouping.GROUP_445,
        last_day_of_week=LastDayOfWeek.SUNDAY,
        last_month_of_year=LastMonthOfYear.OCTOBER,
    )

    def test_arbitrary_leap_year_returns_the_right_data_for_each_week_of_2023(self) -> None:
        calendar = RetailCalendar(self.arbitrary_leap_year_options, 2023)
        expected_weeks = load_fixture("last_day_nearest_eom_445_arbitrary_leap_year_weeks")["lastDayNearestEOM445Weeks"]
        # The JS fixture lists the first 52 weeks only.
        for actual, expected in zip(calendar.weeks, expected_weeks, strict=False):
            assert_same_week(actual, expected)

    @pytest.mark.parametrize("add_leap_week_to_month", range(12))
    def test_add_leap_week_to_month_is_respected(self, add_leap_week_to_month: int) -> None:
        calendar = RetailCalendar(
            dataclasses.replace(self.arbitrary_leap_year_options, add_leap_week_to_month=add_leap_week_to_month), 2023
        )
        expected = [4, 4, 5, 4, 4, 5, 4, 4, 5, 4, 4, 5]
        expected[add_leap_week_to_month] += 1
        assert [len(month.weeks) for month in calendar.months] == expected


class TestNrfCalendar:
    @pytest.mark.parametrize(
        ("year", "number_of_weeks"),
        [(row["year"], row["numberOfWeeks"]) for row in load_fixture("nrf_years")["nrfYears"]],
    )
    def test_number_of_weeks(self, year: int, number_of_weeks: int) -> None:
        assert RetailCalendar(NRF_CALENDAR_OPTIONS, year).number_of_weeks == number_of_weeks

    def test_months_have_the_correct_number_of_weeks(self) -> None:
        calendar = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018)
        assert [len(month.weeks) for month in calendar.months] == [4, 5, 4, 4, 5, 4, 4, 5, 4, 4, 5, 4]
        assert [month.number_of_weeks for month in calendar.months] == [4, 5, 4, 4, 5, 4, 4, 5, 4, 4, 5, 4]

    def test_months_have_the_correct_start_and_end_dates(self) -> None:
        calendar = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018)
        expected_months = load_fixture("nrf_2018")["nrf2018"]
        for month, expected in zip(calendar.months, expected_months, strict=True):
            assert (month.start_date, month.end_date) == (D(expected["start"]), D(expected["end"]))

    def test_first_month_of_a_leap_year(self) -> None:
        month = RetailCalendar(NRF_CALENDAR_OPTIONS, 2017).months[0]
        expected = load_fixture("nrf_2018")["nrf2017NotRestated"][0]
        assert (month.start_date, month.end_date) == (D(expected["start"]), D(expected["end"]))

    def test_weeks_have_the_correct_month(self) -> None:
        calendar = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018)
        expected = [month for month, weeks in enumerate([4, 5, 4] * 4, start=1) for _ in range(weeks)]
        assert [week.month_of_year for week in calendar.weeks] == expected

    def test_weeks_have_the_correct_start_and_end_dates(self) -> None:
        weeks = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018).weeks
        assert (weeks[0].start_date, weeks[0].end_date) == (D("2018-02-04"), D("2018-02-10"))
        assert (weeks[1].start_date, weeks[1].end_date) == (D("2018-02-11"), D("2018-02-17"))

    def test_weeks_have_0_indexed_week_of_year(self) -> None:
        weeks = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018).weeks
        assert [week.week_of_year for week in weeks] == list(range(52))

    def test_quarters(self) -> None:
        calendar = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018)
        assert [month.quarter_of_year for month in calendar.months] == [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
        weeks = calendar.weeks
        assert [weeks[i].week_of_quarter for i in (0, 13, 26, 39, 51)] == [0, 0, 0, 0, 12]


class TestNrfLeapYearWithWeekAddedToPenultimateMonth:
    @pytest.fixture
    def calendar(self) -> RetailCalendar:
        return RetailCalendar(options(week_grouping=WeekGrouping.GROUP_445, add_leap_week_to_month=10), 2017)

    def test_keeps_the_first_week_in_the_year(self, calendar: RetailCalendar) -> None:
        first_week = calendar.weeks[0]
        assert (first_week.month_of_year, first_week.week_of_month, first_week.week_of_year) == (1, 0, 0)
        assert first_week.week_of_quarter == 0
        assert calendar.months[0].weeks[0] == first_week

    def test_keeps_the_last_week_in_the_year(self, calendar: RetailCalendar) -> None:
        last_week = calendar.weeks[52]
        assert (last_week.month_of_year, last_week.week_of_month, last_week.week_of_year) == (12, 4, 52)
        assert not last_week.is_leap_week

    def test_adds_a_week_to_the_11th_month(self, calendar: RetailCalendar) -> None:
        assert [len(month.weeks) for month in calendar.months] == [4, 4, 5, 4, 4, 5, 4, 4, 5, 4, 5, 5]
        assert calendar.weeks[1].week_of_year == 1


class TestNrfLeapYearDroppingLastWeek:
    @pytest.fixture
    def calendar(self) -> RetailCalendar:
        return RetailCalendar(NRF_CALENDAR_OPTIONS, 2017)

    def test_returns_week_52_as_the_last_week_of_the_year(self, calendar: RetailCalendar) -> None:
        assert len(calendar.weeks) == 53
        last_week = calendar.weeks[52]
        assert last_week.week_of_year == 52
        assert last_week.is_leap_week
        assert (last_week.month_of_year, last_week.week_of_month) == (None, None)
        assert (last_week.quarter_of_year, last_week.week_of_quarter) == (None, None)

    def test_assigns_first_52_weeks_to_months_and_quarters(self, calendar: RetailCalendar) -> None:
        for index, week in enumerate(calendar.weeks[:52]):
            assert week.quarter_of_year == index // 13 + 1
            assert week.week_of_quarter == index % 13

    def test_does_not_assign_any_month_to_the_last_week(self, calendar: RetailCalendar) -> None:
        assert calendar.months[0].weeks[0].week_of_year == 0
        last_month = calendar.months[11]
        assert calendar.weeks[52] not in last_month.weeks
        assert last_month.weeks[3] == calendar.weeks[51]


class TestLastDayBeforeEom:
    base = RetailCalendarOptions(
        week_grouping=WeekGrouping.GROUP_454,
        last_day_of_week=LastDayOfWeek.SATURDAY,
        last_month_of_year=LastMonthOfYear.AUGUST,
        week_calculation=WeekCalculation.LAST_DAY_BEFORE_EOM,
    )

    @pytest.mark.parametrize(
        ("year", "number_of_weeks"),
        [
            (row["year"], row["numberOfWeeks"])
            for row in load_fixture("last_day_before_eom_years")["lastDayBeforeEOMYears"]
        ],
    )
    def test_number_of_weeks(self, year: int, number_of_weeks: int) -> None:
        assert RetailCalendar(self.base, year).number_of_weeks == number_of_weeks

    @pytest.mark.parametrize(
        ("week_grouping", "expected"),
        [
            (WeekGrouping.GROUP_544, [5, 4, 4] * 4),
            (WeekGrouping.GROUP_445, [4, 4, 5] * 4),
        ],
    )
    def test_week_grouping_distributes_weeks(self, week_grouping: WeekGrouping, expected: list[int]) -> None:
        calendar = RetailCalendar(dataclasses.replace(self.base, week_grouping=week_grouping), 2015)
        assert [len(month.weeks) for month in calendar.months] == expected


def test_december_year_end_stays_in_the_given_gregorian_year() -> None:
    calendar = RetailCalendar(
        RetailCalendarOptions(
            week_grouping=WeekGrouping.GROUP_445,
            last_day_of_week=LastDayOfWeek.SATURDAY,
            last_month_of_year=LastMonthOfYear.DECEMBER,
            week_calculation=WeekCalculation.LAST_DAY_NEAREST_EOM,
        ),
        2019,
    )
    assert calendar.months[11].start_date.year == 2019


def test_first_bow_of_first_month_month_dates() -> None:
    first_bow_options = RetailCalendarOptions(
        week_grouping=WeekGrouping.GROUP_445,
        last_day_of_week=LastDayOfWeek.SATURDAY,
        last_month_of_year=LastMonthOfYear.DECEMBER,
        week_calculation=WeekCalculation.FIRST_BOW_OF_FIRST_MONTH,
    )
    for year_data in load_fixture("first_bow")["firstBow"]:
        calendar = RetailCalendar(first_bow_options, year_data["year"])
        for expected in year_data["months"]:
            month = calendar.months[expected["monthOfYear"]]
            assert (month.start_date, month.end_date) == (D(expected["start"]), D(expected["end"]))


class TestBeginningMonthIndex:
    @pytest.fixture
    def calendar(self) -> RetailCalendar:
        return RetailCalendar(options(beginning_month_index=0), 2018)

    def test_month_of_year_of_each_month_and_week(self, calendar: RetailCalendar) -> None:
        expected = [month for month, weeks in enumerate([4, 5, 4] * 4) for _ in range(weeks)]
        assert [week.month_of_year for week in calendar.weeks] == expected
        assert [month.month_of_year for month in calendar.months] == list(range(12))

    def test_quarter_of_year_of_each_month(self, calendar: RetailCalendar) -> None:
        assert [month.quarter_of_year for month in calendar.months] == [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]


def test_last_day_before_eom_except_leap_year_moves_53rd_week_to_previous_year() -> None:
    except_leap_year_options = RetailCalendarOptions(
        week_grouping=WeekGrouping.GROUP_445,
        last_day_of_week=LastDayOfWeek.SATURDAY,
        last_month_of_year=LastMonthOfYear.DECEMBER,
        week_calculation=WeekCalculation.LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR,
    )
    for year_data in load_fixture("last_day_before_eom_except_leap_year")["lastDayBeforeEomExceptLeapYear"]:
        calendar = RetailCalendar(except_leap_year_options, year_data["year"])
        for expected in year_data["months"]:
            month = calendar.months[expected["monthOfYear"]]
            assert (month.start_date, month.end_date) == (D(expected["start"]), D(expected["end"]))
        if leap_week := year_data.get("leapWeek"):
            week = calendar.weeks[52]
            assert (week.start_date, week.end_date) == (D(leap_week["start"]), D(leap_week["end"]))


@pytest.mark.parametrize("year", [0, 1, 9998, -5])
def test_unsupported_years_raise(year: int) -> None:
    # The JS package has a "year 0" test; Python dates only cover years 1 to 9999.
    with pytest.raises(ValueError, match="year must be between"):
        RetailCalendar(options(last_month_of_year=LastMonthOfYear.DECEMBER), year)


def test_penultimate_day_of_week_nearest_eom() -> None:
    # NRF has 53 weeks in 2023 with weeks ending on Saturday ...
    assert len(RetailCalendar(NRF_CALENDAR_OPTIONS, 2023).weeks) == 53
    # ... but only 52 when weeks end on Sunday.
    assert len(RetailCalendar(options(last_day_of_week=LastDayOfWeek.SUNDAY), 2023).weeks) == 52

    # The penultimate strategy keeps Sunday week ends but NRF's year boundaries.
    calendar = RetailCalendar(
        options(
            last_day_of_week=LastDayOfWeek.SUNDAY,
            week_calculation=WeekCalculation.PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM,
        ),
        2023,
    )
    assert len(calendar.weeks) == 53
    assert all(week.end_date.isoweekday() == 7 for week in calendar.weeks)
    assert calendar.weeks[0].start_date == D("2023-01-30")
    assert calendar.weeks[52].end_date == D("2024-02-04")


class TestMemoization:
    def test_returns_the_same_calendar_for_the_same_options_and_year(self) -> None:
        memo_options = RetailCalendarOptions(
            week_grouping=WeekGrouping.GROUP_454,
            last_day_of_week=LastDayOfWeek.SATURDAY,
            last_month_of_year=LastMonthOfYear.DECEMBER,
            week_calculation=WeekCalculation.LAST_DAY_NEAREST_EOM,
            beginning_month_index=0,
        )
        calendar_2022 = get_retail_calendar(memo_options, 2022)
        assert get_retail_calendar(memo_options, 2022) is calendar_2022
        assert get_retail_calendar(dataclasses.replace(memo_options), 2022) is calendar_2022
        assert get_retail_calendar(memo_options, 2023) is not calendar_2022

    def test_different_custom_leap_year_options_are_different_keys(self) -> None:
        custom = options(
            week_calculation=WeekCalculation.CUSTOM_LEAP_YEAR,
            leap_year=2006,
            leap_year_end_date=D("2006-03-11"),
            leap_year_frequency=6,
        )
        other = dataclasses.replace(custom, leap_year_frequency=7)
        assert custom != other
        assert get_retail_calendar(custom, 2020) is not get_retail_calendar(other, 2020)


class TestCalendarApi:
    def test_calendars_are_immutable(self) -> None:
        calendar = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018)
        with pytest.raises(dataclasses.FrozenInstanceError):
            calendar.year = 2019  # type: ignore[misc]
        with pytest.raises(dataclasses.FrozenInstanceError):
            calendar.weeks[0].week_of_year = 3  # type: ignore[misc]

    def test_repr_omits_weeks_months_and_days(self) -> None:
        text = repr(RetailCalendar(NRF_CALENDAR_OPTIONS, 2018))
        assert "year=2018" in text
        assert ", weeks=" not in text

    def test_contains_and_lookups(self) -> None:
        calendar = RetailCalendar(NRF_CALENDAR_OPTIONS, 2018)
        assert (calendar.first_day, calendar.last_day) == (D("2018-02-04"), D("2019-02-02"))
        assert D("2018-02-04") in calendar
        assert D("2019-02-03") not in calendar
        assert dt.datetime(2018, 2, 10, 23, 59) in calendar.weeks[0]
        assert D("2018-02-11") not in calendar.weeks[0]
        assert D("2018-03-03") in calendar.months[0]
        assert calendar.week_of(D("2018-02-11")) == calendar.weeks[1]
        assert calendar.day_of(dt.datetime(2018, 2, 5, 12)).date == D("2018-02-05")
        assert calendar.week(51) == calendar.weeks[-1]
        assert calendar.segment_of(D("2019-02-02")).week == 51
        assert not calendar.is_leap_year

    @pytest.mark.parametrize("week_of_year", [-1, 52])
    def test_week_out_of_range(self, week_of_year: int) -> None:
        with pytest.raises(ValueError, match=f"Week {week_of_year} not found in year 2018"):
            RetailCalendar(NRF_CALENDAR_OPTIONS, 2018).week(week_of_year)

    def test_date_outside_of_calendar(self) -> None:
        with pytest.raises(ValueError, match="is not in retail year 2018"):
            RetailCalendar(NRF_CALENDAR_OPTIONS, 2018).week_of(D("2018-01-01"))

    def test_options_producing_an_invalid_number_of_weeks_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # No valid configuration produces anything but 52 or 53 weeks, so fake a strategy that does.
        def broken_strategy(last_day_of_gregorian_year: dt.date, _weekday: int, retail_year: int) -> dt.date:
            return last_day_of_gregorian_year + dt.timedelta(weeks=10 * (retail_year % 2))

        monkeypatch.setattr("retail_calendar.calendar.strategy_for", lambda _options: broken_strategy)
        with pytest.raises(ValueError, match="expected 52 or 53"):
            RetailCalendar(NRF_CALENDAR_OPTIONS, 2019)
