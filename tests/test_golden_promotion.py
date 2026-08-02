import json
from pathlib import Path

import pytest

from cinema_brain.golden_dataset import GoldenRecord
from cinema_brain.golden_promotion import promote_records, write_promoted_dataset
from cinema_brain.golden_review import GoldenReviewDecision


def record(reviewed: bool = False) -> GoldenRecord:
    return GoldenRecord(
        film_key="title:undertone:2025",
        canonical_title="Undertone",
        release_year=2025,
        accepted_titles=(),
        entity_type="film",
        hazards=("recent obscure title",),
        expected_traits=("psychological", "found footage"),
        reviewed=reviewed,
    )


def decision(status: str = "approved", identity_status: str = "exact") -> GoldenReviewDecision:
    return GoldenReviewDecision(
        film_key="title:undertone:2025",
        status=status,
        reviewer="Daniel",
        reviewed_at="2026-08-02T18:00:00+00:00",
        reason="Title and year manually verified.",
        expected_title="Undertone",
        expected_year=2025,
        provider_title="Undertone",
        provider_year=2025,
        identity_status=identity_status,
    )


def test_only_approved_exact_decisions_promote():
    promoted, summary = promote_records((record(),), (decision(),))
    assert promoted[0].reviewed is True
    assert summary["promoted_keys"] == ["title:undertone:2025"]


@pytest.mark.parametrize("status", ["rejected", "quarantined"])
def test_nonapproved_decisions_never_promote(status: str):
    promoted, summary = promote_records((record(),), (decision(status=status),))
    assert promoted[0].reviewed is False
    assert summary["promoted"] == 0
    assert summary["skipped"]["title:undertone:2025"] == status


def test_identity_drift_blocks_promotion():
    bad = decision()
    bad = GoldenReviewDecision(**{**bad.__dict__, "provider_year": 2024})
    with pytest.raises(ValueError, match="provider year mismatch"):
        promote_records((record(),), (bad,))


def test_write_promoted_dataset_versions_and_preserves_history(tmp_path: Path):
    source = tmp_path / "golden.json"
    packet = tmp_path / "reviews.json"
    output = tmp_path / "golden-v1.1.json"
    source.write_text(json.dumps({
        "version": "1.0",
        "records": [{
            "film_key": "title:undertone:2025",
            "canonical_title": "Undertone",
            "release_year": 2025,
            "accepted_titles": [],
            "entity_type": "film",
            "hazards": [],
            "expected_traits": ["psychological"],
            "reviewed": False,
        }],
    }), encoding="utf-8")
    packet.write_text(json.dumps({
        "benchmark_version": "1.0",
        "decisions": [decision().__dict__],
    }), encoding="utf-8")

    summary = write_promoted_dataset(source, packet, output, next_version="1.1")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert summary["promoted"] == 1
    assert payload["previous_version"] == "1.0"
    assert payload["version"] == "1.1"
    assert payload["records"][0]["reviewed"] is True


def test_stale_review_packet_cannot_promote(tmp_path: Path):
    source = tmp_path / "golden.json"
    packet = tmp_path / "reviews.json"
    source.write_text(json.dumps({
        "version": "2.0",
        "records": [{
            "film_key": "title:undertone:2025",
            "canonical_title": "Undertone",
            "release_year": 2025,
            "accepted_titles": [],
            "entity_type": "film",
            "hazards": [],
            "expected_traits": [],
            "reviewed": False,
        }],
    }), encoding="utf-8")
    packet.write_text(json.dumps({
        "benchmark_version": "1.0",
        "decisions": [decision().__dict__],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="review packet targets"):
        write_promoted_dataset(source, packet, tmp_path / "out.json", next_version="2.1")
