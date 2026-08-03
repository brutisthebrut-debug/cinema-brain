from pathlib import Path


DASHBOARD = Path("tools/brain-health/index.html")


def test_dashboard_is_a_thin_read_only_audit_surface() -> None:
    html = DASHBOARD.read_text(encoding="utf-8")

    required_contract_fields = [
        "recommendation_release_audit",
        "verified_read_only",
        "release_id",
        "audit_id",
        "input_integrity",
        "gate_audit",
        "release_counts",
        "rank_movement",
        "abstention_audit",
        "evidence_coverage",
        "health_metrics",
        "awaiting_outcome",
    ]
    for field in required_contract_fields:
        assert field in html

    assert 'accept=".json,application/json"' in html
    assert "Recommendation Trust" in html
    assert "does not rerank films or record outcomes" in html
    assert "fetch(" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "XMLHttpRequest" not in html


def test_dashboard_is_dependency_free_mobile_ready_and_escapes_audit_text() -> None:
    html = DASHBOARD.read_text(encoding="utf-8")

    assert 'name="viewport"' in html
    assert "<script src=" not in html
    assert "<link rel=" not in html
    assert "@media(max-width:540px)" in html
    assert "const esc=" in html
    assert "esc(item.title)" in html
    assert "esc(audit.release_id)" in html
    assert "Audit rejected" in html


def test_dashboard_rejects_unverified_or_post_outcome_inputs() -> None:
    html = DASHBOARD.read_text(encoding="utf-8")

    assert "only accepts Recommendation Audit v1.0.0" in html
    assert "Audit input integrity is not verified" in html
    assert "Prediction was not frozen before outcome capture" in html
    assert "ineligible or failed release gate" in html
    assert "only accepts the pre-outcome audit state" in html
    assert "Outcome contract does not require release_id" in html
