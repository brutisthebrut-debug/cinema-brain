from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .personal_taste_graph import build_personal_taste_graph


def load_persisted_signals(db_path: Path, reviewed_profiles: dict[str, Any]) -> list[dict[str, Any]]:
    film_keys = [film["film_key"] for film in reviewed_profiles["films"]]
    if not film_keys:
        return []
    placeholders = ",".join("?" for _ in film_keys)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT film_key, rating, liked, watch_count, review_count, list_count
            FROM films
            WHERE watched=1 AND film_key IN ({placeholders})
            ORDER BY film_key
            """,
            film_keys,
        ).fetchall()
        outcomes = {
            row["film_key"]: row
            for row in conn.execute(
                f"""
                SELECT film_key, actual_rating, reaction_text, scared, moved, comforted, bored, surprised
                FROM recommendation_outcomes
                WHERE film_key IN ({placeholders})
                ORDER BY recorded_at DESC
                """,
                film_keys,
            ).fetchall()
        }
    finally:
        conn.close()

    signals: list[dict[str, Any]] = []
    for row in rows:
        source_types = ["rating"] if row["rating"] is not None else []
        if row["liked"]:
            source_types.append("like")
        if int(row["watch_count"] or 0) > 1:
            source_types.append("rewatch")
        if int(row["review_count"] or 0) > 0:
            source_types.append("review")
        if int(row["list_count"] or 0) > 0:
            source_types.append("list")

        explicit_sentiment = 0.0
        outcome = outcomes.get(row["film_key"])
        rating = row["rating"]
        if outcome:
            source_types.append("recommendation_outcome")
            if outcome["actual_rating"] is not None:
                rating = outcome["actual_rating"]
            explicit_sentiment += 0.2 if outcome["scared"] else 0.0
            explicit_sentiment += 0.15 if outcome["moved"] else 0.0
            explicit_sentiment += 0.1 if outcome["comforted"] else 0.0
            explicit_sentiment -= 0.2 if outcome["bored"] else 0.0
            explicit_sentiment += 0.1 if outcome["surprised"] else 0.0

        signals.append({
            "film_key": row["film_key"],
            "rating": rating,
            "liked": bool(row["liked"]),
            "watch_count": int(row["watch_count"] or 0),
            "explicit_sentiment": round(explicit_sentiment, 3),
            "source_types": sorted(set(source_types)) or ["watched"],
        })
    return signals


def build_persisted_personal_taste_graph(
    db_path: Path,
    profiles_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    signals = load_persisted_signals(db_path, profiles)
    graph = build_personal_taste_graph(profiles, signals)
    graph["source"] = {
        "type": "sqlite",
        "db": str(db_path),
        "matched_signal_count": len(signals),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    return graph
