from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
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


def _is_letterboxd_list(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return handle.readline().strip().lower().startswith("letterboxd list export")
    except OSError:
        return False


def _read_rows(path: Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        lines = handle.readlines()
    if lines and lines[0].strip().lower().startswith("letterboxd list export"):
        start = next((i for i, line in enumerate(lines) if line.lower().startswith("position,")), None)
        if start is None:
            return [], tuple()
        reader = csv.DictReader(lines[start:])
    else:
        reader = csv.DictReader(lines)
    headers = tuple(_norm_header(h or "") for h in (reader.fieldnames or []))
    rows = []
    for raw in reader:
        row = {_norm_header(k or ""): (v or "").strip() for k, v in raw.items() if k is not None}
        if any(row.values()):
            rows.append(row)
    return rows, headers


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path, headers: Iterable[str]) -> str:
    hs = set(headers)
    parents = {part.lower() for part in path.parts}
    name = path.name.lower()
    if _is_letterboxd_list(path):
        return "list"
    if name == "manual_watches.csv":
        return "diary"
    if "liked" in parents and name == "films.csv":
        return "liked_films"
    if "liked" in parents or name == "comments.csv":
        return "auxiliary"
    if name == "profile.csv":
        return "profile"
    if name == "reviews.csv" and "review" in hs:
        return "reviews"
    if name == "diary.csv":
        return "diary"
    if name == "ratings.csv":
        return "ratings"
    if name == "watchlist.csv":
        return "watchlist"
    if name == "watched.csv":
        return "watched"
    if "position" in hs and {"name", "year"}.issubset(hs):
        return "list"
    return "unknown"


def discover(data_dir: Path) -> list[Source]:
    result = []
    for path in sorted(data_dir.rglob("*.csv")):
        rows, headers = _read_rows(path)
        result.append(Source(path, headers, classify(path, headers), len(rows), _sha256(path)))
    return result


def _pick(row: dict[str, str], *keys: str) -> str:
    return next((row.get(key, "").strip() for key in keys if row.get(key, "").strip()), "")


def _year(value: str) -> int | None:
    try:
        year = int(float(value))
        return year if 1870 <= year <= 2200 else None
    except (TypeError, ValueError):
        return None


def _integer(value: str) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _rating(value: str) -> float | None:
    try:
        rating = float(value)
        return rating if 0 <= rating <= 5 else None
    except (TypeError, ValueError):
        return None


def _bool(value: str) -> int:
    return int(value.strip().lower() in {"1", "true", "yes", "y", "x"})


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def film_identity(row: dict[str, str]) -> tuple[str, str, int | None, str]:
    name = _pick(row, "name", "title", "film_name")
    year = _year(_pick(row, "year", "film_year"))
    uri = _pick(row, "letterboxd_uri", "uri", "film_uri", "url")
    return f"title:{_slug(name)}:{year or 'unknown'}", name or "(unknown)", year, uri


def _upsert_film(conn: sqlite3.Connection, row: dict[str, str], **flags) -> str:
    key, name, year, uri = film_identity(row)
    conn.execute(
        """INSERT INTO films(film_key,name,year,letterboxd_uri) VALUES(?,?,?,?)
        ON CONFLICT(film_key) DO UPDATE SET
        name=CASE WHEN excluded.name!='(unknown)' THEN excluded.name ELSE films.name END,
        year=COALESCE(excluded.year,films.year),
        letterboxd_uri=COALESCE(films.letterboxd_uri,NULLIF(excluded.letterboxd_uri,''))""",
        (key, name, year, uri or None),
    )
    for field, value in flags.items():
        if field in {"watched", "liked", "watchlist"} and value:
            conn.execute(f"UPDATE films SET {field}=1 WHERE film_key=?", (key,))
        elif field == "rating" and value is not None:
            conn.execute("UPDATE films SET rating=? WHERE film_key=?", (value, key))
    return key


def ingest(data_dir: Path, db_path: Path) -> dict:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    summary: dict = {"files": 0, "rows": 0, "by_kind": {}}
    now = datetime.now(timezone.utc).isoformat()

    for source in discover(data_dir):
        rows, headers = _read_rows(source.path)
        rel = str(source.path)
        conn.execute(
            "INSERT OR REPLACE INTO source_files(path,sha256,row_count,headers_json,classified_as,ingested_at) VALUES(?,?,?,?,?,?)",
            (rel, source.sha256, source.row_count, json.dumps(headers), source.kind, now),
        )
        summary["files"] += 1
        summary["rows"] += len(rows)
        summary["by_kind"][source.kind] = summary["by_kind"].get(source.kind, 0) + len(rows)

        for idx, row in enumerate(rows, start=2):
            kind = source.kind
            if kind in {"profile", "auxiliary", "unknown"} or not _pick(row, "name", "title", "film_name"):
                continue
            rating = _rating(_pick(row, "rating"))
            key = _upsert_film(
                conn, row,
                watched=kind in {"watched", "diary", "ratings", "reviews"},
                liked=kind == "liked_films",
                watchlist=kind == "watchlist",
                rating=rating if kind in {"ratings", "diary", "reviews"} else None,
            )
            if kind == "diary":
                conn.execute(
                    "INSERT OR REPLACE INTO viewing_events(film_key,watched_date,rewatch,rating,tags,source_path,source_row) VALUES(?,?,?,?,?,?,?)",
                    (key, _pick(row, "watched_date", "date"), _bool(_pick(row, "rewatch")), rating, _pick(row, "tags"), rel, idx),
                )
            elif kind == "reviews":
                conn.execute(
                    "INSERT OR REPLACE INTO reviews(film_key,review_date,rating,rewatch,review_text,tags,source_path,source_row) VALUES(?,?,?,?,?,?,?,?)",
                    (key, _pick(row, "watched_date", "date"), rating, _bool(_pick(row, "rewatch")), _pick(row, "review"), _pick(row, "tags"), rel, idx),
                )
            elif kind == "list":
                conn.execute(
                    "INSERT OR REPLACE INTO list_entries(film_key,list_name,rank_value,notes,source_path,source_row) VALUES(?,?,?,?,?,?)",
                    (key, source.path.stem, _integer(_pick(row, "position", "rank")), _pick(row, "description", "notes"), rel, idx),
                )

    conn.execute("""UPDATE films SET
      watch_count=(SELECT COUNT(*) FROM viewing_events e WHERE e.film_key=films.film_key),
      review_count=(SELECT COUNT(*) FROM reviews r WHERE r.film_key=films.film_key),
      list_count=(SELECT COUNT(*) FROM list_entries l WHERE l.film_key=films.film_key),
      first_watched_date=(SELECT MIN(watched_date) FROM viewing_events e WHERE e.film_key=films.film_key),
      last_watched_date=(SELECT MAX(watched_date) FROM viewing_events e WHERE e.film_key=films.film_key)""")
    conn.commit()
    for label, query in {
        "films": "SELECT COUNT(*) FROM films",
        "watched_films": "SELECT COUNT(*) FROM films WHERE watched=1",
        "watchlist_films": "SELECT COUNT(*) FROM films WHERE watchlist=1",
        "rated_films": "SELECT COUNT(*) FROM films WHERE rating IS NOT NULL",
        "liked_films": "SELECT COUNT(*) FROM films WHERE liked=1",
        "viewing_events": "SELECT COUNT(*) FROM viewing_events",
        "reviews": "SELECT COUNT(*) FROM reviews",
        "list_entries": "SELECT COUNT(*) FROM list_entries",
    }.items():
        summary[label] = conn.execute(query).fetchone()[0]
    conn.close()
    return summary
