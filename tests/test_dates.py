"""Unit tests for timestamp and date math functions in src/dates.py."""

from datetime import date, datetime

from src.dates import (
    calculate_24h_blocks,
    calculate_calendar_days,
    count_midnights_between,
    hours_between,
    parse_iso_timestamp,
)


def test_parse_iso_timestamp():
    # Valid ISO strings
    dt = parse_iso_timestamp("2026-06-23T21:00")
    assert dt == datetime(2026, 6, 23, 21, 0)

    dt2 = parse_iso_timestamp("2026-06-23 21:00:00")
    assert dt2 == datetime(2026, 6, 23, 21, 0, 0)

    dt3 = parse_iso_timestamp("2026-06-23")
    assert dt3 == datetime(2026, 6, 23, 0, 0)

    # Pass datetime directly
    now = datetime.now()
    assert parse_iso_timestamp(now) == now

    # Pass date
    d = date(2026, 6, 23)
    assert parse_iso_timestamp(d) == datetime(2026, 6, 23, 0, 0)

    # Null / empty / invalid
    assert parse_iso_timestamp(None) is None
    assert parse_iso_timestamp("") is None
    assert parse_iso_timestamp("null") is None
    assert parse_iso_timestamp("None") is None
    assert parse_iso_timestamp("invalid-date") is None


def test_calculate_calendar_days():
    # Same calendar day (e.g. 08:00 to 16:00 on June 23)
    start = datetime(2026, 6, 23, 8, 0)
    end = datetime(2026, 6, 23, 16, 0)
    assert calculate_calendar_days(start, end) == 1

    # Crosses midnight into next day (June 23 21:00 to June 24 16:00)
    end_next = datetime(2026, 6, 24, 16, 0)
    assert calculate_calendar_days(start, end_next) == 2

    # Negative range returns 0
    assert calculate_calendar_days(end_next, start) == 0


def test_calculate_24h_blocks():
    # 19 hours elapsed -> ceil(19/24) = 1 block
    start = datetime(2026, 6, 23, 21, 0)
    end = datetime(2026, 6, 24, 16, 0)
    assert calculate_24h_blocks(start, end) == 1

    # Exactly 24 hours -> 1 block
    end_24h = datetime(2026, 6, 24, 21, 0)
    assert calculate_24h_blocks(start, end_24h) == 1

    # 24 hours + 1 minute -> ceil(24.016/24) = 2 blocks
    end_25h = datetime(2026, 6, 24, 21, 1)
    assert calculate_24h_blocks(start, end_25h) == 2

    # Zero or negative seconds
    assert calculate_24h_blocks(start, start) == 0
    assert calculate_24h_blocks(end, start) == 0


def test_count_midnights_between():
    # 21:00 on June 23 to 08:00 on June 24 crosses 1 midnight
    start = datetime(2026, 6, 23, 21, 0)
    end = datetime(2026, 6, 24, 8, 0)
    assert count_midnights_between(start, end) == 1

    # Same day does not cross midnight
    same_day = datetime(2026, 6, 23, 23, 30)
    assert count_midnights_between(start, same_day) == 0

    # 3 midnights
    three_days = datetime(2026, 6, 26, 8, 0)
    assert count_midnights_between(start, three_days) == 3


def test_hours_between():
    start = datetime(2026, 6, 24, 8, 0)
    end = datetime(2026, 6, 24, 12, 30)
    assert hours_between(start, end) == 4.5
    assert hours_between(end, start) == 0.0
