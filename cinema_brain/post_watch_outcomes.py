from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from cinema_brain.recommendation_audit import (
    RecommendationAuditError,
    build_recommendation_audit,
)


OUTCOME_TEMPLATE_VERSION = "1.0.0"
OUTCOME_VERSION = "1.0.0"
TRUST_SUMMARY_VERSION = "1.0.0"
REGRESSION_FIXTURE_VERSION = "1.0.0"
RATING_PROJECTION_METHOD = "linear_taste_score_to_letterboxd_0.5_5.0_v1"
REGRESSION_ERROR_THRESHOLD = 1.0


class PostWatchOutcomeError(ValueError):
    """Raised when post-watch evidence cannot be linked to a frozen release safely."""


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PostWatchOutcomeError(f"submission.{field} is required")
    return value.strip()


def _verify_pre_outcome_contract(
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
    audit: dict[str, Any],
) -> None:
    """Rebuild Audit v1 and reject any modified or post-outcome input."""
    try:
        expected_audit = build_recommendation_audit(manifest, snapshot)
    except RecommendationAuditError as error:
        raise PostWatchOutcomeError(str(error)) from error
    if audit != expected_audit:
        raise PostWatchOutcomeError(
            "audit does not match the verified pre-outcome release contract"
        )
    if audit.get("outcome_status", {}).get("status") != "awaiting_outcome":
        raise PostWatchOutcomeError("audit is not awaiting an outcome")


def _released_prediction(
    snapshot: dict[str, Any],
    film_key: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in snapshot.get("balanced_slate", [])
        if isinstance(item, dict) and item.get("film_key") == film_key
    ]
    if len(matches) != 1:
        raise PostWatchOutcomeError(
            "submission.film_key must identify exactly one released prediction"
        )
    return matches[0]


def _project_rating(taste_score: Any) -> float:
    if not _is_number(taste_score) or not -1 <= float(taste_score) <= 1:
        raise PostWatchOutcomeError("released prediction has an invalid taste_score")
    return round(2.75 + (2.25 * float(taste_score)), 3)


def build_outcome_capture_template(
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Build the fillable, release-bound post-watch submission contract."""
    _verify_pre_outcome_contract(manifest, snapshot, audit)
    return {
        "version": OUTCOME_TEMPLATE_VERSION,
        "submission_type": "post_watch_outcome_submission",
        "release_id": manifest["release_id"],
        "audit_id": audit["audit_id"],
        "instructions": {
            "immutable_fields": ["version", "submission_type", "release_id", "audit_id"],
            "required_fields": [
                "film_key",
                "watched_at",
                "recorded_at",
                "actual_rating",
                "reaction_text",
                "completed",
                "glad_watched",
            ],
            "rating_scale": "Letterboxd 0.5 to 5.0",
            "fit_the_moment_may_be_null": True,
        },
        "released_predictions": [
            {
                "film_key": item["film_key"],
                "title": item.get("title"),
                "slate_rank": item.get("slate_rank"),
                "slate_role": item.get("slate_role"),
            }
            for item in snapshot["balanced_slate"]
        ],
        "film_key": None,
        "watched_at": None,
        "recorded_at": None,
        "actual_rating": None,
        "reaction_text": None,
        "completed": None,
        "glad_watched": None,
        "fit_the_moment": None,
    }


def _validate_submission(
    submission: dict[str, Any],
    manifest: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(submission, dict):
        raise PostWatchOutcomeError("submission must be a JSON object")
    if submission.get("version") != OUTCOME_TEMPLATE_VERSION:
        raise PostWatchOutcomeError(
            f"submission.version must be {OUTCOME_TEMPLATE_VERSION}"
        )
    if submission.get("submission_type") != "post_watch_outcome_submission":
        raise PostWatchOutcomeError("submission_type must be post_watch_outcome_submission")
    if submission.get("release_id") != manifest.get("release_id"):
        raise PostWatchOutcomeError("submission.release_id does not match the release")
    if submission.get("audit_id") != audit.get("audit_id"):
        raise PostWatchOutcomeError("submission.audit_id does not match the verified audit")

    film_key = _require_text(submission, "film_key")
    watched_at = _require_text(submission, "watched_at")
    recorded_at = _require_text(submission, "recorded_at")
    reaction_text = _require_text(submission, "reaction_text")
    rating = submission.get("actual_rating")
    if not _is_number(rating) or not 0.5 <= float(rating) <= 5.0:
        raise PostWatchOutcomeError("submission.actual_rating must be between 0.5 and 5.0")
    for field in ("completed", "glad_watched"):
        if not isinstance(submission.get(field), bool):
            raise PostWatchOutcomeError(f"submission.{field} must be true or false")
    fit = submission.get("fit_the_moment")
    if fit is not None and not isinstance(fit, bool):
        raise PostWatchOutcomeError(
            "submission.fit_the_moment must be true, false, or null"
        )
    return {
        "film_key": film_key,
        "watched_at": watched_at,
        "recorded_at": recorded_at,
        "actual_rating": round(float(rating), 3),
        "reaction_text": reaction_text,
        "completed": submission["completed"],
        "glad_watched": submission["glad_watched"],
        "fit_the_moment": fit,
    }


def capture_post_watch_outcome(
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
    audit: dict[str, Any],
    submission: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Append explicit outcome evidence without mutating any frozen release input."""
    _verify_pre_outcome_contract(manifest, snapshot, audit)
    actual = _validate_submission(submission, manifest, audit)
    prediction = _released_prediction(snapshot, actual["film_key"])
    projected_rating = _project_rating(prediction.get("taste_score"))
    prediction_error = round(actual["actual_rating"] - projected_rating, 3)
    absolute_error = round(abs(prediction_error), 3)
    recommendation_trust = 1.0 if actual["glad_watched"] else 0.0

    regression_reasons: list[str] = []
    if not actual["glad_watched"]:
        regression_reasons.append("not_glad_watched")
    if not actual["completed"]:
        regression_reasons.append("not_completed")
    if actual["fit_the_moment"] is False:
        regression_reasons.append("wrong_for_moment")
    if absolute_error >= REGRESSION_ERROR_THRESHOLD:
        regression_reasons.append("rating_projection_miss")
        confidence = prediction.get("confidence")
        if _is_number(confidence) and float(confidence) >= 0.6:
            regression_reasons.append("overconfident_miss")

    identity_payload = {
        "contract_version": OUTCOME_VERSION,
        "release_id": manifest["release_id"],
        "audit_id": audit["audit_id"],
        "prediction_snapshot_sha256": manifest["prediction_snapshot_sha256"],
        "submission": actual,
    }
    outcome_id = "recommendation-outcome-" + _digest(identity_payload)[:20]
    fixture_id = (
        "recommendation-regression-"
        + _digest(
            {
                "fixture_version": REGRESSION_FIXTURE_VERSION,
                "outcome_id": outcome_id,
                "reasons": regression_reasons,
            }
        )[:20]
        if regression_reasons
        else None
    )

    outcome = {
        "version": OUTCOME_VERSION,
        "outcome_type": "post_watch_recommendation_outcome",
        "outcome_id": outcome_id,
        "release_id": manifest["release_id"],
        "audit_id": audit["audit_id"],
        "source_revision": manifest["source_revision"],
        "prediction_snapshot_sha256": manifest["prediction_snapshot_sha256"],
        "recorded_at": actual["recorded_at"],
        "watched_at": actual["watched_at"],
        "prediction": {
            "film_key": prediction["film_key"],
            "title": prediction.get("title"),
            "year": prediction.get("year"),
            "raw_rank": prediction.get("raw_rank"),
            "slate_rank": prediction.get("slate_rank"),
            "slate_role": prediction.get("slate_role"),
            "taste_score": prediction.get("taste_score"),
            "confidence": prediction.get("confidence"),
            "projected_rating": projected_rating,
            "rating_projection_method": RATING_PROJECTION_METHOD,
        },
        "actual": {
            "rating": actual["actual_rating"],
            "reaction_text": actual["reaction_text"],
            "completed": actual["completed"],
            "glad_watched": actual["glad_watched"],
            "fit_the_moment": actual["fit_the_moment"],
        },
        "evaluation": {
            "recommendation_trust": recommendation_trust,
            "trust_definition": "1 when Daniel is genuinely glad he watched; otherwise 0",
            "prediction_error": prediction_error,
            "absolute_prediction_error": absolute_error,
            "regression_required": bool(regression_reasons),
            "regression_reasons": regression_reasons,
            "regression_fixture_id": fixture_id,
        },
        "provenance": {
            "source_type": "explicit_post_watch_submission",
            "prediction_frozen_before_outcome": True,
            "release_inputs_modified": False,
        },
    }

    fixture = None
    if fixture_id:
        fixture = {
            "version": REGRESSION_FIXTURE_VERSION,
            "fixture_type": "recommendation_outcome_regression",
            "fixture_id": fixture_id,
            "outcome_id": outcome_id,
            "release_id": manifest["release_id"],
            "film_key": prediction["film_key"],
            "reasons": regression_reasons,
            "frozen_prediction": {
                "taste_score": prediction.get("taste_score"),
                "confidence": prediction.get("confidence"),
                "raw_rank": prediction.get("raw_rank"),
                "slate_rank": prediction.get("slate_rank"),
                "slate_role": prediction.get("slate_role"),
                "top_matches": prediction.get("top_matches"),
                "top_mismatches": prediction.get("top_mismatches"),
                "all_components": prediction.get("all_components"),
            },
            "observed_outcome": outcome["actual"],
            "calibration": {
                "projected_rating": projected_rating,
                "actual_rating": actual["actual_rating"],
                "prediction_error": prediction_error,
                "absolute_prediction_error": absolute_error,
                "recommendation_trust": recommendation_trust,
            },
            "promotion_status": "candidate_not_promoted",
        }
    return outcome, fixture


def summarize_recommendation_trust(
    outcomes: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate explicit outcome records without changing their release-level evidence."""
    records = list(outcomes)
    seen: set[str] = set()
    release_ids: set[str] = set()
    for record in records:
        if record.get("version") != OUTCOME_VERSION or record.get("outcome_type") != (
            "post_watch_recommendation_outcome"
        ):
            raise PostWatchOutcomeError("trust summary accepts only Post-watch Outcome v1")
        outcome_id = record.get("outcome_id")
        if not isinstance(outcome_id, str) or not outcome_id or outcome_id in seen:
            raise PostWatchOutcomeError("outcome IDs must be present and unique")
        seen.add(outcome_id)
        release_ids.add(str(record.get("release_id")))

    count = len(records)
    glad_count = sum(record["actual"]["glad_watched"] is True for record in records)
    completed_count = sum(record["actual"]["completed"] is True for record in records)
    known_moment = [
        record["actual"]["fit_the_moment"]
        for record in records
        if record["actual"]["fit_the_moment"] is not None
    ]
    errors = [float(record["evaluation"]["absolute_prediction_error"]) for record in records]
    return {
        "version": TRUST_SUMMARY_VERSION,
        "summary_type": "recommendation_trust_summary",
        "outcome_count": count,
        "release_count": len(release_ids),
        "release_ids": sorted(release_ids),
        "glad_watched_count": glad_count,
        "recommendation_trust": round(glad_count / count, 6) if count else None,
        "completion_rate": round(completed_count / count, 6) if count else None,
        "moment_fit_rate": (
            round(sum(value is True for value in known_moment) / len(known_moment), 6)
            if known_moment
            else None
        ),
        "mean_absolute_prediction_error": (
            round(sum(errors) / len(errors), 6) if errors else None
        ),
        "regression_fixture_count": sum(
            record["evaluation"]["regression_required"] is True for record in records
        ),
    }


def write_outcome_capture_template(
    manifest_path: Path,
    snapshot_path: Path,
    audit_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    template = build_outcome_capture_template(manifest, snapshot, audit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(template, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return template


def write_post_watch_outcome(
    manifest_path: Path,
    snapshot_path: Path,
    audit_path: Path,
    submission_path: Path,
    output_root: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None, Path, Path | None]:
    """Write one append-only outcome directory and optional regression fixture."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    outcome, fixture = capture_post_watch_outcome(
        manifest,
        snapshot,
        audit,
        submission,
    )

    release_dir = output_root / outcome["release_id"]
    release_dir.mkdir(parents=True, exist_ok=True)
    outcome_dir = release_dir / outcome["outcome_id"]
    outcome_dir.mkdir(exist_ok=False)
    outcome_path = outcome_dir / "recommendation_outcome_v1.json"
    with outcome_path.open("x", encoding="utf-8") as handle:
        json.dump(outcome, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    fixture_path = None
    if fixture is not None:
        fixture_path = outcome_dir / "recommendation_regression_fixture_v1.json"
        with fixture_path.open("x", encoding="utf-8") as handle:
            json.dump(fixture, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    return outcome, fixture, outcome_path, fixture_path
