"""Configuration management for HydroKey."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
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
    hotkey: str = field(default="cmd+shift+w")


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

    kwargs: dict[str, int | str] = {}
    defaults = Config()
    for key in asdict(defaults):
        if key in raw:
            kwargs[key] = raw[key]

    try:
        return Config(**kwargs)  # type: ignore[arg-type]
    except TypeError:
        logger.warning("Invalid config data, using defaults")
        return Config()


def save_config(config: Config, path: Path = CONFIG_PATH) -> None:
    """Atomically save configuration to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(asdict(config), indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.rename(path)
