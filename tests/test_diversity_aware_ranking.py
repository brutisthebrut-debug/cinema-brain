from cinema_brain.diversity_aware_ranking import build_diverse_slate


def film(key, title, score, confidence, traits):
    return {
        "film_key": key,
        "title": title,
        "taste_score": score,
        "confidence": confidence,
        "traits": [{"trait_id": trait} for trait in traits],
    }


def test_diversity_can_promote_nonredundant_candidate_without_losing_top_pick():
    ranking = {
        "version": "0.3.0",
        "recommendations": [
            film("a", "A", 0.95, 0.8, ["dread", "isolation"]),
            film("b", "B", 0.93, 0.8, ["dread", "isolation"]),
            film("c", "C", 0.89, 0.7, ["grief", "occult"]),
        ],
    }
    result = build_diverse_slate(ranking, slate_size=2)
    assert [item["film_key"] for item in result["slate"]] == ["a", "c"]
    assert result["slate"][0]["raw_rank"] == 1
    assert result["slate"][1]["raw_rank"] == 3
    assert result["slate_metrics"]["unique_trait_count"] == 4


def test_low_confidence_high_score_candidate_is_marked_discovery():
    ranking = {
        "version": "0.3.0",
        "recommendations": [
            film("a", "A", 0.9, 0.8, ["dread", "isolation"]),
            film("b", "B", 0.8, 0.4, ["cosmic", "uncertainty"]),
        ],
    }
    result = build_diverse_slate(ranking, slate_size=2)
    roles = {item["film_key"]: item["slate_role"] for item in result["slate"]}
    assert roles["b"] == "discovery"
    assert result["slate_metrics"]["discovery_count"] == 1


def test_weights_must_sum_to_one():
    ranking = {"recommendations": []}
    try:
        build_diverse_slate(ranking, relevance_weight=0.8, diversity_weight=0.3)
    except ValueError as error:
        assert "sum to 1" in str(error)
    else:
        raise AssertionError("expected ValueError")
