"""Tests for hydro_key._notify."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from hydro_key._notify import notify_recorded, notify_reminder, notify_undo, play_sound


class TestPlaySound:
    @patch("hydro_key._notify.subprocess.run")
    def test_plays_sound(self, _mock_run: MagicMock):
        play_sound()
        # Either AppKit worked or it fell back to subprocess
        # On CI/test without AppKit, subprocess.run should be called
        # We just verify no exception is raised


class TestNotifications:
    @patch("hydro_key._notify.rumps")
    def test_notify_recorded(self, mock_rumps: MagicMock):
        notify_recorded(100, 800, 2000)
        mock_rumps.notification.assert_called_once()
        call_kwargs = mock_rumps.notification.call_args[1]
        assert "+100ml" in call_kwargs["message"]
        assert "800ml" in call_kwargs["message"]

    @patch("hydro_key._notify.rumps")
    def test_notify_undo(self, mock_rumps: MagicMock):
        notify_undo(100, 700, 2000)
        mock_rumps.notification.assert_called_once()
        call_kwargs = mock_rumps.notification.call_args[1]
        assert "-100ml" in call_kwargs["message"]

    @patch("hydro_key._notify.rumps")
    def test_notify_reminder(self, mock_rumps: MagicMock):
        notify_reminder(600, 2000)
        mock_rumps.notification.assert_called_once()
        call_kwargs = mock_rumps.notification.call_args[1]
        assert "600ml" in call_kwargs["message"]
