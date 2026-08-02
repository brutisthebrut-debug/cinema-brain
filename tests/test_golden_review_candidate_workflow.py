from pathlib import Path


def test_candidate_workflow_is_read_only_and_review_gated():
    path = Path(".github/workflows/golden-review-candidate.yml")
    text = path.read_text(encoding="utf-8")

    assert "permissions:\n  contents: read" in text
    assert "ref: main" in text
    assert "Checkout review input only" in text
    assert "sparse-checkout:" in text
    assert "Worksheet path escapes review-input" in text
    assert "golden-review-compile" in text
    assert "golden-promote" in text
    assert "golden_review_decisions.json" in text
    assert "golden_horror_candidate.json" in text
    assert "benchmark.patch" in text
    assert "SHA256SUMS" in text
    assert "actions/upload-artifact@v4" in text

    forbidden = (
        "contents: write",
        "pull-requests: write",
        "git push",
        "gh pr create",
        "merge_pull_request",
    )
    for token in forbidden:
        assert token not in text
