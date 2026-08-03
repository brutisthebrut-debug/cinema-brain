import json
import sqlite3
from pathlib import Path

from cinema_brain.persisted_taste_signals import build_persisted_personal_taste_graph, load_persisted_signals
from cinema_brain.schema import SCHEMA_SQL


def _profiles() -> dict:
    return {
        "version": "1.0.0",
        "registry_version": "1.0.0",
        "films": [
            {
                "film_key": "title:undertone:2025",
                "title": "Undertone",
                "year": 2025,
                "status": "reviewed",
                "traits": [
                    {"trait_id": "creeping_dread", "value": 0.98, "confidence": 0.99},
                    {"trait_id": "genuine_fear_response", "value": 0.95, "confidence": 0.99},
                ],
            }
        ],
    }


def test_loads_only_reviewed_profile_films(tmp_path: Path):
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.executemany(
        "INSERT INTO films (film_key,name,year,watched,rating,liked,watch_count) VALUES(?,?,?,?,?,?,?)",
        [
            ("title:undertone:2025", "Undertone", 2025, 1, 4.0, 1, 2),
            ("title:other:2020", "Other", 2020, 1, 5.0, 1, 3),
        ],
    )
    conn.commit()
    conn.close()

    signals = load_persisted_signals(db, _profiles())
    assert len(signals) == 1
    assert signals[0]["film_key"] == "title:undertone:2025"
    assert set(signals[0]["source_types"]) == {"like", "rating", "rewatch"}


def test_builds_versioned_graph_from_sqlite(tmp_path: Path):
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT INTO films (film_key,name,year,watched,rating,liked,watch_count) VALUES(?,?,?,?,?,?,?)",
        ("title:undertone:2025", "Undertone", 2025, 1, 4.5, 1, 2),
    )
    conn.commit()
    conn.close()

    profiles = tmp_path / "profiles.json"
    profiles.write_text(json.dumps(_profiles()), encoding="utf-8")
    output = tmp_path / "taste_graph.json"
    graph = build_persisted_personal_taste_graph(db, profiles, output)

    assert output.exists()
    assert graph["source"]["matched_signal_count"] == 1
    assert graph["traits"]["creeping_dread"]["affinity"] > 0
    assert graph["profile_version"] == "1.0.0"
