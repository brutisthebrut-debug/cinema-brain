from __future__ import annotations

from typing import Any

SENTIMENT_VALUES = {"dislike": -0.45, "neutral": 0.0, "like": 0.35, "love": 0.7}
TRAIT_VALUES = {"dislike": -0.6, "neutral": 0.0, "like": 0.55, "admire_not_enjoy": 0.25}


def validate_benchmark_reactions(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, film in enumerate(payload.get("films", [])):
        key = film.get("film_key")
        if not key:
            errors.append(f"films[{index}] missing film_key")
            continue
        if key in seen:
            errors.append(f"duplicate film_key: {key}")
        seen.add(key)
        rating = film.get("overall_rating")
        if rating is not None and not 0.5 <= float(rating) <= 5.0:
            errors.append(f"{key}: overall_rating must be between 0.5 and 5.0")
        sentiment = film.get("overall_sentiment")
        if sentiment is not None and sentiment not in SENTIMENT_VALUES:
            errors.append(f"{key}: invalid overall_sentiment {sentiment!r}")
        for trait_id, reaction in film.get("trait_reactions", {}).items():
            if reaction is not None and reaction not in TRAIT_VALUES:
                errors.append(f"{key}: invalid reaction {reaction!r} for {trait_id}")
    return errors


def compile_benchmark_reaction_signals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    errors = validate_benchmark_reactions(payload)
    if errors:
        raise ValueError("; ".join(errors))

    signals: list[dict[str, Any]] = []
    for film in payload.get("films", []):
        rating = film.get("overall_rating")
        sentiment = film.get("overall_sentiment")
        rewatch = film.get("would_rewatch")
        if rating is None and sentiment is None and rewatch is None:
            continue
        explicit_sentiment = SENTIMENT_VALUES.get(sentiment, 0.0)
        if rewatch is True:
            explicit_sentiment += 0.15
        elif rewatch is False:
            explicit_sentiment -= 0.05
        signals.append({
            "film_key": film["film_key"],
            "rating": rating,
            "liked": sentiment in {"like", "love"},
            "watch_count": 2 if rewatch is True else 1,
            "explicit_sentiment": round(explicit_sentiment, 3),
            "source_types": ["benchmark_reaction"],
            "trait_reactions": {
                trait_id: TRAIT_VALUES[reaction]
                for trait_id, reaction in film.get("trait_reactions", {}).items()
                if reaction is not None
            },
            "notes": film.get("notes", ""),
        })
    return signals
