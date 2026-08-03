from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from cinema_brain.canonical_taste_scoring import score_canonical_films

MIN_ACTIVE_TRAITS = 2
MIN_TRAIT_COVERAGE = 0.50
MIN_CONFIDENCE = 0.15


def _identity_key(title: str, year: int) -> str:
    slug = "-".join(title.casefold().replace("'", "").split())
    return f"title:{slug}:{year}"


def load_watched_film_keys(db_path: Path) -> set[str]:
    """Return stable title/year keys for films marked watched in the canonical database."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(films)").fetchall()
        }
        title_column = "name" if "name" in columns else "title"
        if title_column not in columns or "year" not in columns or "watched" not in columns:
            raise ValueError("films table must contain title/name, year, and watched columns")
        rows = connection.execute(
            f"SELECT {title_column} AS title, year FROM films WHERE watched = 1"
        ).fetchall()
        return {
            _identity_key(str(row["title"]), int(row["year"]))
            for row in rows
            if row["title"] and row["year"] is not None
        }
    finally:
        connection.close()


def rank_eligible_candidates(
    corpus: dict[str, Any],
    taste_graph: dict[str, Any],
    *,
    watched_film_keys: set[str] | None = None,
) -> dict[str, Any]:
    watched = watched_film_keys or set()
    eligible = [film for film in corpus.get("films", []) if film["film_key"] not in watched]
    excluded = [film for film in corpus.get("films", []) if film["film_key"] in watched]

    scored = score_canonical_films(
        {
            "version": corpus.get("version"),
            "registry_version": corpus.get("registry_version"),
            "films": eligible,
        },
        taste_graph,
    )

    recommendations: list[dict[str, Any]] = []
    abstentions: list[dict[str, Any]] = []
    for film in scored["films"]:
        reasons: list[str] = []
        if film["active_trait_count"] < MIN_ACTIVE_TRAITS:
            reasons.append("too_few_active_traits")
        if film["trait_coverage"] < MIN_TRAIT_COVERAGE:
            reasons.append("insufficient_trait_coverage")
        if film["confidence"] < MIN_CONFIDENCE:
            reasons.append("low_confidence")

        record = dict(film)
        record["decision"] = "abstain" if reasons else "recommend"
        record["abstention_reasons"] = reasons
        if reasons:
            abstentions.append(record)
        else:
            recommendations.append(record)

    recommendations.sort(
        key=lambda item: (item["taste_score"], item["confidence"], item["title"]),
        reverse=True,
    )
    for rank, film in enumerate(recommendations, start=1):
        film["recommendation_rank"] = rank

    return {
        "version": "0.3.0",
        "model_version": scored["model_version"],
        "taste_model_version": scored.get("taste_model_version"),
        "corpus_version": corpus.get("version"),
        "registry_version": corpus.get("registry_version"),
        "candidate_count": len(corpus.get("films", [])),
        "watched_excluded_count": len(excluded),
        "eligible_count": len(eligible),
        "recommended_count": len(recommendations),
        "abstained_count": len(abstentions),
        "watched_exclusions": [
            {"film_key": film["film_key"], "title": film["title"], "year": film["year"]}
            for film in excluded
        ],
        "recommendations": recommendations,
        "abstentions": abstentions,
    }


def rank_eligible_candidates_file(
    corpus_path: Path,
    taste_graph_path: Path,
    db_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    graph = json.loads(taste_graph_path.read_text(encoding="utf-8"))
    result = rank_eligible_candidates(
        corpus,
        graph,
        watched_film_keys=load_watched_film_keys(db_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
