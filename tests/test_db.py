"""Tests for hydro_key._db."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from hydro_key._db import (
    add_record,
    delete_record,
    ensure_db,
    today_total,
)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    ensure_db(path)
    return path


class TestEnsureDb:
    def test_creates_database_file(self, tmp_path: Path):
        path = tmp_path / "subdir" / "test.db"
        ensure_db(path)
        assert path.exists()

    def test_idempotent(self, db_path: Path):
        ensure_db(db_path)
        ensure_db(db_path)
        assert db_path.exists()

    def test_recreates_corrupted_database(self, tmp_path: Path):
        path = tmp_path / "bad.db"
        path.write_bytes(b"not a sqlite database")
        ensure_db(path)
        assert path.exists()
        backup = path.with_suffix(".db.bak")
        assert backup.exists()


class TestAddRecord:
    def test_returns_positive_id(self, db_path: Path):
        record_id = add_record(100, db_path)
        assert record_id > 0

    def test_increments_ids(self, db_path: Path):
        id1 = add_record(100, db_path)
        id2 = add_record(200, db_path)
        assert id2 > id1


class TestDeleteRecord:
    def test_deletes_existing_record(self, db_path: Path):
        record_id = add_record(100, db_path)
        assert today_total(db_path) == 100
        delete_record(record_id, db_path)
        assert today_total(db_path) == 0

    def test_delete_nonexistent_record_is_noop(self, db_path: Path):
        delete_record(99999, db_path)


class TestTodayTotal:
    def test_zero_when_empty(self, db_path: Path):
        assert today_total(db_path) == 0

    def test_sums_multiple_records(self, db_path: Path):
        add_record(100, db_path)
        add_record(200, db_path)
        add_record(500, db_path)
        assert today_total(db_path) == 800
