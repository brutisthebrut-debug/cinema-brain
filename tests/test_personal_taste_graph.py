from cinema_brain.personal_taste_graph import build_personal_taste_graph


def profiles():
    return {
        "version": "1.0.0",
        "registry_version": "1.0.0",
        "films": [
            {
                "film_key": "a",
                "title": "Atmospheric Favorite",
                "year": 2000,
                "traits": [
                    {"trait_id": "creeping_dread", "value": 1.0, "confidence": 1.0},
                    {"trait_id": "jump_scares", "value": 0.8, "confidence": 0.9},
                ],
            },
            {
                "film_key": "b",
                "title": "Dread Disappointment",
                "year": 2001,
                "traits": [
                    {"trait_id": "creeping_dread", "value": 0.9, "confidence": 0.9},
                ],
            },
        ],
    }


def test_graph_separates_support_and_contradiction():
    signals = [
        {"film_key": "a", "rating": 4.5, "liked": True, "watch_count": 2, "source_types": ["rating", "like", "rewatch"]},
        {"film_key": "b", "rating": 1.5, "liked": False, "watch_count": 1, "source_types": ["rating"]},
    ]
    graph = build_personal_taste_graph(profiles(), signals)
    dread = graph["traits"]["creeping_dread"]
    assert dread["conflict"] is True
    assert dread["positive_evidence_count"] == 1
    assert dread["negative_evidence_count"] == 1
    assert dread["supporting_films"][0]["film_key"] == "a"
    assert dread["contradicting_films"][0]["film_key"] == "b"


def test_graph_is_deterministic_and_sparse_traits_are_provisional():
    signals = [{"film_key": "a", "rating": 4.0, "liked": True, "watch_count": 1, "source_types": ["rating", "like"]}]
    first = build_personal_taste_graph(profiles(), signals)
    second = build_personal_taste_graph(profiles(), signals)
    assert first == second
    assert first["traits"]["jump_scares"]["status"] == "provisional"
    assert first["profile_version"] == "1.0.0"
    assert first["registry_version"] == "1.0.0"


def test_unknown_films_do_not_contaminate_graph():
    graph = build_personal_taste_graph(profiles(), [{"film_key": "unknown", "rating": 5.0}])
    assert graph["signal_count"] == 0
    assert graph["learned_trait_count"] == 0
    assert graph["traits"] == {}
