from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .evidence import EvidenceStore
from .metadata import FilmMetadata
from .metadata_evidence import MODEL_VERSION, build_metadata_registry, extract_metadata_evidence


@dataclass(frozen=True)
class FilmExtractionResult:
    film_key: str
    emitted: int
    inserted: int
    duplicates: int
    unmatched_labels: tuple[str, ...]


@dataclass(frozen=True)
class BatchExtractionReport:
    model_version: str
    processed: int
    emitted: int
    inserted: int
    duplicates: int
    unmatched_labels: tuple[str, ...]
    films: tuple[FilmExtractionResult, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _metadata_rows(db_path: Path, film_keys: Iterable[str] | None, limit: int) -> list[sqlite3.Row]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        keys = tuple(dict.fromkeys(film_keys or ()))
        if keys:
            placeholders = ",".join("?" for _ in keys)
            return conn.execute(
                f"SELECT * FROM film_metadata WHERE film_key IN ({placeholders}) ORDER BY film_key, provider",
                keys,
            ).fetchall()
        return conn.execute(
            """
            SELECT fm.*
            FROM film_metadata fm
            LEFT JOIN films f ON f.film_key=fm.film_key
            ORDER BY COALESCE(f.last_watched, '') DESC, fm.film_key, fm.provider
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()


def _to_metadata(row: sqlite3.Row) -> FilmMetadata:
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


def extract_and_persist_metadata_evidence(
    db_path: Path,
    *,
    film_keys: Iterable[str] | None = None,
    limit: int = 10,
    model_version: str = MODEL_VERSION,
) -> BatchExtractionReport:
    rows = _metadata_rows(Path(db_path), film_keys, limit)
    registry = build_metadata_registry()
    store = EvidenceStore(Path(db_path))
    film_results: list[FilmExtractionResult] = []
    unmatched: set[str] = set()
    total_emitted = total_inserted = total_duplicates = 0

    for row in rows:
        metadata = _to_metadata(row)
        evidence, report = extract_metadata_evidence(metadata, model_version=model_version)
        inserted = 0
        for item in evidence:
            if store.save(item, registry):
                inserted += 1
        duplicates = len(evidence) - inserted
        unmatched.update(report.unmatched_labels)
        total_emitted += len(evidence)
        total_inserted += inserted
        total_duplicates += duplicates
        film_results.append(FilmExtractionResult(
            film_key=metadata.film_key,
            emitted=len(evidence),
            inserted=inserted,
            duplicates=duplicates,
            unmatched_labels=report.unmatched_labels,
        ))

    return BatchExtractionReport(
        model_version=model_version,
        processed=len(rows),
        emitted=total_emitted,
        inserted=total_inserted,
        duplicates=total_duplicates,
        unmatched_labels=tuple(sorted(unmatched)),
        films=tuple(film_results),
    )


def write_batch_report(report: BatchExtractionReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
