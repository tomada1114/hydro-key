"""Tests for hydro_key._hotkey."""

from __future__ import annotations

from queue import SimpleQueue
from unittest.mock import MagicMock, patch

import pytest

from hydro_key._config import HOTKEY_OPTIONS
from hydro_key._hotkey import HOTKEY_MAP, HotkeyListener


class TestHotkeyMap:
    def test_all_options_have_pynput_format(self):
        for name, pynput_key in HOTKEY_MAP.items():
            assert "+" in name
            assert "<" in pynput_key

    def test_hotkey_map_matches_config_options(self):
        assert set(HOTKEY_MAP.keys()) == set(HOTKEY_OPTIONS)


class TestHotkeyListener:
    def test_raises_on_unknown_hotkey(self):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        with pytest.raises(ValueError, match="Unknown hotkey"):
            listener.start("invalid+key")

    @patch("hydro_key._hotkey.keyboard.GlobalHotKeys")
    def test_start_creates_listener(self, mock_hotkeys_cls: MagicMock):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("cmd+shift+w")

        mock_hotkeys_cls.assert_called_once()
        mock_instance = mock_hotkeys_cls.return_value
        assert mock_instance.daemon is True
        mock_instance.start.assert_called_once()

    @patch("hydro_key._hotkey.keyboard.GlobalHotKeys")
    def test_stop_stops_listener(self, mock_hotkeys_cls: MagicMock):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("cmd+shift+w")
        listener.stop()

        mock_hotkeys_cls.return_value.stop.assert_called_once()

    @patch("hydro_key._hotkey.keyboard.GlobalHotKeys")
    def test_on_activate_pushes_to_queue(self, mock_hotkeys_cls: MagicMock):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)

        # Extract the callback that was passed to GlobalHotKeys
        listener.start("cmd+shift+w")
        call_args = mock_hotkeys_cls.call_args
        hotkey_dict = call_args[0][0]
        callback = next(iter(hotkey_dict.values()))

        assert queue.empty()
        callback()
        assert not queue.empty()

    @patch("hydro_key._hotkey.keyboard.GlobalHotKeys")
    def test_calls_on_error_when_registration_fails(self, mock_hotkeys_cls: MagicMock):
        mock_hotkeys_cls.side_effect = RuntimeError("no accessibility")
        errors: list[Exception] = []
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue, on_error=errors.append)

        listener.start("cmd+shift+w")
        assert len(errors) == 1
        assert "no accessibility" in str(errors[0])

    @patch("hydro_key._hotkey.keyboard.GlobalHotKeys")
    def test_start_stops_previous_listener(self, mock_hotkeys_cls: MagicMock):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.start("cmd+shift+w")
        first_instance = mock_hotkeys_cls.return_value

        listener.start("cmd+shift+h")
        first_instance.stop.assert_called_once()

    def test_stop_when_not_started_is_noop(self):
        queue: SimpleQueue[None] = SimpleQueue()
        listener = HotkeyListener(queue)
        listener.stop()  # should not raise
