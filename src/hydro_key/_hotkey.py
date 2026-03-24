"""Global hotkey listener for HydroKey."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hydro_key._config import MODIFIER_OPTIONS

if TYPE_CHECKING:
    from collections.abc import Callable
    from queue import SimpleQueue

logger = logging.getLogger(__name__)


def _import_keyboard() -> Any:
    """Lazily import pynput.keyboard to avoid X11 errors on headless Linux."""
    from pynput import keyboard  # noqa: PLC0415

    return keyboard


MODIFIER_KEYS: frozenset[str] = frozenset(MODIFIER_OPTIONS)


def validate_hotkey(hotkey: str) -> None:
    """Validate that a hotkey string contains at least one modifier and one regular key.

    Raises ``ValueError`` if the hotkey is invalid.
    """
    if not hotkey or not hotkey.strip():
        msg = "hotkey must not be empty"
        raise ValueError(msg)

    parts = [p.strip().lower() for p in hotkey.split("+")]
    modifiers = [p for p in parts if p in MODIFIER_KEYS]
    regular = [p for p in parts if p not in MODIFIER_KEYS]

    if not modifiers:
        msg = f"hotkey must contain at least one modifier ({', '.join(sorted(MODIFIER_KEYS))}), got '{hotkey}'"
        raise ValueError(msg)
    if len(regular) != 1:
        msg = f"hotkey must contain exactly one non-modifier key, got '{hotkey}'"
        raise ValueError(msg)


def parse_hotkey(hotkey: str) -> str:
    """Convert a user-friendly hotkey string to pynput GlobalHotKeys format.

    Example: ``"cmd+shift+w"`` -> ``"<cmd>+<shift>+w"``

    Single characters remain bare; modifiers and multi-character key names
    (e.g. ``f1``, ``space``) are wrapped in angle brackets.

    Raises ``ValueError`` if the hotkey is invalid.
    """
    validate_hotkey(hotkey)
    parts = [p.strip().lower() for p in hotkey.split("+")]
    pynput_parts = [f"<{p}>" if p in MODIFIER_KEYS or len(p) > 1 else p for p in parts]
    return "+".join(pynput_parts)


class HotkeyListener:
    """Manages a global hotkey that pushes events to a queue.

    Uses ``keyboard.Listener`` with ``keyboard.HotKey`` instead of
    ``keyboard.GlobalHotKeys`` to work around a pynput 1.8.x bug where
    the darwin backend omits the ``injected`` argument on special-key
    events.
    """

    def __init__(
        self,
        queue: SimpleQueue[None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._queue = queue
        self._on_error = on_error
        self._listener: Any = None

    def start(self, hotkey: str) -> None:
        """Start listening for the specified hotkey."""
        self.stop()

        pynput_key = parse_hotkey(hotkey)
        kb = _import_keyboard()

        try:
            hotkey_obj = kb.HotKey(
                kb.HotKey.parse(pynput_key),
                self._on_activate,
            )
            self._listener = kb.Listener(
                on_press=lambda key, *_args: hotkey_obj.press(
                    self._listener.canonical(key)
                ),
                on_release=lambda key, *_args: hotkey_obj.release(
                    self._listener.canonical(key)
                ),
            )
            self._listener.daemon = True  # exits with main thread
            self._listener.start()
        except (OSError, RuntimeError) as exc:
            self._listener = None
            logger.exception("Failed to register hotkey %s: %s", hotkey, exc)
            if self._on_error:
                self._on_error(exc)

    def stop(self) -> None:
        """Stop the current hotkey listener if running."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_activate(self) -> None:
        self._queue.put(None)
