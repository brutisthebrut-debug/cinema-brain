from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from cinema_brain.post_watch_outcomes import (
    PostWatchOutcomeError,
    build_outcome_capture_template,
    capture_post_watch_outcome,
    summarize_recommendation_trust,
    write_post_watch_outcome,
)
from cinema_brain.recommendation_audit import build_recommendation_audit
from cinema_brain.recommendation_release_gates import (
    build_recommendation_release_package,
)


def _prediction(index: int) -> dict:
    return {
        "film_key": f"title:film-{index}:2026",
        "title": f"Film {index}",
        "year": 2026,
        "taste_score": round(0.9 - index * 0.1, 3),
        "confidence": 0.75,
        "active_trait_count": 3,
        "trait_coverage": 0.75,
        "top_matches": [{"trait_id": "creeping_dread", "contribution": 0.4}],
        "top_mismatches": [],
        "all_components": [{"trait_id": "creeping_dread", "contribution": 0.4}],
        "decision": "recommend",
        "abstention_reasons": [],
        "recommendation_rank": index,
    }


def _release() -> tuple[dict, dict, dict]:
    recommendations = [_prediction(index) for index in range(1, 7)]
    ranking = {
        "version": "0.3.0",
        "model_version": "canonical-taste-score-1.0.0",
        "taste_model_version": "taste-1.0.0",
        "corpus_version": "1.0.0-candidate",
        "registry_version": "1.0.0",
        "candidate_count": 7,
        "watched_excluded_count": 0,
        "eligible_count": 7,
        "recommended_count": 6,
        "abstained_count": 1,
        "watched_exclusions": [],
        "recommendations": recommendations,
        "abstentions": [
            {
                "film_key": "title:abstain:2026",
                "title": "Abstain",
                "taste_score": 0.1,
                "confidence": 0.1,
                "active_trait_count": 1,
                "trait_coverage": 0.25,
                "abstention_reasons": ["low_confidence"],
            }
        ],
    }
    slate = []
    for index, item in enumerate(recommendations[:5], start=1):
        released = deepcopy(item)
        released.update(
            {
                "raw_rank": index,
                "slate_rank": index,
                "novelty_score": round(1 - index * 0.1, 3),
                "slate_score": round(0.95 - index * 0.03, 3),
                "slate_role": "discovery" if index == 5 else "core",
            }
        )
        slate.append(released)
    balanced = {
        "version": "0.3.0",
        "source_ranking_version": ranking["version"],
        "model_version": ranking["model_version"],
        "taste_model_version": ranking["taste_model_version"],
        "corpus_version": ranking["corpus_version"],
        "raw_recommendations": recommendations,
        "balanced_slate": slate,
        "slate_metrics": {
            "unique_trait_count": 1,
            "trait_assignment_count": 5,
            "trait_diversity_ratio": 0.2,
            "discovery_count": 1,
            "average_novelty": 0.7,
        },
        "abstentions": ranking["abstentions"],
        "watched_exclusions": [],
    }
    manifest, snapshot = build_recommendation_release_package(
        ranking,
        balanced,
        generated_at="2026-08-04T12:00:00Z",
        source_revision="abc123",
    )
    return manifest, snapshot, build_recommendation_audit(manifest, snapshot)


def _submission(manifest: dict, audit: dict, **updates: object) -> dict:
    payload = {
        "version": "1.0.0",
        "submission_type": "post_watch_outcome_submission",
        "release_id": manifest["release_id"],
        "audit_id": audit["audit_id"],
        "film_key": "title:film-1:2026",
        "watched_at": "2026-08-04T02:00:00Z",
        "recorded_at": "2026-08-04T04:00:00Z",
        "actual_rating": 4.5,
        "reaction_text": "The creeping dread worked and I stayed locked in.",
        "completed": True,
        "glad_watched": True,
        "fit_the_moment": True,
    }
    payload.update(updates)
    return payload


def test_template_is_verified_and_restricted_to_released_predictions() -> None:
    manifest, snapshot, audit = _release()
    template = build_outcome_capture_template(manifest, snapshot, audit)

    assert template["release_id"] == manifest["release_id"]
    assert template["audit_id"] == audit["audit_id"]
    assert [item["film_key"] for item in template["released_predictions"]] == [
        item["film_key"] for item in snapshot["balanced_slate"]
    ]
    assert template["film_key"] is None
    assert template["glad_watched"] is None


def test_capture_preserves_inputs_and_calculates_trust_and_error() -> None:
    manifest, snapshot, audit = _release()
    originals = deepcopy((manifest, snapshot, audit))

    outcome, fixture = capture_post_watch_outcome(
        manifest,
        snapshot,
        audit,
        _submission(manifest, audit),
    )

    assert (manifest, snapshot, audit) == originals
    assert outcome["release_id"] == manifest["release_id"]
    assert outcome["prediction"]["projected_rating"] == 4.55
    assert outcome["evaluation"]["prediction_error"] == -0.05
    assert outcome["evaluation"]["recommendation_trust"] == 1.0
    assert outcome["evaluation"]["regression_required"] is False
    assert fixture is None


def test_meaningful_miss_creates_deterministic_regression_fixture() -> None:
    manifest, snapshot, audit = _release()
    submission = _submission(
        manifest,
        audit,
        actual_rating=2.0,
        reaction_text="It felt generic and completely wrong for tonight.",
        completed=False,
        glad_watched=False,
        fit_the_moment=False,
    )

    first = capture_post_watch_outcome(manifest, snapshot, audit, submission)
    second = capture_post_watch_outcome(manifest, snapshot, audit, submission)
    assert first == second
    outcome, fixture = first
    assert outcome["evaluation"]["recommendation_trust"] == 0.0
    assert outcome["evaluation"]["prediction_error"] == -2.55
    assert outcome["evaluation"]["regression_reasons"] == [
        "not_glad_watched",
        "not_completed",
        "wrong_for_moment",
        "rating_projection_miss",
        "overconfident_miss",
    ]
    assert fixture is not None
    assert fixture["promotion_status"] == "candidate_not_promoted"
    assert fixture["frozen_prediction"]["top_matches"] == snapshot["balanced_slate"][0][
        "top_matches"
    ]


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"release_id": "recommendation-wrong"}, "release_id"),
        ({"audit_id": "recommendation-audit-wrong"}, "audit_id"),
        ({"film_key": "title:not-released:2026"}, "released prediction"),
    ],
)
def test_capture_fails_closed_on_identity_mismatch(updates: dict, message: str) -> None:
    manifest, snapshot, audit = _release()
    with pytest.raises(PostWatchOutcomeError, match=message):
        capture_post_watch_outcome(
            manifest,
            snapshot,
            audit,
            _submission(manifest, audit, **updates),
        )


def test_capture_rejects_modified_audit() -> None:
    manifest, snapshot, audit = _release()
    audit["health_metrics"]["average_novelty"] = 0.0

    with pytest.raises(PostWatchOutcomeError, match="audit does not match"):
        capture_post_watch_outcome(
            manifest,
            snapshot,
            audit,
            _submission(manifest, audit),
        )


def test_outcome_storage_is_append_only(tmp_path: Path) -> None:
    manifest, snapshot, audit = _release()
    paths = {
        "manifest": tmp_path / "manifest.json",
        "snapshot": tmp_path / "snapshot.json",
        "audit": tmp_path / "audit.json",
        "submission": tmp_path / "submission.json",
    }
    for key, payload in (
        ("manifest", manifest),
        ("snapshot", snapshot),
        ("audit", audit),
        ("submission", _submission(manifest, audit)),
    ):
        paths[key].write_text(json.dumps(payload), encoding="utf-8")

    _, _, outcome_path, fixture_path = write_post_watch_outcome(
        paths["manifest"],
        paths["snapshot"],
        paths["audit"],
        paths["submission"],
        tmp_path / "outcomes",
    )
    assert outcome_path.exists()
    assert fixture_path is None

    with pytest.raises(FileExistsError):
        write_post_watch_outcome(
            paths["manifest"],
            paths["snapshot"],
            paths["audit"],
            paths["submission"],
            tmp_path / "outcomes",
        )


def test_trust_summary_keeps_north_star_and_calibration_separate() -> None:
    manifest, snapshot, audit = _release()
    trusted, _ = capture_post_watch_outcome(
        manifest,
        snapshot,
        audit,
        _submission(manifest, audit),
    )
    miss, _ = capture_post_watch_outcome(
        manifest,
        snapshot,
        audit,
        _submission(
            manifest,
            audit,
            recorded_at="2026-08-05T04:00:00Z",
            actual_rating=2.0,
            glad_watched=False,
            fit_the_moment=False,
        ),
    )

    summary = summarize_recommendation_trust([trusted, miss])
    assert summary["recommendation_trust"] == 0.5
    assert summary["completion_rate"] == 1.0
    assert summary["moment_fit_rate"] == 0.5
    assert summary["mean_absolute_prediction_error"] == 1.3
    assert summary["regression_fixture_count"] == 1
