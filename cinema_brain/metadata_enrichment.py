from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from .metadata import FilmLookup, MetadataCache, MetadataProvider, fetch_with_cache
from .metadata_store import MetadataStore, sync_metadata


@dataclass(frozen=True)
class EnrichmentResult:
    film_key: str
    title: str
    year: int | None
    status: str
    source: str | None = None
    confidence: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class EnrichmentReport:
    provider: str
    requested: int
    enriched: int
    cached: int
    missed: int
    failed: int
    results: tuple[EnrichmentResult, ...]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["results"] = [asdict(item) for item in self.results]
        return data


def _lookups(db_path: Path, film_keys: list[str] | None, limit: int) -> list[FilmLookup]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if film_keys:
            placeholders = ",".join("?" for _ in film_keys)
            rows = conn.execute(
                f"SELECT film_key, name, year FROM films WHERE film_key IN ({placeholders}) ORDER BY film_key",
                tuple(film_keys),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT film_key, name, year FROM films
                WHERE watched=1
                ORDER BY COALESCE(last_watched_date, first_watched_date) DESC, film_key
                LIMIT ?""",
                (max(1, limit),),
            ).fetchall()
    finally:
        conn.close()
    return [FilmLookup(str(row["film_key"]), str(row["name"]), row["year"]) for row in rows]


def enrich_films(
    db_path: Path,
    provider: MetadataProvider,
    cache_root: Path,
    *,
    film_keys: list[str] | None = None,
    limit: int = 10,
    refresh: bool = False,
) -> EnrichmentReport:
    """Enrich a bounded film set and preserve every miss or failure in the report."""
    cache = MetadataCache(cache_root)
    store = MetadataStore(db_path)
    results: list[EnrichmentResult] = []
    enriched = cached = missed = failed = 0

    for lookup in _lookups(db_path, film_keys, limit):
        try:
            item, source = fetch_with_cache(provider, lookup, cache, refresh=refresh)
            if item is None:
                missed += 1
                results.append(EnrichmentResult(lookup.film_key, lookup.title, lookup.year, "miss"))
                continue
            sync_metadata(item, store)
            enriched += 1
            if source == "cache":
                cached += 1
            results.append(
                EnrichmentResult(
                    lookup.film_key,
                    lookup.title,
                    lookup.year,
                    "enriched",
                    source=source,
                    confidence=item.confidence,
                )
            )
        except Exception as exc:  # report per-film failures; do not lose the rest of the batch
            failed += 1
            results.append(
                EnrichmentResult(
                    lookup.film_key,
                    lookup.title,
                    lookup.year,
                    "failed",
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    return EnrichmentReport(
        provider=provider.name,
        requested=len(results),
        enriched=enriched,
        cached=cached,
        missed=missed,
        failed=failed,
        results=tuple(results),
    )


def write_enrichment_report(report: EnrichmentReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
