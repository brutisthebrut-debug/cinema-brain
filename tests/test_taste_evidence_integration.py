import json
import sqlite3
from pathlib import Path

from cinema_brain.schema import SCHEMA_SQL
from cinema_brain.taste import MODEL_VERSION, build_taste_profile


def test_taste_profile_persists_and_reuses_canonical_evidence(tmp_path: Path):
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        """INSERT INTO films
        (film_key, name, year, watched, rating, liked, watch_count, review_count, list_count)
        VALUES ('title:undertone:2025', 'Undertone', 2025, 1, 4.0, 0, 1, 1, 0)"""
    )
    conn.execute(
        """INSERT INTO reviews
        (film_key, review_date, rating, rewatch, review_text, tags, source_path, source_row)
        VALUES ('title:undertone:2025', '2026-08-02', 4.0, 0,
        'It scared me like Blair Witch with great atmosphere.', '', 'manual', 2)"""
    )
    conn.commit()
    conn.close()

    taxonomy = tmp_path / "traits.json"
    taxonomy.write_text(json.dumps({
        "families": {
            "fear": ["creeping_dread", "found_footage_realism", "sustained_uncertainty"],
            "style": ["slow_burn"]
        },
        "aliases": {
            "scared me": ["creeping_dread"],
            "blair witch": ["found_footage_realism", "creeping_dread", "sustained_uncertainty"],
            "atmosphere": ["creeping_dread", "slow_burn"]
        }
    }), encoding="utf-8")

    first = build_taste_profile(db, taxonomy)
    second = build_taste_profile(db, taxonomy)

    assert first["source_counts"]["persisted_evidence_records"] == 4
    assert second["source_counts"]["persisted_evidence_records"] == 4
    assert second["traits"]["creeping_dread"]["affinity"] > 0
    assert second["traits"]["found_footage_realism"]["status"] == "persisted_explicit_text"

    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT trait_id, model_version, source_ref FROM trait_evidence ORDER BY trait_id"
    ).fetchall()
    conn.close()
    assert len(rows) == 4
    assert {row[0] for row in rows} == {
        "creeping_dread", "found_footage_realism", "slow_burn", "sustained_uncertainty"
    }
    assert all(row[1] == MODEL_VERSION for row in rows)
    assert all(row[2] == "manual:2" for row in rows)
