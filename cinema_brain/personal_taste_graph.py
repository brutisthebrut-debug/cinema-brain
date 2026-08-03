from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

MODEL_VERSION = "personal-taste-graph-1.0.0"


def _signal_strength(signal: dict[str, Any]) -> float:
    rating = signal.get("rating")
    rating_component = 0.0 if rating is None else (float(rating) - 2.75) / 2.25
    liked_component = 0.25 if signal.get("liked") else 0.0
    rewatches = max(int(signal.get("watch_count", 1)) - 1, 0)
    rewatch_component = min(rewatches, 4) * 0.12
    explicit = float(signal.get("explicit_sentiment", 0.0))
    return max(-1.5, min(1.5, rating_component + liked_component + rewatch_component + explicit))


def _confidence(evidence_count: int, diversity: int, agreement: float) -> float:
    if evidence_count == 0:
        return 0.0
    volume = 1 - math.exp(-evidence_count / 4)
    diversity_term = min(diversity / 3, 1.0)
    return round(min(0.95, 0.15 + 0.35 * volume + 0.25 * diversity_term + 0.2 * agreement), 3)


def build_personal_taste_graph(
    reviewed_profiles: dict[str, Any],
    signals: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    films = {film["film_key"]: film for film in reviewed_profiles["films"]}
    contributions: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for signal in signals:
        film = films.get(signal["film_key"])
        if not film:
            continue
        strength = _signal_strength(signal)
        source_types = sorted(set(signal.get("source_types", ["rating"])))
        for trait in film["traits"]:
            contribution = strength * float(trait["value"]) * float(trait["confidence"])
            contributions[trait["trait_id"]].append({
                "film_key": film["film_key"],
                "film": film["title"],
                "year": film["year"],
                "contribution": round(contribution, 4),
                "signal_strength": round(strength, 4),
                "trait_value": trait["value"],
                "trait_confidence": trait["confidence"],
                "source_types": source_types,
            })

    traits: dict[str, Any] = {}
    for trait_id, items in sorted(contributions.items()):
        positive = [x for x in items if x["contribution"] > 0]
        negative = [x for x in items if x["contribution"] < 0]
        total = sum(x["contribution"] for x in items)
        absolute = sum(abs(x["contribution"]) for x in items) or 1.0
        agreement = abs(total) / absolute
        diversity = len({source for x in items for source in x["source_types"]})
        traits[trait_id] = {
            "affinity": round(total / max(len(items), 1), 4),
            "confidence": _confidence(len(items), diversity, agreement),
            "evidence_count": len(items),
            "positive_evidence_count": len(positive),
            "negative_evidence_count": len(negative),
            "conflict": bool(positive and negative),
            "supporting_films": sorted(positive, key=lambda x: x["contribution"], reverse=True)[:5],
            "contradicting_films": sorted(negative, key=lambda x: x["contribution"])[:5],
            "status": "learned" if len(items) >= 2 else "provisional",
        }

    return {
        "version": "0.2.0",
        "model_version": MODEL_VERSION,
        "profile_version": reviewed_profiles["version"],
        "registry_version": reviewed_profiles["registry_version"],
        "signal_count": sum(1 for signal in signals if signal.get("film_key") in films),
        "learned_trait_count": len(traits),
        "traits": traits,
    }


def build_personal_taste_graph_file(
    profiles_path: Path,
    signals_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    signals = json.loads(signals_path.read_text(encoding="utf-8"))
    graph = build_personal_taste_graph(profiles, signals["signals"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    return graph
