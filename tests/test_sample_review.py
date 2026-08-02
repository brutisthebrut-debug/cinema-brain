import json
import sqlite3
from pathlib import Path

from cinema_brain.sample_review import build_sample_review
from cinema_brain.schema import SCHEMA_SQL


def test_sample_review_flags_identity_and_counts_evidence(tmp_path: Path):
    db = tmp_path / "brain.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT INTO films (film_key,name,year,watched,rating,last_watched_date) VALUES (?,?,?,?,?,?)",
        ("title:undertone:2025", "Undertone", 2025, 1, 4.0, "2026-08-01"),
    )
    conn.execute(
        """INSERT INTO film_metadata
        (film_key,provider,title,year,confidence,runtime_minutes,genres_json,directors_json,
         cast_json,countries_json,languages_json,keywords_json,retrieved_at,payload_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("title:undertone:2025", "wikidata", "Undertone", 2025, 0.9, 94,
         '["psychological horror"]', '["Director"]', '[]', '[]', '["English"]',
         '["found footage"]', "2026-08-02T12:00:00+00:00", '{}'),
    )
    conn.execute(
        """INSERT INTO trait_evidence
        (film_key,trait_id,polarity,strength,confidence,source_type,source_ref,evidence_text,model_version,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        ("title:undertone:2025", "psychological", 1, 0.6, 0.72, "metadata_inference",
         "wikidata:psychological horror", "derived", "metadata-evidence-1.0.0",
         "2026-08-02T12:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    output = tmp_path / "review.json"
    report = build_sample_review(db, output, limit=5)
    assert report["sample_size"] == 1
    assert report["exact_identity_count"] == 1
    assert report["films"][0]["evidence_count"] == 1
    assert json.loads(output.read_text())["films"][0]["genres"] == ["psychological horror"]


def test_sample_review_rejects_nonpositive_limit(tmp_path: Path):
    try:
        build_sample_review(tmp_path / "missing.db", tmp_path / "review.json", 0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
