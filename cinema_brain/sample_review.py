from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def build_sample_review(db_path: Path, output: Path, limit: int = 10) -> dict:
    if limit <= 0:
        raise ValueError("limit must be positive")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT f.film_key, f.name, f.year, f.rating, f.liked,
                   m.provider, m.title AS provider_title, m.year AS provider_year,
                   m.confidence, m.runtime_minutes, m.genres_json,
                   m.keywords_json, m.directors_json, m.retrieved_at,
                   COUNT(e.id) AS evidence_count
            FROM films f
            JOIN film_metadata m ON m.film_key=f.film_key
            LEFT JOIN trait_evidence e ON e.film_key=f.film_key
              AND e.source_type='metadata_inference'
            GROUP BY f.film_key, m.provider
            ORDER BY COALESCE(f.last_watched_date, f.first_watched_date, '') DESC,
                     f.name, m.provider
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    films = []
    for row in rows:
        identity_ok = (
            row["name"].strip().casefold() == row["provider_title"].strip().casefold()
            and (row["year"] is None or row["provider_year"] == row["year"])
        )
        films.append({
            "film_key": row["film_key"],
            "letterboxd_title": row["name"],
            "letterboxd_year": row["year"],
            "rating": row["rating"],
            "liked": bool(row["liked"]),
            "provider": row["provider"],
            "provider_title": row["provider_title"],
            "provider_year": row["provider_year"],
            "identity_exact": identity_ok,
            "confidence": float(row["confidence"]),
            "runtime_minutes": row["runtime_minutes"],
            "genres": json.loads(row["genres_json"]),
            "keywords": json.loads(row["keywords_json"]),
            "directors": json.loads(row["directors_json"]),
            "evidence_count": int(row["evidence_count"]),
            "retrieved_at": row["retrieved_at"],
        })

    report = {
        "sample_size": len(films),
        "exact_identity_count": sum(1 for film in films if film["identity_exact"]),
        "needs_review_count": sum(1 for film in films if not film["identity_exact"]),
        "films": films,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
