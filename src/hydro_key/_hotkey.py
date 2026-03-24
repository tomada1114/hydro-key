"""Global hotkey listener for HydroKey."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from pynput import keyboard

if TYPE_CHECKING:
    from collections.abc import Callable
    from queue import SimpleQueue

logger = logging.getLogger(__name__)

MODIFIER_KEYS: frozenset[str] = frozenset({"cmd", "ctrl", "shift", "alt"})
_MODIFIER_ORDER: list[str] = ["cmd", "ctrl", "alt", "shift"]

# Mapping from pynput Key objects to our canonical modifier names.
_PYNPUT_MODIFIER_MAP: dict[keyboard.Key, str] = {
    keyboard.Key.cmd: "cmd",
    keyboard.Key.cmd_l: "cmd",
    keyboard.Key.cmd_r: "cmd",
    keyboard.Key.ctrl: "ctrl",
    keyboard.Key.ctrl_l: "ctrl",
    keyboard.Key.ctrl_r: "ctrl",
    keyboard.Key.shift: "shift",
    keyboard.Key.shift_l: "shift",
    keyboard.Key.shift_r: "shift",
    keyboard.Key.alt: "alt",
    keyboard.Key.alt_l: "alt",
    keyboard.Key.alt_r: "alt",
}


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


class HotkeyRecorder:
    """Temporary keyboard listener that captures a modifier+key combination.

    Usage::

        recorder = HotkeyRecorder()
        recorder.start()
        # ... wait for user to press a key combo ...
        recorder.stop()
        hotkey = recorder.result  # e.g. "cmd+shift+w" or None
    """

    def __init__(self) -> None:
        self._held_modifiers: set[str] = set()
        self._result: str | None = None
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    @property
    def result(self) -> str | None:
        """The captured hotkey string, or ``None`` if nothing was captured."""
        with self._lock:
            return self._result

    def start(self) -> None:
        """Start listening for key events."""
        self.stop()
        self._held_modifiers.clear()
        self._result = None
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop the listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return

        modifier = _PYNPUT_MODIFIER_MAP.get(key)
        if modifier:
            self._held_modifiers.add(modifier)
            return

        # Non-modifier key pressed — capture if we have at least one modifier held.
        if not self._held_modifiers:
            return

        char = self._key_to_str(key)
        if char is None:
            return

        # Build hotkey string with stable modifier order.
        ordered = sorted(self._held_modifiers, key=_MODIFIER_ORDER.index)
        with self._lock:
            self._result = "+".join([*ordered, char])

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        modifier = _PYNPUT_MODIFIER_MAP.get(key)
        if modifier:
            self._held_modifiers.discard(modifier)

    @staticmethod
    def _key_to_str(key: keyboard.Key | keyboard.KeyCode) -> str | None:
        """Convert a pynput key to a string representation."""
        if isinstance(key, keyboard.KeyCode):
            char: str | None = key.char
            if char:
                return char.lower()
            if key.vk is not None:
                return f"<{key.vk}>"
            return None
        # Named keys like Key.f1, Key.space, etc.
        name: str | None = key.name
        return name


class HotkeyListener:
    """Manages a global hotkey that pushes events to a queue."""

    def __init__(
        self,
        queue: SimpleQueue[None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._queue = queue
        self._on_error = on_error
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self, hotkey: str) -> None:
        """Start listening for the specified hotkey."""
        self.stop()

        pynput_key = parse_hotkey(hotkey)

        try:
            self._listener = keyboard.GlobalHotKeys(
                {pynput_key: self._on_activate},
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
