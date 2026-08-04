"""Reconcile manual post-watch handoffs with frozen pre-release predictions.

Manual handoffs are useful explicit evidence, but they are not equivalent to the
content-addressed Outcome Capture v1 contract. This module verifies the strongest
binding available without inventing a release ID and keeps the resulting metrics
outside formal release-bound Recommendation Trust.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


RECONCILIATION_VERSION = "1.0.0"
MANUAL_INTAKE_VERSION = "1.0.0"
EXPECTED_BINDING_STATUS = (
    "manual_unbound_do_not_count_as_recommendation_trust_until_verified"
)
RATING_PROJECTION_METHOD = "legacy_linear_predicted_score_to_letterboxd_0.5_5.0_v1"
REGRESSION_ERROR_THRESHOLD = 1.0


class ManualOutcomeReconciliationError(ValueError):
    """Raised when a manual handoff cannot be reconciled safely."""


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
        raise ManualOutcomeReconciliationError(f"submission.{field} is required")
    return value.strip()


def _validate_submission(submission: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(submission, dict):
        raise ManualOutcomeReconciliationError("submission must be a JSON object")
    if submission.get("version") != MANUAL_INTAKE_VERSION:
        raise ManualOutcomeReconciliationError(
            f"submission.version must be {MANUAL_INTAKE_VERSION}"
        )
    if submission.get("submission_type") != "post_watch_manual_intake":
        raise ManualOutcomeReconciliationError(
            "submission_type must be post_watch_manual_intake"
        )
    if submission.get("release_binding_status") != EXPECTED_BINDING_STATUS:
        raise ManualOutcomeReconciliationError(
            "manual intake must preserve its unbound release status"
        )

    rating = submission.get("actual_rating")
    if not _is_number(rating) or not 0.5 <= float(rating) <= 5.0:
        raise ManualOutcomeReconciliationError(
            "submission.actual_rating must be between 0.5 and 5.0"
        )
    for field in ("completed", "glad_watched"):
        if not isinstance(submission.get(field), bool):
            raise ManualOutcomeReconciliationError(
                f"submission.{field} must be true or false"
            )
    fit = submission.get("fit_the_moment")
    if fit is not None and not isinstance(fit, bool):
        raise ManualOutcomeReconciliationError(
            "submission.fit_the_moment must be true, false, or null"
        )
    if submission.get("already_seen") is not False:
        raise ManualOutcomeReconciliationError(
            "manual outcome must identify a film that was unwatched before recommendation"
        )
    if submission.get("watched_after_recommendation") != "yes":
        raise ManualOutcomeReconciliationError(
            "manual outcome must confirm the watch followed the recommendation"
        )

    return {
        "source_artifact": _require_text(submission, "source_artifact"),
        "film_key": _require_text(submission, "film_key"),
        "title": _require_text(submission, "title"),
        "year": submission.get("year"),
        "watched_at": _require_text(submission, "watched_at"),
        "recorded_at": _require_text(submission, "recorded_at"),
        "actual_rating": round(float(rating), 3),
        "reaction_text": _require_text(submission, "reaction_text"),
        "completed": submission["completed"],
        "glad_watched": submission["glad_watched"],
        "fit_the_moment": fit,
        "interest": submission.get("interest"),
        "prediction_reaction": submission.get("prediction_reaction"),
        "actual_sentiment": submission.get("actual_sentiment"),
        "would_recommend": submission.get("would_recommend"),
        "notes": str(submission.get("notes") or "").strip(),
    }


def _verify_frozen_prediction(
    frozen_evaluation: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(frozen_evaluation, dict):
        raise ManualOutcomeReconciliationError(
            "frozen evaluation must be a JSON object"
        )
    if frozen_evaluation.get("evaluation_type") != "frozen_top_five":
        raise ManualOutcomeReconciliationError(
            "frozen evaluation must have evaluation_type frozen_top_five"
        )
    if frozen_evaluation.get("source_artifact") != actual["source_artifact"]:
        raise ManualOutcomeReconciliationError(
            "submission.source_artifact does not match the frozen evaluation"
        )
    films = frozen_evaluation.get("films")
    if not isinstance(films, list) or len(films) != 5:
        raise ManualOutcomeReconciliationError(
            "frozen evaluation must contain exactly five predictions"
        )
    matches = [film for film in films if film.get("film_key") == actual["film_key"]]
    if len(matches) != 1:
        raise ManualOutcomeReconciliationError(
            "submission.film_key must identify exactly one frozen prediction"
        )
    prediction = matches[0]
    if prediction.get("title") != actual["title"] or prediction.get("year") != actual["year"]:
        raise ManualOutcomeReconciliationError(
            "submission title/year do not match the frozen prediction"
        )
    if prediction.get("already_seen") is not False:
        raise ManualOutcomeReconciliationError(
            "frozen prediction does not prove the film was unwatched"
        )
    if prediction.get("watched_after_recommendation") != "not_yet":
        raise ManualOutcomeReconciliationError(
            "frozen prediction was not preserved before the watch"
        )
    for field in ("actual_rating", "actual_sentiment"):
        if prediction.get(field) is not None:
            raise ManualOutcomeReconciliationError(
                "frozen prediction already contains post-watch evidence"
            )
    score = prediction.get("predicted_score")
    confidence = prediction.get("predicted_confidence")
    if not _is_number(score) or not -1 <= float(score) <= 1:
        raise ManualOutcomeReconciliationError(
            "frozen prediction has an invalid predicted_score"
        )
    if not _is_number(confidence) or not 0 <= float(confidence) <= 1:
        raise ManualOutcomeReconciliationError(
            "frozen prediction has an invalid predicted_confidence"
        )
    return prediction


def reconcile_manual_outcome(
    frozen_evaluation: dict[str, Any],
    submission: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Verify a manual intake and emit separate, non-release-bound evidence."""
    actual = _validate_submission(submission)
    prediction = _verify_frozen_prediction(frozen_evaluation, actual)

    predicted_score = round(float(prediction["predicted_score"]), 6)
    confidence = round(float(prediction["predicted_confidence"]), 6)
    projected_rating = round(2.75 + (2.25 * predicted_score), 3)
    prediction_error = round(actual["actual_rating"] - projected_rating, 3)
    absolute_error = round(abs(prediction_error), 3)
    observed_trust = 1.0 if actual["glad_watched"] else 0.0

    review_reasons: list[str] = []
    if not actual["glad_watched"]:
        review_reasons.append("not_glad_watched")
    if not actual["completed"]:
        review_reasons.append("not_completed")
    if actual["fit_the_moment"] is False:
        review_reasons.append("wrong_for_moment")
    if absolute_error >= REGRESSION_ERROR_THRESHOLD:
        review_reasons.append("rating_projection_miss")
        if confidence >= 0.6:
            review_reasons.append("overconfident_miss")

    drift_fields = [
        field
        for field in ("interest", "prediction_reaction")
        if actual.get(field) is not None and actual.get(field) != prediction.get(field)
    ]
    identity = {
        "version": RECONCILIATION_VERSION,
        "source_artifact": actual["source_artifact"],
        "frozen_prediction_digest": _digest(prediction),
        "submission": actual,
    }
    outcome_id = "manual-outcome-" + _digest(identity)[:20]
    review_id = (
        "manual-regression-"
        + _digest({"outcome_id": outcome_id, "reasons": review_reasons})[:20]
        if review_reasons
        else None
    )

    outcome = {
        "version": RECONCILIATION_VERSION,
        "outcome_type": "verified_manual_recommendation_outcome",
        "outcome_id": outcome_id,
        "binding": {
            "status": "verified_legacy_frozen_prediction",
            "source_artifact": actual["source_artifact"],
            "frozen_prediction_digest": _digest(prediction),
            "release_id": None,
            "formal_release_bound_trust_eligible": False,
            "reason": "prediction predates Recommendation Release Gates v1",
        },
        "prediction": {
            "film_key": prediction["film_key"],
            "title": prediction["title"],
            "year": prediction["year"],
            "predicted_score": predicted_score,
            "predicted_confidence": confidence,
            "drivers": prediction.get("drivers", []),
            "uncertainty": prediction.get("uncertainty"),
            "frozen_pre_watch": {
                "interest": prediction.get("interest"),
                "prediction_reaction": prediction.get("prediction_reaction"),
            },
        },
        "actual": {
            "watched_at": actual["watched_at"],
            "recorded_at": actual["recorded_at"],
            "rating": actual["actual_rating"],
            "reaction_text": actual["reaction_text"],
            "completed": actual["completed"],
            "glad_watched": actual["glad_watched"],
            "fit_the_moment": actual["fit_the_moment"],
            "sentiment": actual["actual_sentiment"],
            "would_recommend": actual["would_recommend"],
            "notes": actual["notes"],
        },
        "evaluation": {
            "observed_recommendation_trust": observed_trust,
            "formal_release_bound_recommendation_trust": None,
            "projected_rating": projected_rating,
            "rating_projection_method": RATING_PROJECTION_METHOD,
            "prediction_error": prediction_error,
            "absolute_prediction_error": absolute_error,
            "review_required": bool(review_reasons),
            "review_reasons": review_reasons,
            "review_candidate_id": review_id,
            "submitted_pre_watch_field_drift": drift_fields,
        },
        "provenance": {
            "source_type": "manual_handoff_verified_against_frozen_evaluation",
            "prediction_frozen_before_outcome": True,
            "release_id_invented_or_backdated": False,
            "taste_weights_modified": False,
        },
    }

    candidate = None
    if review_id:
        candidate = {
            "version": RECONCILIATION_VERSION,
            "fixture_type": "manual_outcome_regression_candidate",
            "fixture_id": review_id,
            "outcome_id": outcome_id,
            "source_artifact": actual["source_artifact"],
            "film_key": prediction["film_key"],
            "reasons": review_reasons,
            "calibration": {
                "projected_rating": projected_rating,
                "actual_rating": actual["actual_rating"],
                "prediction_error": prediction_error,
                "absolute_prediction_error": absolute_error,
                "predicted_confidence": confidence,
                "observed_recommendation_trust": observed_trust,
            },
            "promotion_status": "candidate_not_promoted",
            "formal_release_bound_fixture": False,
        }
    return outcome, candidate


def write_manual_outcome_reconciliation(
    frozen_evaluation_path: Path,
    submission_path: Path,
    output_root: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None, Path, Path | None]:
    frozen_evaluation = json.loads(
        frozen_evaluation_path.read_text(encoding="utf-8")
    )
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    outcome, candidate = reconcile_manual_outcome(frozen_evaluation, submission)

    source_dir = output_root / outcome["binding"]["source_artifact"]
    source_dir.mkdir(parents=True, exist_ok=True)
    outcome_dir = source_dir / outcome["outcome_id"]
    outcome_dir.mkdir(exist_ok=False)
    outcome_path = outcome_dir / "manual_outcome_reconciliation_v1.json"
    with outcome_path.open("x", encoding="utf-8") as handle:
        json.dump(outcome, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    candidate_path = None
    if candidate is not None:
        candidate_path = outcome_dir / "manual_outcome_regression_candidate_v1.json"
        with candidate_path.open("x", encoding="utf-8") as handle:
            json.dump(candidate, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    return outcome, candidate, outcome_path, candidate_path
