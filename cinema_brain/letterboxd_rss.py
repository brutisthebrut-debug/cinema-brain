from __future__ import annotations

import hashlib
import html
import re
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

LETTERBOXD_NS = "https://letterboxd.com"
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"


@dataclass(frozen=True)
class RssItem:
    guid: str
    link: str
    title: str
    film_title: str | None
    film_year: int | None
    watched_date: str | None
    member_rating: float | None
    rewatch: bool
    description: str
    published_at: str | None
    item_type: str


def profile_feed_url(username: str) -> str:
    clean = username.strip().strip("/")
    if not clean or any(ch.isspace() for ch in clean):
        raise ValueError("valid Letterboxd username is required")
    return f"https://letterboxd.com/{clean}/rss/"


def fetch_feed(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "CinemaBrain/1.0 (+private personal project)"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _text(item: ET.Element, name: str) -> str:
    node = item.find(name)
    return (node.text or "").strip() if node is not None else ""


def _clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _float(value: str) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def _year(value: str) -> int | None:
    try:
        year = int(value)
        return year if 1880 <= year <= 2200 else None
    except (TypeError, ValueError):
        return None


def parse_feed(xml_bytes: bytes) -> tuple[RssItem, ...]:
    root = ET.fromstring(xml_bytes)
    items: list[RssItem] = []
    for node in root.findall("./channel/item"):
        link = _text(node, "link")
        title = _text(node, "title")
        description = _clean_html(
            _text(node, f"{{{CONTENT_NS}}}encoded") or _text(node, "description")
        )
        guid = _text(node, "guid") or link or hashlib.sha256(
            f"{title}|{_text(node, 'pubDate')}".encode("utf-8")
        ).hexdigest()
        film_title = _text(node, f"{{{LETTERBOXD_NS}}}filmTitle") or None
        film_year = _year(_text(node, f"{{{LETTERBOXD_NS}}}filmYear"))
        watched_date = _text(node, f"{{{LETTERBOXD_NS}}}watchedDate") or None
        rating = _float(_text(node, f"{{{LETTERBOXD_NS}}}memberRating"))
        rewatch_text = _text(node, f"{{{LETTERBOXD_NS}}}rewatch").lower()
        published = _text(node, "pubDate") or _text(node, f"{{{DC_NS}}}date") or None
        lower_link = link.lower()
        item_type = "diary"
        if "/list/" in lower_link:
            item_type = "list"
        elif description and not watched_date:
            item_type = "review"
        items.append(RssItem(
            guid=guid,
            link=link,
            title=title,
            film_title=film_title,
            film_year=film_year,
            watched_date=watched_date,
            member_rating=rating,
            rewatch=rewatch_text in {"yes", "true", "1"},
            description=description,
            published_at=published,
            item_type=item_type,
        ))
    return tuple(items)


def ingest_feed(db_path: Path, feed_url: str, xml_bytes: bytes) -> dict[str, int]:
    items = parse_feed(xml_bytes)
    conn = sqlite3.connect(db_path)
    inserted = 0
    updated = 0
    try:
        for item in items:
            existing = conn.execute("SELECT content_hash FROM rss_items WHERE guid=?", (item.guid,)).fetchone()
            payload = "|".join([
                item.link, item.title, item.film_title or "", str(item.film_year or ""),
                item.watched_date or "", str(item.member_rating or ""), str(int(item.rewatch)),
                item.description, item.published_at or "", item.item_type,
            ])
            content_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            conn.execute(
                """
                INSERT INTO rss_items
                (guid, feed_url, link, title, film_title, film_year, watched_date,
                 member_rating, rewatch, description, published_at, item_type,
                 content_hash, first_seen_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guid) DO UPDATE SET
                  feed_url=excluded.feed_url, link=excluded.link, title=excluded.title,
                  film_title=excluded.film_title, film_year=excluded.film_year,
                  watched_date=excluded.watched_date, member_rating=excluded.member_rating,
                  rewatch=excluded.rewatch, description=excluded.description,
                  published_at=excluded.published_at, item_type=excluded.item_type,
                  content_hash=excluded.content_hash, last_seen_at=excluded.last_seen_at
                """,
                (
                    item.guid, feed_url, item.link, item.title, item.film_title, item.film_year,
                    item.watched_date, item.member_rating, int(item.rewatch), item.description,
                    item.published_at, item.item_type, content_hash,
                    datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(),
                ),
            )
            if existing is None:
                inserted += 1
            elif existing[0] != content_hash:
                updated += 1
        conn.commit()
    finally:
        conn.close()
    return {"seen": len(items), "inserted": inserted, "updated": updated}
