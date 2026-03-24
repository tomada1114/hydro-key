"""Global hotkey listener for HydroKey."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pynput import keyboard

if TYPE_CHECKING:
    from collections.abc import Callable
    from queue import SimpleQueue

logger = logging.getLogger(__name__)

HOTKEY_MAP: dict[str, str] = {
    "cmd+shift+w": "<cmd>+<shift>+w",
    "cmd+shift+h": "<cmd>+<shift>+h",
    "cmd+shift+d": "<cmd>+<shift>+d",
    "ctrl+shift+w": "<ctrl>+<shift>+w",
    "ctrl+shift+h": "<ctrl>+<shift>+h",
}


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

    def start(self, hotkey_name: str) -> None:
        """Start listening for the specified hotkey."""
        self.stop()

        pynput_key = HOTKEY_MAP.get(hotkey_name)
        if pynput_key is None:
            msg = f"Unknown hotkey: {hotkey_name}"
            raise ValueError(msg)

        try:
            self._listener = keyboard.GlobalHotKeys(
                {pynput_key: self._on_activate},
            )
            self._listener.daemon = True
            self._listener.start()
        except Exception as exc:
            logger.warning("Failed to register hotkey %s: %s", hotkey_name, exc)
            if self._on_error:
                self._on_error(exc)

    def stop(self) -> None:
        """Stop the current hotkey listener if running."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_activate(self) -> None:
        self._queue.put(None)
