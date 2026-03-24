"""Main menu bar application for HydroKey."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from queue import Empty, SimpleQueue
from typing import TYPE_CHECKING

import rumps

if TYPE_CHECKING:
    from collections.abc import Callable

from hydro_key._config import (
    ACTIVE_END_OPTIONS,
    ACTIVE_START_OPTIONS,
    APP_DIR,
    GOAL_OPTIONS,
    KEY_OPTIONS,
    MODIFIER_DISPLAY,
    MODIFIER_OPTIONS,
    PER_PRESS_OPTIONS,
    REMINDER_OPTIONS,
    load_config,
    save_config,
)
from hydro_key._db import add_record, delete_record, ensure_db, today_total
from hydro_key._hotkey import HotkeyListener, validate_hotkey
from hydro_key._reminder import should_fire_reminder

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    """Configure logging to file with rotation."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        APP_DIR / "hydrokey.log",
        maxBytes=1_000_000,
        backupCount=3,
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"),
    )
    logging.getLogger("hydro_key").addHandler(handler)
    logging.getLogger("hydro_key").setLevel(logging.INFO)


class HydroKeyApp(rumps.App):  # type: ignore[misc]  # rumps has no type stubs
    """macOS menu bar water intake tracker."""

    def __init__(self) -> None:
        super().__init__("HydroKey", quit_button=None)

        _setup_logging()
        ensure_db()

        self._config = load_config()
        self._last_record_id: int | None = None
        self._last_interaction: datetime | None = datetime.now(
            tz=UTC
        )  # Non-None: suppress reminder on startup
        self._hotkey_queue: SimpleQueue[None] = SimpleQueue()
        self._hotkey_listener = HotkeyListener(
            self._hotkey_queue,
            on_error=self._on_hotkey_error,
        )

        self._submenus: dict[str, rumps.MenuItem] = {}
        self._int_values: dict[str, int] = {}

        self._build_menu()
        self._update_title()
        self._hotkey_listener.start(self._config.hotkey)

    def _build_menu(self) -> None:
        """Construct the full dropdown menu."""
        # Today total (non-clickable)
        self._today_item = rumps.MenuItem("Today: 0ml")
        self._today_item.set_callback(None)

        # Undo
        self._undo_item = rumps.MenuItem("Undo Last", callback=self._on_undo)
        self._undo_item.set_callback(None)  # disabled initially

        # Settings submenus
        goal_menu = self._make_int_submenu(
            "Goal",
            GOAL_OPTIONS,
            self._config.goal_ml,
            self._on_goal,
            fmt=lambda v: f"{v}ml",
        )
        per_press_menu = self._make_int_submenu(
            "Per Press",
            PER_PRESS_OPTIONS,
            self._config.per_press_ml,
            self._on_per_press,
            fmt=lambda v: f"{v}ml",
        )
        reminder_menu = self._make_int_submenu(
            "Reminder",
            REMINDER_OPTIONS,
            self._config.reminder_interval_min,
            self._on_reminder,
            fmt=lambda v: "OFF" if v == 0 else f"{v}min",
        )
        active_start_menu = self._make_int_submenu(
            "Active Start",
            ACTIVE_START_OPTIONS,
            self._config.active_start_hour,
            self._on_active_start,
            fmt=lambda v: f"{v}:00",
        )
        active_end_menu = self._make_int_submenu(
            "Active End",
            ACTIVE_END_OPTIONS,
            self._config.active_end_hour,
            self._on_active_end,
            fmt=lambda v: f"{v}:00",
        )
        hotkey_menu = rumps.MenuItem("Hotkey")
        current_modifiers, current_key = self._parse_current_hotkey()

        modifier_menu = rumps.MenuItem("Modifier")
        self._modifier_items: dict[str, rumps.MenuItem] = {}
        for mod in MODIFIER_OPTIONS:
            item = rumps.MenuItem(MODIFIER_DISPLAY[mod], callback=self._on_modifier)
            item.state = 1 if mod in current_modifiers else 0
            modifier_menu.add(item)
            self._modifier_items[mod] = item

        key_menu = rumps.MenuItem("Key")
        self._key_items: dict[str, rumps.MenuItem] = {}
        for key in KEY_OPTIONS:
            item = rumps.MenuItem(key.upper(), callback=self._on_key)
            item.state = 1 if key == current_key else 0
            key_menu.add(item)
            self._key_items[key] = item

        hotkey_menu.add(modifier_menu)
        hotkey_menu.add(key_menu)

        quit_item = rumps.MenuItem("Quit", callback=self._on_quit)

        self.menu = [
            self._today_item,
            self._undo_item,
            None,  # separator
            goal_menu,
            per_press_menu,
            reminder_menu,
            active_start_menu,
            active_end_menu,
            hotkey_menu,
            None,  # separator
            quit_item,
        ]

    def _make_int_submenu(
        self,
        title: str,
        options: list[int],
        current: int,
        callback: Callable[..., object],
        fmt: Callable[[int], str],
    ) -> rumps.MenuItem:
        """Create a submenu with integer options and checkmarks."""
        parent = rumps.MenuItem(title)
        for opt in options:
            label = fmt(opt)
            item = rumps.MenuItem(label, callback=callback)
            self._int_values[label] = opt
            item.state = 1 if opt == current else 0
            parent.add(item)
        self._submenus[title] = parent
        return parent

    def _update_checkmarks_int(self, parent_title: str, new_value: int) -> None:
        """Update checkmarks in an integer submenu."""
        parent = self._submenus[parent_title]
        for item in parent.values():
            item.state = 1 if self._int_values.get(item.title) == new_value else 0

    def _update_title(self) -> int:
        """Update the menu bar title with current intake and return the total."""
        total = today_total()
        goal = self._config.goal_ml
        icon = "\u2705" if total >= goal else "\U0001f4a7"
        self.title = f"{icon} {total}ml"
        self._today_item.title = f"Today: {total}ml"
        return total

    def _save_and_update(self) -> None:
        save_config(self._config)
        self._update_title()

    @rumps.timer(0.1)  # type: ignore[untyped-decorator]  # rumps has no type stubs
    def _drain_hotkey_queue(self, _sender: object) -> None:
        """Drain hotkey events and check reminders (100 ms timer, main thread)."""
        try:
            while True:
                self._hotkey_queue.get_nowait()
                try:
                    self._record_intake()
                except Exception:
                    logger.exception("Failed to record intake")
                    rumps.notification(
                        title="HydroKey",
                        subtitle="Error",
                        message="Failed to save intake record. Check logs.",
                    )
        except Empty:
            pass

        now = datetime.now(tz=UTC).astimezone()  # local wall-clock for active hours
        if should_fire_reminder(
            now,
            self._last_interaction,
            self._config.reminder_interval_min,
            self._config.active_start_hour,
            self._config.active_end_hour,
        ):
            self._last_interaction = now

    def _record_intake(self) -> None:
        amount = self._config.per_press_ml
        record_id = add_record(amount)
        self._last_record_id = record_id
        self._last_interaction = datetime.now(tz=UTC)
        self._update_title()

        # Enable undo
        self._undo_item.set_callback(self._on_undo)

    def _on_undo(self, _sender: object) -> None:
        if self._last_record_id is None:
            return

        delete_record(self._last_record_id)
        self._last_record_id = None
        self._last_interaction = datetime.now(tz=UTC)
        self._update_title()

        # Disable undo
        self._undo_item.set_callback(None)

    def _on_goal(self, sender: rumps.MenuItem) -> None:
        self._config.goal_ml = self._int_values[sender.title]
        self._update_checkmarks_int("Goal", self._config.goal_ml)
        self._save_and_update()

    def _on_per_press(self, sender: rumps.MenuItem) -> None:
        self._config.per_press_ml = self._int_values[sender.title]
        self._update_checkmarks_int("Per Press", self._config.per_press_ml)
        self._save_and_update()

    def _on_reminder(self, sender: rumps.MenuItem) -> None:
        self._config.reminder_interval_min = self._int_values[sender.title]
        self._update_checkmarks_int("Reminder", self._config.reminder_interval_min)
        self._save_and_update()

    def _on_active_start(self, sender: rumps.MenuItem) -> None:
        self._config.active_start_hour = self._int_values[sender.title]
        self._update_checkmarks_int("Active Start", self._config.active_start_hour)
        self._save_and_update()

    def _on_active_end(self, sender: rumps.MenuItem) -> None:
        self._config.active_end_hour = self._int_values[sender.title]
        self._update_checkmarks_int("Active End", self._config.active_end_hour)
        self._save_and_update()

    def _parse_current_hotkey(self) -> tuple[set[str], str]:
        """Extract modifier set and trigger key from the current hotkey string."""
        parts = [p.strip().lower() for p in self._config.hotkey.split("+")]
        modifier_set = frozenset(MODIFIER_OPTIONS)
        modifiers = {p for p in parts if p in modifier_set}
        keys = [p for p in parts if p not in modifier_set]
        return modifiers, keys[0] if keys else KEY_OPTIONS[0]

    def _build_hotkey_from_ui(self) -> str:
        """Build a hotkey string from the current UI checkmark state."""
        modifiers = [mod for mod, item in self._modifier_items.items() if item.state]
        key = next(
            (k for k, item in self._key_items.items() if item.state),
            KEY_OPTIONS[0],
        )
        return "+".join([*modifiers, key])

    def _on_modifier(self, sender: rumps.MenuItem) -> None:
        sender.state = 0 if sender.state else 1

        if not any(item.state for item in self._modifier_items.values()):
            sender.state = 1
            rumps.alert(
                title="Invalid Hotkey",
                message="At least one modifier key is required.",
            )
            return

        self._apply_hotkey_change()

    def _on_key(self, sender: rumps.MenuItem) -> None:
        for item in self._key_items.values():
            item.state = 0
        sender.state = 1
        self._apply_hotkey_change()

    def _apply_hotkey_change(self) -> None:
        """Rebuild hotkey from UI state, validate, save, and restart listener."""
        new_hotkey = self._build_hotkey_from_ui()
        if new_hotkey == self._config.hotkey:
            return

        try:
            validate_hotkey(new_hotkey)
        except ValueError as exc:
            rumps.alert(title="Invalid Hotkey", message=str(exc))
            return

        self._config.hotkey = new_hotkey
        self._save_and_update()
        self._hotkey_listener.start(new_hotkey)

    def _on_hotkey_error(self, exc: Exception) -> None:
        logger.error("Hotkey registration failed: %s", exc)
        rumps.notification(
            title="HydroKey",
            subtitle="Hotkey Error",
            message=f"Failed to register hotkey: {exc}. Try a different one.",
        )

    def _on_quit(self, _sender: object) -> None:
        self._hotkey_listener.stop()
        rumps.quit_application()
