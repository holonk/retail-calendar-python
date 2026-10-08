import dataclasses
import datetime as dt
from typing import Any

import pytest

from retail_calendar import (
    NRF_CALENDAR_OPTIONS,
    LastDayOfWeek,
    LastMonthOfYear,
    RetailCalendarOptions,
    WeekCalculation,
    WeekGrouping,
)


class TestEnums:
    def test_values_match_the_js_package(self) -> None:
        assert [int(member) for member in WeekGrouping] == [0, 1, 2]
        assert [int(member) for member in LastDayOfWeek] == list(range(1, 8))
        assert [int(member) for member in LastMonthOfYear] == list(range(12))
        assert [int(member) for member in WeekCalculation] == list(range(6))

    @pytest.mark.parametrize(
        ("enum", "label", "member"),
        [
            (WeekGrouping, "4-4-5", WeekGrouping.GROUP_445),
            (WeekGrouping, "5-4-4", WeekGrouping.GROUP_544),
            (WeekGrouping, "4-5-4", WeekGrouping.GROUP_454),
            (LastDayOfWeek, "Saturday", LastDayOfWeek.SATURDAY),
            (LastMonthOfYear, "January", LastMonthOfYear.JANUARY),
            (WeekCalculation, "lastDayBeforeEndOfMonth", WeekCalculation.LAST_DAY_BEFORE_EOM),
            (
                WeekCalculation,
                "lastDayBeforeEndOfMonthExceptLeapYear",
                WeekCalculation.LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR,
            ),
            (WeekCalculation, "lastDayNearestEndOfMonth", WeekCalculation.LAST_DAY_NEAREST_EOM),
            (WeekCalculation, "firstBOWOfFirstMonth", WeekCalculation.FIRST_BOW_OF_FIRST_MONTH),
            (
                WeekCalculation,
                "penultimateDayOfWeekNearestEndOfMonth",
                WeekCalculation.PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM,
            ),
            (WeekCalculation, "customLeapYear", WeekCalculation.CUSTOM_LEAP_YEAR),
        ],
    )
    def test_labels_match_retail_calendar_api(self, enum: Any, label: str, member: Any) -> None:
        assert enum.from_label(label) is member
        assert member.label == label
        assert enum.coerce(label) is member
        assert enum.coerce(int(member)) is member
        assert enum.coerce(member) is member

    def test_invalid_values(self) -> None:
        with pytest.raises(ValueError, match="'4-4-4' is not a valid WeekGrouping label"):
            WeekGrouping.from_label("4-4-4")
        with pytest.raises(ValueError, match="7 is not a valid WeekGrouping"):
            WeekGrouping.coerce(7)
        with pytest.raises(TypeError, match="bool"):
            WeekGrouping.coerce(True)
        with pytest.raises(TypeError, match="float"):
            WeekGrouping.coerce(1.0)  # type: ignore[arg-type]

    def test_last_month_of_year_month_is_1_based(self) -> None:
        assert LastMonthOfYear.JANUARY.month == 1
        assert LastMonthOfYear.DECEMBER.month == 12

    def test_weeks_per_month(self) -> None:
        assert WeekGrouping.GROUP_445.weeks_per_month == (4, 4, 5)
        assert WeekGrouping.GROUP_544.weeks_per_month == (5, 4, 4)
        assert WeekGrouping.GROUP_454.weeks_per_month == (4, 5, 4)


class TestOptions:
    def test_ints_and_labels_are_coerced_to_enums(self) -> None:
        options = RetailCalendarOptions(
            week_grouping=2,  # type: ignore[arg-type]
            last_day_of_week="Saturday",  # type: ignore[arg-type]
            last_month_of_year=0,  # type: ignore[arg-type]
            week_calculation="lastDayNearestEndOfMonth",  # type: ignore[arg-type]
        )
        assert options == NRF_CALENDAR_OPTIONS
        assert options.week_grouping is WeekGrouping.GROUP_454
        assert hash(options) == hash(NRF_CALENDAR_OPTIONS)

    def test_options_are_immutable(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            NRF_CALENDAR_OPTIONS.leap_year = 2000  # type: ignore[misc]

    @pytest.mark.parametrize("value", [-1, 12])
    def test_add_leap_week_to_month_range(self, value: int) -> None:
        with pytest.raises(ValueError, match="add_leap_week_to_month must be between 0 and 11"):
            dataclasses.replace(NRF_CALENDAR_OPTIONS, add_leap_week_to_month=value)

    def test_custom_leap_year_requires_its_options(self) -> None:
        with pytest.raises(ValueError, match="requires leap_year, leap_year_end_date and leap_year_frequency"):
            dataclasses.replace(NRF_CALENDAR_OPTIONS, week_calculation=WeekCalculation.CUSTOM_LEAP_YEAR, leap_year=2005)

    def test_custom_leap_year_frequency_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="leap_year_frequency must be at least 1"):
            dataclasses.replace(
                NRF_CALENDAR_OPTIONS,
                week_calculation=WeekCalculation.CUSTOM_LEAP_YEAR,
                leap_year=2005,
                leap_year_end_date=dt.date(2006, 3, 11),
                leap_year_frequency=0,
            )

    @pytest.mark.parametrize("end_date", ["2006-03-11", dt.datetime(2006, 3, 11, 12)])
    def test_leap_year_end_date_is_coerced_to_a_date(self, end_date: Any) -> None:
        options = dataclasses.replace(NRF_CALENDAR_OPTIONS, leap_year_end_date=end_date)
        assert options.leap_year_end_date == dt.date(2006, 3, 11)
        assert type(options.leap_year_end_date) is dt.date


class TestFromDict:
    def test_js_package_shape(self) -> None:
        data = {"weekGrouping": 2, "lastDayOfWeek": 6, "lastMonthOfYear": 0, "weekCalculation": 2}
        assert RetailCalendarOptions.from_dict(data) == NRF_CALENDAR_OPTIONS

    def test_calendarconfiguration_row_shape(self) -> None:
        row = {
            "id": 7,
            "granularity": "Weekly",
            "weekGrouping": "4-4-5",
            "lastDayOfTheWeek": "Saturday",
            "lastMonthOfTheYear": "February",
            "lastWeekCalculationMethod": "customLeapYear",
            "leapYear": 2005,
            "leapYearEndDate": "2006-03-11",
            "leapYearFrequency": 6,
            "addLeapWeekToMonth": None,
        }
        assert RetailCalendarOptions.from_dict(row) == RetailCalendarOptions(
            week_grouping=WeekGrouping.GROUP_445,
            last_day_of_week=LastDayOfWeek.SATURDAY,
            last_month_of_year=LastMonthOfYear.FEBRUARY,
            week_calculation=WeekCalculation.CUSTOM_LEAP_YEAR,
            leap_year=2005,
            leap_year_end_date=dt.date(2006, 3, 11),
            leap_year_frequency=6,
        )

    def test_minus_one_add_leap_week_to_month_means_none(self) -> None:
        data = {**NRF_CALENDAR_OPTIONS.to_dict(), "addLeapWeekToMonth": -1}
        assert RetailCalendarOptions.from_dict(data).add_leap_week_to_month is None

    def test_null_beginning_month_index_uses_the_default(self) -> None:
        data = {**NRF_CALENDAR_OPTIONS.to_dict(), "beginningMonthIndex": None}
        assert RetailCalendarOptions.from_dict(data).beginning_month_index == 1

    def test_missing_required_options(self) -> None:
        with pytest.raises(ValueError, match="Missing required calendar options: weekGrouping, weekCalculation"):
            RetailCalendarOptions.from_dict({"lastDayOfTheWeek": "Saturday", "lastMonthOfTheYear": "January"})

    def test_conflicting_keys(self) -> None:
        data = {**NRF_CALENDAR_OPTIONS.to_dict(), "lastDayOfTheWeek": "Sunday"}
        with pytest.raises(ValueError, match="Conflicting keys for last_day_of_week: lastDayOfWeek, lastDayOfTheWeek"):
            RetailCalendarOptions.from_dict(data)

    def test_unknown_label(self) -> None:
        data = {**NRF_CALENDAR_OPTIONS.to_dict(), "weekCalculation": "nearestSomething"}
        with pytest.raises(ValueError, match="'nearestSomething' is not a valid WeekCalculation label"):
            RetailCalendarOptions.from_dict(data)

    @pytest.mark.parametrize(
        "options",
        [
            NRF_CALENDAR_OPTIONS,
            dataclasses.replace(
                NRF_CALENDAR_OPTIONS,
                week_calculation=WeekCalculation.CUSTOM_LEAP_YEAR,
                leap_year=2005,
                leap_year_end_date=dt.date(2006, 3, 11),
                leap_year_frequency=6,
                add_leap_week_to_month=10,
                beginning_month_index=0,
            ),
        ],
    )
    def test_round_trip(self, options: RetailCalendarOptions) -> None:
        assert RetailCalendarOptions.from_dict(options.to_dict()) == options

    def test_to_dict_omits_unset_fields(self) -> None:
        assert NRF_CALENDAR_OPTIONS.to_dict() == {
            "weekGrouping": 2,
            "lastDayOfWeek": 6,
            "lastMonthOfYear": 0,
            "weekCalculation": 2,
            "beginningMonthIndex": 1,
        }
