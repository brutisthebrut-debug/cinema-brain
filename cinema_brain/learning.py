from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .schema import SCHEMA_SQL


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def record_trait_evidence(
    db_path: Path,
    *,
    film_key: str,
    trait_id: str,
    polarity: float,
    strength: float,
    confidence: float,
    source_type: str,
    source_ref: str,
    evidence_text: str | None,
    model_version: str,
) -> int:
    ensure_schema(db_path)
    if not -1 <= polarity <= 1:
        raise ValueError("polarity must be between -1 and 1")
    if strength < 0:
        raise ValueError("strength must be non-negative")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO trait_evidence(
                film_key, trait_id, polarity, strength, confidence,
                source_type, source_ref, evidence_text, model_version, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(film_key, trait_id, source_type, source_ref, model_version)
            DO UPDATE SET
                polarity=excluded.polarity,
                strength=excluded.strength,
                confidence=excluded.confidence,
                evidence_text=excluded.evidence_text,
                created_at=excluded.created_at
            """,
            (
                film_key, trait_id, polarity, strength, confidence,
                source_type, source_ref, evidence_text, model_version, _now(),
            ),
        )
        return int(cursor.lastrowid or 0)


def freeze_recommendation(
    db_path: Path,
    *,
    request: dict[str, Any],
    model_version: str,
    candidates: Iterable[dict[str, Any]],
    selected_film_key: str | None,
    predicted_score: float | None,
    confidence: float | None,
    explanation: dict[str, Any],
    availability: dict[str, Any],
    run_id: str | None = None,
) -> str:
    ensure_schema(db_path)
    frozen_candidates = list(candidates)
    run_id = run_id or str(uuid.uuid4())

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO recommendation_runs(
                id, created_at, request_json, model_version, candidate_count,
                selected_film_key, predicted_score, confidence,
                explanation_json, availability_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                run_id,
                _now(),
                json.dumps(request, sort_keys=True),
                model_version,
                len(frozen_candidates),
                selected_film_key,
                predicted_score,
                confidence,
                json.dumps(explanation, sort_keys=True),
                json.dumps(availability, sort_keys=True),
            ),
        )
        for position, candidate in enumerate(frozen_candidates, start=1):
            conn.execute(
                """
                INSERT INTO recommendation_candidates(
                    run_id, film_key, rank_position, score, accepted,
                    rejection_reasons_json, score_components_json
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    candidate["film_key"],
                    int(candidate.get("rank_position", position)),
                    float(candidate["score"]),
                    int(bool(candidate.get("accepted", False))),
                    json.dumps(candidate.get("rejection_reasons", []), sort_keys=True),
                    json.dumps(candidate.get("score_components", {}), sort_keys=True),
                ),
            )
    return run_id


def record_outcome(
    db_path: Path,
    *,
    run_id: str,
    film_key: str,
    actual_rating: float | None,
    reaction_text: str | None,
    started: bool | None = None,
    completed: bool | None = None,
    scared: bool | None = None,
    moved: bool | None = None,
    comforted: bool | None = None,
    bored: bool | None = None,
    surprised: bool | None = None,
) -> float | None:
    ensure_schema(db_path)
    if actual_rating is not None and not 0 <= actual_rating <= 5:
        raise ValueError("actual_rating must be between 0 and 5")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT selected_film_key, predicted_score FROM recommendation_runs WHERE id=?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown recommendation run: {run_id}")
        if row[0] is not None and row[0] != film_key:
            raise ValueError("outcome film does not match frozen selected film")

        prediction_error = None
        if actual_rating is not None and row[1] is not None:
            prediction_error = round(actual_rating - float(row[1]), 3)

        conn.execute(
            """
            INSERT INTO recommendation_outcomes(
                run_id, film_key, started, completed, actual_rating,
                scared, moved, comforted, bored, surprised,
                reaction_text, recorded_at, prediction_error
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(run_id) DO UPDATE SET
                film_key=excluded.film_key,
                started=excluded.started,
                completed=excluded.completed,
                actual_rating=excluded.actual_rating,
                scared=excluded.scared,
                moved=excluded.moved,
                comforted=excluded.comforted,
                bored=excluded.bored,
                surprised=excluded.surprised,
                reaction_text=excluded.reaction_text,
                recorded_at=excluded.recorded_at,
                prediction_error=excluded.prediction_error
            """,
            (
                run_id,
                film_key,
                None if started is None else int(started),
                None if completed is None else int(completed),
                actual_rating,
                None if scared is None else int(scared),
                None if moved is None else int(moved),
                None if comforted is None else int(comforted),
                None if bored is None else int(bored),
                None if surprised is None else int(surprised),
                reaction_text,
                _now(),
                prediction_error,
            ),
        )
    return prediction_error


def fetch_learning_record(db_path: Path, run_id: str) -> dict[str, Any]:
    ensure_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        run = conn.execute("SELECT * FROM recommendation_runs WHERE id=?", (run_id,)).fetchone()
        if run is None:
            raise KeyError(run_id)
        candidates = conn.execute(
            "SELECT * FROM recommendation_candidates WHERE run_id=? ORDER BY rank_position",
            (run_id,),
        ).fetchall()
        outcome = conn.execute(
            "SELECT * FROM recommendation_outcomes WHERE run_id=?",
            (run_id,),
        ).fetchone()

    result = dict(run)
    for key in ("request_json", "explanation_json", "availability_json"):
        result[key.removesuffix("_json")] = json.loads(result.pop(key))
    result["candidates"] = []
    for candidate in candidates:
        item = dict(candidate)
        item["rejection_reasons"] = json.loads(item.pop("rejection_reasons_json"))
        item["score_components"] = json.loads(item.pop("score_components_json"))
        result["candidates"].append(item)
    result["outcome"] = dict(outcome) if outcome else None
    return result
