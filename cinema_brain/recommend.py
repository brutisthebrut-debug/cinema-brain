from __future__ import annotations
import sqlite3
from pathlib import Path


def recommend(db_path: Path, limit: int = 10, min_rating: float = 0.0) -> list[dict]:
    """Return an explainable shortlist from unwatched watchlist entries."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT name, year, rating, liked, list_count, letterboxd_uri,
               (COALESCE(rating, 0) * 2.0 + liked * 1.5 + list_count * 0.25) AS score
        FROM films
        WHERE watchlist=1 AND watched=0 AND COALESCE(rating, 0) >= ?
        ORDER BY score DESC, name ASC
        LIMIT ?
        """, (min_rating, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
