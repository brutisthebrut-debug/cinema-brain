from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .ingest import film_identity


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _refresh_film_rollups(conn: sqlite3.Connection, film_key: str) -> None:
    conn.execute(
        """UPDATE films SET
        watched=CASE WHEN EXISTS(SELECT 1 FROM viewing_events e WHERE e.film_key=films.film_key) THEN 1 ELSE watched END,
        rating=COALESCE((SELECT rating FROM viewing_events e WHERE e.film_key=films.film_key AND rating IS NOT NULL ORDER BY watched_date DESC, id DESC LIMIT 1), rating),
        watch_count=(SELECT COUNT(*) FROM viewing_events e WHERE e.film_key=films.film_key),
        review_count=(SELECT COUNT(*) FROM reviews r WHERE r.film_key=films.film_key),
        first_watched_date=(SELECT MIN(watched_date) FROM viewing_events e WHERE e.film_key=films.film_key),
        last_watched_date=(SELECT MAX(watched_date) FROM viewing_events e WHERE e.film_key=films.film_key)
        WHERE film_key=?""",
        (film_key,),
    )


def _match_viewing_event(
    conn: sqlite3.Connection,
    film_key: str,
    watched_date: str | None,
) -> int | None:
    if not watched_date:
        return None
    row = conn.execute(
        """SELECT id FROM viewing_events
        WHERE film_key=? AND watched_date=?
        ORDER BY CASE WHEN source_path LIKE 'rss:%' THEN 1 ELSE 0 END, id
        LIMIT 1""",
        (film_key, watched_date),
    ).fetchone()
    return int(row[0]) if row else None


def reconcile_rss(db_path: Path) -> dict[str, int]:
    """Promote raw RSS deltas into canonical records without double counting.

    CSV/manual rows win identity for an existing same-film/same-day viewing event.
    RSS enriches missing rating, rewatch, and review text, while every source link
    remains auditable in source_reconciliations.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    created_films = created_events = linked_events = created_reviews = skipped = 0
    try:
        rows = conn.execute(
            """SELECT * FROM rss_items
            WHERE film_title IS NOT NULL AND TRIM(film_title)!=''
            ORDER BY COALESCE(watched_date, published_at), guid"""
        ).fetchall()
        for row in rows:
            existing_link = conn.execute(
                "SELECT canonical_type, canonical_id FROM source_reconciliations WHERE source_type='letterboxd_rss' AND source_id=?",
                (row["guid"],),
            ).fetchone()
            if existing_link:
                skipped += 1
                continue

            film_key, name, year, _ = film_identity({
                "name": row["film_title"],
                "year": str(row["film_year"] or ""),
                "letterboxd_uri": row["link"] or "",
            })
            film_exists = conn.execute("SELECT 1 FROM films WHERE film_key=?", (film_key,)).fetchone()
            conn.execute(
                """INSERT INTO films(film_key,name,year,letterboxd_uri,watched,rating)
                VALUES(?,?,?,?,1,?)
                ON CONFLICT(film_key) DO UPDATE SET
                  name=excluded.name,
                  year=COALESCE(excluded.year,films.year),
                  letterboxd_uri=COALESCE(films.letterboxd_uri,excluded.letterboxd_uri),
                  watched=1,
                  rating=COALESCE(excluded.rating,films.rating)""",
                (film_key, name, year, row["link"] or None, row["member_rating"]),
            )
            if not film_exists:
                created_films += 1

            event_id = _match_viewing_event(conn, film_key, row["watched_date"])
            if event_id is None and row["item_type"] in {"diary", "review"}:
                source_path = f"rss:{row['guid']}"
                cursor = conn.execute(
                    """INSERT INTO viewing_events
                    (film_key,watched_date,rewatch,rating,tags,source_path,source_row)
                    VALUES(?,?,?,?,?,?,1)""",
                    (film_key, row["watched_date"], int(row["rewatch"]), row["member_rating"], "", source_path),
                )
                event_id = int(cursor.lastrowid)
                created_events += 1
            elif event_id is not None:
                conn.execute(
                    """UPDATE viewing_events SET
                    rating=COALESCE(rating,?), rewatch=MAX(rewatch,?)
                    WHERE id=?""",
                    (row["member_rating"], int(row["rewatch"]), event_id),
                )
                linked_events += 1

            canonical_type = "film"
            canonical_id = film_key
            if event_id is not None:
                canonical_type = "viewing_event"
                canonical_id = str(event_id)

            if row["description"] and row["item_type"] in {"review", "diary"}:
                review = conn.execute(
                    """SELECT id FROM reviews WHERE film_key=? AND review_date IS ? AND review_text=? LIMIT 1""",
                    (film_key, row["watched_date"], row["description"]),
                ).fetchone()
                if not review:
                    cur = conn.execute(
                        """INSERT INTO reviews
                        (film_key,review_date,rating,rewatch,review_text,tags,source_path,source_row)
                        VALUES(?,?,?,?,?,?,?,1)""",
                        (film_key, row["watched_date"], row["member_rating"], int(row["rewatch"]), row["description"], "", f"rss:{row['guid']}"),
                    )
                    created_reviews += 1
                    if event_id is None:
                        canonical_type, canonical_id = "review", str(cur.lastrowid)

            conn.execute(
                """INSERT INTO source_reconciliations
                (source_type,source_id,canonical_type,canonical_id,film_key,match_rule,content_hash,reconciled_at)
                VALUES('letterboxd_rss',?,?,?,?,?,?,?)""",
                (row["guid"], canonical_type, canonical_id, film_key,
                 "film+watched_date" if row["watched_date"] else "film_identity",
                 row["content_hash"], _now()),
            )
            _refresh_film_rollups(conn, film_key)
        conn.commit()
    finally:
        conn.close()
    return {
        "created_films": created_films,
        "created_events": created_events,
        "linked_events": linked_events,
        "created_reviews": created_reviews,
        "skipped_already_reconciled": skipped,
    }
