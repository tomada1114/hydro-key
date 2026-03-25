"""Tests for the _entry.py crash dialog."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from hydro_key._entry import _show_crash_dialog


class TestShowCrashDialog:
    def test_shows_alert_and_calls_run_modal(self):
        mock_appkit = MagicMock()
        exc = RuntimeError("dependency missing")

        with patch.dict(sys.modules, {"AppKit": mock_appkit}):
            _show_crash_dialog(exc)

        alert = mock_appkit.NSAlert.alloc().init()
        alert.setMessageText_.assert_called_once_with("HydroKey failed to start")
        alert.setAlertStyle_.assert_called_once_with(
            mock_appkit.NSAlertStyleCritical,
        )
        alert.runModal.assert_called_once()

    def test_informative_text_contains_exception_class_and_message(self):
        mock_appkit = MagicMock()
        exc = ValueError("bad config")

        with patch.dict(sys.modules, {"AppKit": mock_appkit}):
            _show_crash_dialog(exc)

        call_args = mock_appkit.NSAlert.alloc().init().setInformativeText_.call_args
        text = call_args[0][0]
        assert "ValueError" in text
        assert "bad config" in text

    def test_writes_to_stderr_when_appkit_unavailable(self, capsys):
        exc = RuntimeError("boom")

        with patch.dict(sys.modules, {"AppKit": None}):
            _show_crash_dialog(exc)

        captured = capsys.readouterr()
        assert "crash dialog failed" in captured.err
        assert "RuntimeError: boom" in captured.err

    def test_does_not_propagate_when_dialog_fails(self):
        mock_appkit = MagicMock()
        mock_appkit.NSAlert.alloc().init().runModal.side_effect = OSError("no display")
        exc = RuntimeError("boom")

        with patch.dict(sys.modules, {"AppKit": mock_appkit}):
            _show_crash_dialog(exc)  # must not raise
