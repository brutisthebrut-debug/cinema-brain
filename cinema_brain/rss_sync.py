from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

from .letterboxd_rss import fetch_feed, ingest_feed, parse_feed, profile_feed_url
from .reconcile import reconcile_rss


@dataclass(frozen=True)
class SyncReport:
    feed_url: str
    dry_run: bool
    fetched_items: int
    inserted_raw: int = 0
    updated_raw: int = 0
    created_films: int = 0
    created_events: int = 0
    linked_events: int = 0
    created_reviews: int = 0
    skipped_already_reconciled: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_feed_url(username: str | None = None, feed_url: str | None = None) -> str:
    explicit = (feed_url or os.getenv("LETTERBOXD_RSS_URL", "")).strip()
    if explicit:
        if not explicit.startswith("https://letterboxd.com/") or not explicit.endswith("/rss/"):
            raise ValueError("LETTERBOXD_RSS_URL must be a Letterboxd profile RSS URL")
        return explicit
    user = (username or os.getenv("LETTERBOXD_USERNAME", "")).strip()
    if not user:
        raise ValueError("provide --username, --feed-url, LETTERBOXD_USERNAME, or LETTERBOXD_RSS_URL")
    return profile_feed_url(user)


def sync_rss(
    db_path: Path,
    *,
    username: str | None = None,
    feed_url: str | None = None,
    dry_run: bool = False,
    fetcher: Callable[[str], bytes] = fetch_feed,
) -> SyncReport:
    url = resolve_feed_url(username, feed_url)
    xml = fetcher(url)
    items = parse_feed(xml)
    if dry_run:
        return SyncReport(feed_url=url, dry_run=True, fetched_items=len(items))
    if not db_path.exists():
        raise FileNotFoundError(f"database does not exist: {db_path}; run ingest first")
    raw = ingest_feed(db_path, url, xml)
    canonical = reconcile_rss(db_path)
    return SyncReport(
        feed_url=url,
        dry_run=False,
        fetched_items=raw["seen"],
        inserted_raw=raw["inserted"],
        updated_raw=raw["updated"],
        **canonical,
    )


def write_report(report: SyncReport, output: Path | None) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
