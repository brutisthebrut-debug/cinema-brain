import pytest

from cinema_brain.contracts import (
    AvailabilityEvidence,
    RecommendationResult,
    ScoreComponents,
    TraitEvidence,
    WatchRequest,
)


def test_trait_evidence_preserves_direction_and_confidence():
    evidence = TraitEvidence(
        film_key="title:undertone:2025",
        trait="creeping_dread",
        polarity=1,
        strength=4.0,
        confidence=0.75,
        source_type="explicit_reaction",
        source_text="It honestly scared me like The Blair Witch.",
    )
    assert evidence.signed_strength == 3.0
    assert evidence.to_dict()["source_type"] == "explicit_reaction"


def test_watch_request_rejects_conflicting_rewatch_rules():
    with pytest.raises(ValueError):
        WatchRequest(exclude_watched=True, allow_rewatch=True)


def test_score_components_are_bounded_and_explainable():
    components = ScoreComponents(
        taste_fit=0.9,
        mood_fit=0.8,
        context_fit=0.7,
        novelty=0.6,
        quality_floor=0.8,
        watchlist_intent=0.5,
        underexplored_bonus=0.4,
        risk_penalty=0.1,
    )
    assert 0 <= components.weighted_total() <= 1
    assert components.to_dict()["weighted_total"] == components.weighted_total()


def test_recommendation_requires_caveat_and_versions():
    components = ScoreComponents(
        taste_fit=0.9,
        mood_fit=0.8,
        context_fit=0.8,
        novelty=0.5,
        quality_floor=0.7,
    )
    result = RecommendationResult(
        film_key="title:example:2026",
        name="Example",
        year=2026,
        predicted_rating=4.2,
        confidence=0.78,
        score_components=components,
        evidence=({"trait": "creeping_dread", "contribution": 0.8},),
        caveat="May be more psychological than supernatural.",
        availability=AvailabilityEvidence(
            service="paramount_plus",
            region="US",
            verified_at="2026-08-02T05:00:00Z",
            source="manual_test",
        ),
    )
    payload = result.to_dict()
    assert payload["versions"]["taste"] == "taste-0.2.0"
    assert payload["score_components"]["weighted_total"] > 0

    with pytest.raises(ValueError):
        RecommendationResult(
            film_key="title:bad:2026",
            name="Bad",
            year=2026,
            predicted_rating=4.0,
            confidence=0.5,
            score_components=components,
            evidence=(),
            caveat="",
            availability=None,
        )
