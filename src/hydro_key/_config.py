"""Configuration management for HydroKey."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

logger = logging.getLogger(__name__)

APP_DIR = Path.home() / ".config" / "hydrokey"
CONFIG_PATH = APP_DIR / "config.json"

GOAL_OPTIONS: list[int] = [1000, 1500, 2000, 2500, 3000]
PER_PRESS_OPTIONS: list[int] = [50, 100, 150, 200, 250, 300, 500]
REMINDER_OPTIONS: list[int] = [0, 30, 45, 60, 90]
ACTIVE_START_OPTIONS: list[int] = list(range(6, 13))
ACTIVE_END_OPTIONS: list[int] = list(range(18, 24))
HOTKEY_OPTIONS: list[str] = [
    "cmd+shift+w",
    "cmd+shift+h",
    "cmd+shift+d",
    "ctrl+shift+w",
    "ctrl+shift+h",
]


@dataclass
class Config:
    """Application configuration with sensible defaults."""

    goal_ml: int = 2000
    per_press_ml: int = 100
    reminder_interval_min: int = 60
    active_start_hour: int = 9
    active_end_hour: int = 21
    hotkey: str = "cmd+shift+w"

    def __post_init__(self) -> None:
        if self.goal_ml not in GOAL_OPTIONS:
            msg = f"goal_ml must be one of {GOAL_OPTIONS}, got {self.goal_ml}"
            raise ValueError(msg)
        if self.per_press_ml not in PER_PRESS_OPTIONS:
            msg = f"per_press_ml must be one of {PER_PRESS_OPTIONS}, got {self.per_press_ml}"
            raise ValueError(msg)
        if self.reminder_interval_min not in REMINDER_OPTIONS:
            msg = f"reminder_interval_min must be one of {REMINDER_OPTIONS}, got {self.reminder_interval_min}"
            raise ValueError(msg)
        if self.active_start_hour not in ACTIVE_START_OPTIONS:
            msg = f"active_start_hour must be one of {ACTIVE_START_OPTIONS}, got {self.active_start_hour}"
            raise ValueError(msg)
        if self.active_end_hour not in ACTIVE_END_OPTIONS:
            msg = f"active_end_hour must be one of {ACTIVE_END_OPTIONS}, got {self.active_end_hour}"
            raise ValueError(msg)
        if self.hotkey not in HOTKEY_OPTIONS:
            msg = f"hotkey must be one of {HOTKEY_OPTIONS}, got {self.hotkey}"
            raise ValueError(msg)
        if self.active_start_hour >= self.active_end_hour:
            msg = "active_start_hour must be < active_end_hour"
            raise ValueError(msg)


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Load configuration from JSON file, returning defaults for missing/invalid data."""
    if not path.is_file():
        return Config()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to read config from %s, using defaults", path)
        return Config()

    if not isinstance(raw, dict):
        return Config()

    known_keys = {f.name for f in fields(Config)}
    kwargs = {k: v for k, v in raw.items() if k in known_keys}

    try:
        return Config(**kwargs)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid config data (keys=%s), using defaults",
            list(kwargs.keys()),
            exc_info=True,
        )
        return Config()


def save_config(config: Config, path: Path = CONFIG_PATH) -> None:
    """Atomically save configuration to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            json.dumps(asdict(config), indent=2) + "\n",
            encoding="utf-8",
        )
        tmp_path.rename(path)
    except OSError:
        logger.exception("Failed to save config to %s", path)
        raise
