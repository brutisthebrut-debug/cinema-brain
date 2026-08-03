from __future__ import annotations

import copy
from typing import Any

from .canonical_taste_scoring import score_canonical_films
from .personal_taste_graph import _signal_strength, build_personal_taste_graph

VALIDATION_VERSION = "leave-one-film-out-1.0.0"


def apply_explicit_preferences(
    graph: dict[str, Any],
    explicit_preferences: dict[str, Any] | None,
) -> dict[str, Any]:
    result = copy.deepcopy(graph)
    if not explicit_preferences:
        return result

    for preference in explicit_preferences.get("preferences", []):
        trait_id = preference["trait_id"]
        existing = result.setdefault("traits", {}).get(trait_id)
        explicit_affinity = float(preference["affinity"])
        explicit_confidence = float(preference["confidence"])

        if existing:
            learned_weight = max(float(existing.get("confidence", 0.0)), 0.01)
            explicit_weight = max(explicit_confidence, 0.01)
            combined = (
                float(existing.get("affinity", 0.0)) * learned_weight
                + explicit_affinity * explicit_weight
            ) / (learned_weight + explicit_weight)
            existing["affinity"] = round(combined, 4)
            existing["confidence"] = round(max(learned_weight, explicit_confidence), 3)
            existing["explicit_preference"] = preference
            existing["status"] = "explicitly_confirmed"
        else:
            result["traits"][trait_id] = {
                "affinity": round(explicit_affinity, 4),
                "confidence": round(explicit_confidence, 3),
                "evidence_count": 0,
                "positive_evidence_count": 0,
                "negative_evidence_count": 0,
                "conflict": False,
                "supporting_films": [],
                "contradicting_films": [],
                "status": "explicitly_confirmed",
                "explicit_preference": preference,
            }

    result["explicit_preference_version"] = explicit_preferences.get("version")
    result["learned_trait_count"] = len(result.get("traits", {}))
    return result


def leave_one_film_out_validation(
    reviewed_profiles: dict[str, Any],
    signals: list[dict[str, Any]],
    explicit_preferences: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signal_by_film = {signal["film_key"]: signal for signal in signals}
    folds: list[dict[str, Any]] = []

    for held_out in reviewed_profiles.get("films", []):
        held_key = held_out["film_key"]
        held_signal = signal_by_film.get(held_key)
        if not held_signal:
            continue

        training_signals = [signal for signal in signals if signal["film_key"] != held_key]
        graph = build_personal_taste_graph(reviewed_profiles, training_signals)
        graph = apply_explicit_preferences(graph, explicit_preferences)
        ranking = score_canonical_films(reviewed_profiles, graph)
        predicted = next(film for film in ranking["films"] if film["film_key"] == held_key)
        actual_strength = _signal_strength(held_signal)

        folds.append({
            "film_key": held_key,
            "title": held_out["title"],
            "actual_signal_strength": round(actual_strength, 6),
            "predicted_taste_score": predicted["taste_score"],
            "predicted_rank": predicted["rank"],
            "confidence": predicted["confidence"],
            "trait_coverage": predicted["trait_coverage"],
            "direction_correct": (
                predicted["taste_score"] >= 0 and actual_strength >= 0
            ) or (
                predicted["taste_score"] < 0 and actual_strength < 0
            ),
            "top_matches": predicted["top_matches"],
            "top_mismatches": predicted["top_mismatches"],
        })

    direction_accuracy = (
        sum(1 for fold in folds if fold["direction_correct"]) / len(folds)
        if folds else 0.0
    )
    mean_absolute_error = (
        sum(abs(fold["predicted_taste_score"] - fold["actual_signal_strength"]) for fold in folds)
        / len(folds)
        if folds else 0.0
    )

    return {
        "version": "0.2.2",
        "validation_model_version": VALIDATION_VERSION,
        "fold_count": len(folds),
        "direction_accuracy": round(direction_accuracy, 6),
        "mean_absolute_error": round(mean_absolute_error, 6),
        "folds": folds,
    }
