from cinema_brain.canonical_taste_scoring import score_canonical_films


def _profiles():
    return {
        "version": "1.0.0",
        "registry_version": "1.0.0",
        "films": [
            {
                "film_key": "film:a",
                "title": "Film A",
                "year": 2000,
                "traits": [
                    {"trait_id": "dread", "value": 1.0, "confidence": 1.0},
                    {"trait_id": "comedy", "value": 0.9, "confidence": 1.0},
                ],
            },
            {
                "film_key": "film:b",
                "title": "Film B",
                "year": 2001,
                "traits": [
                    {"trait_id": "dread", "value": 0.5, "confidence": 1.0},
                    {"trait_id": "beauty", "value": 1.0, "confidence": 1.0},
                ],
            },
        ],
    }


def _graph():
    return {
        "model_version": "taste-test",
        "traits": {
            "dread": {"affinity": 0.8, "confidence": 0.9, "status": "learned"},
            "comedy": {"affinity": -0.7, "confidence": 0.8, "status": "learned"},
            "beauty": {"affinity": 0.4, "confidence": 0.6, "status": "provisional"},
            "neutral": {"affinity": 0.0, "confidence": 0.9, "status": "learned"},
        },
    }


def test_scores_are_deterministic_and_ranked():
    first = score_canonical_films(_profiles(), _graph())
    second = score_canonical_films(_profiles(), _graph())
    assert first == second
    assert [film["rank"] for film in first["films"]] == [1, 2]
    assert first["films"][0]["title"] == "Film B"


def test_explanations_separate_matches_and_mismatches():
    result = score_canonical_films(_profiles(), _graph())
    film_a = next(film for film in result["films"] if film["title"] == "Film A")
    assert film_a["top_matches"][0]["trait_id"] == "dread"
    assert film_a["top_mismatches"][0]["trait_id"] == "comedy"
    assert film_a["active_trait_count"] == 2


def test_neutral_affinities_do_not_count_as_active_evidence():
    profiles = _profiles()
    profiles["films"][0]["traits"].append(
        {"trait_id": "neutral", "value": 1.0, "confidence": 1.0}
    )
    result = score_canonical_films(profiles, _graph())
    film_a = next(film for film in result["films"] if film["title"] == "Film A")
    assert film_a["active_trait_count"] == 2
    assert all(item["trait_id"] != "neutral" for item in film_a["all_components"])


def test_unknown_traits_reduce_coverage_without_changing_score():
    profiles = _profiles()
    profiles["films"][1]["traits"].append(
        {"trait_id": "unknown", "value": 1.0, "confidence": 1.0}
    )
    result = score_canonical_films(profiles, _graph())
    film_b = next(film for film in result["films"] if film["title"] == "Film B")
    assert film_b["active_trait_count"] == 2
    assert film_b["trait_coverage"] == 0.666667
