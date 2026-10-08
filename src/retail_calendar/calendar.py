"""The retail calendar of a single retail year."""

import datetime as dt
import functools
from dataclasses import dataclass, field

from retail_calendar._dates import ONE_DAY, ONE_WEEK, end_of_month, to_date, weeks_between
from retail_calendar.enums import LastMonthOfYear
from retail_calendar.models import DateSegment, RetailDay, RetailMonth, RetailWeek
from retail_calendar.options import RetailCalendarOptions
from retail_calendar.strategies import strategy_for

MIN_YEAR = 2
"""Smallest supported retail year (the calendar looks one Gregorian year back)."""
MAX_YEAR = 9997
"""Largest supported retail year (the calendar looks up to two Gregorian years ahead)."""

_DAYS_IN_WEEK = 7
_MONTHS_IN_YEAR = 12
_MONTHS_IN_QUARTER = 3


@dataclass(frozen=True, slots=True, init=False)
class RetailCalendar:
    """The weeks, months and days of one retail year.

    ``year`` is the retail (plan) year: the Gregorian year of its first month. With the NRF calendar, retail year
    2017 runs from February 2017 to January 2018.

    Building a calendar is cheap but not free; use :func:`get_retail_calendar` to reuse cached instances.
    """

    options: RetailCalendarOptions
    year: int
    number_of_weeks: int
    """52 or 53."""
    first_day: dt.date
    last_day: dt.date
    weeks: tuple[RetailWeek, ...] = field(repr=False)
    months: tuple[RetailMonth, ...] = field(repr=False)
    _days: tuple[RetailDay, ...] | None = field(repr=False, compare=False, hash=False)

    def __init__(self, options: RetailCalendarOptions, year: int) -> None:
        if not MIN_YEAR <= year <= MAX_YEAR:
            raise ValueError(f"year must be between {MIN_YEAR} and {MAX_YEAR}, got {year}")

        gregorian_year = year if options.last_month_of_year is LastMonthOfYear.DECEMBER else year + 1
        last_day = _last_day_of_year(options, gregorian_year, year)
        number_of_weeks = weeks_between(last_day, _last_day_of_year(options, gregorian_year - 1, year - 1))
        if number_of_weeks not in (52, 53):
            raise ValueError(f"Options produce {number_of_weeks} weeks for retail year {year}; expected 52 or 53")
        first_day = last_day - number_of_weeks * ONE_WEEK + ONE_DAY

        weeks = _generate_weeks(options, first_day, number_of_weeks)
        months = _generate_months(options, weeks, number_of_weeks)

        set_field = functools.partial(object.__setattr__, self)
        set_field("options", options)
        set_field("year", year)
        set_field("number_of_weeks", number_of_weeks)
        set_field("first_day", first_day)
        set_field("last_day", last_day)
        set_field("weeks", weeks)
        set_field("months", months)
        set_field("_days", None)

    @property
    def days(self) -> tuple[RetailDay, ...]:
        """Every day of the year. Built on first access, since most uses only need weeks."""
        if self._days is None:
            object.__setattr__(
                self, "_days", tuple(_day(week, index) for week in self.weeks for index in range(_DAYS_IN_WEEK))
            )
        assert self._days is not None
        return self._days

    @property
    def is_leap_year(self) -> bool:
        """Whether the year has 53 weeks."""
        return self.number_of_weeks == 53

    def __contains__(self, date: dt.date) -> bool:
        return self.first_day <= to_date(date) <= self.last_day

    def week_of(self, date: dt.date) -> RetailWeek:
        """The week containing ``date``. Raises ``ValueError`` if the date is outside of this calendar."""
        return self.weeks[self._day_index(date) // _DAYS_IN_WEEK]

    def day_of(self, date: dt.date) -> RetailDay:
        """The day for ``date``. Raises ``ValueError`` if the date is outside of this calendar."""
        week_index, day_index = divmod(self._day_index(date), _DAYS_IN_WEEK)
        return _day(self.weeks[week_index], day_index)

    def week(self, week_of_year: int) -> RetailWeek:
        """The week with the given 0-based ``week_of_year``. Raises ``ValueError`` if there is no such week."""
        if not 0 <= week_of_year < self.number_of_weeks:
            raise ValueError(f"Week {week_of_year} not found in year {self.year} ({self.number_of_weeks} weeks)")
        return self.weeks[week_of_year]

    def segment_of(self, date: dt.date) -> DateSegment:
        """The (retail year, week of year) of ``date``. Raises ``ValueError`` if it is outside of this calendar."""
        return DateSegment(year=self.year, week=self.week_of(date).week_of_year)

    def _day_index(self, date: dt.date) -> int:
        date = to_date(date)
        if date not in self:
            raise ValueError(f"{date} is not in retail year {self.year} ({self.first_day} to {self.last_day})")
        return (date - self.first_day).days


@functools.lru_cache(maxsize=4096)
def get_retail_calendar(options: RetailCalendarOptions, year: int) -> RetailCalendar:
    """A cached :class:`RetailCalendar`. Calendars are immutable, so sharing instances is safe."""
    return RetailCalendar(options, year)


def _last_day_of_year(options: RetailCalendarOptions, gregorian_year: int, retail_year: int) -> dt.date:
    last_day_of_gregorian_year = end_of_month(gregorian_year, options.last_month_of_year.month)
    strategy = strategy_for(options)
    return strategy(last_day_of_gregorian_year, options.last_day_of_week, retail_year)


def _week_distribution(options: RetailCalendarOptions, number_of_weeks: int) -> list[int]:
    distribution = list(options.week_grouping.weeks_per_month) * (_MONTHS_IN_YEAR // _MONTHS_IN_QUARTER)
    if options.add_leap_week_to_month is not None and number_of_weeks == 53:
        distribution[options.add_leap_week_to_month] += 1
    return distribution


def _generate_weeks(options: RetailCalendarOptions, first_day: dt.date, number_of_weeks: int) -> tuple[RetailWeek, ...]:
    weeks: list[RetailWeek] = []
    week_of_quarter = 0
    for month_index, weeks_in_month in enumerate(_week_distribution(options, number_of_weeks)):
        if month_index % _MONTHS_IN_QUARTER == 0:
            week_of_quarter = 0
        for week_of_month in range(weeks_in_month):
            start_date = first_day + len(weeks) * ONE_WEEK
            weeks.append(
                RetailWeek(
                    week_of_year=len(weeks),
                    week_of_month=week_of_month,
                    week_of_quarter=week_of_quarter,
                    month_of_year=month_index + options.beginning_month_index,
                    quarter_of_year=month_index // _MONTHS_IN_QUARTER + 1,
                    start_date=start_date,
                    end_date=start_date + ONE_WEEK - ONE_DAY,
                )
            )
            week_of_quarter += 1

    # A 53rd week that was not added to any month.
    while len(weeks) < number_of_weeks:
        start_date = first_day + len(weeks) * ONE_WEEK
        weeks.append(
            RetailWeek(
                week_of_year=len(weeks),
                week_of_month=None,
                week_of_quarter=None,
                month_of_year=None,
                quarter_of_year=None,
                start_date=start_date,
                end_date=start_date + ONE_WEEK - ONE_DAY,
            )
        )
    return tuple(weeks)


def _generate_months(
    options: RetailCalendarOptions, weeks: tuple[RetailWeek, ...], number_of_weeks: int
) -> tuple[RetailMonth, ...]:
    months: list[RetailMonth] = []
    for month_index, weeks_in_month in enumerate(_week_distribution(options, number_of_weeks)):
        month_of_year = month_index + options.beginning_month_index
        weeks_of_month = tuple(week for week in weeks if week.month_of_year == month_of_year)
        months.append(
            RetailMonth(
                month_of_year=month_of_year,
                quarter_of_year=month_index // _MONTHS_IN_QUARTER + 1,
                number_of_weeks=weeks_in_month,
                weeks=weeks_of_month,
                start_date=weeks_of_month[0].start_date,
                end_date=weeks_of_month[-1].end_date,
            )
        )
    return tuple(months)


def _day(week: RetailWeek, day_index: int) -> RetailDay:
    """The ``day_index``-th (0-based) day of ``week``."""
    return RetailDay(
        date=week.start_date + dt.timedelta(days=day_index),
        day_of_year=week.week_of_year * _DAYS_IN_WEEK + day_index + 1,
        day_of_week=day_index + 1,
        day_of_month=None if week.week_of_month is None else week.week_of_month * _DAYS_IN_WEEK + day_index + 1,
        week_of_year=week.week_of_year,
        month_of_year=week.month_of_year,
    )
