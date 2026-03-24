"""Tests for hydro_key._hotkey."""

from __future__ import annotations

from queue import SimpleQueue
from unittest.mock import MagicMock, patch

import pytest

from hydro_key._hotkey import (
    MODIFIER_KEYS,
    HotkeyListener,
    parse_hotkey,
    validate_hotkey,
)


class TestValidateHotkey:
    def test_valid_hotkey_with_single_modifier(self):
        validate_hotkey("cmd+w")

    def test_valid_hotkey_with_multiple_modifiers(self):
        validate_hotkey("cmd+shift+w")

    def test_all_modifier_keys_accepted(self):
        for mod in MODIFIER_KEYS:
            validate_hotkey(f"{mod}+x")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_hotkey("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_hotkey("   ")

    def test_rejects_no_modifier(self):
        with pytest.raises(ValueError, match="at least one modifier"):
            validate_hotkey("w")

    def test_rejects_modifier_only(self):
        with pytest.raises(ValueError, match="exactly one non-modifier"):
            validate_hotkey("cmd+shift")

    def test_rejects_multiple_regular_keys(self):
        with pytest.raises(ValueError, match="exactly one non-modifier"):
            validate_hotkey("cmd+a+b")

    def test_case_insensitive(self):
        validate_hotkey("CMD+SHIFT+W")


class TestParseHotkey:
    def test_single_modifier(self):
        assert parse_hotkey("cmd+w") == "<cmd>+w"

    def test_multiple_modifiers(self):
        assert parse_hotkey("cmd+shift+w") == "<cmd>+<shift>+w"

    def test_ctrl_modifier(self):
        assert parse_hotkey("ctrl+shift+h") == "<ctrl>+<shift>+h"

    def test_preserves_key_order(self):
        assert parse_hotkey("shift+cmd+w") == "<shift>+<cmd>+w"

    def test_wraps_multi_char_key_names(self):
        assert parse_hotkey("cmd+f1") == "<cmd>+<f1>"
        assert parse_hotkey("ctrl+space") == "<ctrl>+<space>"

    def test_single_char_key_stays_bare(self):
        assert parse_hotkey("cmd+w") == "<cmd>+w"

    def test_raises_on_invalid(self):
        with pytest.raises(ValueError):
            parse_hotkey("just_a_key")


class TestHotkeyListener:
    def test_raises_on_invalid_hotkey(self):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        with pytest.raises(ValueError, match="at least one modifier"):
            listener.start("just_a_key")

    @patch("hydro_key._hotkey.keyboard.Listener")
    @patch("hydro_key._hotkey.keyboard.HotKey")
    def test_start_creates_listener(
        self, mock_hotkey_cls: MagicMock, mock_listener_cls: MagicMock
    ):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("cmd+shift+w")

        mock_hotkey_cls.assert_called_once()
        mock_listener_cls.assert_called_once()
        mock_instance = mock_listener_cls.return_value
        assert mock_instance.daemon is True
        mock_instance.start.assert_called_once()

    @patch("hydro_key._hotkey.keyboard.Listener")
    @patch("hydro_key._hotkey.keyboard.HotKey")
    def test_stop_stops_listener(
        self, _mock_hotkey_cls: MagicMock, mock_listener_cls: MagicMock
    ):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("cmd+shift+w")
        listener.stop()

        mock_listener_cls.return_value.stop.assert_called_once()

    @patch("hydro_key._hotkey.keyboard.Listener")
    @patch("hydro_key._hotkey.keyboard.HotKey")
    def test_on_activate_pushes_to_queue(
        self, mock_hotkey_cls: MagicMock, _mock_listener_cls: MagicMock
    ):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)

        listener.start("cmd+shift+w")
        # The on_activate callback is the second arg to HotKey()
        callback = mock_hotkey_cls.call_args[0][1]

        assert queue.empty()
        callback()
        assert not queue.empty()

    @patch("hydro_key._hotkey.keyboard.Listener")
    @patch("hydro_key._hotkey.keyboard.HotKey")
    def test_calls_on_error_when_registration_fails(
        self, _mock_hotkey_cls: MagicMock, mock_listener_cls: MagicMock
    ):
        mock_listener_cls.side_effect = RuntimeError("no accessibility")
        errors: list[Exception] = []
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue, on_error=errors.append)

        listener.start("cmd+shift+w")
        assert len(errors) == 1
        assert "no accessibility" in str(errors[0])

    @patch("hydro_key._hotkey.keyboard.Listener")
    @patch("hydro_key._hotkey.keyboard.HotKey")
    def test_start_stops_previous_listener(
        self, _mock_hotkey_cls: MagicMock, mock_listener_cls: MagicMock
    ):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("cmd+shift+w")
        first_instance = mock_listener_cls.return_value

        listener.start("cmd+shift+h")
        first_instance.stop.assert_called_once()

    def test_stop_when_not_started_is_noop(self):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.stop()  # should not raise

    @patch("hydro_key._hotkey.keyboard.Listener")
    @patch("hydro_key._hotkey.keyboard.HotKey")
    def test_accepts_freeform_hotkey(
        self, mock_hotkey_cls: MagicMock, _mock_listener_cls: MagicMock
    ):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("alt+ctrl+f5")

        mock_hotkey_cls.parse.assert_called_with("<alt>+<ctrl>+<f5>")
