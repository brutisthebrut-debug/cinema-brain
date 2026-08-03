import pytest

from cinema_brain.benchmark_reactions import compile_benchmark_reaction_signals, validate_benchmark_reactions


def test_separates_overall_enjoyment_from_trait_admiration():
    payload = {
        "films": [{
            "film_key": "title:the-fly:1986",
            "overall_rating": 2.5,
            "overall_sentiment": "neutral",
            "would_rewatch": False,
            "trait_reactions": {"practical_effects": "admire_not_enjoy"},
            "notes": "Amazing craft, not a personal favorite."
        }]
    }
    signal = compile_benchmark_reaction_signals(payload)[0]
    assert signal["liked"] is False
    assert signal["trait_reactions"]["practical_effects"] > 0
    assert signal["explicit_sentiment"] < 0


def test_incomplete_template_rows_are_skipped():
    payload = {"films": [{"film_key": "a", "overall_rating": None, "overall_sentiment": None, "would_rewatch": None, "trait_reactions": {}}]}
    assert compile_benchmark_reaction_signals(payload) == []


def test_invalid_reactions_are_rejected():
    payload = {"films": [{"film_key": "a", "overall_rating": 6, "overall_sentiment": "obsessed", "trait_reactions": {"practical_effects": "maybe"}}]}
    errors = validate_benchmark_reactions(payload)
    assert len(errors) == 3
    with pytest.raises(ValueError):
        compile_benchmark_reaction_signals(payload)
