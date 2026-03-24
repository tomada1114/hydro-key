"""Tests for hydro_key._notify."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from hydro_key._notify import notify_recorded, notify_reminder, notify_undo, play_sound


class TestPlaySound:
    @patch("hydro_key._notify._NSSound")
    def test_appkit_path(self, mock_nssound_cls: MagicMock):
        mock_sound = MagicMock()
        mock_nssound_cls.soundNamed_.return_value = mock_sound

        play_sound()

        mock_sound.play.assert_called_once()

    @patch("hydro_key._notify.subprocess.run")
    @patch("hydro_key._notify._NSSound", None)
    def test_subprocess_fallback(self, mock_run: MagicMock):
        play_sound()

        mock_run.assert_called_once_with(
            ["/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff"],
            check=False,
            capture_output=True,
        )

    @patch("hydro_key._notify.subprocess.run")
    @patch("hydro_key._notify._NSSound")
    def test_nssound_returns_none_falls_back_to_subprocess(
        self, mock_nssound_cls: MagicMock, mock_run: MagicMock
    ):
        mock_nssound_cls.soundNamed_.return_value = None
        play_sound()
        mock_run.assert_called_once()


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
