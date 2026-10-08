import datetime as dt
import json
from pathlib import Path
from typing import Any

from retail_calendar import RetailWeek

DATA_DIR = Path(__file__).parent / "data"


def load_fixture(name: str) -> Any:
    """Load a fixture converted from the JS package's ``__tests__/data`` directory."""
    return json.loads((DATA_DIR / f"{name}.json").read_text())


def nullable(value: int) -> int | None:
    """The JS package uses -1 where the Python port uses None."""
    return None if value == -1 else value


def assert_same_week(actual: RetailWeek, expected: dict[str, Any]) -> None:
    """Port of the JS ``toBeTheSameWeekAs`` matcher."""
    assert actual == RetailWeek(
        week_of_year=expected["weekOfYear"],
        week_of_month=nullable(expected["weekOfMonth"]),
        week_of_quarter=nullable(expected["weekOfQuarter"]),
        month_of_year=nullable(expected["monthOfYear"]),
        quarter_of_year=nullable(expected["quarterOfYear"]),
        start_date=dt.date.fromisoformat(expected["gregorianStartDate"]),
        end_date=dt.date.fromisoformat(expected["gregorianEndDate"]),
    )
