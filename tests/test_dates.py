"""Date helpers, including the cases of the JS package's ``__tests__/date_utils.test.ts``."""

import datetime as dt

import pytest

from retail_calendar._dates import end_of_month, to_date, weeks_between, with_iso_weekday


@pytest.mark.parametrize(
    ("days", "expected"),
    [(1, dt.date(2023, 3, 30)), (2, dt.date(2023, 3, 31)), (3, dt.date(2023, 4, 1)), (-29, dt.date(2023, 2, 28))],
)
def test_adding_days_across_month_ends(days: int, expected: dt.date) -> None:
    # The JS package needed these to guard against Date.setDate overflow bugs; timedelta has none.
    assert dt.date(2023, 3, 29) + dt.timedelta(days=days) == expected


def test_end_of_month() -> None:
    assert end_of_month(2024, 2) == dt.date(2024, 2, 29)
    assert end_of_month(2023, 2) == dt.date(2023, 2, 28)
    assert end_of_month(2023, 12) == dt.date(2023, 12, 31)


def test_with_iso_weekday_stays_in_the_monday_to_sunday_week() -> None:
    wednesday = dt.date(2023, 3, 29)
    assert with_iso_weekday(wednesday, 1) == dt.date(2023, 3, 27)
    assert with_iso_weekday(wednesday, 3) == wednesday
    assert with_iso_weekday(wednesday, 7) == dt.date(2023, 4, 2)


def test_weeks_between_rounds_down() -> None:
    assert weeks_between(dt.date(2023, 1, 15), dt.date(2023, 1, 1)) == 2
    assert weeks_between(dt.date(2023, 1, 14), dt.date(2023, 1, 1)) == 1
    assert weeks_between(dt.date(2023, 1, 1), dt.date(2023, 1, 2)) == -1


def test_to_date() -> None:
    assert to_date(dt.datetime(2023, 1, 1, 23, 59)) == dt.date(2023, 1, 1)
    assert type(to_date(dt.datetime(2023, 1, 1))) is dt.date
    assert to_date(dt.date(2023, 1, 1)) == dt.date(2023, 1, 1)
