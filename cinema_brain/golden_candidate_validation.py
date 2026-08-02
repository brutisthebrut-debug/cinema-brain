from __future__ import annotations

import json
from pathlib import Path

from .golden_dataset import load_golden_dataset
from .golden_promotion import load_review_packet


def validate_candidate(source: Path, candidate: Path, decisions: Path) -> dict:
    source_version, source_records = load_golden_dataset(source)
    candidate_payload = json.loads(Path(candidate).read_text(encoding="utf-8"))
    candidate_version, candidate_records = load_golden_dataset(candidate)
    packet_version, review_decisions = load_review_packet(decisions)

    errors: list[str] = []
    warnings: list[str] = []
    if candidate_version == source_version:
        errors.append("candidate version must change")
    if candidate_payload.get("previous_version") != source_version:
        errors.append("candidate lineage does not match source version")
    if packet_version != source_version:
        errors.append("decision packet targets the wrong benchmark version")

    before = {item.film_key: item for item in source_records}
    after = {item.film_key: item for item in candidate_records}
    decisions_by_key = {item.film_key: item for item in review_decisions}

    if set(before) != set(after):
        errors.append("candidate must preserve the exact benchmark record set")

    promoted: list[str] = []
    for film_key in sorted(set(before) & set(after)):
        old = before[film_key]
        new = after[film_key]
        if (
            old.canonical_title != new.canonical_title
            or old.release_year != new.release_year
            or old.accepted_titles != new.accepted_titles
            or old.entity_type != new.entity_type
            or old.hazards != new.hazards
            or old.expected_traits != new.expected_traits
        ):
            errors.append(f"non-review benchmark data changed for {film_key}")
        if old.reviewed and not new.reviewed:
            errors.append(f"reviewed record regressed for {film_key}")
        if not old.reviewed and new.reviewed:
            decision = decisions_by_key.get(film_key)
            if decision is None:
                errors.append(f"missing decision for promoted record {film_key}")
            elif decision.status != "approved" or decision.identity_status != "exact":
                errors.append(f"invalid decision for promoted record {film_key}")
            elif decision.expected_title != old.canonical_title or decision.expected_year != old.release_year:
                errors.append(f"decision identity drift for {film_key}")
            elif decision.provider_year != old.release_year:
                errors.append(f"provider year mismatch for {film_key}")
            elif decision.provider_title not in {old.canonical_title, *old.accepted_titles}:
                errors.append(f"provider title mismatch for {film_key}")
            else:
                promoted.append(film_key)

    approved = {item.film_key for item in review_decisions if item.status == "approved"}
    unused = sorted(approved - set(promoted))
    if unused:
        warnings.append("unused approved decisions: " + ", ".join(unused))
    if not promoted:
        errors.append("candidate contains no newly reviewed records")

    return {
        "source_version": source_version,
        "candidate_version": candidate_version,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "promoted": promoted,
        "promoted_count": len(promoted),
    }


def write_validation_report(report: dict, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output
