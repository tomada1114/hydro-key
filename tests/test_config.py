"""Tests for hydro_key._config."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from hydro_key._config import (
    HOTKEY_OPTIONS,
    Config,
    load_config,
    save_config,
)


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


class TestConfigDefaults:
    def test_default_values(self):
        cfg = Config()
        assert cfg.goal_ml == 2000
        assert cfg.per_press_ml == 100
        assert cfg.reminder_interval_min == 60
        assert cfg.active_start_hour == 9
        assert cfg.active_end_hour == 21
        assert cfg.hotkey == "cmd+shift+w"


class TestLoadConfig:
    def test_returns_defaults_when_file_missing(self, config_path: Path):
        cfg = load_config(config_path)
        assert cfg == Config()

    def test_loads_valid_config(self, config_path: Path):
        data = {"goal_ml": 3000, "per_press_ml": 200, "hotkey": "cmd+shift+h"}
        config_path.write_text(json.dumps(data), encoding="utf-8")
        cfg = load_config(config_path)
        assert cfg.goal_ml == 3000
        assert cfg.per_press_ml == 200
        assert cfg.hotkey == "cmd+shift+h"
        assert cfg.reminder_interval_min == 60  # default preserved

    def test_returns_defaults_for_invalid_json(self, config_path: Path):
        config_path.write_text("{invalid json", encoding="utf-8")
        cfg = load_config(config_path)
        assert cfg == Config()

    def test_returns_defaults_for_non_dict_json(self, config_path: Path):
        config_path.write_text('"just a string"', encoding="utf-8")
        cfg = load_config(config_path)
        assert cfg == Config()

    def test_ignores_unknown_keys(self, config_path: Path):
        data = {"goal_ml": 1500, "unknown_field": 42}
        config_path.write_text(json.dumps(data), encoding="utf-8")
        cfg = load_config(config_path)
        assert cfg.goal_ml == 1500

    def test_partial_config_preserves_defaults(self, config_path: Path):
        data = {"active_end_hour": 22}
        config_path.write_text(json.dumps(data), encoding="utf-8")
        cfg = load_config(config_path)
        assert cfg.active_end_hour == 22
        assert cfg.goal_ml == 2000


class TestSaveConfig:
    def test_creates_directory_and_file(self, tmp_path: Path):
        path = tmp_path / "subdir" / "config.json"
        cfg = Config(goal_ml=1500)
        save_config(cfg, path)

        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["goal_ml"] == 1500

    def test_overwrites_existing_file(self, config_path: Path):
        save_config(Config(goal_ml=1000), config_path)
        save_config(Config(goal_ml=2500), config_path)

        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data["goal_ml"] == 2500

    def test_roundtrip(self, config_path: Path):
        original = Config(
            goal_ml=3000,
            per_press_ml=500,
            reminder_interval_min=30,
            active_start_hour=7,
            active_end_hour=22,
            hotkey="ctrl+shift+w",
        )
        save_config(original, config_path)
        loaded = load_config(config_path)
        assert loaded == original

    def test_no_tmp_file_left_after_save(self, config_path: Path):
        save_config(Config(), config_path)
        tmp_file = config_path.with_suffix(".tmp")
        assert not tmp_file.exists()


class TestHotkeyOptions:
    def test_default_hotkey_in_options(self):
        assert Config().hotkey in HOTKEY_OPTIONS

    @pytest.mark.parametrize("hotkey", HOTKEY_OPTIONS)
    def test_all_options_are_valid_config_values(self, hotkey: str):
        cfg = Config(hotkey=hotkey)
        assert cfg.hotkey == hotkey
