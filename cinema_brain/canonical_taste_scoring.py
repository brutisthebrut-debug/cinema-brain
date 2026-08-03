from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCORING_MODEL_VERSION = "canonical-taste-score-1.0.0"
MIN_ACTIVE_AFFINITY = 0.01


def score_canonical_films(
    reviewed_profiles: dict[str, Any],
    taste_graph: dict[str, Any],
) -> dict[str, Any]:
    taste_traits = taste_graph.get("traits", {})
    scored: list[dict[str, Any]] = []

    for film in reviewed_profiles.get("films", []):
        components: list[dict[str, Any]] = []
        for trait in film.get("traits", []):
            learned = taste_traits.get(trait["trait_id"])
            if not learned:
                continue
            affinity = float(learned.get("affinity", 0.0))
            confidence = float(learned.get("confidence", 0.0))
            if abs(affinity) < MIN_ACTIVE_AFFINITY:
                continue
            contribution = affinity * confidence * float(trait["value"]) * float(trait["confidence"])
            components.append({
                "trait_id": trait["trait_id"],
                "contribution": round(contribution, 6),
                "affinity": affinity,
                "taste_confidence": confidence,
                "film_trait_value": trait["value"],
                "film_trait_confidence": trait["confidence"],
                "taste_status": learned.get("status", "unknown"),
            })

        numerator = sum(item["contribution"] for item in components)
        denominator = sum(
            abs(item["affinity"] * item["taste_confidence"])
            for item in components
        ) or 1.0
        raw_score = numerator / denominator
        coverage = len(components) / max(len(film.get("traits", [])), 1)
        score_confidence = (
            sum(item["taste_confidence"] for item in components) / len(components)
            if components else 0.0
        ) * coverage

        positive = sorted(
            (item for item in components if item["contribution"] > 0),
            key=lambda item: item["contribution"],
            reverse=True,
        )
        negative = sorted(
            (item for item in components if item["contribution"] < 0),
            key=lambda item: item["contribution"],
        )
        scored.append({
            "film_key": film["film_key"],
            "title": film["title"],
            "year": film["year"],
            "taste_score": round(raw_score, 6),
            "confidence": round(score_confidence, 6),
            "active_trait_count": len(components),
            "trait_coverage": round(coverage, 6),
            "top_matches": positive[:5],
            "top_mismatches": negative[:5],
            "all_components": sorted(
                components,
                key=lambda item: abs(item["contribution"]),
                reverse=True,
            ),
        })

    ranked = sorted(
        scored,
        key=lambda item: (item["taste_score"], item["confidence"], item["title"]),
        reverse=True,
    )
    for rank, film in enumerate(ranked, start=1):
        film["rank"] = rank

    return {
        "version": "0.2.1",
        "model_version": SCORING_MODEL_VERSION,
        "taste_model_version": taste_graph.get("model_version"),
        "profile_version": reviewed_profiles.get("version"),
        "registry_version": reviewed_profiles.get("registry_version"),
        "film_count": len(ranked),
        "films": ranked,
    }


def score_canonical_films_file(
    profiles_path: Path,
    taste_graph_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    graph = json.loads(taste_graph_path.read_text(encoding="utf-8"))
    result = score_canonical_films(profiles, graph)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
