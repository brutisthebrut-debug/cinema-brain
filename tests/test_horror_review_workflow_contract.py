from pathlib import Path


def test_horror_review_workflow_builds_complete_private_bundle():
    workflow = Path(".github/workflows/horror-sample-review.yml").read_text(encoding="utf-8")

    required_commands = (
        "enrich-metadata",
        "extract-metadata-evidence",
        "sample-review",
        "golden-review-template",
        "sha256sum",
    )
    for command in required_commands:
        assert command in workflow

    required_artifacts = (
        "golden_horror_v1.json",
        "horror_sample_enrichment.json",
        "horror_sample_evidence.json",
        "horror_sample_review.json",
        "golden_horror_review.csv",
        "REVIEW_INSTRUCTIONS.md",
        "SHA256SUMS.txt",
        "cinema_brain.db",
    )
    for artifact in required_artifacts:
        assert artifact in workflow

    assert "retention-days: 30" in workflow
    assert "permissions:\n  contents: read" in workflow
