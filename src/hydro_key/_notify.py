"""macOS notification and sound helpers for HydroKey."""

from __future__ import annotations

import logging
import subprocess

import rumps

logger = logging.getLogger(__name__)


def play_sound() -> None:
    """Play the Glass system sound."""
    try:
        from AppKit import NSSound  # noqa: PLC0415

        sound = NSSound.soundNamed_("Glass")
        if sound:
            sound.play()
            return
    except ImportError:
        pass

    try:
        subprocess.run(
            ["/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff"],
            check=False,
            capture_output=True,
        )
    except OSError:
        logger.warning("Failed to play sound")


def notify_recorded(added_ml: int, total_ml: int, goal_ml: int) -> None:
    """Show notification for a recorded intake."""
    rumps.notification(
        title="HydroKey",
        subtitle="",
        message=f"+{added_ml}ml → {total_ml}ml / {goal_ml}ml",
    )


def notify_undo(removed_ml: int, total_ml: int, goal_ml: int) -> None:
    """Show notification for an undone intake."""
    rumps.notification(
        title="HydroKey",
        subtitle="",
        message=f"-{removed_ml}ml → {total_ml}ml / {goal_ml}ml",
    )


def notify_reminder(total_ml: int, goal_ml: int) -> None:
    """Show a reminder notification."""
    rumps.notification(
        title="HydroKey",
        subtitle="",
        message=f"Time to drink water! ({total_ml}ml / {goal_ml}ml)",
    )
