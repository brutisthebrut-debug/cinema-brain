import sqlite3
from pathlib import Path

from cinema_brain.reconcile import reconcile_rss
from cinema_brain.schema import SCHEMA_SQL


def _db(tmp_path: Path) -> Path:
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    return db


def _rss(conn: sqlite3.Connection, guid: str, title: str, year: int, date: str, rating: float = 4.0, description: str = ""):
    conn.execute(
        """INSERT INTO rss_items
        (guid,feed_url,link,title,film_title,film_year,watched_date,member_rating,rewatch,
         description,published_at,item_type,content_hash,first_seen_at,last_seen_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (guid, "https://letterboxd.com/dmarlin/rss/", f"https://letterboxd.com/dmarlin/film/{title.lower()}/",
         title, title, year, date, rating, 0, description, date, "diary", f"hash-{guid}", date, date),
    )


def test_rss_links_to_existing_csv_event_without_double_counting(tmp_path: Path):
    db = _db(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO films(film_key,name,year,watched) VALUES('title:undertone:2025','Undertone',2025,1)")
    conn.execute(
        """INSERT INTO viewing_events(film_key,watched_date,rewatch,rating,tags,source_path,source_row)
        VALUES('title:undertone:2025','2026-08-02',0,NULL,'','data/raw/diary.csv',2)"""
    )
    _rss(conn, "rss-1", "Undertone", 2025, "2026-08-02", 4.0, "Creeping dread.")
    conn.commit()
    conn.close()

    first = reconcile_rss(db)
    second = reconcile_rss(db)

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM viewing_events").fetchone()[0] == 1
    assert conn.execute("SELECT rating FROM viewing_events").fetchone()[0] == 4.0
    assert conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM source_reconciliations").fetchone()[0] == 1
    conn.close()
    assert first["linked_events"] == 1
    assert second["skipped_already_reconciled"] == 1


def test_rss_creates_new_canonical_event_when_no_export_row_exists(tmp_path: Path):
    db = _db(tmp_path)
    conn = sqlite3.connect(db)
    _rss(conn, "rss-2", "Vicious", 2025, "2026-08-03", 3.5)
    conn.commit()
    conn.close()

    result = reconcile_rss(db)
    conn = sqlite3.connect(db)
    film = conn.execute("SELECT watched,rating,watch_count FROM films WHERE film_key='title:vicious:2025'").fetchone()
    assert film == (1, 3.5, 1)
    assert conn.execute("SELECT COUNT(*) FROM viewing_events").fetchone()[0] == 1
    conn.close()
    assert result["created_films"] == 1
    assert result["created_events"] == 1
