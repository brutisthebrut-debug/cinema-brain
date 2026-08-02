import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cinema_brain.metadata import FilmMetadata
from cinema_brain.metadata_store import MetadataStore, sync_metadata
from cinema_brain.schema import SCHEMA_SQL


def make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.executemany(
        "INSERT INTO films(film_key, name, year) VALUES (?, ?, ?)",
        [
            ("title:undertone:2025", "Undertone", 2025),
            ("title:vicious:2025", "Vicious", 2025),
        ],
    )
    conn.commit()
    conn.close()


def test_metadata_round_trip_and_upsert(tmp_path: Path):
    db = tmp_path / "cinema.db"
    make_db(db)
    store = MetadataStore(db)
    first = FilmMetadata(
        film_key="title:undertone:2025",
        title="Undertone",
        year=2025,
        provider="fixture",
        confidence=0.9,
        genres=("Horror",),
        directors=("Ian Tuason",),
        countries=("Canada",),
        languages=("English",),
        runtime_minutes=94,
        keywords=("audio", "isolation", "creeping dread"),
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
    assert sync_metadata(first, store) == first

    changed = FilmMetadata(**{**first.__dict__, "runtime_minutes": 96})
    store.save(changed)
    assert store.get(first.film_key, first.provider) == changed


def test_coverage_and_staleness(tmp_path: Path):
    db = tmp_path / "cinema.db"
    make_db(db)
    store = MetadataStore(db)
    old = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    store.save(FilmMetadata(
        film_key="title:undertone:2025",
        title="Undertone",
        year=2025,
        provider="fixture",
        genres=("Horror",),
        retrieved_at=old,
    ))
    report = store.coverage(provider="fixture", stale_after_days=30)
    assert report["film_count"] == 2
    assert report["enriched_records"] == 1
    assert report["coverage_ratio"] == 0.5
    assert report["stale_records"] == 1


def test_unknown_film_is_rejected(tmp_path: Path):
    db = tmp_path / "cinema.db"
    make_db(db)
    store = MetadataStore(db)
    with pytest.raises(KeyError):
        store.save(FilmMetadata(
            film_key="title:missing:2025",
            title="Missing",
            year=2025,
            provider="fixture",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        ))
