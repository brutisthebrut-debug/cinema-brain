from cinema_brain.human_evaluation import summarize_human_evaluation


def packet():
    films = []
    for index in range(5):
        films.append({
            "film_key": f"title:test-{index}:2026",
            "interest": "yes",
            "prediction_reaction": "nailed_it",
            "already_seen": False,
            "watched_after_recommendation": "not_yet",
            "actual_rating": None,
            "actual_sentiment": None,
            "would_recommend": "unknown",
        })
    return {"evaluation_type": "frozen_top_five", "films": films}


def test_pre_watch_packet_reports_appeal_without_claiming_trust():
    summary = summarize_human_evaluation(packet())
    assert summary.recommendation_appeal == 1.0
    assert summary.explanation_fit == 1.0
    assert summary.watched_outcome_count == 0
    assert summary.recommendation_trust is None


def test_post_watch_outcomes_calculate_recommendation_trust():
    payload = packet()
    payload["films"][0].update({
        "watched_after_recommendation": "yes",
        "actual_rating": 4.5,
        "actual_sentiment": "love",
        "would_recommend": "yes",
    })
    payload["films"][1].update({
        "watched_after_recommendation": "yes",
        "actual_rating": 2.0,
        "actual_sentiment": "dislike",
        "would_recommend": "no",
    })
    summary = summarize_human_evaluation(payload)
    assert summary.watched_outcome_count == 2
    assert summary.recommendation_trust == 0.5
