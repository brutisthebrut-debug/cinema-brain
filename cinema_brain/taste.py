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
RATING_WEIGHTS = {0.5: -4.0, 1.0: -3.4, 1.5: -2.6, 2.0: -1.6, 2.5: -0.6, 3.0: 0.3, 3.5: 1.4, 4.0: 2.6, 4.5: 3.4, 5.0: 4.0}


def rating_weight(rating: float | None) -> float:
    if rating is None:
        return 0.0
    return RATING_WEIGHTS.get(round(float(rating) * 2) / 2, 0.0)


def evidence_score(rating: float | None, liked: bool = False, watch_count: int = 0, review_count: int = 0, list_count: int = 0) -> float:
    score = rating_weight(rating)
    score += 1.5 if liked else 0.0
    score += min(max(watch_count - 1, 0), 4) * 0.8
    score += min(review_count, 2) * 0.25
    score += min(list_count, 4) * 0.15
    return round(score, 3)


def load_taxonomy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_registry(taxonomy: dict[str, Any]) -> TraitRegistry:
    registry = TraitRegistry()
    for trait in sorted({t for values in taxonomy.get("families", {}).values() for t in values}):
        registry.register(trait)
    return registry


def infer_traits(text: str, taxonomy: dict[str, Any]) -> dict[str, float]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    scores: dict[str, float] = defaultdict(float)
    for phrase, traits in taxonomy.get("aliases", {}).items():
        if phrase.lower() in normalized:
            for trait in traits:
                scores[trait] += 1.0
    positive = ("love", "loved", "great", "good", "scared me", "worked", "effective")
    negative = ("hate", "hated", "boring", "bad", "didn't work", "did not work", "annoying")
    multiplier = -1.0 if any(x in normalized for x in negative) else 1.25 if any(x in normalized for x in positive) else 1.0
    return {trait: round(value * multiplier, 3) for trait, value in scores.items()}


def _profile_confidence(count: int, total: float, agreement: float) -> float:
    if count == 0:
        return 0.0
    volume = 1 - math.exp(-count / 5)
    magnitude = min(abs(total) / count, 1)
    return round(min(0.95, 0.2 + 0.35 * volume + 0.2 * magnitude + 0.2 * agreement), 3)


def _clear_generated_evidence(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM trait_evidence WHERE model_version=?", (MODEL_VERSION,))
        conn.commit()
    finally:
        conn.close()


def _film_score(row: sqlite3.Row) -> float:
    return evidence_score(row["rating"], bool(row["liked"]), int(row["watch_count"] or 0), int(row["review_count"] or 0), int(row["list_count"] or 0))


def build_taste_profile(db_path: Path, taxonomy_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    taxonomy = load_taxonomy(taxonomy_path)
    registry = build_registry(taxonomy)
    store = EvidenceStore(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    film_rows = conn.execute("SELECT film_key, name, year, rating, liked, watch_count, review_count, list_count FROM films WHERE watched=1").fetchall()
    films = [{"film_key": r["film_key"], "name": r["name"], "year": r["year"], "rating": r["rating"], "evidence_score": _film_score(r)} for r in film_rows]
    film_by_key = {film["film_key"]: film for film in films}
    text_rows = conn.execute(
        """
        SELECT f.film_key, f.rating, f.liked, f.watch_count, f.review_count, f.list_count,
               r.review_text text, 'review' source, r.source_path || ':' || r.source_row source_ref
        FROM reviews r JOIN films f ON f.film_key=r.film_key
        WHERE TRIM(COALESCE(r.review_text,''))!=''
        UNION ALL
        SELECT f.film_key, f.rating, f.liked, f.watch_count, f.review_count, f.list_count,
               e.tags text, 'viewing_event' source, e.source_path || ':' || e.source_row source_ref
        FROM viewing_events e JOIN films f ON f.film_key=e.film_key
        WHERE TRIM(COALESCE(e.tags,''))!=''
        """
    ).fetchall()
    conn.close()

    _clear_generated_evidence(db_path)
    for row in text_rows:
        base = _film_score(row)
        for trait, phrase_strength in infer_traits(row["text"], taxonomy).items():
            raw = phrase_strength * (1 + abs(base) / 4)
            raw = -abs(raw) if base < 0 else raw
            store.save(Evidence(
                subject_key=row["film_key"], trait=trait, weight=min(abs(raw) / 4, 1.0),
                confidence=min(0.98, 0.55 + min(abs(base), 4) * 0.08), source_type=row["source"],
                source_ref=row["source_ref"], model_version=MODEL_VERSION, observed_at=now_iso(),
                polarity=1 if raw >= 0 else -1, note=row["text"],
            ), registry)

    graph = store.load_graph(registry, model_version=MODEL_VERSION)
    by_trait: dict[str, list[Evidence]] = defaultdict(list)
    for item in graph.items():
        by_trait[item.trait].append(item)

    traits: dict[str, Any] = {}
    for family, family_traits in taxonomy.get("families", {}).items():
        for trait in family_traits:
            items = by_trait.get(trait, [])
            total = round(sum(x.signed_strength for x in items), 4)
            denominator = sum(abs(x.signed_strength) for x in items) or 1.0
            agreement = abs(total) / denominator
            strongest = sorted(items, key=lambda x: abs(x.signed_strength), reverse=True)[:5]
            traits[trait] = {
                "family": family,
                "affinity": total,
                "confidence": _profile_confidence(len(items), total, agreement),
                "positive_evidence": sum(x.signed_strength > 0 for x in items),
                "negative_evidence": sum(x.signed_strength < 0 for x in items),
                "strongest_evidence": [{
                    "film_key": x.subject_key,
                    "film": film_by_key.get(x.subject_key, {}).get("name", x.subject_key),
                    "year": film_by_key.get(x.subject_key, {}).get("year"),
                    "source": x.source_type,
                    "source_ref": x.source_ref,
                    "text": x.note,
                    "contribution": round(x.signed_strength, 4),
                    "model_version": x.model_version,
                } for x in strongest],
                "status": "persisted_explicit_text" if items else "unlearned",
                "conflict": any(x.signed_strength > 0 for x in items) and any(x.signed_strength < 0 for x in items),
            }

    profile = {
        "version": "0.2.0",
        "model_name": "Daniel Cinematic DNA",
        "evidence_model_version": MODEL_VERSION,
        "source_counts": {
            "watched_films": len(films), "text_evidence_rows": len(text_rows),
            "persisted_evidence_records": store.count(MODEL_VERSION),
            "learned_traits": sum(v["status"] != "unlearned" for v in traits.values()),
        },
        "weights": {"ratings": RATING_WEIGHTS, "liked": 1.5, "rewatch_beyond_first": 0.8, "review_presence": 0.25, "list_presence": 0.15},
        "traits": traits,
        "top_positive_films": sorted(films, key=lambda x: x["evidence_score"], reverse=True)[:25],
        "top_negative_films": sorted(films, key=lambda x: x["evidence_score"])[:25],
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
