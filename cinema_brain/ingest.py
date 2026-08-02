from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .schema import SCHEMA_SQL


@dataclass(frozen=True)
class Source:
    path: Path
    headers: tuple[str, ...]
    kind: str
    row_count: int
    sha256: str


def _norm_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _read_rows(path: Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(_norm_header(h or "") for h in (reader.fieldnames or []))
        rows = []
        for raw in reader:
            rows.append({_norm_header(k or ""): (v or "").strip() for k, v in raw.items()})
    return rows, headers


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(path: Path, headers: Iterable[str]) -> str:
    hs = set(headers)
    p = "/".join(part.lower() for part in path.parts)
    name = path.name.lower()

    if {"watched_date", "rewatch"} & hs and ("diary" in name or "date" in hs):
        return "diary"
    if "rating" in hs and "review" not in hs and ("ratings" in name or len(hs) <= 6):
        return "ratings"
    if "review" in hs or "review_text" in hs:
        return "reviews"
    if "watched" in name:
        return "watched"
    if "watchlist" in name:
        return "watchlist"
    if "liked" in p and ("film" in p or "films" in name):
        return "liked_films"
    if "profile" in name:
        return "profile"
    if "rank" in hs or "position" in hs or "lists" in p:
        return "list"
    return "unknown"


def discover(raw_dir: Path) -> list[Source]:
    sources = []
    for path in sorted(raw_dir.rglob("*.csv")):
        rows, headers = _read_rows(path)
        sources.append(Source(path=path, headers=headers, kind=classify(path, headers), row_count=len(rows), sha256=_sha256(path)))
    return sources


def _pick(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key, "").strip()
        if value:
            return value
    return ""


def _year(value: str) -> int | None:
    try:
        y = int(float(value))
        return y if 1870 <= y <= 2200 else None
    except (TypeError, ValueError):
        return None


def _rating(value: str) -> float | None:
    try:
        r = float(value)
        return r if 0 <= r <= 5 else None
    except (TypeError, ValueError):
        return None


def _bool(value: str) -> int:
    return int(value.strip().lower() in {"1", "true", "yes", "y", "x"})


def film_identity(row: dict[str, str]) -> tuple[str, str, int | None, str]:
    name = _pick(row, "name", "title", "film_name")
    year = _year(_pick(row, "year", "film_year"))
    uri = _pick(row, "letterboxd_uri", "uri", "film_uri", "url")
    if uri:
        key = "lb:" + uri.rstrip("/").split("/")[-1].lower()
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        key = f"title:{slug}:{year or 'unknown'}"
    return key, name or "(unknown)", year, uri


def _upsert_film(conn: sqlite3.Connection, row: dict[str, str], **flags) -> str:
    key, name, year, uri = film_identity(row)
    conn.execute("""
        INSERT INTO films(film_key, name, year, letterboxd_uri)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(film_key) DO UPDATE SET
            name = CASE WHEN excluded.name != '(unknown)' THEN excluded.name ELSE films.name END,
            year = COALESCE(excluded.year, films.year),
            letterboxd_uri = COALESCE(NULLIF(excluded.letterboxd_uri, ''), films.letterboxd_uri)
        """, (key, name, year, uri or None))
    for field, value in flags.items():
        if field in {"watched", "liked", "watchlist"} and value:
            conn.execute(f"UPDATE films SET {field}=1 WHERE film_key=?", (key,))
        elif field == "rating" and value is not None:
            conn.execute("UPDATE films SET rating=? WHERE film_key=?", (value, key))
    return key


def ingest(raw_dir: Path, db_path: Path) -> dict:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    now = datetime.now(timezone.utc).isoformat()
    summary = {"files": 0, "rows": 0, "by_kind": {}}

    for source in discover(raw_dir):
        rows, headers = _read_rows(source.path)
        rel = str(source.path)
        conn.execute("""INSERT OR REPLACE INTO source_files
            (path, sha256, row_count, headers_json, classified_as, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?)""", (rel, source.sha256, source.row_count, json.dumps(headers), source.kind, now))
        summary["files"] += 1
        summary["rows"] += len(rows)
        summary["by_kind"][source.kind] = summary["by_kind"].get(source.kind, 0) + len(rows)

        for idx, row in enumerate(rows, start=2):
            kind = source.kind
            if kind in {"profile", "unknown"}:
                continue
            rating = _rating(_pick(row, "rating"))
            key = _upsert_film(conn, row, watched=kind in {"watched", "diary", "ratings", "reviews"}, liked=kind == "liked_films", watchlist=kind == "watchlist", rating=rating if kind in {"ratings", "diary", "reviews"} else None)
            if kind == "diary":
                conn.execute("""INSERT OR REPLACE INTO viewing_events
                    (film_key, watched_date, rewatch, rating, tags, source_path, source_row)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", (key, _pick(row, "watched_date", "date"), _bool(_pick(row, "rewatch")), rating, _pick(row, "tags"), rel, idx))
            elif kind == "reviews":
                conn.execute("""INSERT OR REPLACE INTO reviews
                    (film_key, review_date, rating, rewatch, review_text, tags, source_path, source_row)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (key, _pick(row, "review_date", "date"), rating, _bool(_pick(row, "rewatch")), _pick(row, "review", "review_text"), _pick(row, "tags"), rel, idx))
            elif kind == "list":
                conn.execute("""INSERT OR REPLACE INTO list_entries
                    (film_key, list_name, rank_value, notes, source_path, source_row)
                    VALUES (?, ?, ?, ?, ?, ?)""", (key, source.path.stem, _year(_pick(row, "rank", "position")), _pick(row, "notes", "description"), rel, idx))

    conn.execute("""UPDATE films SET
        watch_count = (SELECT COUNT(*) FROM viewing_events e WHERE e.film_key=films.film_key),
        review_count = (SELECT COUNT(*) FROM reviews r WHERE r.film_key=films.film_key),
        list_count = (SELECT COUNT(*) FROM list_entries l WHERE l.film_key=films.film_key),
        first_watched_date = (SELECT MIN(watched_date) FROM viewing_events e WHERE e.film_key=films.film_key),
        last_watched_date = (SELECT MAX(watched_date) FROM viewing_events e WHERE e.film_key=films.film_key)
        """)
    conn.commit()
    summary["films"] = conn.execute("SELECT COUNT(*) FROM films").fetchone()[0]
    summary["viewing_events"] = conn.execute("SELECT COUNT(*) FROM viewing_events").fetchone()[0]
    conn.close()
    return summary
