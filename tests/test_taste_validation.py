from cinema_brain.taste_validation import apply_explicit_preferences, leave_one_film_out_validation


def _profiles():
    return {
        "version": "1.0.0",
        "registry_version": "1.0.0",
        "films": [
            {"film_key": "a", "title": "A", "year": 2000, "traits": [{"trait_id": "practical_effects", "value": 1.0, "confidence": 1.0}, {"trait_id": "dread", "value": 0.9, "confidence": 1.0}]},
            {"film_key": "b", "title": "B", "year": 2001, "traits": [{"trait_id": "practical_effects", "value": 0.8, "confidence": 1.0}, {"trait_id": "dread", "value": 0.8, "confidence": 1.0}]},
            {"film_key": "c", "title": "C", "year": 2002, "traits": [{"trait_id": "practical_effects", "value": 0.1, "confidence": 1.0}, {"trait_id": "dread", "value": 0.2, "confidence": 1.0}]},
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


def test_leave_one_out_uses_three_way_labels_and_reports_abstentions():
    signals = [
        {"film_key": "a", "rating": 5.0, "liked": True, "watch_count": 2, "source_types": ["rating", "like", "rewatch"]},
        {"film_key": "b", "rating": 2.75, "liked": False, "watch_count": 1, "source_types": ["rating"]},
        {"film_key": "c", "rating": 2.0, "liked": False, "watch_count": 1, "source_types": ["rating"]},
    ]
    prefs = {"version": "1.0.0", "preferences": [{"trait_id": "practical_effects", "affinity": 1.0, "confidence": 0.95}]}
    result = leave_one_film_out_validation(_profiles(), signals, prefs)
    assert result["fold_count"] == 3
    assert 0.0 <= result["three_way_accuracy"] <= 1.0
    assert result["eligible_fold_count"] + result["abstained_fold_count"] == 3
    assert {fold["actual_label"] for fold in result["folds"]} == {"positive", "neutral", "negative"}
    assert all("dominant_trait_share" in fold for fold in result["folds"])
