from __future__ import annotations
import sqlite3
from pathlib import Path


def validate(db_path: Path) -> tuple[list[str], list[str]]:
    conn = sqlite3.connect(db_path)
    errors: list[str] = []
    warnings: list[str] = []
    if conn.execute("SELECT COUNT(*) FROM source_files").fetchone()[0] == 0:
        errors.append("No CSV source files were ingested.")
    if conn.execute("SELECT COUNT(*) FROM films").fetchone()[0] == 0:
        errors.append("No films were normalized.")
    for path, count in conn.execute("SELECT path, row_count FROM source_files WHERE classified_as='unknown'").fetchall():
        warnings.append(f"Unclassified CSV: {path} ({count} rows)")
    missing_name = conn.execute("SELECT COUNT(*) FROM films WHERE name='(unknown)' OR TRIM(name)='' ").fetchone()[0]
    if missing_name:
        warnings.append(f"{missing_name} normalized films have no usable title.")
    impossible_ratings = conn.execute("SELECT COUNT(*) FROM films WHERE rating < 0 OR rating > 5").fetchone()[0]
    if impossible_ratings:
        errors.append(f"{impossible_ratings} films have ratings outside 0–5.")
    watched_watchlist = conn.execute("SELECT COUNT(*) FROM films WHERE watched=1 AND watchlist=1").fetchone()[0]
    if watched_watchlist:
        warnings.append(f"{watched_watchlist} films are both watched and on the watchlist.")
    conn.close()
    return errors, warnings
