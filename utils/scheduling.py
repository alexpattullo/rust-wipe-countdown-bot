"""Small, dependency-free helpers for wipe schedule calculations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


LONDON = ZoneInfo("Europe/London")


def next_force_wipe(now: datetime | None = None) -> int:
    """Return the next Thursday at 19:00 in the Europe/London timezone."""

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(LONDON)

    candidate = current.replace(hour=19, minute=0, second=0, microsecond=0)
    days_until_thursday = (3 - candidate.weekday()) % 7
    candidate += timedelta(days=days_until_thursday)

    if candidate <= current:
        candidate += timedelta(days=7)

    return int(candidate.timestamp())


def roll_forward(timestamp: int | float, interval: int, now: int | None = None) -> int:
    """Move a scheduled Unix timestamp into the future by whole intervals."""

    if interval <= 0:
        raise ValueError("The schedule interval must be greater than zero")

    current = int(now if now is not None else datetime.now(timezone.utc).timestamp())
    value = int(timestamp)
    while value <= current:
        value += interval
    return value
