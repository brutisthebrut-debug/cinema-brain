from __future__ import annotations

from copy import deepcopy

import pytest

from cinema_brain.manual_outcome_reconciliation import (
    ManualOutcomeReconciliationError,
    reconcile_manual_outcome,
    write_manual_outcome_reconciliation,
)


def frozen_evaluation() -> dict:
    films = []
    for index in range(5):
        films.append(
            {
                "film_key": f"title:film-{index}:2026",
                "title": f"Film {index}",
                "year": 2026,
                "predicted_score": round(0.888 - (index * 0.05), 3),
                "predicted_confidence": 0.678,
                "drivers": ["creeping dread", "sustained uncertainty"],
                "uncertainty": "Limited direct evidence.",
                "already_seen": False,
                "interest": "yes",
                "prediction_reaction": "nailed_it",
                "watched_after_recommendation": "not_yet",
                "actual_rating": None,
                "actual_sentiment": None,
                "would_recommend": "unknown",
            }
        )
    return {
        "version": "1.0.0",
        "source_artifact": "daniel-unwatched-horror-ranking-v2",
        "evaluation_type": "frozen_top_five",
        "films": films,
    }


def submission() -> dict:
    return {
        "version": "1.0.0",
        "submission_type": "post_watch_manual_intake",
        "source_artifact": "daniel-unwatched-horror-ranking-v2",
        "film_key": "title:film-0:2026",
        "title": "Film 0",
        "year": 2026,
        "watched_at": "2026-08-04T01:09:00.000Z",
        "recorded_at": "2026-08-04T01:11:48.659Z",
        "actual_rating": 3.5,
        "reaction_text": "The pacing and uncertainty worked.",
        "completed": True,
        "glad_watched": True,
        "fit_the_moment": True,
        "already_seen": False,
        "interest": "maybe",
        "prediction_reaction": "nailed_it",
        "watched_after_recommendation": "yes",
        "actual_sentiment": "like",
        "would_recommend": "yes",
        "notes": "Eerie but a little hard to follow.",
        "release_binding_status": (
            "manual_unbound_do_not_count_as_recommendation_trust_until_verified"
        ),
    }


def test_reconciles_verified_manual_outcome_without_inventing_release_trust():
    outcome, candidate = reconcile_manual_outcome(frozen_evaluation(), submission())

    assert outcome["binding"]["status"] == "verified_legacy_frozen_prediction"
    assert outcome["binding"]["release_id"] is None
    assert outcome["binding"]["formal_release_bound_trust_eligible"] is False
    assert outcome["evaluation"]["observed_recommendation_trust"] == 1.0
    assert outcome["evaluation"]["formal_release_bound_recommendation_trust"] is None
    assert outcome["evaluation"]["projected_rating"] == 4.748
    assert outcome["evaluation"]["prediction_error"] == -1.248
    assert outcome["evaluation"]["review_reasons"] == [
        "rating_projection_miss",
        "overconfident_miss",
    ]
    assert outcome["evaluation"]["submitted_pre_watch_field_drift"] == ["interest"]
    assert candidate is not None
    assert candidate["promotion_status"] == "candidate_not_promoted"
    assert candidate["formal_release_bound_fixture"] is False


def test_reconciliation_is_deterministic():
    first = reconcile_manual_outcome(frozen_evaluation(), submission())
    second = reconcile_manual_outcome(frozen_evaluation(), submission())
    assert first == second


def test_rejects_wrong_source_artifact():
    changed = submission()
    changed["source_artifact"] = "later-ranking"
    with pytest.raises(ManualOutcomeReconciliationError, match="source_artifact"):
        reconcile_manual_outcome(frozen_evaluation(), changed)


def test_rejects_prediction_that_was_not_frozen_before_watch():
    changed = frozen_evaluation()
    changed["films"][0]["actual_rating"] = 3.5
    with pytest.raises(ManualOutcomeReconciliationError, match="post-watch evidence"):
        reconcile_manual_outcome(changed, submission())


def test_rejects_attempt_to_present_manual_input_as_release_bound():
    changed = submission()
    changed["release_binding_status"] = "release_bound"
    with pytest.raises(ManualOutcomeReconciliationError, match="unbound release status"):
        reconcile_manual_outcome(frozen_evaluation(), changed)


def test_writes_append_only_outcome_and_candidate(tmp_path):
    evaluation_path = tmp_path / "evaluation.json"
    submission_path = tmp_path / "submission.json"
    evaluation_path.write_text(__import__("json").dumps(frozen_evaluation()))
    submission_path.write_text(__import__("json").dumps(submission()))

    outcome, candidate, outcome_path, candidate_path = write_manual_outcome_reconciliation(
        evaluation_path,
        submission_path,
        tmp_path / "outcomes",
    )
    assert outcome_path.exists()
    assert candidate is not None
    assert candidate_path is not None and candidate_path.exists()

    with pytest.raises(FileExistsError):
        write_manual_outcome_reconciliation(
            evaluation_path,
            submission_path,
            tmp_path / "outcomes",
        )


def test_no_candidate_when_recommendation_and_calibration_both_land():
    evaluation = frozen_evaluation()
    evaluation["films"][0]["predicted_score"] = 0.4
    actual = deepcopy(submission())
    actual["actual_rating"] = 3.5
    outcome, candidate = reconcile_manual_outcome(evaluation, actual)
    assert outcome["evaluation"]["review_required"] is False
    assert candidate is None
