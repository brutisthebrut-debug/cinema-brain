from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


RATING_WEIGHTS = {
    0.5: -4.0,
    1.0: -3.4,
    1.5: -2.6,
    2.0: -1.6,
    2.5: -0.6,
    3.0: 0.3,
    3.5: 1.4,
    4.0: 2.6,
    4.5: 3.4,
    5.0: 4.0,
}


def rating_weight(rating: float | None) -> float:
    if rating is None:
        return 0.0
    rounded = round(float(rating) * 2) / 2
    return RATING_WEIGHTS.get(rounded, 0.0)


def evidence_score(
    rating: float | None,
    liked: bool = False,
    watch_count: int = 0,
    review_count: int = 0,
    list_count: int = 0,
) -> float:
    score = rating_weight(rating)
    if liked:
        score += 1.5
    score += min(max(watch_count - 1, 0), 4) * 0.8
    score += min(review_count, 2) * 0.25
    score += min(list_count, 4) * 0.15
    return round(score, 3)


def load_taxonomy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_traits(text: str, taxonomy: dict[str, Any]) -> dict[str, float]:
    """Conservative phrase matcher for explicit reactions.

    This intentionally captures only explicit language. Metadata-driven and
    semantic inference will be added later with provenance and confidence.
    """
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    scores: dict[str, float] = defaultdict(float)
    aliases = taxonomy.get("aliases", {})
    for phrase, traits in aliases.items():
        if phrase.lower() in normalized:
            for trait in traits:
                scores[trait] += 1.0

    positive_markers = ("love", "loved", "great", "good", "scared me", "worked", "effective")
    negative_markers = ("hate", "hated", "boring", "bad", "didn't work", "did not work", "annoying")
    polarity = 1.0
    if any(marker in normalized for marker in negative_markers):
        polarity = -1.0
    elif any(marker in normalized for marker in positive_markers):
        polarity = 1.25

    return {trait: round(value * polarity, 3) for trait, value in scores.items()}


def _confidence(evidence_count: int, total_magnitude: float) -> float:
    if evidence_count <= 0:
        return 0.0
    # Saturating confidence: evidence volume matters, but never implies certainty.
    volume = 1 - math.exp(-evidence_count / 5)
    magnitude = min(abs(total_magnitude) / max(evidence_count, 1) / 4, 1)
    return round(min(0.95, 0.25 + 0.5 * volume + 0.2 * magnitude), 3)


def build_taste_profile(
    db_path: Path,
    taxonomy_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    taxonomy = load_taxonomy(taxonomy_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    film_rows = conn.execute(
        """
        SELECT film_key, name, year, rating, liked, watch_count,
               review_count, list_count
        FROM films
        WHERE watched=1
        """
    ).fetchall()

    films = []
    for row in film_rows:
        score = evidence_score(
            row["rating"],
            bool(row["liked"]),
            int(row["watch_count"] or 0),
            int(row["review_count"] or 0),
            int(row["list_count"] or 0),
        )
        films.append(
            {
                "film_key": row["film_key"],
                "name": row["name"],
                "year": row["year"],
                "rating": row["rating"],
                "evidence_score": score,
            }
        )

    trait_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    text_rows = conn.execute(
        """
        SELECT f.film_key, f.name, f.year, f.rating, f.liked, f.watch_count,
               f.review_count, f.list_count, r.review_text AS text, 'review' AS source
        FROM reviews r JOIN films f ON f.film_key=r.film_key
        WHERE TRIM(COALESCE(r.review_text,''))!=''
        UNION ALL
        SELECT f.film_key, f.name, f.year, f.rating, f.liked, f.watch_count,
               f.review_count, f.list_count, e.tags AS text, 'viewing_event' AS source
        FROM viewing_events e JOIN films f ON f.film_key=e.film_key
        WHERE TRIM(COALESCE(e.tags,''))!=''
        """
    ).fetchall()

    for row in text_rows:
        base = evidence_score(
            row["rating"],
            bool(row["liked"]),
            int(row["watch_count"] or 0),
            int(row["review_count"] or 0),
            int(row["list_count"] or 0),
        )
        inferred = infer_traits(row["text"], taxonomy)
        for trait, phrase_strength in inferred.items():
            contribution = phrase_strength * (1.0 + abs(base) / 4)
            if base < 0:
                contribution *= -1
            trait_evidence[trait].append(
                {
                    "film_key": row["film_key"],
                    "film": row["name"],
                    "year": row["year"],
                    "source": row["source"],
                    "text": row["text"],
                    "contribution": round(contribution, 3),
                }
            )

    traits = {}
    for family, family_traits in taxonomy.get("families", {}).items():
        for trait in family_traits:
            evidence = trait_evidence.get(trait, [])
            total = round(sum(item["contribution"] for item in evidence), 3)
            positive = sum(1 for item in evidence if item["contribution"] > 0)
            negative = sum(1 for item in evidence if item["contribution"] < 0)
            strongest = sorted(evidence, key=lambda item: abs(item["contribution"]), reverse=True)[:5]
            traits[trait] = {
                "family": family,
                "affinity": total,
                "confidence": _confidence(len(evidence), total),
                "positive_evidence": positive,
                "negative_evidence": negative,
                "strongest_evidence": strongest,
                "status": "explicit_text" if evidence else "unlearned",
            }

    top_positive_films = sorted(films, key=lambda item: item["evidence_score"], reverse=True)[:25]
    top_negative_films = sorted(films, key=lambda item: item["evidence_score"])[:25]

    profile = {
        "version": "0.1.0",
        "model_name": "Daniel Cinematic DNA",
        "source_counts": {
            "watched_films": len(films),
            "text_evidence_rows": len(text_rows),
            "learned_traits": sum(1 for value in traits.values() if value["status"] != "unlearned"),
        },
        "weights": {
            "ratings": RATING_WEIGHTS,
            "liked": 1.5,
            "rewatch_beyond_first": 0.8,
            "review_presence": 0.25,
            "list_presence": 0.15,
        },
        "traits": traits,
        "top_positive_films": top_positive_films,
        "top_negative_films": top_negative_films,
        "limitations": [
            "Trait inference currently uses explicit phrase matching only.",
            "Most films do not yet have enriched genre, style, theme, cast, or director metadata.",
            "Confidence is evidence-based and intentionally conservative.",
        ],
    }
    conn.close()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return profile
