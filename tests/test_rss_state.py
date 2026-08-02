from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cinema_brain.rss_state import export_rss_state, import_rss_state
from cinema_brain.schema import SCHEMA_SQL


def _db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def test_rss_state_round_trip(tmp_path: Path) -> None:
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"
    state = tmp_path / "rss-state.json"
    _db(source_db)
    _db(target_db)
    conn = sqlite3.connect(source_db)
    conn.execute(
        "INSERT INTO rss_items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("g1", "https://letterboxd.com/dmarlin/rss/", "https://letterboxd.com/dmarlin/film/x/", "X, 2026", "X", 2026, "2026-08-02", 4.0, 0, "creepy", "2026-08-02", "diary", "hash", "first", "last"),
    )
    conn.commit()
    conn.close()

    assert export_rss_state(source_db, state) == {"exported": 1}
    assert import_rss_state(target_db, state) == {"imported": 1}
    conn = sqlite3.connect(target_db)
    row = conn.execute("SELECT guid, film_title, member_rating FROM rss_items").fetchone()
    conn.close()
    assert row == ("g1", "X", 4.0)


def test_missing_state_is_empty(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    _db(db)
    assert import_rss_state(db, tmp_path / "missing.json") == {"imported": 0}


def test_rejects_unknown_state_version(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    _db(db)
    state = tmp_path / "bad.json"
    state.write_text('{"version":999,"items":[]}', encoding="utf-8")
    with pytest.raises(ValueError):
        import_rss_state(db, state)
