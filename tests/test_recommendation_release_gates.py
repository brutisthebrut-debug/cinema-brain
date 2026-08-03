from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from cinema_brain.recommendation_release_gates import (
    RecommendationReleaseError,
    build_recommendation_release_package,
    evaluate_recommendation_release,
    verify_recommendation_release_package,
    write_recommendation_release_package,
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
        "raw_rank": index,
        "slate_rank": index,
        "novelty_score": round(1 - (index - 1) * 0.1, 3),
        "slate_score": round(0.95 - index * 0.03, 3),
        "slate_role": "discovery" if index == 5 else "core",
    }


def _artifacts() -> tuple[dict, dict]:
    recommendations = [_prediction(index) for index in range(1, 7)]
    for item in recommendations:
        item.pop("slate_rank")
        item.pop("raw_rank")
        item.pop("novelty_score")
        item.pop("slate_score")
        item.pop("slate_role")
    abstentions = [{"film_key": "title:abstain:2026", "title": "Abstain"}]
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
    slate = []
    for index, item in enumerate(recommendations[:5], start=1):
        released = deepcopy(item)
        released.update(
            {
                "raw_rank": index,
                "slate_rank": index,
                "novelty_score": round(1 - (index - 1) * 0.1, 3),
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
            "average_novelty": 0.8,
        },
        "abstentions": abstentions,
        "watched_exclusions": watched,
    }
    return ranking, balanced


def test_eligible_release_builds_a_deterministic_manifest_and_snapshot() -> None:
    ranking, balanced = _artifacts()
    gates = evaluate_recommendation_release(ranking, balanced)
    assert gates["eligible"] is True

    first = build_recommendation_release_package(
        ranking,
        balanced,
        generated_at="2026-08-03T23:30:00Z",
        source_revision="abc123",
    )
    second = build_recommendation_release_package(
        ranking,
        balanced,
        generated_at="2026-08-04T00:30:00Z",
        source_revision="abc123",
    )

    assert first[1] == second[1]
    assert first[0]["prediction_snapshot_sha256"] == second[0]["prediction_snapshot_sha256"]
    manifest, snapshot = first
    assert manifest["status"] == "eligible_for_private_evaluation"
    assert manifest["counts"]["released_predictions"] == 5
    assert snapshot["balanced_slate"] == balanced["balanced_slate"]
    verify_recommendation_release_package(manifest, snapshot)


def test_release_fails_closed_when_a_watched_film_enters_the_slate() -> None:
    ranking, balanced = _artifacts()
    watched_key = ranking["watched_exclusions"][0]["film_key"]
    ranking["recommendations"][0]["film_key"] = watched_key
    balanced["raw_recommendations"] = deepcopy(ranking["recommendations"])
    balanced["balanced_slate"][0]["film_key"] = watched_key

    gates = evaluate_recommendation_release(ranking, balanced)
    assert gates["eligible"] is False
    watched_gate = next(item for item in gates["checks"] if item["id"] == "watched_exclusion")
    assert watched_gate["passed"] is False

    with pytest.raises(RecommendationReleaseError, match="watched films entered"):
        build_recommendation_release_package(
            ranking,
            balanced,
            generated_at="2026-08-03T23:30:00Z",
            source_revision="abc123",
        )


def test_snapshot_tampering_is_detected() -> None:
    ranking, balanced = _artifacts()
    manifest, snapshot = build_recommendation_release_package(
        ranking,
        balanced,
        generated_at="2026-08-03T23:30:00Z",
        source_revision="abc123",
    )
    snapshot["balanced_slate"][0]["taste_score"] = -1.0

    with pytest.raises(RecommendationReleaseError, match="digest mismatch"):
        verify_recommendation_release_package(manifest, snapshot)


def test_release_files_are_create_once(tmp_path: Path) -> None:
    ranking, balanced = _artifacts()
    ranking_path = tmp_path / "ranking.json"
    balanced_path = tmp_path / "balanced.json"
    output_dir = tmp_path / "release"
    ranking_path.write_text(json.dumps(ranking), encoding="utf-8")
    balanced_path.write_text(json.dumps(balanced), encoding="utf-8")

    manifest_path, snapshot_path = write_recommendation_release_package(
        ranking_path,
        balanced_path,
        output_dir,
        generated_at="2026-08-03T23:30:00Z",
        source_revision="abc123",
    )
    assert manifest_path.exists()
    assert snapshot_path.exists()

    with pytest.raises(FileExistsError, match="already exists"):
        write_recommendation_release_package(
            ranking_path,
            balanced_path,
            output_dir,
            generated_at="2026-08-03T23:30:00Z",
            source_revision="abc123",
        )
