"""Value objects describing the weeks, months and days of a retail calendar."""

import datetime as dt
from dataclasses import dataclass

from retail_calendar._dates import to_date


@dataclass(frozen=True, slots=True)
class RetailWeek:
    """A retail week. Both ``start_date`` and ``end_date`` are inclusive.

    In 53-week years whose 53rd week is not assigned to a month (the default), that week has ``None`` for every
    month and quarter field; see :attr:`is_leap_week`.
    """

    week_of_year: int
    """0-based week number within the retail year."""
    week_of_month: int | None
    """0-based week number within the retail month."""
    week_of_quarter: int | None
    """0-based week number within the retail quarter."""
    month_of_year: int | None
    """Retail month, counted from ``RetailCalendarOptions.beginning_month_index`` (1 by default)."""
    quarter_of_year: int | None
    """Retail quarter, 1 to 4."""
    start_date: dt.date
    end_date: dt.date

    @property
    def is_leap_week(self) -> bool:
        """Whether this is a 53rd week that does not belong to any month."""
        return self.month_of_year is None

    def __contains__(self, date: dt.date) -> bool:
        return self.start_date <= to_date(date) <= self.end_date


@dataclass(frozen=True, slots=True)
class RetailMonth:
    """A retail month made of whole retail weeks. Both ``start_date`` and ``end_date`` are inclusive."""

    month_of_year: int
    """Retail month, counted from ``RetailCalendarOptions.beginning_month_index`` (1 by default)."""
    quarter_of_year: int
    """Retail quarter, 1 to 4."""
    number_of_weeks: int
    weeks: tuple[RetailWeek, ...]
    start_date: dt.date
    end_date: dt.date

    def __contains__(self, date: dt.date) -> bool:
        return self.start_date <= to_date(date) <= self.end_date


@dataclass(frozen=True, slots=True)
class RetailDay:
    """A single day of a retail calendar.

    Days of a 53rd week that does not belong to any month have ``None`` for ``month_of_year`` and ``day_of_month``.
    """

    date: dt.date
    day_of_year: int
    """1-based day number within the retail year."""
    day_of_week: int
    """1-based day number within the retail week (1 is the first day of the week, not necessarily Monday)."""
    day_of_month: int | None
    """1-based day number within the retail month."""
    week_of_year: int
    """0-based week number within the retail year."""
    month_of_year: int | None
    """Retail month, counted from ``RetailCalendarOptions.beginning_month_index`` (1 by default)."""

    @property
    def gregorian_month_of_year(self) -> int:
        """1-based Gregorian month of :attr:`date`."""
        return self.date.month

    @property
    def gregorian_day_of_month(self) -> int:
        """1-based Gregorian day of month of :attr:`date`."""
        return self.date.day

    @property
    def gregorian_day_of_year(self) -> int:
        """1-based Gregorian day of year of :attr:`date`."""
        return self.date.timetuple().tm_yday


@dataclass(frozen=True, slots=True)
class DateSegment:
    """A retail week identified the way retail-calendar-api and toolio-ml do: retail year plus 0-based week."""

    year: int
    week: int
