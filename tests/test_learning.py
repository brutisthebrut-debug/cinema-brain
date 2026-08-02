import sqlite3
from pathlib import Path

from cinema_brain.learning import (
    fetch_learning_record,
    freeze_recommendation,
    record_outcome,
    record_trait_evidence,
)
from cinema_brain.schema import SCHEMA_SQL


def setup_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO films(film_key,name,year,watched) VALUES(?,?,?,?)",
            ("title:vicious:2025", "Vicious", 2025, 0),
        )
        conn.execute(
            "INSERT INTO films(film_key,name,year,watched) VALUES(?,?,?,?)",
            ("title:undertone:2025", "Undertone", 2025, 1),
        )


def test_learning_ledger_freezes_prediction_and_records_error(tmp_path):
    db = tmp_path / "brain.db"
    setup_db(db)

    record_trait_evidence(
        db,
        film_key="title:undertone:2025",
        trait_id="creeping_dread",
        polarity=1.0,
        strength=4.0,
        confidence=0.95,
        source_type="chat_reaction",
        source_ref="2026-08-02-undertone",
        evidence_text="Scared me like The Blair Witch.",
        model_version="taste-0.1.0",
    )

    run_id = freeze_recommendation(
        db,
        run_id="charlotte-vicious-test",
        request={"mood": ["creepy"], "services": ["paramount_plus"]},
        model_version="recommend-0.1.0",
        candidates=[{
            "film_key": "title:vicious:2025",
            "score": 3.8,
            "accepted": True,
            "score_components": {"mood_fit": 0.8, "trait_fit": 0.7},
        }],
        selected_film_key="title:vicious:2025",
        predicted_score=3.8,
        confidence=0.72,
        explanation={"why": ["creeping dread", "isolation"]},
        availability={"service": "paramount_plus", "verified": "2026-08-02"},
    )

    error = record_outcome(
        db,
        run_id=run_id,
        film_key="title:vicious:2025",
        actual_rating=4.0,
        reaction_text="Strong atmosphere and sustained unease.",
        started=True,
        completed=True,
        scared=True,
    )
    assert error == 0.2

    record = fetch_learning_record(db, run_id)
    assert record["request"]["services"] == ["paramount_plus"]
    assert record["candidates"][0]["score_components"]["mood_fit"] == 0.8
    assert record["outcome"]["actual_rating"] == 4.0
    assert record["outcome"]["prediction_error"] == 0.2


def test_outcome_cannot_be_attached_to_different_film(tmp_path):
    db = tmp_path / "brain.db"
    setup_db(db)
    run_id = freeze_recommendation(
        db,
        request={},
        model_version="recommend-0.1.0",
        candidates=[{"film_key": "title:vicious:2025", "score": 3.0}],
        selected_film_key="title:vicious:2025",
        predicted_score=3.0,
        confidence=0.5,
        explanation={},
        availability={},
    )

    try:
        record_outcome(
            db,
            run_id=run_id,
            film_key="title:undertone:2025",
            actual_rating=4.0,
            reaction_text=None,
        )
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("mismatched outcome should fail")
