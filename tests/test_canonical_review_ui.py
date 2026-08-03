from pathlib import Path


def test_review_ui_preserves_guarded_csv_contract():
    html = Path("tools/canonical-review/index.html").read_text(encoding="utf-8")
    required = [
        "film_key", "title", "year", "trait_id", "candidate_value",
        "candidate_confidence", "source", "rationale", "decision",
        "reviewed_value", "reviewed_confidence", "review_note",
    ]
    for field in required:
        assert field in html
    assert "approve" in html
    assert "reject" in html
    assert "edit" in html
    assert "localStorage" in html
    assert "text/csv" in html


def test_review_ui_is_dependency_free_and_mobile_ready():
    html = Path("tools/canonical-review/index.html").read_text(encoding="utf-8")
    assert 'name="viewport"' in html
    assert "<script src=" not in html
    assert "fetch(" not in html
    assert "reviewed_value" in html
    assert "reviewed_confidence" in html
