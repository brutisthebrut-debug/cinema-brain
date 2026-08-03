from __future__ import annotations

from collections import Counter
from typing import Any

DEFAULT_SLATE_SIZE = 5
DEFAULT_RELEVANCE_WEIGHT = 0.78
DEFAULT_DIVERSITY_WEIGHT = 0.22
DISCOVERY_CONFIDENCE_MAX = 0.45
DISCOVERY_SCORE_MIN = 0.65


def _trait_ids(film: dict[str, Any]) -> set[str]:
    traits = film.get("traits") or film.get("trait_scores") or []
    result: set[str] = set()
    for trait in traits:
        if isinstance(trait, str):
            result.add(trait)
        elif isinstance(trait, dict):
            trait_id = trait.get("trait_id") or trait.get("id")
            if trait_id:
                result.add(str(trait_id))
    if not result:
        for driver in film.get("drivers", []):
            if isinstance(driver, str):
                result.add(driver.casefold().replace(" ", "_"))
            elif isinstance(driver, dict) and driver.get("trait_id"):
                result.add(str(driver["trait_id"]))
    return result


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _novelty(candidate: dict[str, Any], selected: list[dict[str, Any]]) -> float:
    if not selected:
        return 1.0
    candidate_traits = _trait_ids(candidate)
    max_similarity = max(_jaccard(candidate_traits, _trait_ids(item)) for item in selected)
    return 1.0 - max_similarity


def build_diverse_slate(
    ranking: dict[str, Any],
    *,
    slate_size: int = DEFAULT_SLATE_SIZE,
    relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT,
    diversity_weight: float = DEFAULT_DIVERSITY_WEIGHT,
) -> dict[str, Any]:
    """Re-rank eligible recommendations into a relevance-preserving diverse slate."""
    candidates = [dict(item) for item in ranking.get("recommendations", [])]
    if slate_size < 1:
        raise ValueError("slate_size must be positive")
    if abs((relevance_weight + diversity_weight) - 1.0) > 1e-9:
        raise ValueError("relevance_weight and diversity_weight must sum to 1")

    raw = sorted(
        candidates,
        key=lambda item: (item.get("taste_score", 0.0), item.get("confidence", 0.0), item.get("title", "")),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    remaining = raw[:]

    while remaining and len(selected) < slate_size:
        best: dict[str, Any] | None = None
        best_value = float("-inf")
        for candidate in remaining:
            relevance = float(candidate.get("taste_score", 0.0))
            novelty = _novelty(candidate, selected)
            slate_value = relevance_weight * relevance + diversity_weight * novelty
            if slate_value > best_value:
                best = candidate
                best_value = slate_value
        assert best is not None
        remaining.remove(best)
        best["raw_rank"] = next(
            index for index, item in enumerate(raw, start=1) if item.get("film_key") == best.get("film_key")
        )
        best["slate_rank"] = len(selected) + 1
        best["novelty_score"] = round(_novelty(best, selected), 6)
        best["slate_score"] = round(best_value, 6)
        best["slate_role"] = "core"
        selected.append(best)

    discovery_candidates = [
        item for item in selected
        if float(item.get("confidence", 0.0)) <= DISCOVERY_CONFIDENCE_MAX
        and float(item.get("taste_score", 0.0)) >= DISCOVERY_SCORE_MIN
    ]
    if discovery_candidates:
        discovery = max(discovery_candidates, key=lambda item: (item["novelty_score"], item["taste_score"]))
        discovery["slate_role"] = "discovery"

    trait_counter: Counter[str] = Counter()
    for item in selected:
        trait_counter.update(_trait_ids(item))
    unique_traits = len(trait_counter)
    total_assignments = sum(trait_counter.values())
    diversity_ratio = unique_traits / total_assignments if total_assignments else 0.0

    return {
        "version": "0.3.0",
        "source_version": ranking.get("version"),
        "slate_size": len(selected),
        "relevance_weight": relevance_weight,
        "diversity_weight": diversity_weight,
        "raw_top": [
            {"film_key": item.get("film_key"), "title": item.get("title"), "raw_rank": index}
            for index, item in enumerate(raw[:slate_size], start=1)
        ],
        "slate": selected,
        "slate_metrics": {
            "unique_trait_count": unique_traits,
            "trait_assignment_count": total_assignments,
            "trait_diversity_ratio": round(diversity_ratio, 6),
            "discovery_count": sum(1 for item in selected if item["slate_role"] == "discovery"),
            "average_novelty": round(
                sum(float(item["novelty_score"]) for item in selected) / len(selected), 6
            ) if selected else 0.0,
        },
    }
