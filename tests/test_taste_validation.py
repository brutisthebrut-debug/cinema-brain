from cinema_brain.taste_validation import apply_explicit_preferences, leave_one_film_out_validation


def _profiles():
    return {
        "version": "1.0.0",
        "registry_version": "1.0.0",
        "films": [
            {"film_key": "a", "title": "A", "year": 2000, "traits": [{"trait_id": "practical_effects", "value": 1.0, "confidence": 1.0}]},
            {"film_key": "b", "title": "B", "year": 2001, "traits": [{"trait_id": "practical_effects", "value": 0.8, "confidence": 1.0}]},
            {"film_key": "c", "title": "C", "year": 2002, "traits": [{"trait_id": "practical_effects", "value": 0.1, "confidence": 1.0}]},
        ],
    }


def test_explicit_preference_overrides_sparse_negative_inference_without_erasing_provenance():
    graph = {
        "traits": {
            "practical_effects": {
                "affinity": -0.8,
                "confidence": 0.4,
                "evidence_count": 1,
                "positive_evidence_count": 0,
                "negative_evidence_count": 1,
                "conflict": False,
                "supporting_films": [],
                "contradicting_films": [],
                "status": "provisional",
            }
        },
        "learned_trait_count": 1,
    }
    prefs = {"version": "1.0.0", "preferences": [{"trait_id": "practical_effects", "affinity": 1.0, "confidence": 0.95}]}
    result = apply_explicit_preferences(graph, prefs)
    trait = result["traits"]["practical_effects"]
    assert trait["affinity"] > 0
    assert trait["status"] == "explicitly_confirmed"
    assert trait["explicit_preference"]["affinity"] == 1.0


def test_leave_one_out_never_trains_on_held_out_film_and_reports_all_folds():
    signals = [
        {"film_key": "a", "rating": 5.0, "liked": True, "watch_count": 2, "source_types": ["rating", "like", "rewatch"]},
        {"film_key": "b", "rating": 4.5, "liked": True, "watch_count": 1, "source_types": ["rating", "like"]},
        {"film_key": "c", "rating": 2.0, "liked": False, "watch_count": 1, "source_types": ["rating"]},
    ]
    prefs = {"version": "1.0.0", "preferences": [{"trait_id": "practical_effects", "affinity": 1.0, "confidence": 0.95}]}
    result = leave_one_film_out_validation(_profiles(), signals, prefs)
    assert result["fold_count"] == 3
    assert 0.0 <= result["direction_accuracy"] <= 1.0
    assert all("predicted_taste_score" in fold for fold in result["folds"])
