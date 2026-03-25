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

MODIFIER_OPTIONS: list[str] = ["cmd", "ctrl", "alt", "shift"]
MODIFIER_DISPLAY: dict[str, str] = {
    "cmd": "Cmd",
    "ctrl": "Ctrl",
    "alt": "Opt",
    "shift": "Shift",
}
KEY_OPTIONS: list[str] = [chr(c) for c in range(ord("a"), ord("z") + 1)]


@dataclass
class Config:
    """Application configuration with sensible defaults."""

    goal_ml: int = 2000
    per_press_ml: int = 100
    hotkey: str = "cmd+shift+w"

    def __post_init__(self) -> None:
        if self.goal_ml not in GOAL_OPTIONS:
            msg = f"goal_ml must be one of {GOAL_OPTIONS}, got {self.goal_ml}"
            raise ValueError(msg)
        if self.per_press_ml not in PER_PRESS_OPTIONS:
            msg = f"per_press_ml must be one of {PER_PRESS_OPTIONS}, got {self.per_press_ml}"
            raise ValueError(msg)
        from hydro_key._hotkey import validate_hotkey  # noqa: PLC0415

        validate_hotkey(self.hotkey)


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
