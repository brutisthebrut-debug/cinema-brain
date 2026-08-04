import csv
import sqlite3
from pathlib import Path

from cinema_brain.ingest import film_identity, ingest
from cinema_brain.validate import validate


def write_csv(path: Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_ingest_merges_different_letterboxd_urls(tmp_path):
    raw = tmp_path / "raw"
    write_csv(
        raw / "watched.csv",
        ["Date", "Name", "Year", "Letterboxd URI"],
        [{"Date": "2020-01-01", "Name": "Example", "Year": "2020", "Letterboxd URI": "https://boxd.it/film-code"}],
    )
    write_csv(
        raw / "ratings.csv",
        ["Date", "Name", "Year", "Letterboxd URI", "Rating"],
        [{"Date": "2020-01-01", "Name": "Example", "Year": "2020", "Letterboxd URI": "https://boxd.it/film-code", "Rating": "4.5"}],
    )
    write_csv(
        raw / "diary.csv",
        ["Date", "Name", "Year", "Letterboxd URI", "Rating", "Rewatch", "Tags", "Watched Date"],
        [{"Date": "2020-01-02", "Name": "Example", "Year": "2020", "Letterboxd URI": "https://boxd.it/activity-code", "Rating": "4.5", "Rewatch": "No", "Tags": "test", "Watched Date": "2020-01-01"}],
    )

    db = tmp_path / "test.db"
    result = ingest(raw, db)
    assert result["films"] == 1
    assert result["viewing_events"] == 1

    conn = sqlite3.connect(db)
    film = conn.execute("SELECT name, watched, rating, watch_count FROM films").fetchone()
    event = conn.execute("SELECT watched_date FROM viewing_events").fetchone()
    conn.close()

    assert film == ("Example", 1, 4.5, 1)
    assert event == ("2020-01-01",)
    errors, _ = validate(db)
    assert errors == []


def test_film_identity_drops_apostrophes_and_normalizes_other_punctuation():
    assert film_identity({"name": "The Blackcoat's Daughter", "year": "2015"})[
        0
    ] == "title:the-blackcoats-daughter:2015"
    assert film_identity({"name": "Noroi: The Curse", "year": "2005"})[
        0
    ] == "title:noroi-the-curse:2005"


def test_letterboxd_list_export_is_parsed(tmp_path):
    raw = tmp_path / "raw" / "lists"
    raw.mkdir(parents=True)
    (raw / "favorites.csv").write_text(
        "Letterboxd list export v7\n"
        "Date,Name,Tags,URL,Description\n"
        "2026-01-01,Favorites,,https://boxd.it/list,Best first\n"
        "\n"
        "Position,Name,Year,URL,Description\n"
        "1,Example,2020,https://boxd.it/example,Top pick\n",
        encoding="utf-8",
    )

    db = tmp_path / "list.db"
    result = ingest(tmp_path / "raw", db)
    assert result["list_entries"] == 1

    conn = sqlite3.connect(db)
    entry = conn.execute("SELECT list_name, rank_value, notes FROM list_entries").fetchone()
    conn.close()
    assert entry == ("favorites", 1, "Top pick")
