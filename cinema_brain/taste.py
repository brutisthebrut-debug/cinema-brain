from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from .evidence import Evidence, EvidenceStore, TraitRegistry
from .evidence.model import now_iso


MODEL_VERSION = "taste-text-1.0.0"

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


def build_registry(taxonomy: dict[str, Any]) -> TraitRegistry:
    registry = TraitRegistry()
    traits = {
        trait
        for family_traits in taxonomy.get("families", {}).values()
        for trait in family_traits
    }
    reverse_aliases: dict[str, list[str]] = defaultdict(list)
    for phrase, mapped_traits in taxonomy.get("aliases", {}).items():
        for trait in mapped_traits:
            if phrase.strip().lower() != trait.strip().lower():
                reverse_aliases[trait].append(phrase)
    for trait in sorted(traits):
        registry.register(trait, reverse_aliases.get(trait, ()))
    return registry


def infer_traits(text: str, taxonomy: dict[str, Any]) -> dict[str, float]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    scores: dict[str, float] = defaultdict(float)
    for phrase, traits in taxonomy.get("aliases", {}).items():
        if phrase.lower() in normalized:
            for trait in traits:
                scores[trait] += 1.0

    positive_markers = ("love", "loved", "great", "good", "scared me", "worked", "effective")
    negative_markers = ("hate", "hated", "boring", "bad", "didn't work", "did not work", "annoying")
    multiplier = -1.0 if any(m in normalized for m in negative_markers) else 1.25 if any(m in normalized for m in positive_markers) else 1.0
    return {trait: round(value * multiplier, 3) for trait, value in scores.items()}


def _confidence(evidence_count: int, total_magnitude: float, agreement: float) -> float:
    if evidence_count <= 0:
        return 0.0
    volume = 1 - math.exp(-evidence_count / 5)
    magnitude = min(abs(total_magnitude) / max(evidence_count, 1), 1)
    return round(min(0.95, 0.2 + 0.35 * volume + 0.2 * magnitude + 0.2 * agreement), 3)


def _replace_model_evidence(db_path: Path, model_version: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM trait_evidence WHERE model_version=?", (model_version,))
        conn.commit()
    finally:
        conn.close()


def build_taste_profile(
    db_path: Path,
    taxonomy_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    taxonomy = load_taxonomy(taxonomy_path)
    registry = build_registry(taxonomy)
    store = EvidenceStore(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    film_rows = conn.execute(
        """
        SELECT film_key, name, year, rating, liked, watch_count, review_count, list_count
        FROM films WHERE watched=1
        """
    ).fetchall()
    films = []
    film_by_key = {}
    for row in film_rows:
        score = evidence_score(row["rating"], bool(row["liked"]), int(row["watch_count"] or 0), int(row["review_count"] or 0), int(row["list_count"] or 0))
        film = {"film_key": row["film_key"], "name": row["name"], "year": row["year"], "rating": row["rating"], "evidence_score": score}
        films.append(film)
        film_by_key[row["film_key"]] = film

    text_rows = conn.execute(
        """
        SELECT f.film_key, f.rating, f.liked, f.watch_count, f.review_count, f.list_count,
               r.review_text AS text, 'review' AS source,
               r.source_path || ':' || r.source_row AS source_ref
        FROM reviews r JOIN films f ON f.film_key=r.film_key
        WHERE TRIM(COALESCE(r.review_text,''))!=''
        UNION ALL
        SELECT f.film_key, f.rating, f.liked, f.watch_count, f.review_count, f.list_count,
               e.tags AS text, 'viewing_event' AS source,
               e.source_path || ':' || e.source_row AS source_ref
        FROM viewing_events e JOIN films f ON f.film_key=e.film_key
        WHERE TRIM(COALESCE(e.tags,''))!=''
        """
    ).fetchall()
    conn.close()

    _replace_model_evidence(db_path, MODEL_VERSION)
    for row in text_rows:
        base = evidence_score(row["rating"], bool(row["liked"]), int(row["watch_count"] or 0), int(row["review_count"] or 0), int(row["list_count"] or 0))
        for trait, phrase_strength in infer_traits(row["text"], taxonomy).items():
            raw = phrase_strength * (1.0 + abs(base) / 4)
            if base < 0:
                raw *= -1
            polarity = 1 if raw >= 0 else -1
            weight = min(abs(raw) / 4.0, 1.0)
            confidence = min(0.98, 0.55 + min(abs(base), 4.0) * 0.08)
            store.save(
                Evidence(
                    subject_key=row["film_key"],
                    trait=trait,
                    weight=weight,
                    confidence=confidence,
                    source_type=row["source"],
                    source_ref=row["source_ref"],
                    model_version=MODEL_VERSION,
                    observed_at=now_iso(),
                    polarity=polarity,
                    note=row["text"],
                ),
                registry,
            )

    graph = store.load_graph(registry, model_version=MODEL_VERSION)
    by_trait: dict[str, list[Evidence]] = defaultdict(list)
    for item in graph.items():
        by_trait[item.trait].append(item)

    traits = {}
    for family, family_traits in taxonomy.get("families", {}).items():
        for trait in family_traits:
            items = by_trait.get(trait, [])
            total = round(sum(item.signed_strength for item in items), 4)
            denominator = sum(abs(item.signed_strength) for item in items) or 1.0
            agreement = abs(total) / denominator
            strongest_items = sorted(items, key=lambda item: abs(item.signed_strength), reverse=True)[:5]
            traits[trait] = {
                "family": family,
                "affinity": total,
                "confidence": _confidence(len(items), total, agreement),
                "positive_evidence": sum(1 for item in items if item.signed_strength > 0),
                "negative_evidence": sum(1 for item in items if item.signed_strength < 0),
                "strongest_evidence": [
                    {
                        "film_key": item.subject_key,
                        "film": film_by_key.get(item.subject_key, {}).get("name", item.subject_key),
                        "year": film_by_key.get(item.subject_key, {}).get("year"),
                        "source": item.source_type,
                        "source_ref": item.source_ref,
                        "text": item.note,
                        "contribution": round(item.signed_strength, 4),
                        "model_version": item.model_version,
                    }
                    for item in strongest_items
                ],
                "status": "persisted_explicit_text" if items else "unlearned",
                "conflict": bool(items) and any(i.signed_strength > 0 for i in items) and any(i.signed_strength < 0 for i in items),
            }

    profile = {
        "version": "0.2.0",
        "model_name": "Daniel Cinematic DNA",
        "evidence_model_version": MODEL_VERSION,
        "source_counts": {
            "watched_films": len(films),
            "text_evidence_rows": len(text_rows),
            "persisted_evidence_records": store.count(MODEL_VERSION),
            "learned_traits": sum(1 for value in traits.values() if value["status"] != "unlearned"),
        },
        "weights": {"ratings": RATING_WEIGHTS, "liked": 1.5, "rewatch_beyond_first": 0.8, "review_presence": 0.25, "list_presence": 0.15},
        "traits": traits,
        "top_positive_films": sorted(films, key=lambda item: item["evidence_score"], reverse=True)[:25],
        "top_negative_films": sorted(films, key=lambda item: item["evidence_score"])[:25],
        "limitations": [
            "Trait inference currently uses explicit phrase matching only.",
            "Most films do not yet have enriched genre, style, theme, cast, or director metadata.",
            "Confidence is conservative and based on persisted evidence agreement and volume.",
        ],
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return profile
