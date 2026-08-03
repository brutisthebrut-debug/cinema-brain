from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from cinema_brain.recommendation_release_gates import (
    RecommendationReleaseError,
    verify_recommendation_release_package,
)


AUDIT_VERSION = "1.0.0"


class RecommendationAuditError(ValueError):
    """Raised when a frozen recommendation release cannot be audited safely."""


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


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def _verify_release_links(manifest: dict[str, Any], snapshot: dict[str, Any]) -> None:
    """Verify links not covered by the snapshot digest before exposing audit results."""
    try:
        verify_recommendation_release_package(manifest, snapshot)
    except RecommendationReleaseError as error:
        raise RecommendationAuditError(str(error)) from error

    failures: list[str] = []
    if manifest.get("source_revision") != snapshot.get("source_revision"):
        failures.append("manifest and snapshot source_revision differ")
    if manifest.get("input_sha256") != snapshot.get("input_sha256"):
        failures.append("manifest and snapshot input_sha256 differ")

    input_digests = snapshot.get("input_sha256")
    gate_version = manifest.get("release_gates", {}).get("version")
    if not isinstance(input_digests, dict):
        failures.append("snapshot.input_sha256 must be an object")
    elif not gate_version:
        failures.append("manifest.release_gates.version is required")
    else:
        expected_release_id = "recommendation-" + _digest(
            {
                "contract_version": gate_version,
                "ranking_sha256": input_digests.get("ranking"),
                "balanced_sha256": input_digests.get("balanced_slate"),
            }
        )[:20]
        if manifest.get("release_id") != expected_release_id:
            failures.append("release_id does not match the frozen input digests")

    counts = manifest.get("counts")
    raw = snapshot.get("raw_recommendations")
    slate = snapshot.get("balanced_slate")
    abstentions = snapshot.get("abstentions")
    watched = snapshot.get("watched_exclusions")
    if not isinstance(counts, dict):
        failures.append("manifest.counts must be an object")
    elif not all(isinstance(records, list) for records in (raw, slate, abstentions, watched)):
        failures.append("snapshot recommendation collections must be lists")
    else:
        expected_counts = {
            "candidates": len(raw) + len(abstentions) + len(watched),
            "watched_excluded": len(watched),
            "eligible": len(raw) + len(abstentions),
            "recommended": len(raw),
            "abstained": len(abstentions),
            "released_predictions": len(slate),
        }
        for field, expected in expected_counts.items():
            if counts.get(field) != expected:
                failures.append(
                    f"manifest.counts.{field} is {counts.get(field)!r}; expected {expected}"
                )

    if failures:
        raise RecommendationAuditError(
            "recommendation release links are invalid:\n- " + "\n- ".join(failures)
        )


def _build_rank_movement(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    raw_by_key = {
        item["film_key"]: item
        for item in snapshot["raw_recommendations"]
        if isinstance(item, dict) and item.get("film_key")
    }
    movement: list[dict[str, Any]] = []
    failures: list[str] = []
    for prediction in snapshot["balanced_slate"]:
        key = prediction.get("film_key")
        raw = raw_by_key.get(key)
        if raw is None:
            failures.append(f"released film {key!r} is missing from raw recommendations")
            continue
        raw_rank = raw.get("recommendation_rank")
        slate_rank = prediction.get("slate_rank")
        recorded_raw_rank = prediction.get("raw_rank")
        if not isinstance(raw_rank, int) or not isinstance(slate_rank, int):
            failures.append(f"released film {key!r} has invalid raw or slate rank")
            continue
        if recorded_raw_rank != raw_rank:
            failures.append(
                f"released film {key!r} records raw_rank {recorded_raw_rank!r}; expected {raw_rank}"
            )
            continue
        delta = raw_rank - slate_rank
        movement.append(
            {
                "film_key": key,
                "title": prediction.get("title"),
                "raw_rank": raw_rank,
                "slate_rank": slate_rank,
                "rank_delta": delta,
                "movement": "promoted" if delta > 0 else "demoted" if delta < 0 else "unchanged",
                "slate_role": prediction.get("slate_role"),
                "taste_score": prediction.get("taste_score"),
                "confidence": prediction.get("confidence"),
                "novelty_score": prediction.get("novelty_score"),
                "slate_score": prediction.get("slate_score"),
            }
        )
    if failures:
        raise RecommendationAuditError(
            "rank movement cannot be audited:\n- " + "\n- ".join(failures)
        )
    return movement


def _build_abstention_audit(
    abstentions: list[dict[str, Any]],
    eligible_count: int,
) -> dict[str, Any]:
    reason_counts: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    for item in abstentions:
        reasons = item.get("abstention_reasons")
        if not isinstance(reasons, list) or not reasons:
            raise RecommendationAuditError(
                f"abstention {item.get('film_key')!r} has no auditable reasons"
            )
        reason_counts.update(str(reason) for reason in reasons)
        records.append(
            {
                "film_key": item.get("film_key"),
                "title": item.get("title"),
                "taste_score": item.get("taste_score"),
                "confidence": item.get("confidence"),
                "trait_coverage": item.get("trait_coverage"),
                "active_trait_count": item.get("active_trait_count"),
                "reasons": list(reasons),
            }
        )
    return {
        "count": len(records),
        "eligible_count": eligible_count,
        "rate": _ratio(len(records), eligible_count),
        "reason_counts": dict(sorted(reason_counts.items())),
        "records": records,
    }


def _build_evidence_coverage(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    trait_coverages: list[float] = []
    confidences: list[float] = []
    complete_count = 0
    for item in predictions:
        top_matches = item.get("top_matches")
        top_mismatches = item.get("top_mismatches")
        components = item.get("all_components")
        complete = (
            isinstance(top_matches, list)
            and bool(top_matches)
            and isinstance(top_mismatches, list)
            and isinstance(components, list)
            and bool(components)
        )
        complete_count += int(complete)
        coverage = item.get("trait_coverage")
        confidence = item.get("confidence")
        if isinstance(coverage, (int, float)) and not isinstance(coverage, bool):
            trait_coverages.append(float(coverage))
        if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
            confidences.append(float(confidence))
        records.append(
            {
                "film_key": item.get("film_key"),
                "title": item.get("title"),
                "trait_coverage": coverage,
                "active_trait_count": item.get("active_trait_count"),
                "positive_driver_count": len(top_matches) if isinstance(top_matches, list) else 0,
                "negative_driver_count": len(top_mismatches) if isinstance(top_mismatches, list) else 0,
                "score_component_count": len(components) if isinstance(components, list) else 0,
                "complete": complete,
            }
        )
    return {
        "released_prediction_count": len(predictions),
        "complete_prediction_count": complete_count,
        "complete_prediction_ratio": _ratio(complete_count, len(predictions)),
        "average_trait_coverage": _mean(trait_coverages),
        "average_confidence": _mean(confidences),
        "predictions": records,
    }


def build_recommendation_audit(
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic, read-only diagnostic view of a frozen release."""
    _verify_release_links(manifest, snapshot)
    rank_movement = _build_rank_movement(snapshot)
    counts = manifest["counts"]
    abstention_audit = _build_abstention_audit(
        snapshot["abstentions"],
        counts["eligible"],
    )
    evidence_coverage = _build_evidence_coverage(snapshot["balanced_slate"])
    checks = manifest["release_gates"]["checks"]
    passed = sum(1 for check in checks if check.get("passed"))
    snapshot_digest = manifest["prediction_snapshot_sha256"]
    audit_id = "recommendation-audit-" + _digest(
        {
            "audit_version": AUDIT_VERSION,
            "release_id": manifest["release_id"],
            "prediction_snapshot_sha256": snapshot_digest,
        }
    )[:20]

    return {
        "version": AUDIT_VERSION,
        "audit_type": "recommendation_release_audit",
        "audit_id": audit_id,
        "release_id": manifest["release_id"],
        "status": "verified_read_only",
        "source_revision": manifest["source_revision"],
        "input_integrity": {
            "verified": True,
            "prediction_snapshot_sha256": snapshot_digest,
            "input_sha256": manifest["input_sha256"],
            "prediction_frozen_before_outcome": manifest["immutability"][
                "prediction_frozen_before_outcome"
            ],
        },
        "gate_audit": {
            "eligible": manifest["release_gates"]["eligible"],
            "check_count": len(checks),
            "passed_check_count": passed,
            "failed_check_count": len(checks) - passed,
            "failure_count": manifest["release_gates"]["failure_count"],
            "checks": [
                {
                    "id": check.get("id"),
                    "passed": check.get("passed"),
                    "failure_count": len(check.get("failures", [])),
                    "failures": list(check.get("failures", [])),
                }
                for check in checks
            ],
        },
        "release_counts": dict(counts),
        "rank_movement": rank_movement,
        "abstention_audit": abstention_audit,
        "evidence_coverage": evidence_coverage,
        "slate_metrics": snapshot["slate_metrics"],
        "health_metrics": {
            "release_gate_pass_ratio": _ratio(passed, len(checks)),
            "prediction_snapshot_integrity": True,
            "frozen_release_awaiting_outcome": True,
            "abstention_rate": abstention_audit["rate"],
            "explanation_evidence_coverage": evidence_coverage[
                "complete_prediction_ratio"
            ],
            "trait_diversity_ratio": snapshot["slate_metrics"].get(
                "trait_diversity_ratio"
            ),
            "average_novelty": snapshot["slate_metrics"].get("average_novelty"),
        },
        "outcome_status": {
            "status": "awaiting_outcome",
            "release_id_required": True,
            "recommendation_trust": None,
            "prediction_error": None,
        },
    }


def write_recommendation_audit(
    manifest_path: Path,
    snapshot_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Write a deterministic audit once without changing either frozen release input."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    audit = build_recommendation_audit(manifest, snapshot)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return audit
