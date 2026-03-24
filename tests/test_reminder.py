"""Tests for hydro_key._reminder."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from hydro_key._reminder import is_within_active_hours, should_fire_reminder


class TestIsWithinActiveHours:
    @pytest.mark.parametrize(
        ("hour", "expected"),
        [
            pytest.param(8, False, id="before_start"),
            pytest.param(9, True, id="at_start"),
            pytest.param(14, True, id="midday"),
            pytest.param(20, True, id="before_end"),
            pytest.param(21, False, id="at_end"),
            pytest.param(23, False, id="late_night"),
        ],
    )
    def test_default_hours(self, hour: int, expected: bool):
        now = datetime(2026, 3, 24, hour, 30)
        assert is_within_active_hours(now, 9, 21) is expected


class TestShouldFireReminder:
    def _make_now(self, hour: int = 12, minute: int = 0) -> datetime:
        return datetime(2026, 3, 24, hour, minute)

    def test_disabled_when_interval_zero(self):
        assert not should_fire_reminder(self._make_now(), None, 0, 9, 21)

    def test_fires_when_no_prior_interaction(self):
        assert should_fire_reminder(self._make_now(), None, 60, 9, 21)

    def test_does_not_fire_outside_active_hours(self):
        now = self._make_now(hour=22)
        assert not should_fire_reminder(now, None, 60, 9, 21)

    def test_fires_after_interval_elapsed(self):
        now = self._make_now(hour=12)
        last = now - timedelta(minutes=61)
        assert should_fire_reminder(now, last, 60, 9, 21)

    def test_does_not_fire_before_interval(self):
        now = self._make_now(hour=12)
        last = now - timedelta(minutes=30)
        assert not should_fire_reminder(now, last, 60, 9, 21)

    def test_fires_at_exact_interval(self):
        now = self._make_now(hour=12)
        last = now - timedelta(minutes=60)
        assert should_fire_reminder(now, last, 60, 9, 21)

    def test_does_not_fire_one_second_before_interval(self):
        now = self._make_now(hour=12)
        last = now - timedelta(minutes=60) + timedelta(seconds=1)
        assert not should_fire_reminder(now, last, 60, 9, 21)
