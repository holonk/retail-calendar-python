"""Retail calendar configuration."""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self

from retail_calendar.enums import LastDayOfWeek, LastMonthOfYear, WeekCalculation, WeekGrouping

# Each option accepts the key used by the JS package and the key used by the calendarconfiguration table and
# retail-calendar-api request bodies.
_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "week_grouping": ("weekGrouping", "week_grouping"),
    "last_day_of_week": ("lastDayOfWeek", "lastDayOfTheWeek", "last_day_of_week"),
    "last_month_of_year": ("lastMonthOfYear", "lastMonthOfTheYear", "last_month_of_year"),
    "week_calculation": ("weekCalculation", "lastWeekCalculationMethod", "week_calculation"),
    "add_leap_week_to_month": ("addLeapWeekToMonth", "add_leap_week_to_month"),
    "beginning_month_index": ("beginningMonthIndex", "beginning_month_index"),
    "leap_year": ("leapYear", "leap_year"),
    "leap_year_end_date": ("leapYearEndDate", "leap_year_end_date"),
    "leap_year_frequency": ("leapYearFrequency", "leap_year_frequency"),
}


@dataclass(frozen=True, slots=True, kw_only=True)
class RetailCalendarOptions:
    """Configuration of a retail calendar.

    Instances are immutable and hashable, so they can be used as cache or dictionary keys. Integer values and
    labels are accepted for the enum fields and are converted to enum members.
    """

    week_grouping: WeekGrouping
    last_day_of_week: LastDayOfWeek
    last_month_of_year: LastMonthOfYear
    week_calculation: WeekCalculation

    add_leap_week_to_month: int | None = None
    """0-based index of the month that gets the 53rd week in 53-week years.

    ``None`` (the default) leaves the 53rd week outside of any month.
    """

    beginning_month_index: int = 1
    """The ``month_of_year`` value of the first month of the year."""

    leap_year: int | None = None
    """For ``CUSTOM_LEAP_YEAR``: a retail year known to have 53 weeks."""

    leap_year_end_date: dt.date | None = None
    """For ``CUSTOM_LEAP_YEAR``: the last day of ``leap_year``."""

    leap_year_frequency: int | None = None
    """For ``CUSTOM_LEAP_YEAR``: every ``leap_year_frequency`` years from ``leap_year`` has 53 weeks."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "week_grouping", WeekGrouping.coerce(self.week_grouping))
        object.__setattr__(self, "last_day_of_week", LastDayOfWeek.coerce(self.last_day_of_week))
        object.__setattr__(self, "last_month_of_year", LastMonthOfYear.coerce(self.last_month_of_year))
        object.__setattr__(self, "week_calculation", WeekCalculation.coerce(self.week_calculation))
        # Accept ISO strings and datetimes too, as found in database rows and JSON payloads.
        end_date: object = self.leap_year_end_date
        if isinstance(end_date, str):
            object.__setattr__(self, "leap_year_end_date", dt.date.fromisoformat(end_date))
        elif isinstance(end_date, dt.datetime):
            object.__setattr__(self, "leap_year_end_date", end_date.date())
        self._validate()

    def _validate(self) -> None:
        if self.add_leap_week_to_month is not None and not 0 <= self.add_leap_week_to_month <= 11:
            raise ValueError(f"add_leap_week_to_month must be between 0 and 11, got {self.add_leap_week_to_month}")

        if self.week_calculation is not WeekCalculation.CUSTOM_LEAP_YEAR:
            return
        if self.leap_year is None or self.leap_year_end_date is None or self.leap_year_frequency is None:
            raise ValueError(
                "CUSTOM_LEAP_YEAR week calculation requires leap_year, leap_year_end_date and leap_year_frequency"
            )
        if self.leap_year_frequency < 1:
            raise ValueError(f"leap_year_frequency must be at least 1, got {self.leap_year_frequency}")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Build options from a camelCase mapping.

        Accepts the keys of the JS package (``weekGrouping``, ``lastDayOfWeek``, ...) and of the
        ``calendarconfiguration`` table / retail-calendar-api (``lastDayOfTheWeek``, ``lastWeekCalculationMethod``,
        ...). Values may be enum members, integers or labels. ``None`` values fall back to the defaults, an
        ``addLeapWeekToMonth`` of ``-1`` means "no month", and unrelated keys are ignored.
        """
        kwargs: dict[str, Any] = {}
        for field_name, aliases in _KEY_ALIASES.items():
            present = [alias for alias in aliases if data.get(alias) is not None]
            if len(present) > 1:
                raise ValueError(f"Conflicting keys for {field_name}: {', '.join(present)}")
            if present:
                kwargs[field_name] = data[present[0]]

        if kwargs.get("add_leap_week_to_month") == -1:
            del kwargs["add_leap_week_to_month"]

        missing = [
            aliases[0]
            for field_name, aliases in _KEY_ALIASES.items()
            if field_name in _REQUIRED_FIELDS and field_name not in kwargs
        ]
        if missing:
            raise ValueError(f"Missing required calendar options: {', '.join(missing)}")
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the camelCase shape of the JS package's options, omitting unset optional fields."""
        data: dict[str, Any] = {
            "weekGrouping": int(self.week_grouping),
            "lastDayOfWeek": int(self.last_day_of_week),
            "lastMonthOfYear": int(self.last_month_of_year),
            "weekCalculation": int(self.week_calculation),
            "beginningMonthIndex": self.beginning_month_index,
        }
        if self.add_leap_week_to_month is not None:
            data["addLeapWeekToMonth"] = self.add_leap_week_to_month
        if self.leap_year is not None:
            data["leapYear"] = self.leap_year
        if self.leap_year_end_date is not None:
            data["leapYearEndDate"] = self.leap_year_end_date.isoformat()
        if self.leap_year_frequency is not None:
            data["leapYearFrequency"] = self.leap_year_frequency
        return data


_REQUIRED_FIELDS = frozenset({"week_grouping", "last_day_of_week", "last_month_of_year", "week_calculation"})

NRF_CALENDAR_OPTIONS = RetailCalendarOptions(
    week_grouping=WeekGrouping.GROUP_454,
    last_day_of_week=LastDayOfWeek.SATURDAY,
    last_month_of_year=LastMonthOfYear.JANUARY,
    week_calculation=WeekCalculation.LAST_DAY_NEAREST_EOM,
)
"""The National Retail Federation 4-5-4 calendar: weeks end on Saturday, years end nearest the end of January."""
