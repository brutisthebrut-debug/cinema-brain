from pathlib import Path

import pytest

from cinema_brain.golden_dataset import GoldenRecord, IdentityEvaluation
from cinema_brain.golden_review import decide_review, summarize_review_decisions, write_review_decisions


def record() -> GoldenRecord:
    return GoldenRecord(
        film_key="title:undertone:2025",
        canonical_title="Undertone",
        release_year=2025,
        accepted_titles=(),
        entity_type="film",
        hazards=("recent independent title",),
        expected_traits=("psychological",),
        reviewed=False,
    )


def evaluation(status: str = "exact") -> IdentityEvaluation:
    return IdentityEvaluation(
        film_key="title:undertone:2025",
        status=status,
        title_match=status in {"exact", "year_mismatch"},
        year_match=status in {"exact", "title_mismatch"},
        reviewed=False,
        provider_title="Undertone",
        provider_year=2025 if status != "year_mismatch" else 2024,
        explanation="fixture",
    )


def test_exact_match_can_be_approved_and_written(tmp_path: Path):
    decision = decide_review(
        record(), evaluation(), status="approved", reviewer="daniel", reason="Title and year verified.", reviewed_at="2026-08-02T18:00:00+00:00"
    )
    assert summarize_review_decisions((decision,))["ready_for_promotion"] is True
    output = write_review_decisions((decision,), tmp_path / "decisions.json", benchmark_version="0.1.0")
    assert '"approved"' in output.read_text(encoding="utf-8")


def test_mismatch_cannot_be_approved():
    with pytest.raises(ValueError, match="only exact"):
        decide_review(record(), evaluation("year_mismatch"), status="approved", reviewer="daniel", reason="wrong year")


def test_quarantine_blocks_promotion():
    decision = decide_review(
        record(), evaluation("title_mismatch"), status="quarantined", reviewer="daniel", reason="Needs alternate-title verification."
    )
    summary = summarize_review_decisions((decision,))
    assert summary["quarantined"] == 1
    assert summary["ready_for_promotion"] is False


def test_duplicate_decisions_are_rejected(tmp_path: Path):
    decision = decide_review(record(), evaluation(), status="approved", reviewer="daniel", reason="verified")
    with pytest.raises(ValueError, match="duplicate"):
        write_review_decisions((decision, decision), tmp_path / "decisions.json", benchmark_version="0.1.0")
