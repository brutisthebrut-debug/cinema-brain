from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


class RecommendationCorpusError(ValueError):
    """Raised when a recommendation corpus violates its production contract."""


def validate_recommendation_corpus(
    payload: dict[str, Any],
    *,
    known_trait_ids: set[str],
    watched_film_keys: Iterable[str] = (),
) -> list[str]:
    errors: list[str] = []
    watched = set(watched_film_keys)

    if not str(payload.get("version", "")).strip():
        errors.append("version is required")
    if not str(payload.get("registry_version", "")).strip():
        errors.append("registry_version is required")

    films = payload.get("films")
    if not isinstance(films, list) or not films:
        return errors + ["films must be a non-empty list"]

    keys: list[str] = []
    identities: list[tuple[str, int]] = []
    for index, film in enumerate(films):
        prefix = f"films[{index}]"
        if not isinstance(film, dict):
            errors.append(f"{prefix} must be an object")
            continue

        film_key = str(film.get("film_key", "")).strip()
        title = str(film.get("title", "")).strip()
        year = film.get("year")
        if not film_key:
            errors.append(f"{prefix}.film_key is required")
        else:
            keys.append(film_key)
            if film_key in watched:
                errors.append(f"{film_key}: watched films cannot enter the recommendation corpus")
        if not title:
            errors.append(f"{prefix}.title is required")
        if not isinstance(year, int):
            errors.append(f"{prefix}.year must be an integer")
        elif title:
            identities.append((title.casefold(), year))

        traits = film.get("traits")
        if not isinstance(traits, list) or len(traits) < 3:
            errors.append(f"{prefix}.traits must contain at least 3 assignments")
            continue
        seen_traits: set[str] = set()
        for trait_index, trait in enumerate(traits):
            tprefix = f"{prefix}.traits[{trait_index}]"
            trait_id = str(trait.get("trait_id", ""))
            if trait_id not in known_trait_ids:
                errors.append(f"{tprefix}.trait_id is unknown: {trait_id}")
            if trait_id in seen_traits:
                errors.append(f"{prefix} repeats trait: {trait_id}")
            seen_traits.add(trait_id)
            for field in ("value", "confidence"):
                value = trait.get(field)
                if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                    errors.append(f"{tprefix}.{field} must be between 0 and 1")
            if not str(trait.get("rationale", "")).strip():
                errors.append(f"{tprefix}.rationale is required")

    for key, count in Counter(keys).items():
        if count > 1:
            errors.append(f"duplicate film_key: {key}")
    for identity, count in Counter(identities).items():
        if count > 1:
            errors.append(f"duplicate title/year identity: {identity[0]} ({identity[1]})")
    return errors


def corpus_report(payload: dict[str, Any]) -> dict[str, Any]:
    films = payload.get("films", [])
    assignments = [trait for film in films for trait in film.get("traits", [])]
    counts = Counter(trait["trait_id"] for trait in assignments)
    return {
        "version": payload.get("version"),
        "registry_version": payload.get("registry_version"),
        "film_count": len(films),
        "assignment_count": len(assignments),
        "unique_trait_count": len(counts),
        "trait_counts": dict(sorted(counts.items())),
        "minimum_traits_per_film": min((len(film.get("traits", [])) for film in films), default=0),
    }


def load_recommendation_corpus(
    corpus_path: Path,
    *,
    known_trait_ids: set[str],
    watched_film_keys: Iterable[str] = (),
) -> dict[str, Any]:
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    errors = validate_recommendation_corpus(
        payload,
        known_trait_ids=known_trait_ids,
        watched_film_keys=watched_film_keys,
    )
    if errors:
        raise RecommendationCorpusError("invalid recommendation corpus:\n- " + "\n- ".join(errors))
    return payload
