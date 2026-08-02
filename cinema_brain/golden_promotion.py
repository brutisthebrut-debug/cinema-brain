from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

from .golden_dataset import GoldenRecord, load_golden_dataset
from .golden_review import GoldenReviewDecision


def load_review_packet(path: Path) -> tuple[str, tuple[GoldenReviewDecision, ...]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    benchmark_version = str(payload.get("benchmark_version", "")).strip()
    if not benchmark_version:
        raise ValueError("review packet benchmark_version is required")
    raw = payload.get("decisions")
    if not isinstance(raw, list) or not raw:
        raise ValueError("review packet decisions must be a non-empty list")

    decisions: list[GoldenReviewDecision] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"decision {index} must be an object")
        decision = GoldenReviewDecision(**item)
        decision.validate()
        if decision.film_key in seen:
            raise ValueError(f"duplicate review decision: {decision.film_key}")
        seen.add(decision.film_key)
        decisions.append(decision)
    return benchmark_version, tuple(decisions)


def promote_records(
    records: tuple[GoldenRecord, ...],
    decisions: tuple[GoldenReviewDecision, ...],
) -> tuple[tuple[GoldenRecord, ...], dict]:
    by_key = {record.film_key: record for record in records}
    promoted: list[str] = []
    skipped: dict[str, str] = {}

    for decision in decisions:
        decision.validate()
        record = by_key.get(decision.film_key)
        if record is None:
            raise ValueError(f"review decision references unknown film_key: {decision.film_key}")
        if decision.expected_title != record.canonical_title or decision.expected_year != record.release_year:
            raise ValueError(f"review decision expected identity drifted for {decision.film_key}")
        if decision.status != "approved":
            skipped[decision.film_key] = decision.status
            continue
        if decision.identity_status != "exact":
            raise ValueError(f"approved decision is not exact for {decision.film_key}")
        if decision.provider_title != record.canonical_title and decision.provider_title not in record.accepted_titles:
            raise ValueError(f"approved provider title is not accepted for {decision.film_key}")
        if decision.provider_year != record.release_year:
            raise ValueError(f"approved provider year mismatch for {decision.film_key}")
        if not record.reviewed:
            by_key[decision.film_key] = replace(record, reviewed=True)
            promoted.append(decision.film_key)

    ordered = tuple(by_key[record.film_key] for record in records)
    return ordered, {
        "promoted": len(promoted),
        "promoted_keys": promoted,
        "skipped": skipped,
        "reviewed_total": sum(1 for record in ordered if record.reviewed),
    }


def write_promoted_dataset(
    source_path: Path,
    review_packet_path: Path,
    output_path: Path,
    *,
    next_version: str,
) -> dict:
    current_version, records = load_golden_dataset(source_path)
    packet_version, decisions = load_review_packet(review_packet_path)
    if packet_version != current_version:
        raise ValueError(
            f"review packet targets {packet_version}, but dataset is {current_version}"
        )
    if not next_version.strip() or next_version == current_version:
        raise ValueError("next_version must be non-empty and different from current version")

    promoted_records, summary = promote_records(records, decisions)
    if summary["promoted"] == 0:
        raise ValueError("promotion produced no newly reviewed records")

    payload = {
        "version": next_version,
        "previous_version": current_version,
        "records": [asdict(record) for record in promoted_records],
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "previous_version": current_version,
        "version": next_version,
        **summary,
        "output": str(output_path),
    }
