from __future__ import annotations

import copy
from typing import Any

from .canonical_taste_scoring import score_canonical_films
from .personal_taste_graph import _signal_strength, build_personal_taste_graph

VALIDATION_VERSION = "leave-one-film-out-1.1.0"
NEUTRAL_SIGNAL_BAND = 0.15
MIN_PREDICTION_COVERAGE = 0.4
MIN_ACTIVE_TRAITS = 2


def _label(value: float) -> str:
    if value > NEUTRAL_SIGNAL_BAND:
        return "positive"
    if value < -NEUTRAL_SIGNAL_BAND:
        return "negative"
    return "neutral"


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
        actual_label = _label(actual_strength)
        predicted_label = _label(predicted["taste_score"])
        active_traits = int(predicted.get("active_trait_count", 0))
        coverage = float(predicted.get("trait_coverage", 0.0))
        eligible = active_traits >= MIN_ACTIVE_TRAITS and coverage >= MIN_PREDICTION_COVERAGE
        components = predicted.get("all_components", [])
        dominant_share = 0.0
        if components:
            total = sum(abs(float(item["contribution"])) for item in components) or 1.0
            dominant_share = max(abs(float(item["contribution"])) for item in components) / total

        folds.append({
            "film_key": held_key,
            "title": held_out["title"],
            "actual_signal_strength": round(actual_strength, 6),
            "actual_label": actual_label,
            "predicted_taste_score": predicted["taste_score"],
            "predicted_label": predicted_label,
            "predicted_rank": predicted["rank"],
            "confidence": predicted["confidence"],
            "active_trait_count": active_traits,
            "trait_coverage": predicted["trait_coverage"],
            "eligible_prediction": eligible,
            "label_correct": eligible and predicted_label == actual_label,
            "dominant_trait_share": round(dominant_share, 6),
            "single_trait_dominated": dominant_share > 0.7,
            "top_matches": predicted["top_matches"],
            "top_mismatches": predicted["top_mismatches"],
        })

    eligible_folds = [fold for fold in folds if fold["eligible_prediction"]]
    three_way_accuracy = (
        sum(1 for fold in eligible_folds if fold["label_correct"]) / len(eligible_folds)
        if eligible_folds else 0.0
    )
    mean_absolute_error = (
        sum(abs(fold["predicted_taste_score"] - fold["actual_signal_strength"]) for fold in eligible_folds)
        / len(eligible_folds)
        if eligible_folds else 0.0
    )

    return {
        "version": "0.2.3",
        "validation_model_version": VALIDATION_VERSION,
        "neutral_signal_band": NEUTRAL_SIGNAL_BAND,
        "fold_count": len(folds),
        "eligible_fold_count": len(eligible_folds),
        "abstained_fold_count": len(folds) - len(eligible_folds),
        "three_way_accuracy": round(three_way_accuracy, 6),
        "mean_absolute_error": round(mean_absolute_error, 6),
        "single_trait_dominated_fold_count": sum(1 for fold in folds if fold["single_trait_dominated"]),
        "folds": folds,
    }
