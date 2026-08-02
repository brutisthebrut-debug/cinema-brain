from __future__ import annotations

import json
import sqlite3
from pathlib import Path

STATE_VERSION = 1
RSS_COLUMNS = (
    "guid", "feed_url", "link", "title", "film_title", "film_year",
    "watched_date", "member_rating", "rewatch", "description", "published_at",
    "item_type", "content_hash", "first_seen_at", "last_seen_at",
)


def export_rss_state(db_path: Path, output: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in conn.execute(
            "SELECT " + ",".join(RSS_COLUMNS) + " FROM rss_items ORDER BY guid"
        )]
    finally:
        conn.close()
    payload = {"version": STATE_VERSION, "items": rows}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"exported": len(rows)}


def import_rss_state(db_path: Path, source: Path) -> dict[str, int]:
    if not source.exists():
        return {"imported": 0}
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("version") != STATE_VERSION or not isinstance(payload.get("items"), list):
        raise ValueError("unsupported or malformed RSS state file")
    conn = sqlite3.connect(db_path)
    imported = 0
    try:
        placeholders = ",".join("?" for _ in RSS_COLUMNS)
        columns = ",".join(RSS_COLUMNS)
        for item in payload["items"]:
            if not isinstance(item, dict) or not item.get("guid"):
                raise ValueError("RSS state item is malformed")
            conn.execute(
                f"INSERT OR REPLACE INTO rss_items ({columns}) VALUES ({placeholders})",
                tuple(item.get(column) for column in RSS_COLUMNS),
            )
            imported += 1
        conn.commit()
    finally:
        conn.close()
    return {"imported": imported}
