"""Validate and summarize private human-evaluation packets.

The packet itself should remain outside source control. This module accepts an
exported JSON file and emits aggregate metrics that are safe to persist.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_INTEREST = {"yes", "maybe", "no"}
_ALLOWED_PREDICTION_REACTION = {"wrong", "partly_right", "nailed_it"}
_ALLOWED_WATCHED = {"not_yet", "yes", "no"}
_ALLOWED_SENTIMENT = {None, "dislike", "neutral", "like", "love"}
_ALLOWED_RECOMMEND = {"unknown", "yes", "no"}


@dataclass(frozen=True)
class EvaluationSummary:
    film_count: int
    unseen_count: int
    interested_count: int
    explanation_hit_count: int
    watched_outcome_count: int
    recommendation_appeal: float
    explanation_fit: float
    recommendation_trust: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "film_count": self.film_count,
            "unseen_count": self.unseen_count,
            "interested_count": self.interested_count,
            "explanation_hit_count": self.explanation_hit_count,
            "watched_outcome_count": self.watched_outcome_count,
            "recommendation_appeal": self.recommendation_appeal,
            "explanation_fit": self.explanation_fit,
            "recommendation_trust": self.recommendation_trust,
        }


def load_human_evaluation(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_human_evaluation(payload)
    return payload


def validate_human_evaluation(payload: dict[str, Any]) -> None:
    if payload.get("evaluation_type") != "frozen_top_five":
        raise ValueError("evaluation_type must be frozen_top_five")
    films = payload.get("films")
    if not isinstance(films, list) or len(films) != 5:
        raise ValueError("human evaluation must contain exactly five films")

    seen_keys: set[str] = set()
    for index, film in enumerate(films, start=1):
        if not isinstance(film, dict):
            raise ValueError(f"film {index} must be an object")
        key = film.get("film_key")
        if not isinstance(key, str) or not key:
            raise ValueError(f"film {index} is missing film_key")
        if key in seen_keys:
            raise ValueError(f"duplicate film_key: {key}")
        seen_keys.add(key)
        if film.get("interest") not in _ALLOWED_INTEREST:
            raise ValueError(f"invalid interest for {key}")
        if film.get("prediction_reaction") not in _ALLOWED_PREDICTION_REACTION:
            raise ValueError(f"invalid prediction_reaction for {key}")
        if film.get("watched_after_recommendation") not in _ALLOWED_WATCHED:
            raise ValueError(f"invalid watched_after_recommendation for {key}")
        if film.get("actual_sentiment") not in _ALLOWED_SENTIMENT:
            raise ValueError(f"invalid actual_sentiment for {key}")
        if film.get("would_recommend") not in _ALLOWED_RECOMMEND:
            raise ValueError(f"invalid would_recommend for {key}")
        rating = film.get("actual_rating")
        if rating is not None and (not isinstance(rating, (int, float)) or not 0.5 <= rating <= 5.0):
            raise ValueError(f"actual_rating for {key} must be 0.5-5.0")


def summarize_human_evaluation(payload: dict[str, Any]) -> EvaluationSummary:
    validate_human_evaluation(payload)
    films = payload["films"]
    unseen = [film for film in films if film.get("already_seen") is False]
    interested = [film for film in films if film.get("interest") == "yes"]
    explanation_hits = [film for film in films if film.get("prediction_reaction") == "nailed_it"]
    outcomes = [
        film
        for film in films
        if film.get("watched_after_recommendation") == "yes"
        and film.get("actual_sentiment") is not None
    ]
    trusted = [
        film
        for film in outcomes
        if film.get("actual_sentiment") in {"like", "love"}
        and film.get("would_recommend") == "yes"
    ]
    count = len(films)
    return EvaluationSummary(
        film_count=count,
        unseen_count=len(unseen),
        interested_count=len(interested),
        explanation_hit_count=len(explanation_hits),
        watched_outcome_count=len(outcomes),
        recommendation_appeal=round(len(interested) / count, 3),
        explanation_fit=round(len(explanation_hits) / count, 3),
        recommendation_trust=(round(len(trusted) / len(outcomes), 3) if outcomes else None),
    )
