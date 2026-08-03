import json
from pathlib import Path

import pytest

from cinema_brain.recommendation_corpus import (
    RecommendationCorpusError,
    corpus_report,
    load_recommendation_corpus,
    validate_recommendation_corpus,
)
from cinema_brain.trait_registry import load_trait_registry


CORPUS = Path("config/horror_recommendation_corpus_v1.json")
REGISTRY = Path("config/trait_registry_v1.json")


def known_traits() -> set[str]:
    return {trait.trait_id for trait in load_trait_registry(REGISTRY).traits}


def test_seed_corpus_is_versioned_unique_and_canonically_typed():
    payload = load_recommendation_corpus(CORPUS, known_trait_ids=known_traits())
    report = corpus_report(payload)
    assert report["film_count"] == 12
    assert report["assignment_count"] == 48
    assert report["minimum_traits_per_film"] == 4
    assert report["unique_trait_count"] >= 12


def test_watched_films_are_rejected_before_ranking():
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    watched = {payload["films"][0]["film_key"]}
    errors = validate_recommendation_corpus(
        payload,
        known_trait_ids=known_traits(),
        watched_film_keys=watched,
    )
    assert any("watched films cannot enter" in error for error in errors)
    with pytest.raises(RecommendationCorpusError, match="watched films"):
        load_recommendation_corpus(
            CORPUS,
            known_trait_ids=known_traits(),
            watched_film_keys=watched,
        )


def test_duplicate_identity_and_unknown_traits_are_rejected():
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    payload["films"].append(dict(payload["films"][0]))
    payload["films"][1]["traits"][0]["trait_id"] = "not_a_canonical_trait"
    errors = validate_recommendation_corpus(payload, known_trait_ids=known_traits())
    assert any("duplicate film_key" in error for error in errors)
    assert any("duplicate title/year identity" in error for error in errors)
    assert any("unknown" in error for error in errors)


def test_sparse_or_unexplained_assignments_are_rejected():
    payload = {
        "version": "test",
        "registry_version": "1.0.0",
        "films": [{
            "film_key": "title:test:2020",
            "title": "Test",
            "year": 2020,
            "traits": [{"trait_id": "creeping_dread", "value": 1.0, "confidence": 1.0, "rationale": ""}],
        }],
    }
    errors = validate_recommendation_corpus(payload, known_trait_ids=known_traits())
    assert any("at least 3 assignments" in error for error in errors)
