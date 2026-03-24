"""Entry point for the HydroKey.app bundle."""

from __future__ import annotations

import sys
import traceback


def _show_crash_dialog(exc: BaseException) -> None:
    """Show a native macOS alert when the app fails to start."""
    try:
        import AppKit  # noqa: PLC0415  # deferred import: AppKit may not be available

        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("HydroKey failed to start")
        alert.setInformativeText_(
            f"{type(exc).__name__}: {exc}\n\n"
            "Try reinstalling or check Console.app for details."
        )
        alert.setAlertStyle_(AppKit.NSAlertStyleCritical)
        alert.runModal()
    except Exception:  # noqa: S110  # last-resort handler, nothing to do
        pass


if __name__ == "__main__":
    try:
        from hydro_key import run

        run()
    except Exception as exc:
        traceback.print_exc()
        _show_crash_dialog(exc)
        sys.exit(1)
