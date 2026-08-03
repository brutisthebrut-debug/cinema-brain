from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical_profiles import validate_profiles
from .trait_registry import load_trait_registry

DECISIONS = {"approve", "reject", "edit"}
REVIEW_FIELDS = [
    "film_key", "title", "year", "trait_id", "candidate_value",
    "candidate_confidence", "source", "rationale", "decision",
    "reviewed_value", "reviewed_confidence", "review_note",
]


class ProfileReviewError(ValueError):
    """Raised when a canonical profile review is incomplete or unsafe."""


def build_review_worksheet(profiles_path: Path, output_path: Path) -> dict[str, Any]:
    raw = json.loads(profiles_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for film in raw["films"]:
        for assignment in film["traits"]:
            rows.append({
                "film_key": film["film_key"],
                "title": film["title"],
                "year": film["year"],
                "trait_id": assignment["trait_id"],
                "candidate_value": assignment["value"],
                "candidate_confidence": assignment["confidence"],
                "source": assignment["source"],
                "rationale": assignment["rationale"],
                "decision": "",
                "reviewed_value": "",
                "reviewed_confidence": "",
                "review_note": "",
            })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {"film_count": len(raw["films"]), "assignment_count": len(rows), "output": str(output_path)}


def compile_review(
    profiles_path: Path,
    worksheet_path: Path,
    output_path: Path,
    *,
    reviewer: str,
) -> dict[str, Any]:
    if not reviewer.strip():
        raise ProfileReviewError("reviewer is required")
    source = json.loads(profiles_path.read_text(encoding="utf-8"))
    expected = {
        (film["film_key"], trait["trait_id"]): (film, trait)
        for film in source["films"]
        for trait in film["traits"]
    }
    seen: set[tuple[str, str]] = set()
    decisions: list[dict[str, Any]] = []
    with worksheet_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = set(REVIEW_FIELDS) - set(reader.fieldnames or [])
        if missing_columns:
            raise ProfileReviewError(f"worksheet missing columns: {sorted(missing_columns)}")
        for line, row in enumerate(reader, start=2):
            key = (row["film_key"].strip(), row["trait_id"].strip())
            if key not in expected:
                raise ProfileReviewError(f"line {line}: unknown film/trait pair {key}")
            if key in seen:
                raise ProfileReviewError(f"line {line}: duplicate film/trait pair {key}")
            seen.add(key)
            decision = row["decision"].strip().lower()
            if decision not in DECISIONS:
                raise ProfileReviewError(f"line {line}: decision must be approve, reject, or edit")
            film, candidate = expected[key]
            value = float(candidate["value"])
            confidence = float(candidate["confidence"])
            note = row["review_note"].strip()
            if decision == "edit":
                if row["reviewed_value"].strip() == "" or row["reviewed_confidence"].strip() == "":
                    raise ProfileReviewError(f"line {line}: edit requires reviewed value and confidence")
                value = float(row["reviewed_value"])
                confidence = float(row["reviewed_confidence"])
                if not 0 <= value <= 1 or not 0 <= confidence <= 1:
                    raise ProfileReviewError(f"line {line}: reviewed values must be between 0 and 1")
                if not note:
                    raise ProfileReviewError(f"line {line}: edit requires a review note")
            if decision == "reject" and not note:
                raise ProfileReviewError(f"line {line}: rejection requires a review note")
            decisions.append({
                "film_key": film["film_key"],
                "trait_id": candidate["trait_id"],
                "decision": decision,
                "value": value,
                "confidence": confidence,
                "review_note": note,
            })
    missing = sorted(set(expected) - seen)
    if missing:
        raise ProfileReviewError(f"worksheet is incomplete; missing {len(missing)} assignments")
    packet = {
        "schema_version": "1.0.0",
        "source_profile_version": source["version"],
        "registry_version": source["registry_version"],
        "reviewer": reviewer.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decisions": decisions,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "reviewer": packet["reviewer"],
        "decision_count": len(decisions),
        "approved": sum(x["decision"] == "approve" for x in decisions),
        "edited": sum(x["decision"] == "edit" for x in decisions),
        "rejected": sum(x["decision"] == "reject" for x in decisions),
    }


def promote_reviewed_profiles(
    profiles_path: Path,
    decisions_path: Path,
    registry_path: Path,
    output_path: Path,
    *,
    next_version: str,
) -> dict[str, Any]:
    source = json.loads(profiles_path.read_text(encoding="utf-8"))
    packet = json.loads(decisions_path.read_text(encoding="utf-8"))
    if packet["source_profile_version"] != source["version"]:
        raise ProfileReviewError("decision packet source version does not match profiles")
    decision_index = {(x["film_key"], x["trait_id"]): x for x in packet["decisions"]}
    promoted = deepcopy(source)
    promoted["version"] = next_version
    promoted["review"] = {"reviewer": packet["reviewer"], "reviewed_at": packet["reviewed_at"]}
    for film in promoted["films"]:
        kept: list[dict[str, Any]] = []
        for trait in film["traits"]:
            key = (film["film_key"], trait["trait_id"])
            if key not in decision_index:
                raise ProfileReviewError(f"missing decision for {key}")
            decision = decision_index[key]
            if decision["decision"] == "reject":
                continue
            trait["value"] = decision["value"]
            trait["confidence"] = decision["confidence"]
            trait["source"] = "human_authored"
            trait["review_note"] = decision["review_note"]
            kept.append(trait)
        if not kept:
            raise ProfileReviewError(f"review rejected every trait for {film['film_key']}")
        film["traits"] = kept
        film["status"] = "reviewed"
    registry = load_trait_registry(registry_path)
    errors = validate_profiles(promoted, registry)
    if errors:
        raise ProfileReviewError("promoted profiles are invalid:\n- " + "\n- ".join(errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(promoted, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "version": next_version,
        "film_count": len(promoted["films"]),
        "assignment_count": sum(len(x["traits"]) for x in promoted["films"]),
        "reviewer": packet["reviewer"],
    }
