"""Reminder timer logic for HydroKey."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


def is_within_active_hours(now: datetime, start_hour: int, end_hour: int) -> bool:
    """Check if the current time is within the active hours window."""
    return start_hour <= now.hour < end_hour


def should_fire_reminder(
    now: datetime,
    last_interaction: datetime | None,
    interval_min: int,
    start_hour: int,
    end_hour: int,
) -> bool:
    """Determine whether a reminder notification should fire.

    Returns True when all conditions are met:
    - interval_min > 0 (reminders enabled)
    - Current time is within active hours
    - Enough time has elapsed since last interaction
    """
    if interval_min <= 0:
        return False

    if not is_within_active_hours(now, start_hour, end_hour):
        return False

    if last_interaction is None:
        return True

    elapsed = (now - last_interaction).total_seconds()
    return elapsed >= interval_min * 60
