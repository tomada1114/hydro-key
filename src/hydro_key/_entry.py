"""Entry point for the HydroKey.app bundle."""

from __future__ import annotations

import sys
import traceback


def _show_crash_dialog(exc: Exception) -> None:
    """Show a native macOS alert on an unhandled exception from the application."""
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
    except Exception as dialog_exc:  # last-resort fallback to stderr
        sys.stderr.write(
            f"[HydroKey] crash dialog failed ({type(dialog_exc).__name__}: {dialog_exc})\n"
            f"Original crash: {type(exc).__name__}: {exc}\n"
        )


if __name__ == "__main__":
    try:
        from hydro_key import run  # deferred: only needed inside .app

        run()
    except Exception as exc:
        traceback.print_exc()
        _show_crash_dialog(exc)
        sys.exit(1)
