from __future__ import annotations

from pathlib import Path


UI = Path("tools/canonical-review/evaluate.html")


def test_unified_evaluation_preserves_both_feedback_phases() -> None:
    html = UI.read_text(encoding="utf-8")

    for label in (
        "Before watching",
        "After watching",
        "How interested were you?",
        "Did the explanation sound like you?",
        "Are you genuinely glad you watched it?",
        "Did it fit the moment?",
        "Immediate reaction · one honest sentence",
    ):
        assert label in html


def test_release_bound_export_matches_outcome_capture_v1_fields() -> None:
    html = UI.read_text(encoding="utf-8")

    for field in (
        "submission_type",
        "release_id",
        "audit_id",
        "released_predictions",
        "film_key",
        "watched_at",
        "recorded_at",
        "actual_rating",
        "reaction_text",
        "completed",
        "glad_watched",
        "fit_the_moment",
    ):
        assert field in html
    assert "post_watch_outcome_submission" in html


def test_manual_mode_is_explicitly_unbound_and_not_trust_evidence() -> None:
    html = UI.read_text(encoding="utf-8")

    assert "post_watch_manual_intake" in html
    assert "manual_unbound_do_not_count_as_recommendation_trust_until_verified" in html
    assert "verify against a pre-watch release before counting Recommendation Trust" in html


def test_ui_is_local_first_and_has_no_network_calls() -> None:
    html = UI.read_text(encoding="utf-8")

    assert "Import release" in html
    assert "Copy for chat" in html
    assert "Download JSON" in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html

