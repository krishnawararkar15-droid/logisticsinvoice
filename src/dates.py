"""Date math and timestamp utilities for Accessorial Invoice Checker."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Optional, Union


def parse_iso_timestamp(val: Union[str, datetime, date, None]) -> Optional[datetime]:
    """Safely parse ISO timestamp string or return datetime. Returns None if invalid or empty."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    if not isinstance(val, str):
        return None
    cleaned = val.strip()
    if not cleaned or cleaned.lower() in ("null", "none", "unknown"):
        return None

    # Handle standard ISO formats, allowing space separator instead of 'T'
    cleaned = cleaned.replace(" ", "T")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        # Fallback formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
    return None


def calculate_calendar_days(start_dt: datetime, end_dt: datetime) -> int:
    """Calculate calendar days elapsed inclusive of start and end calendar days:
    (end_dt.date() - start_dt.date()).days + 1.
    E.g. 2026-06-23 to 2026-06-24 is (1) + 1 = 2 days.
    """
    days_diff = (end_dt.date() - start_dt.date()).days
    if days_diff < 0:
        return 0
    return days_diff + 1


def calculate_24h_blocks(start_dt: datetime, end_dt: datetime) -> int:
    """Calculate 24-hour blocks elapsed:
    math.ceil((end_dt - start_dt).total_seconds() / 86400).
    E.g. 19 hours -> ceil(19/24) = 1 block.
    """
    total_seconds = (end_dt - start_dt).total_seconds()
    if total_seconds <= 0:
        return 0
    return math.ceil(total_seconds / 86400.0)


def count_midnights_between(start_dt: datetime, end_dt: datetime) -> int:
    """Count midnights crossed between two timestamps:
    (end_dt.date() - start_dt.date()).days.
    E.g. from 2026-06-23 21:00 to 2026-06-24 08:00 is 1 midnight.
    """
    midnights = (end_dt.date() - start_dt.date()).days
    return max(0, midnights)


def hours_between(start_dt: datetime, end_dt: datetime) -> float:
    """Calculate total elapsed hours as a float."""
    return max(0.0, (end_dt - start_dt).total_seconds() / 3600.0)
