# Retail Calendar

A configurable merchandising and retail calendar for Python: NRF 4-5-4, 4-4-5, 5-4-4 and custom leap year
calendars, with their Gregorian boundaries.

This is a port of the [`retail-calendar`](https://github.com/holonk/retail-calendar) npm package (v4.1.2). It
produces the same calendars, and its integer and label values match the JS package, the `calendarconfiguration` table
and retail-calendar-api, so tenant configurations can be used as they are.

- No dependencies outside the Python standard library.
- Typed (`py.typed`), immutable value objects, cached calendars.
- Python 3.14+.

> [!IMPORTANT]
> **Note for AI agents and contributors: keep this repo and [holonk/retail-calendar](https://github.com/holonk/retail-calendar) in sync.**
>
> The two packages are one calendar in two languages. retail-calendar-api, holonk and the frontend use the JS
> package; toolio-ml uses this one. If they ever disagree, services disagree about which week a date belongs to. When
> you add a feature, fix a bug or change behavior in either repo:
>
> 1. Make the same change in the other repo, in the same piece of work. Never fix a bug on one side only, even an
>    obvious one such as the December-only `LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR` look-ahead.
> 2. Keep the public contract identical: enum integer values and labels, option names (camelCase in JS,
>    `from_dict`/`to_dict` keys here), defaults and validation rules.
> 3. Add the same test cases to both test suites. Fixtures converted from the JS tests live in `tests/data`.
> 4. Release the JS package, pin the new version in `scripts/golden/package.json`, regenerate the reference data
>    (see [Parity with the JS package](#parity-with-the-js-package)) and commit it with the Python change.
>    `tests/test_golden.py` must pass against the regenerated data.
> 5. Update both READMEs, including the [JS to Python table](#coming-from-the-js-package) below.
>
> Python-only conveniences that don't change calendar results don't need a JS counterpart. If you're unsure whether
> a change affects results, it does: mirror it.
>
> Like the JS package, this library stays dependency-free. Integration helpers that need other libraries (pandas
> DataFrame conversions, database access, ...) belong in the consuming repo, such as toolio-ml, not here.

## Installation

```shell
uv add "retail-calendar @ git+ssh://git@github.com/holonk/retail-calendar-python.git@v1.0.0"
```

## Usage

```python
import datetime as dt

from retail_calendar import (
    LastDayOfWeek,
    LastMonthOfYear,
    RetailCalendarOptions,
    WeekCalculation,
    WeekGrouping,
    get_retail_calendar,
)

options = RetailCalendarOptions(
    week_calculation=WeekCalculation.LAST_DAY_NEAREST_EOM,
    week_grouping=WeekGrouping.GROUP_454,
    last_day_of_week=LastDayOfWeek.SATURDAY,
    last_month_of_year=LastMonthOfYear.JANUARY,
)  # the same as NRF_CALENDAR_OPTIONS

calendar = get_retail_calendar(options, 2017)  # cached; RetailCalendar(options, 2017) builds a new one
calendar.year  # 2017, the Gregorian year of the first month
calendar.number_of_weeks  # 52 or 53 (53 for 2017)
calendar.first_day  # datetime.date(2017, 1, 29)
calendar.last_day  # datetime.date(2018, 2, 3)
```

A retail calendar always has 12 months made of whole weeks. Every boundary is a `datetime.date`, and end dates are
inclusive.

```python
month = calendar.months[0]
month.month_of_year  # 1 (counted from beginning_month_index, 1 by default)
month.quarter_of_year  # 1 to 4
month.number_of_weeks  # 4, 5, 4, ... with 4-5-4 week grouping
month.weeks  # tuple of RetailWeek
month.start_date, month.end_date

week = calendar.weeks[0]
week.week_of_year, week.week_of_month, week.week_of_quarter  # all 0-based
week.month_of_year, week.quarter_of_year
week.start_date, week.end_date

day = calendar.days[0]  # one RetailDay per day of the year
day.date, day.day_of_year, day.day_of_week, day.day_of_month, day.week_of_year, day.month_of_year
```

### Dates to retail weeks and back

These mirror retail-calendar-api's endpoints:

```python
from retail_calendar import DateSegment, date_to_segment, leap_years, segment_to_date, week_of_gregorian_date

date_to_segment(dt.date(2020, 2, 1), options)  # DateSegment(year=2019, week=51)
segment_to_date(DateSegment(2019, 51), options)  # datetime.date(2020, 1, 26), the first day of that week
leap_years(range(2010, 2030), options)  # [2012, 2017, 2023, 2028]
week_of_gregorian_date(dt.date(2020, 2, 1), options)  # WeekOfCalendar(calendar=..., week=...)

calendar.week_of(dt.date(2017, 3, 1))  # RetailWeek containing the date
calendar.day_of(dt.date(2017, 3, 1))  # RetailDay of the date
dt.date(2017, 3, 1) in calendar  # True
```

`datetime` values (including `pandas.Timestamp`) are accepted wherever a date is; their time is ignored.

### Configuration from the database or the API

`RetailCalendarOptions.from_dict` accepts the JS package's keys as well as the `calendarconfiguration` /
retail-calendar-api keys, with integer or label values. Unrelated keys are ignored.

```python
RetailCalendarOptions.from_dict(
    {
        "weekGrouping": "4-4-5",
        "lastDayOfTheWeek": "Saturday",
        "lastMonthOfTheYear": "January",
        "lastWeekCalculationMethod": "lastDayNearestEndOfMonth",
        "addLeapWeekToMonth": None,
    }
)
options.to_dict()  # the JS package's camelCase shape
```

## 53-week years

A retail calendar has 52 or 53 weeks. By default the 53rd week belongs to no month: its `month_of_year`,
`week_of_month`, `quarter_of_year` and `week_of_quarter` are `None` (`week.is_leap_week` is `True`), and so are
`day_of_month` and `month_of_year` of its days. Its `week_of_year` is 52.

With `add_leap_week_to_month=10`, the 53rd week is added to the 11th month instead (the value is 0-based).

## Options

| Option | Values |
| --- | --- |
| `week_grouping` | `GROUP_454`, `GROUP_544`, `GROUP_445`: weeks per month in each quarter |
| `last_day_of_week` | `MONDAY` (1) to `SUNDAY` (7): the day every week, month and year ends on |
| `last_month_of_year` | `JANUARY` (0) to `DECEMBER` (11). The retail year is the Gregorian year of its first month: with January, retail year 2017 ends in January 2018 |
| `week_calculation` | How the year end is chosen, below |
| `add_leap_week_to_month` | `None` (default) or 0 to 11: the month that gets the 53rd week |
| `beginning_month_index` | `month_of_year` of the first month, default 1 |
| `leap_year`, `leap_year_end_date`, `leap_year_frequency` | Required for `CUSTOM_LEAP_YEAR` |

`week_calculation`:

- `LAST_DAY_NEAREST_EOM`: the last day of week nearest to the end of the last month (NRF).
- `LAST_DAY_BEFORE_EOM`: the last day of week on or before the end of the last month.
- `LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR`: like `LAST_DAY_BEFORE_EOM`, but if the next year would have 53 weeks, this
  year gets them. As in the JS package, this only works for years ending in December; otherwise it behaves exactly
  like `LAST_DAY_BEFORE_EOM`.
- `FIRST_BOW_OF_FIRST_MONTH`: the year starts on the first beginning of week of its first month.
- `PENULTIMATE_DAY_OF_WEEK_NEAREST_EOM`: weeks end on `last_day_of_week`, but year boundaries follow the day before
  it nearest to the end of month.
- `CUSTOM_LEAP_YEAR`: `leap_year` ends on `leap_year_end_date`, and every `leap_year_frequency`-th year from it has
  53 weeks. With `leap_year=2005, leap_year_end_date=date(2006, 3, 11), leap_year_frequency=6`, years 2005, 2011,
  2017, 2023, ... have 53 weeks.

Supported retail years are 2 to 9997.

## Coming from the JS package

| JS | Python |
| --- | --- |
| `new RetailCalendarFactory(options, year)` | `RetailCalendar(options, year)` |
| `RetailCalendarFactory.getRetailCalendar(options, year)` | `get_retail_calendar(options, year)` |
| `weekOfGregorianDate(date, options)` | `week_of_gregorian_date(date, options)` |
| `NRFCalendarOptions` | `NRF_CALENDAR_OPTIONS` |
| `WeekGrouping.Group454`, `LastDayOfWeek.Saturday`, ... | `WeekGrouping.GROUP_454`, `LastDayOfWeek.SATURDAY`, ... (same integer values) |
| `WeekCalculation.LastDayNearestEOM`, `LastDayBeforeEomExceptLeapYear`, `FirstBOWOfFirstMonth`, ... | `LAST_DAY_NEAREST_EOM`, `LAST_DAY_BEFORE_EOM_EXCEPT_LEAP_YEAR`, `FIRST_BOW_OF_FIRST_MONTH`, ... |
| `weekOfYear`, `monthOfYear`, ... | `week_of_year`, `month_of_year`, ... |
| `gregorianStartDate`, `gregorianEndDate` (`Date`, end at 23:59:59.999) | `start_date`, `end_date` (`datetime.date`, inclusive) |
| day `gregorianStartDate` | `day.date` |
| `-1` for the 53rd week's month fields | `None` |
| `calendar.addLeapWeekToMonth` (`-1` when unset) | `calendar.options.add_leap_week_to_month` (`None` when unset) |
| `leapYearEndDate: "2006-03-11"` | `leap_year_end_date=date(2006, 3, 11)` (ISO strings are accepted too) |

Differences in behavior:

- **No timezone effects.** The JS package does its date math in the host's local time, so DST shifts can move a year
  boundary by a week, depending on where it runs: 9 to 54 of 21,420 tested calendars differ between UTC and other
  zones. This package works on plain dates and always matches the JS package running in UTC, as retail-calendar-api
  does.
- **Validation.** Invalid options (unknown labels, `add_leap_week_to_month` outside 0 to 11, missing custom leap year
  options, unsupported years) raise `ValueError` when created instead of failing later or producing wrong calendars.
- **Immutability.** Calendars, weeks, months, days and options are frozen, so the cache can be shared safely.

## Development

```shell
uv sync
uv run pytest -n auto      # tests, including parity with the JS package
uv run ruff format . && uv run ruff check . && uv run mypy
uv run pre-commit install  # optional: run the checks on commit
```

### Parity with the JS package

`tests/test_golden.py` compares this package with reference data generated from the published JS package (see
`tests/data/golden/SOURCE.txt`):

- year boundaries of every strategy, week end day and year end month for 1950 to 2060,
- every week, month and day of 576 configurations (all strategies, week groupings and leap week options), for 2000 to
  2050 (compared through a digest; full detail for 2023),
- 20,000 random date lookups.

To regenerate it, for example after a change in the JS package:

```shell
cd scripts/golden
npm ci
npm run generate  # runs in TZ=UTC
```

Some fixtures in `tests/data` are converted from the JS package's tests. The JS fixture for the "last day nearest
EOM, 4-4-5, arbitrary leap year" case had stray spaces in some dates (`"2024-01 -08"`), which its parser tolerated;
they are fixed here.
