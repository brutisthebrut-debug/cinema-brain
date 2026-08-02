from __future__ import annotations

import sqlite3
from pathlib import Path

from cinema_brain.metadata import FilmLookup, FilmMetadata
from cinema_brain.metadata_enrichment import enrich_films


class Provider:
    name = "fixture"

    def __init__(self):
        self.calls = 0

    def fetch(self, lookup: FilmLookup) -> FilmMetadata | None:
        self.calls += 1
        if lookup.title == "Missing":
            return None
        if lookup.title == "Broken":
            raise RuntimeError("provider failure")
        return FilmMetadata(
            film_key=lookup.film_key,
            title=lookup.title,
            year=lookup.year,
            provider=self.name,
            genres=("horror film",),
            confidence=0.9,
        )


def _db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE films(
                film_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                year INTEGER,
                watched INTEGER DEFAULT 0,
                first_watched_date TEXT,
                last_watched_date TEXT
            );
            CREATE TABLE film_metadata(
                film_key TEXT NOT NULL,
                provider TEXT NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                confidence REAL NOT NULL,
                runtime_minutes INTEGER,
                genres_json TEXT NOT NULL,
                directors_json TEXT NOT NULL,
                cast_json TEXT NOT NULL,
                countries_json TEXT NOT NULL,
                languages_json TEXT NOT NULL,
                keywords_json TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY(film_key, provider)
            );
            """
        )
        conn.executemany(
            "INSERT INTO films(film_key,name,year,watched,last_watched_date) VALUES(?,?,?,?,?)",
            [
                ("undertone-2025", "Undertone", 2025, 1, "2026-08-01"),
                ("missing-2024", "Missing", 2024, 1, "2026-07-01"),
                ("broken-2023", "Broken", 2023, 1, "2026-06-01"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def test_enrichment_is_bounded_persistent_and_resumable(tmp_path: Path) -> None:
    db = tmp_path / "brain.db"
    _db(db)
    provider = Provider()

    first = enrich_films(
        db,
        provider,
        tmp_path / "cache",
        film_keys=["undertone-2025", "missing-2024", "broken-2023"],
    )
    assert first.requested == 3
    assert first.enriched == 1
    assert first.missed == 1
    assert first.failed == 1
    assert "RuntimeError" in next(item.error for item in first.results if item.status == "failed")

    second = enrich_films(
        db,
        provider,
        tmp_path / "cache",
        film_keys=["undertone-2025"],
    )
    assert second.enriched == 1
    assert second.cached == 1
    assert provider.calls == 3

    conn = sqlite3.connect(db)
    try:
        row = conn.execute(
            "SELECT provider, genres_json, confidence FROM film_metadata WHERE film_key='undertone-2025'"
        ).fetchone()
    finally:
        conn.close()
    assert row == ("fixture", '["horror film"]', 0.9)


def test_default_batch_uses_recent_watches_and_limit(tmp_path: Path) -> None:
    db = tmp_path / "brain.db"
    _db(db)
    provider = Provider()
    report = enrich_films(db, provider, tmp_path / "cache", limit=1)
    assert report.requested == 1
    assert report.results[0].film_key == "undertone-2025"
