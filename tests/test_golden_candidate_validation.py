import json
from pathlib import Path

from cinema_brain.golden_candidate_validation import validate_candidate


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def record(reviewed: bool = False) -> dict:
    return {
        "film_key": "title:undertone:2025",
        "canonical_title": "Undertone",
        "release_year": 2025,
        "accepted_titles": [],
        "entity_type": "film",
        "hazards": ["recent obscure title"],
        "expected_traits": ["psychological"],
        "reviewed": reviewed,
    }


def decision(status: str = "approved", identity_status: str = "exact") -> dict:
    return {
        "film_key": "title:undertone:2025",
        "status": status,
        "reviewer": "Daniel",
        "reviewed_at": "2026-08-02T19:00:00+00:00",
        "reason": "Manually verified title and year.",
        "expected_title": "Undertone",
        "expected_year": 2025,
        "provider_title": "Undertone",
        "provider_year": 2025,
        "identity_status": identity_status,
    }


def setup_files(tmp_path: Path, *, candidate_record: dict, review: dict | None = None):
    source = tmp_path / "source.json"
    candidate = tmp_path / "candidate.json"
    decisions = tmp_path / "decisions.json"
    write_json(source, {"version": "v1", "records": [record()]})
    write_json(candidate, {"version": "v2", "previous_version": "v1", "records": [candidate_record]})
    write_json(decisions, {"benchmark_version": "v1", "decisions": [review or decision()]})
    return source, candidate, decisions


def test_valid_approved_promotion(tmp_path: Path):
    paths = setup_files(tmp_path, candidate_record=record(reviewed=True))
    report = validate_candidate(*paths)
    assert report["valid"] is True
    assert report["promoted"] == ["title:undertone:2025"]


def test_rejected_decision_cannot_promote(tmp_path: Path):
    paths = setup_files(tmp_path, candidate_record=record(reviewed=True), review=decision(status="rejected"))
    report = validate_candidate(*paths)
    assert report["valid"] is False
    assert any("invalid decision" in error for error in report["errors"])


def test_identity_change_is_blocked(tmp_path: Path):
    changed = record(reviewed=True)
    changed["release_year"] = 2024
    paths = setup_files(tmp_path, candidate_record=changed)
    report = validate_candidate(*paths)
    assert report["valid"] is False
    assert any("non-review benchmark data changed" in error for error in report["errors"])


def test_reviewed_truth_cannot_regress(tmp_path: Path):
    source, candidate, decisions = setup_files(tmp_path, candidate_record=record())
    write_json(source, {"version": "v1", "records": [record(reviewed=True)]})
    report = validate_candidate(source, candidate, decisions)
    assert report["valid"] is False
    assert any("regressed" in error for error in report["errors"])
