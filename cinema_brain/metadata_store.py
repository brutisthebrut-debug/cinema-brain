from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .metadata import FilmMetadata


class MetadataStore:
    """Durable canonical storage for provider metadata snapshots."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def save(self, item: FilmMetadata) -> None:
        item.validate()
        conn = sqlite3.connect(self.db_path)
        try:
            exists = conn.execute(
                "SELECT 1 FROM films WHERE film_key=?", (item.film_key,)
            ).fetchone()
            if not exists:
                raise KeyError(f"unknown film_key: {item.film_key}")
            conn.execute(
                """
                INSERT INTO film_metadata
                (film_key, provider, title, year, confidence, runtime_minutes,
                 genres_json, directors_json, cast_json, countries_json,
                 languages_json, keywords_json, retrieved_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(film_key, provider) DO UPDATE SET
                    title=excluded.title,
                    year=excluded.year,
                    confidence=excluded.confidence,
                    runtime_minutes=excluded.runtime_minutes,
                    genres_json=excluded.genres_json,
                    directors_json=excluded.directors_json,
                    cast_json=excluded.cast_json,
                    countries_json=excluded.countries_json,
                    languages_json=excluded.languages_json,
                    keywords_json=excluded.keywords_json,
                    retrieved_at=excluded.retrieved_at,
                    payload_json=excluded.payload_json
                """,
                (
                    item.film_key,
                    item.provider,
                    item.title,
                    item.year,
                    item.confidence,
                    item.runtime_minutes,
                    json.dumps(item.genres),
                    json.dumps(item.directors),
                    json.dumps(item.cast),
                    json.dumps(item.countries),
                    json.dumps(item.languages),
                    json.dumps(item.keywords),
                    item.retrieved_at,
                    json.dumps(asdict(item), sort_keys=True),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, film_key: str, provider: str) -> FilmMetadata | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM film_metadata WHERE film_key=? AND provider=?",
                (film_key, provider),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return FilmMetadata(
            film_key=row["film_key"],
            title=row["title"],
            year=row["year"],
            provider=row["provider"],
            confidence=float(row["confidence"]),
            genres=tuple(json.loads(row["genres_json"])),
            directors=tuple(json.loads(row["directors_json"])),
            cast=tuple(json.loads(row["cast_json"])),
            countries=tuple(json.loads(row["countries_json"])),
            languages=tuple(json.loads(row["languages_json"])),
            runtime_minutes=row["runtime_minutes"],
            keywords=tuple(json.loads(row["keywords_json"])),
            retrieved_at=row["retrieved_at"],
        )

    def coverage(self, provider: str | None = None, stale_after_days: int = 30) -> dict:
        conn = sqlite3.connect(self.db_path)
        try:
            film_count = int(conn.execute("SELECT COUNT(*) FROM films").fetchone()[0])
            params: tuple[str, ...] = ()
            where = ""
            if provider is not None:
                where = " WHERE provider=?"
                params = (provider,)
            rows = conn.execute(
                "SELECT retrieved_at FROM film_metadata" + where,
                params,
            ).fetchall()
        finally:
            conn.close()

        now = datetime.now(timezone.utc)
        stale = 0
        undated = 0
        for (value,) in rows:
            if not value:
                undated += 1
                stale += 1
                continue
            try:
                observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if observed.tzinfo is None:
                    observed = observed.replace(tzinfo=timezone.utc)
                if (now - observed).days >= stale_after_days:
                    stale += 1
            except ValueError:
                undated += 1
                stale += 1

        enriched = len(rows)
        return {
            "provider": provider,
            "film_count": film_count,
            "enriched_records": enriched,
            "coverage_ratio": round(enriched / film_count, 4) if film_count else 0.0,
            "stale_records": stale,
            "undated_records": undated,
            "stale_after_days": stale_after_days,
        }


def sync_metadata(item: FilmMetadata, store: MetadataStore) -> FilmMetadata:
    """Persist a canonical cache/provider result without changing its identity."""
    store.save(item)
    saved = store.get(item.film_key, item.provider)
    if saved != item:
        raise RuntimeError("metadata round-trip mismatch")
    return saved
