import sqlite3
from pathlib import Path

from cinema_brain.letterboxd_rss import ingest_feed, parse_feed, profile_feed_url
from cinema_brain.schema import SCHEMA_SQL


def sample_feed(rating: str = "4.0") -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"
      xmlns:letterboxd="https://letterboxd.com"
      xmlns:content="http://purl.org/rss/1.0/modules/content/">
      <channel>
        <title>Daniel’s diary</title>
        <item>
          <title>Undertone, 2025 - ★★★★</title>
          <link>https://letterboxd.com/dmarlin/film/undertone/</link>
          <guid isPermaLink="false">letterboxd-watch-1</guid>
          <pubDate>Sun, 02 Aug 2026 06:00:00 +0000</pubDate>
          <letterboxd:filmTitle>Undertone</letterboxd:filmTitle>
          <letterboxd:filmYear>2025</letterboxd:filmYear>
          <letterboxd:watchedDate>2026-08-02</letterboxd:watchedDate>
          <letterboxd:memberRating>{rating}</letterboxd:memberRating>
          <letterboxd:rewatch>No</letterboxd:rewatch>
          <content:encoded><![CDATA[<p>Genuinely scary with creeping dread.</p>]]></content:encoded>
        </item>
      </channel>
    </rss>'''.encode()


def test_profile_feed_url():
    assert profile_feed_url("DMarlin") == "https://letterboxd.com/DMarlin/rss/"


def test_parse_letterboxd_feed():
    item = parse_feed(sample_feed())[0]
    assert item.film_title == "Undertone"
    assert item.film_year == 2025
    assert item.watched_date == "2026-08-02"
    assert item.member_rating == 4.0
    assert item.description == "Genuinely scary with creeping dread."
    assert item.item_type == "diary"


def test_ingest_is_idempotent_and_detects_edits(tmp_path: Path):
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.close()

    first = ingest_feed(db, profile_feed_url("DMarlin"), sample_feed())
    second = ingest_feed(db, profile_feed_url("DMarlin"), sample_feed())
    edited = ingest_feed(db, profile_feed_url("DMarlin"), sample_feed("4.5"))

    assert first == {"seen": 1, "inserted": 1, "updated": 0}
    assert second == {"seen": 1, "inserted": 0, "updated": 0}
    assert edited == {"seen": 1, "inserted": 0, "updated": 1}

    conn = sqlite3.connect(db)
    row = conn.execute("SELECT member_rating, first_seen_at, last_seen_at FROM rss_items").fetchone()
    conn.close()
    assert row[0] == 4.5
    assert row[1]
    assert row[2]
