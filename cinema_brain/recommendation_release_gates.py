from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


RELEASE_GATE_VERSION = "1.0.0"
MANIFEST_VERSION = "1.0.0"
PREDICTION_SNAPSHOT_VERSION = "1.0.0"
DEFAULT_SLATE_SIZE = 5


class RecommendationReleaseError(ValueError):
    """Raised when a recommendation package is not eligible for release."""


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


def _check(check_id: str, failures: Iterable[str]) -> dict[str, Any]:
    reasons = list(failures)
    return {"id": check_id, "passed": not reasons, "failures": reasons}


def evaluate_recommendation_release(
    ranking: dict[str, Any],
    balanced: dict[str, Any],
    *,
    expected_slate_size: int = DEFAULT_SLATE_SIZE,
) -> dict[str, Any]:
    """Evaluate the fail-closed eligibility contract for a frozen recommendation release."""
    if expected_slate_size < 1:
        raise ValueError("expected_slate_size must be positive")

    checks: list[dict[str, Any]] = []

    version_failures: list[str] = []
    required_ranking_versions = (
        "version",
        "model_version",
        "taste_model_version",
        "corpus_version",
        "registry_version",
    )
    for field in required_ranking_versions:
        if not str(ranking.get(field, "")).strip():
            version_failures.append(f"ranking.{field} is required")
    version_pairs = (
        ("source_ranking_version", "version"),
        ("model_version", "model_version"),
        ("taste_model_version", "taste_model_version"),
        ("corpus_version", "corpus_version"),
    )
    for balanced_field, ranking_field in version_pairs:
        if balanced.get(balanced_field) != ranking.get(ranking_field):
            version_failures.append(
                f"balanced.{balanced_field} must match ranking.{ranking_field}"
            )
    if not str(balanced.get("version", "")).strip():
        version_failures.append("balanced.version is required")
    checks.append(_check("version_traceability", version_failures))

    accounting_failures: list[str] = []
    count_fields = (
        "candidate_count",
        "watched_excluded_count",
        "eligible_count",
        "recommended_count",
        "abstained_count",
    )
    for field in count_fields:
        value = ranking.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            accounting_failures.append(f"ranking.{field} must be a non-negative integer")
    if not accounting_failures:
        if ranking["candidate_count"] != (
            ranking["watched_excluded_count"] + ranking["eligible_count"]
        ):
            accounting_failures.append("candidate accounting does not reconcile")
        if ranking["eligible_count"] != (
            ranking["recommended_count"] + ranking["abstained_count"]
        ):
            accounting_failures.append("eligible accounting does not reconcile")
        if len(ranking.get("recommendations", [])) != ranking["recommended_count"]:
            accounting_failures.append("recommended_count does not match recommendations")
        if len(ranking.get("abstentions", [])) != ranking["abstained_count"]:
            accounting_failures.append("abstained_count does not match abstentions")
        if len(ranking.get("watched_exclusions", [])) != ranking["watched_excluded_count"]:
            accounting_failures.append(
                "watched_excluded_count does not match watched_exclusions"
            )
    checks.append(_check("candidate_accounting", accounting_failures))

    recommendations = ranking.get("recommendations")
    rank_failures: list[str] = []
    if not isinstance(recommendations, list):
        recommendations = []
        rank_failures.append("ranking.recommendations must be a list")
    recommendation_ranks = [item.get("recommendation_rank") for item in recommendations]
    if recommendation_ranks != list(range(1, len(recommendations) + 1)):
        rank_failures.append("recommendation ranks must be unique and contiguous")
    recommendation_keys = [item.get("film_key") for item in recommendations]
    if any(not isinstance(key, str) or not key for key in recommendation_keys):
        rank_failures.append("every recommendation requires a film_key")
    if len(recommendation_keys) != len(set(recommendation_keys)):
        rank_failures.append("recommendation film_keys must be unique")
    checks.append(_check("ranking_integrity", rank_failures))

    slate = balanced.get("balanced_slate")
    slate_failures: list[str] = []
    if not isinstance(slate, list):
        slate = []
        slate_failures.append("balanced.balanced_slate must be a list")
    if balanced.get("raw_recommendations") != recommendations:
        slate_failures.append("balanced artifact must preserve raw recommendations exactly")
    if len(slate) != expected_slate_size:
        slate_failures.append(
            f"balanced slate must contain exactly {expected_slate_size} predictions"
        )
    slate_ranks = [item.get("slate_rank") for item in slate]
    if slate_ranks != list(range(1, len(slate) + 1)):
        slate_failures.append("slate ranks must be unique and contiguous")
    slate_keys = [item.get("film_key") for item in slate]
    if len(slate_keys) != len(set(slate_keys)):
        slate_failures.append("balanced slate film_keys must be unique")
    if not set(slate_keys).issubset(set(recommendation_keys)):
        slate_failures.append("balanced slate must be a subset of raw recommendations")
    if balanced.get("abstentions") != ranking.get("abstentions"):
        slate_failures.append("balanced artifact must preserve abstentions exactly")
    if balanced.get("watched_exclusions") != ranking.get("watched_exclusions"):
        slate_failures.append("balanced artifact must preserve watched exclusions exactly")
    checks.append(_check("slate_integrity", slate_failures))

    watched_failures: list[str] = []
    watched = ranking.get("watched_exclusions")
    if not isinstance(watched, list):
        watched = []
        watched_failures.append("ranking.watched_exclusions must be a list")
    watched_keys = {item.get("film_key") for item in watched if isinstance(item, dict)}
    overlap = watched_keys & (set(recommendation_keys) | set(slate_keys))
    if overlap:
        watched_failures.append(
            "watched films entered the recommendation release: " + ", ".join(sorted(overlap))
        )
    checks.append(_check("watched_exclusion", watched_failures))

    prediction_failures: list[str] = []
    for index, prediction in enumerate(slate, start=1):
        prefix = f"balanced_slate[{index - 1}]"
        if not isinstance(prediction, dict):
            prediction_failures.append(f"{prefix} must be an object")
            continue
        if not str(prediction.get("title", "")).strip():
            prediction_failures.append(f"{prefix}.title is required")
        if prediction.get("decision") != "recommend":
            prediction_failures.append(f"{prefix}.decision must be recommend")
        if prediction.get("abstention_reasons") not in ([], None):
            prediction_failures.append(f"{prefix} contains abstention reasons")
        score = prediction.get("taste_score")
        if not _is_number(score) or not -1 <= float(score) <= 1:
            prediction_failures.append(f"{prefix}.taste_score must be between -1 and 1")
        confidence = prediction.get("confidence")
        if not _is_number(confidence) or not 0 <= float(confidence) <= 1:
            prediction_failures.append(f"{prefix}.confidence must be between 0 and 1")
        coverage = prediction.get("trait_coverage")
        if not _is_number(coverage) or not 0.5 <= float(coverage) <= 1:
            prediction_failures.append(f"{prefix}.trait_coverage must be between 0.5 and 1")
        active_traits = prediction.get("active_trait_count")
        if not isinstance(active_traits, int) or isinstance(active_traits, bool) or active_traits < 2:
            prediction_failures.append(f"{prefix}.active_trait_count must be at least 2")
        if not isinstance(prediction.get("top_matches"), list) or not prediction["top_matches"]:
            prediction_failures.append(f"{prefix}.top_matches must preserve positive drivers")
        if not isinstance(prediction.get("top_mismatches"), list):
            prediction_failures.append(f"{prefix}.top_mismatches must preserve negative drivers")
        if not isinstance(prediction.get("all_components"), list) or not prediction["all_components"]:
            prediction_failures.append(f"{prefix}.all_components must preserve score evidence")
        novelty = prediction.get("novelty_score")
        if not _is_number(novelty) or not 0 <= float(novelty) <= 1:
            prediction_failures.append(f"{prefix}.novelty_score must be between 0 and 1")
        if prediction.get("slate_role") not in {"core", "discovery"}:
            prediction_failures.append(f"{prefix}.slate_role must be core or discovery")
    checks.append(_check("prediction_quality", prediction_failures))

    metric_failures: list[str] = []
    metrics = balanced.get("slate_metrics")
    if not isinstance(metrics, dict):
        metric_failures.append("balanced.slate_metrics must be an object")
    else:
        ratio_fields = ("trait_diversity_ratio", "average_novelty")
        for field in ratio_fields:
            value = metrics.get(field)
            if not _is_number(value) or not 0 <= float(value) <= 1:
                metric_failures.append(f"slate_metrics.{field} must be between 0 and 1")
        for field in ("unique_trait_count", "trait_assignment_count", "discovery_count"):
            value = metrics.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                metric_failures.append(f"slate_metrics.{field} must be a non-negative integer")
        discovery_count = sum(1 for item in slate if item.get("slate_role") == "discovery")
        if metrics.get("discovery_count") != discovery_count:
            metric_failures.append("slate_metrics.discovery_count does not match slate roles")
    checks.append(_check("slate_metrics", metric_failures))

    failed = [check for check in checks if not check["passed"]]
    return {
        "version": RELEASE_GATE_VERSION,
        "eligible": not failed,
        "expected_slate_size": expected_slate_size,
        "checks": checks,
        "failure_count": sum(len(check["failures"]) for check in failed),
    }


def _require_eligible(gates: dict[str, Any]) -> None:
    if gates["eligible"]:
        return
    failures = [
        f"{check['id']}: {reason}"
        for check in gates["checks"]
        for reason in check["failures"]
    ]
    raise RecommendationReleaseError(
        "recommendation release is not eligible:\n- " + "\n- ".join(failures)
    )


def build_recommendation_release_package(
    ranking: dict[str, Any],
    balanced: dict[str, Any],
    *,
    generated_at: str,
    source_revision: str,
    expected_slate_size: int = DEFAULT_SLATE_SIZE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a manifest and immutable prediction snapshot from eligible frozen inputs."""
    if not generated_at.strip():
        raise ValueError("generated_at is required")
    if not source_revision.strip():
        raise ValueError("source_revision is required")

    gates = evaluate_recommendation_release(
        ranking,
        balanced,
        expected_slate_size=expected_slate_size,
    )
    _require_eligible(gates)

    ranking_sha256 = _digest(ranking)
    balanced_sha256 = _digest(balanced)
    release_fingerprint = _digest(
        {
            "contract_version": RELEASE_GATE_VERSION,
            "ranking_sha256": ranking_sha256,
            "balanced_sha256": balanced_sha256,
        }
    )
    release_id = f"recommendation-{release_fingerprint[:20]}"

    snapshot = {
        "version": PREDICTION_SNAPSHOT_VERSION,
        "snapshot_type": "frozen_recommendation_prediction",
        "release_id": release_id,
        "source_revision": source_revision,
        "versions": {
            "ranking": ranking["version"],
            "model": ranking["model_version"],
            "taste_model": ranking["taste_model_version"],
            "corpus": ranking["corpus_version"],
            "registry": ranking["registry_version"],
            "balanced_slate": balanced["version"],
        },
        "input_sha256": {
            "ranking": ranking_sha256,
            "balanced_slate": balanced_sha256,
        },
        "raw_recommendations": balanced["raw_recommendations"],
        "balanced_slate": balanced["balanced_slate"],
        "slate_metrics": balanced["slate_metrics"],
        "abstentions": balanced["abstentions"],
        "watched_exclusions": balanced["watched_exclusions"],
    }
    snapshot_sha256 = _digest(snapshot)

    manifest = {
        "version": MANIFEST_VERSION,
        "manifest_type": "recommendation_release",
        "release_id": release_id,
        "status": "eligible_for_private_evaluation",
        "generated_at": generated_at,
        "source_revision": source_revision,
        "prediction_snapshot_sha256": snapshot_sha256,
        "input_sha256": snapshot["input_sha256"],
        "counts": {
            "candidates": ranking["candidate_count"],
            "watched_excluded": ranking["watched_excluded_count"],
            "eligible": ranking["eligible_count"],
            "recommended": ranking["recommended_count"],
            "abstained": ranking["abstained_count"],
            "released_predictions": len(balanced["balanced_slate"]),
        },
        "release_gates": gates,
        "immutability": {
            "prediction_frozen_before_outcome": True,
            "outcomes_must_reference_release_id": True,
            "snapshot_must_not_be_rewritten": True,
        },
    }
    return manifest, snapshot


def verify_recommendation_release_package(
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
) -> None:
    """Verify manifest identity and detect any post-release snapshot mutation."""
    if manifest.get("release_id") != snapshot.get("release_id"):
        raise RecommendationReleaseError("manifest and snapshot release_id differ")
    if manifest.get("prediction_snapshot_sha256") != _digest(snapshot):
        raise RecommendationReleaseError("prediction snapshot digest mismatch")
    if manifest.get("status") != "eligible_for_private_evaluation":
        raise RecommendationReleaseError("manifest is not eligible for private evaluation")
    if not manifest.get("release_gates", {}).get("eligible"):
        raise RecommendationReleaseError("manifest release gates are not eligible")


def write_recommendation_release_package(
    ranking_path: Path,
    balanced_path: Path,
    output_dir: Path,
    *,
    generated_at: str,
    source_revision: str,
    expected_slate_size: int = DEFAULT_SLATE_SIZE,
) -> tuple[Path, Path]:
    """Write a release once; exclusive creation prevents silent snapshot replacement."""
    ranking = json.loads(ranking_path.read_text(encoding="utf-8"))
    balanced = json.loads(balanced_path.read_text(encoding="utf-8"))
    manifest, snapshot = build_recommendation_release_package(
        ranking,
        balanced,
        generated_at=generated_at,
        source_revision=source_revision,
        expected_slate_size=expected_slate_size,
    )
    verify_recommendation_release_package(manifest, snapshot)

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "recommendation_release_manifest_v1.json"
    snapshot_path = output_dir / "recommendation_prediction_snapshot_v1.json"
    if manifest_path.exists() or snapshot_path.exists():
        raise FileExistsError("recommendation release package already exists")
    with snapshot_path.open("x", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return manifest_path, snapshot_path
