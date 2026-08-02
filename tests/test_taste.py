import json
import sqlite3
from pathlib import Path

from cinema_brain.schema import SCHEMA_SQL
from cinema_brain.taste import evidence_score, infer_traits, build_taste_profile


def test_evidence_weighting_rewards_rating_like_and_rewatch():
    plain = evidence_score(4.0, liked=False, watch_count=1)
    stronger = evidence_score(4.0, liked=True, watch_count=3)
    disliked = evidence_score(1.0, liked=False, watch_count=1)
    assert stronger > plain > 0
    assert disliked < 0


def test_explicit_reaction_traits():
    taxonomy = {
        "aliases": {
            "blair witch": ["found_footage_realism", "creeping_dread"],
            "scared me": ["creeping_dread"],
        }
    }
    traits = infer_traits(
        "It honestly scared me like the Blair Witch and gave me creeping dread.",
        taxonomy,
    )
    assert traits["found_footage_realism"] > 0
    assert traits["creeping_dread"] > traits["found_footage_realism"]


def test_profile_builds_from_manual_reaction(tmp_path: Path):
    db = tmp_path / "cinema.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        """INSERT INTO films
        (film_key,name,year,watched,rating,liked,watch_count,review_count,list_count)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        ("title:undertone:2025", "Undertone", 2025, 1, 4.0, 0, 1, 0, 0),
    )
    conn.execute(
        """INSERT INTO viewing_events
        (film_key,watched_date,rewatch,rating,tags,source_path,source_row)
        VALUES(?,?,?,?,?,?,?)""",
        (
            "title:undertone:2025",
            "2026-08-02",
            0,
            4.0,
            "Honestly scared me like the Blair Witch; creeping dread and atmosphere.",
            "data/manual/manual_watches.csv",
            2,
        ),
    )
    conn.commit()
    conn.close()

    taxonomy = tmp_path / "traits.json"
    taxonomy.write_text(
        json.dumps(
            {
                "version": "test",
                "families": {
                    "fear": ["creeping_dread", "found_footage_realism"],
                    "style": ["slow_burn"],
                },
                "aliases": {
                    "scared me": ["creeping_dread"],
                    "blair witch": ["found_footage_realism", "creeping_dread"],
                    "atmosphere": ["creeping_dread", "slow_burn"],
                },
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "taste_profile.json"
    profile = build_taste_profile(db, taxonomy, output)
    assert output.exists()
    assert profile["source_counts"]["watched_films"] == 1
    assert profile["traits"]["creeping_dread"]["affinity"] > 0
    assert profile["traits"]["found_footage_realism"]["confidence"] > 0
