"""Calendar configuration enums.

Integer values are identical to the JS ``retail-calendar`` package, so configurations stored as integers (for example
in the ``calendarconfiguration`` table) are interchangeable between the two implementations. Each member also has a
:attr:`~_LabeledIntEnum.label`: the string used by the database and by retail-calendar-api (``"4-4-5"``,
``"Saturday"``, ...).
"""

from __future__ import annotations

from enum import IntEnum
from typing import Self


class _LabeledIntEnum(IntEnum):
    """An ``IntEnum`` whose members also have a string label."""

    @property
    def label(self) -> str:
        """The label used for this member by the database and retail-calendar-api."""
        return self.name.title()

    @classmethod
    def from_label(cls, label: str) -> Self:
        """Look up a member by its label, e.g. ``WeekGrouping.from_label("4-5-4")``."""
        for member in cls:
            if member.label == label:
                return member
        valid = ", ".join(repr(member.label) for member in cls)
        raise ValueError(f"{label!r} is not a valid {cls.__name__} label; expected one of {valid}")

    @classmethod
    def coerce(cls, value: int | str) -> Self:
        """Convert a member, its integer value or its label into a member."""
        if isinstance(value, cls):
            return value
        if isinstance(value, bool):  # bool is an int subclass, but True/False are never meaningful here
            raise TypeError(f"{cls.__name__} cannot be created from a bool")
        if isinstance(value, str):
            return cls.from_label(value)
        if isinstance(value, int):
            return cls(value)
        raise TypeError(f"{cls.__name__} cannot be created from {type(value).__name__}")


class WeekGrouping(_LabeledIntEnum):
    """How many weeks each month of a quarter has. Labels are ``"4-4-5"``, ``"5-4-4"`` and ``"4-5-4"``."""

    GROUP_445 = 0
    GROUP_544 = 1
    GROUP_454 = 2

    @property
    def label(self) -> str:
        """``"4-4-5"``, ``"5-4-4"`` or ``"4-5-4"``."""
        return "-".join(self.name.removeprefix("GROUP_"))

    @property
    def weeks_per_month(self) -> tuple[int, int, int]:
        """Number of weeks of the three months in each quarter."""
        first, second, third = (int(weeks) for weeks in self.name.removeprefix("GROUP_"))
        return first, second, third


class LastDayOfWeek(_LabeledIntEnum):
    """The day retail weeks end on, as an ISO weekday (Monday is 1, Sunday is 7). Labels are ``"Monday"`` etc."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class LastMonthOfYear(_LabeledIntEnum):
    """The Gregorian month the retail year ends in. Labels are ``"January"`` etc.

    Values are 0-based (January is 0) to stay compatible with the JS package. Use :attr:`month` for the 1-based
    month number Python's :mod:`datetime` expects.
    """

    JANUARY = 0
    FEBRUARY = 1
    MARCH = 2
    APRIL = 3
    MAY = 4
    JUNE = 5
    JULY = 6
    AUGUST = 7
    SEPTEMBER = 8
    OCTOBER = 9
    NOVEMBER = 10
    DECEMBER = 11

    @property
    def month(self) -> int:
        """The 1-based Gregorian month number (January is 1)."""
        return self.value + 1


class WeekCalculation(_LabeledIntEnum):
    """How the last day of a retail year is chosen.

    * ``LAST_DAY_BEFORE_EOM``: the last ``last_day_of_week`` on or before the end of the last month.
    * ``LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR``: like ``LAST_DAY_BEFORE_EOM``, but when the next year would have 53
      weeks, this year gets them instead. Faithful to the JS package, the look-ahead only works for years ending in
      December; for any other month this behaves exactly like ``LAST_DAY_BEFORE_EOM``.
    * ``LAST_DAY_NEAREST_EOM``: the ``last_day_of_week`` nearest to the end of the last month (NRF calendar).
    * ``FIRST_BOW_OF_FIRST_MONTH``: the year starts on the first beginning of week on or after the first day of its
      first month.
    * ``PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM``: year boundaries follow the day *before* ``last_day_of_week`` nearest
      to the end of the month, shifted by one day.
    * ``CUSTOM_LEAP_YEAR``: a known year end date plus a fixed leap year frequency; see
      ``RetailCalendarOptions.leap_year``.
    """

    LAST_DAY_BEFORE_EOM = 0
    LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR = 1
    LAST_DAY_NEAREST_EOM = 2
    FIRST_BOW_OF_FIRST_MONTH = 3
    PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM = 4
    CUSTOM_LEAP_YEAR = 5

    @property
    def label(self) -> str:
        """The ``lastWeekCalculationMethod`` value of the database and retail-calendar-api."""
        return _WEEK_CALCULATION_LABELS[self]


_WEEK_CALCULATION_LABELS = {
    WeekCalculation.LAST_DAY_BEFORE_EOM: "lastDayBeforeEndOfMonth",
    WeekCalculation.LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR: "lastDayBeforeEndOfMonthExceptLeapYear",
    WeekCalculation.LAST_DAY_NEAREST_EOM: "lastDayNearestEndOfMonth",
    WeekCalculation.FIRST_BOW_OF_FIRST_MONTH: "firstBOWOfFirstMonth",
    WeekCalculation.PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM: "penultimateDayOfWeekNearestEndOfMonth",
    WeekCalculation.CUSTOM_LEAP_YEAR: "customLeapYear",
}
