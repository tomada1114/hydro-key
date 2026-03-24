"""macOS notification and sound helpers for HydroKey."""

from __future__ import annotations

import logging
import subprocess

import rumps

logger = logging.getLogger(__name__)

try:
    from AppKit import NSSound as _NSSound
except ImportError:
    _NSSound = None


def play_sound() -> None:
    """Play the Glass system sound."""
    if _NSSound is not None:
        sound = _NSSound.soundNamed_("Glass")
        if sound:
            sound.play()
            return
        logger.warning(
            "NSSound.soundNamed_('Glass') returned None; falling back to afplay"
        )

    try:
        result = subprocess.run(
            ["/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff"],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            logger.warning(
                "afplay exited with code %d: %s",
                result.returncode,
                result.stderr.decode(errors="replace"),
            )
    except OSError:
        logger.warning("Failed to play sound via afplay", exc_info=True)


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
