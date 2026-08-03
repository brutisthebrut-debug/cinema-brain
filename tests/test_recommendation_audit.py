from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from cinema_brain.recommendation_audit import (
    RecommendationAuditError,
    build_recommendation_audit,
    write_recommendation_audit,
)
from cinema_brain.recommendation_release_gates import (
    build_recommendation_release_package,
)


def _prediction(index: int) -> dict:
    return {
        "film_key": f"title:film-{index}:2026",
        "title": f"Film {index}",
        "year": 2026,
        "taste_score": round(0.9 - index * 0.03, 3),
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


def _release() -> tuple[dict, dict]:
    recommendations = [_prediction(index) for index in range(1, 7)]
    abstentions = [
        {
            "film_key": "title:abstain:2026",
            "title": "Abstain",
            "taste_score": 0.3,
            "confidence": 0.1,
            "active_trait_count": 1,
            "trait_coverage": 0.25,
            "abstention_reasons": ["low_confidence", "too_few_active_traits"],
        }
    ]
    watched = [{"film_key": "title:watched:2020", "title": "Watched", "year": 2020}]
    ranking = {
        "version": "0.3.0",
        "model_version": "canonical-taste-score-1.0.0",
        "taste_model_version": "taste-1.0.0",
        "corpus_version": "1.0.0-candidate",
        "registry_version": "1.0.0",
        "candidate_count": 8,
        "watched_excluded_count": 1,
        "eligible_count": 7,
        "recommended_count": 6,
        "abstained_count": 1,
        "watched_exclusions": watched,
        "recommendations": recommendations,
        "abstentions": abstentions,
    }
    selected = [recommendations[0], recommendations[2], recommendations[1], recommendations[3], recommendations[4]]
    slate = []
    for slate_rank, item in enumerate(selected, start=1):
        released = deepcopy(item)
        released.update(
            {
                "raw_rank": item["recommendation_rank"],
                "slate_rank": slate_rank,
                "novelty_score": round(1 - (slate_rank - 1) * 0.1, 3),
                "slate_score": round(0.95 - slate_rank * 0.03, 3),
                "slate_role": "discovery" if item["recommendation_rank"] == 3 else "core",
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
            "average_novelty": 0.8,
        },
        "abstentions": abstentions,
        "watched_exclusions": watched,
    }
    return build_recommendation_release_package(
        ranking,
        balanced,
        generated_at="2026-08-04T01:00:00Z",
        source_revision="abc123",
    )


def test_audit_is_deterministic_and_preserves_frozen_inputs() -> None:
    manifest, snapshot = _release()
    original_manifest = deepcopy(manifest)
    original_snapshot = deepcopy(snapshot)

    first = build_recommendation_audit(manifest, snapshot)
    second = build_recommendation_audit(manifest, snapshot)

    assert first == second
    assert manifest == original_manifest
    assert snapshot == original_snapshot
    assert first["status"] == "verified_read_only"
    assert first["release_id"] == manifest["release_id"]
    assert first["gate_audit"]["passed_check_count"] == 7
    assert first["health_metrics"]["release_gate_pass_ratio"] == 1.0


def test_audit_exposes_rank_movement_abstentions_and_evidence_coverage() -> None:
    manifest, snapshot = _release()
    audit = build_recommendation_audit(manifest, snapshot)

    moved = next(item for item in audit["rank_movement"] if item["raw_rank"] == 3)
    assert moved["slate_rank"] == 2
    assert moved["rank_delta"] == 1
    assert moved["movement"] == "promoted"
    assert moved["slate_role"] == "discovery"
    assert audit["abstention_audit"]["reason_counts"] == {
        "low_confidence": 1,
        "too_few_active_traits": 1,
    }
    assert audit["abstention_audit"]["rate"] == round(1 / 7, 6)
    assert audit["evidence_coverage"]["complete_prediction_ratio"] == 1.0
    assert audit["outcome_status"]["status"] == "awaiting_outcome"


def test_audit_fails_closed_on_manifest_snapshot_mismatch() -> None:
    manifest, snapshot = _release()
    manifest["counts"]["recommended"] += 1

    with pytest.raises(RecommendationAuditError, match="counts.recommended"):
        build_recommendation_audit(manifest, snapshot)


def test_audit_fails_closed_on_inconsistent_recorded_raw_rank() -> None:
    manifest, snapshot = _release()
    snapshot["balanced_slate"][0]["raw_rank"] = 99
    # Keep the snapshot digest valid to isolate the semantic rank-link check.
    import hashlib

    canonical = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    manifest["prediction_snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()

    with pytest.raises(RecommendationAuditError, match="records raw_rank 99"):
        build_recommendation_audit(manifest, snapshot)


def test_audit_file_is_create_once(tmp_path: Path) -> None:
    manifest, snapshot = _release()
    manifest_path = tmp_path / "manifest.json"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "audit.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

    result = write_recommendation_audit(manifest_path, snapshot_path, output_path)
    assert json.loads(output_path.read_text(encoding="utf-8")) == result

    with pytest.raises(FileExistsError):
        write_recommendation_audit(manifest_path, snapshot_path, output_path)
