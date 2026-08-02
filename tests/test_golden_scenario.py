from cinema_brain.contracts import (
    AvailabilityEvidence,
    RecommendationResult,
    ScoreComponents,
    TraitEvidence,
    WatchRequest,
)


def test_charlotte_late_night_dogs_scenario_is_traceable():
    request = WatchRequest(
        genres=("horror",),
        moods=("creepy", "atmospheric"),
        desired_destination=("genuinely_scared",),
        max_runtime_minutes=120,
        active_services=("max", "peacock", "paramount_plus"),
        location="US-NC-Charlotte",
        attention="full",
        company="dogs",
        novelty="new",
    )

    undertone = TraitEvidence(
        film_key="title:undertone:2025",
        trait="creeping_dread",
        polarity=1,
        strength=4.0,
        confidence=1.0,
        source_type="explicit_reaction",
        source_text="It honestly scared me like The Blair Witch.",
    )

    result = RecommendationResult(
        film_key="title:vicious:2025",
        name="Vicious",
        year=2025,
        predicted_rating=4.0,
        confidence=0.68,
        score_components=ScoreComponents(
            taste_fit=0.75,
            mood_fit=0.85,
            context_fit=0.90,
            novelty=0.70,
            quality_floor=0.55,
            risk_penalty=0.15,
        ),
        evidence=(undertone.to_dict(),),
        caveat="Early evidence is horror-heavy and confidence should remain conservative.",
        availability=AvailabilityEvidence(
            service="paramount_plus",
            region="US-NC",
            verified_at="2026-08-02T05:45:00Z",
            source="live_lookup",
            confidence=0.9,
        ),
    )

    payload = result.to_dict()
    assert request.exclude_watched is True
    assert request.location == "US-NC-Charlotte"
    assert payload["evidence"][0]["trait"] == "creeping_dread"
    assert payload["availability"]["service"] in request.active_services
    assert payload["versions"]["ranker"] == "ranker-0.1.0"
    assert payload["score_components"]["weighted_total"] > 0.5
