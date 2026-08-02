import csv
import sqlite3
from pathlib import Path

from cinema_brain.ingest import ingest
from cinema_brain.validate import validate


def write_csv(path: Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_ingest_core_exports(tmp_path):
    raw = tmp_path / "raw"
    write_csv(raw / "watched.csv", ["Date", "Name", "Year", "Letterboxd URI"], [{"Date": "2020-01-01", "Name": "Example", "Year": "2020", "Letterboxd URI": "https://letterboxd.com/film/example/"}])
    write_csv(raw / "ratings.csv", ["Date", "Name", "Year", "Letterboxd URI", "Rating"], [{"Date": "2020-01-01", "Name": "Example", "Year": "2020", "Letterboxd URI": "https://letterboxd.com/film/example/", "Rating": "4.5"}])
    write_csv(raw / "diary.csv", ["Date", "Name", "Year", "Letterboxd URI", "Rating", "Rewatch", "Tags"], [{"Date": "2020-01-01", "Name": "Example", "Year": "2020", "Letterboxd URI": "https://letterboxd.com/film/example/", "Rating": "4.5", "Rewatch": "No", "Tags": "test"}])
    db = tmp_path / "test.db"
    result = ingest(raw, db)
    assert result["films"] == 1
    assert result["viewing_events"] == 1
    conn = sqlite3.connect(db)
    film = conn.execute("SELECT name, watched, rating, watch_count FROM films").fetchone()
    conn.close()
    assert film == ("Example", 1, 4.5, 1)
    errors, _ = validate(db)
    assert errors == []
