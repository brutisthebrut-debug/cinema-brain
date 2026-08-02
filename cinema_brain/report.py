from __future__ import annotations
import sqlite3
from pathlib import Path


def build_report(db_path: Path, output_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    one = lambda q: conn.execute(q).fetchone()[0]
    rows = conn.execute("SELECT classified_as, COUNT(*), SUM(row_count) FROM source_files GROUP BY classified_as ORDER BY classified_as").fetchall()
    ratings = conn.execute("SELECT rating, COUNT(*) FROM films WHERE rating IS NOT NULL GROUP BY rating ORDER BY rating").fetchall()
    top_rewatches = conn.execute("SELECT name, year, watch_count, rating FROM films WHERE watch_count > 1 ORDER BY watch_count DESC, rating DESC LIMIT 25").fetchall()
    lines = [
        "# Cinema Brain Baseline Report", "",
        f"- Source files: **{one('SELECT COUNT(*) FROM source_files')}**",
        f"- Source rows: **{one('SELECT COALESCE(SUM(row_count),0) FROM source_files')}**",
        f"- Normalized films: **{one('SELECT COUNT(*) FROM films')}**",
        f"- Watched films: **{one('SELECT COUNT(*) FROM films WHERE watched=1')}**",
        f"- Watchlist films: **{one('SELECT COUNT(*) FROM films WHERE watchlist=1')}**",
        f"- Rated films: **{one('SELECT COUNT(*) FROM films WHERE rating IS NOT NULL')}**",
        f"- Liked films: **{one('SELECT COUNT(*) FROM films WHERE liked=1')}**",
        f"- Viewing events: **{one('SELECT COUNT(*) FROM viewing_events')}**",
        f"- Reviews: **{one('SELECT COUNT(*) FROM reviews')}**", "",
        "## Source coverage", "", "| Type | Files | Rows |", "|---|---:|---:|",
    ]
    lines += [f"| {kind} | {files} | {count or 0} |" for kind, files, count in rows]
    lines += ["", "## Rating distribution", "", "| Rating | Films |", "|---:|---:|"]
    lines += [f"| {rating:g} | {count} |" for rating, count in ratings]
    lines += ["", "## Most rewatched", "", "| Film | Year | Watches | Rating |", "|---|---:|---:|---:|"]
    lines += [f"| {name} | {year or ''} | {count} | {rating if rating is not None else ''} |" for name, year, count, rating in top_rewatches]
    conn.close()
    text = "\n".join(lines) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return text
