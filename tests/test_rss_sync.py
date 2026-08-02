import sqlite3
from pathlib import Path

import pytest

from cinema_brain.rss_sync import resolve_feed_url, sync_rss
from cinema_brain.schema import SCHEMA_SQL

XML = b'''<?xml version="1.0"?><rss xmlns:letterboxd="https://letterboxd.com" version="2.0"><channel><item><guid>g1</guid><link>https://letterboxd.com/dmarlin/film/vicious/</link><title>Vicious, 2025</title><letterboxd:filmTitle>Vicious</letterboxd:filmTitle><letterboxd:filmYear>2025</letterboxd:filmYear><letterboxd:watchedDate>2026-08-02</letterboxd:watchedDate><letterboxd:memberRating>4.0</letterboxd:memberRating><letterboxd:rewatch>No</letterboxd:rewatch><description>Great creeping ambience.</description></item></channel></rss>'''


def make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def test_resolve_feed_url_from_username():
    assert resolve_feed_url(username="DMarlin") == "https://letterboxd.com/DMarlin/rss/"


def test_rejects_non_letterboxd_feed():
    with pytest.raises(ValueError):
        resolve_feed_url(feed_url="https://example.com/feed")


def test_dry_run_does_not_require_database(tmp_path: Path):
    report = sync_rss(tmp_path / "missing.db", username="DMarlin", dry_run=True, fetcher=lambda _: XML)
    assert report.fetched_items == 1
    assert report.dry_run is True
    assert not (tmp_path / "missing.db").exists()


def test_live_sync_is_idempotent(tmp_path: Path):
    db = tmp_path / "cinema.db"
    make_db(db)
    first = sync_rss(db, username="DMarlin", fetcher=lambda _: XML)
    second = sync_rss(db, username="DMarlin", fetcher=lambda _: XML)
    assert first.created_events == 1
    assert second.created_events == 0
    assert second.skipped_already_reconciled == 1
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM viewing_events").fetchone()[0] == 1
    conn.close()
