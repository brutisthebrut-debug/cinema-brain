from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .trait_registry import CanonicalTraitRegistry, load_trait_registry

ALLOWED_STATUSES = {"candidate_review", "reviewed", "rejected", "deprecated"}
ALLOWED_SOURCES = {"human_authored", "provider_evidence", "model_candidate", "daniel_reaction"}


class CanonicalProfileError(ValueError):
    """Raised when canonical film profiles violate their contract."""


@dataclass(frozen=True)
class TraitAssignment:
    trait_id: str
    value: float
    confidence: float
    source: str
    rationale: str


@dataclass(frozen=True)
class CanonicalFilmProfile:
    film_key: str
    title: str
    year: int
    status: str
    profile_version: str
    registry_version: str
    assignments: tuple[TraitAssignment, ...]


def load_profiles(path: Path, registry_path: Path) -> tuple[CanonicalFilmProfile, ...]:
    registry = load_trait_registry(registry_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_profiles(raw, registry)
    if errors:
        raise CanonicalProfileError("invalid canonical profiles:\n- " + "\n- ".join(errors))
    return tuple(_profile_from_dict(item, str(raw["version"]), registry.version) for item in raw["films"])


def _profile_from_dict(raw: dict[str, Any], version: str, registry_version: str) -> CanonicalFilmProfile:
    return CanonicalFilmProfile(
        film_key=str(raw["film_key"]),
        title=str(raw["title"]),
        year=int(raw["year"]),
        status=str(raw["status"]),
        profile_version=version,
        registry_version=registry_version,
        assignments=tuple(
            TraitAssignment(
                trait_id=str(item["trait_id"]),
                value=float(item["value"]),
                confidence=float(item["confidence"]),
                source=str(item["source"]),
                rationale=str(item["rationale"]),
            )
            for item in raw["traits"]
        ),
    )


def validate_profiles(raw: dict[str, Any], registry: CanonicalTraitRegistry) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["profile root must be an object"]
    if not str(raw.get("version", "")).strip():
        errors.append("version is required")
    if raw.get("registry_version") != registry.version:
        errors.append(f"registry_version must equal {registry.version}")
    films = raw.get("films")
    if not isinstance(films, list) or not films:
        errors.append("films must be a non-empty list")
        return errors

    film_keys: set[str] = set()
    known_traits = {trait.trait_id for trait in registry.traits}
    for index, film in enumerate(films):
        prefix = f"films[{index}]"
        if not isinstance(film, dict):
            errors.append(f"{prefix} must be an object")
            continue
        film_key = str(film.get("film_key", ""))
        if not film_key:
            errors.append(f"{prefix}.film_key is required")
        if film_key in film_keys:
            errors.append(f"duplicate film_key: {film_key}")
        film_keys.add(film_key)
        if not str(film.get("title", "")).strip():
            errors.append(f"{prefix}.title is required")
        if not isinstance(film.get("year"), int):
            errors.append(f"{prefix}.year must be an integer")
        if film.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(ALLOWED_STATUSES)}")
        traits = film.get("traits")
        if not isinstance(traits, list) or not traits:
            errors.append(f"{prefix}.traits must be a non-empty list")
            continue
        seen_traits: set[str] = set()
        for trait_index, assignment in enumerate(traits):
            aprefix = f"{prefix}.traits[{trait_index}]"
            trait_id = str(assignment.get("trait_id", ""))
            if trait_id not in known_traits:
                errors.append(f"{aprefix}.trait_id is unknown: {trait_id}")
            if trait_id in seen_traits:
                errors.append(f"{prefix} repeats trait: {trait_id}")
            seen_traits.add(trait_id)
            for field in ("value", "confidence"):
                value = assignment.get(field)
                if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                    errors.append(f"{aprefix}.{field} must be between 0 and 1")
            if assignment.get("source") not in ALLOWED_SOURCES:
                errors.append(f"{aprefix}.source must be one of {sorted(ALLOWED_SOURCES)}")
            if not str(assignment.get("rationale", "")).strip():
                errors.append(f"{aprefix}.rationale is required")
    return errors


def profile_report(profiles_path: Path, registry_path: Path) -> dict[str, Any]:
    profiles = load_profiles(profiles_path, registry_path)
    return {
        "valid": True,
        "profile_version": profiles[0].profile_version,
        "registry_version": profiles[0].registry_version,
        "film_count": len(profiles),
        "reviewed_count": sum(profile.status == "reviewed" for profile in profiles),
        "candidate_count": sum(profile.status == "candidate_review" for profile in profiles),
        "assignment_count": sum(len(profile.assignments) for profile in profiles),
    }
