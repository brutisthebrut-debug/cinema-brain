import csv
import json
from pathlib import Path

import pytest

from cinema_brain.profile_review_workflow import (
    ProfileReviewError,
    build_review_worksheet,
    compile_review,
    promote_reviewed_profiles,
)


def _paths() -> tuple[Path, Path]:
    return Path("config/canonical_horror_profiles_v1.json"), Path("config/trait_registry_v1.json")


def _approve_all(path: Path) -> None:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    for row in rows:
        row["decision"] = "approve"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_build_compile_and_promote_all_assignments(tmp_path: Path):
    profiles, registry = _paths()
    worksheet = tmp_path / "review.csv"
    decisions = tmp_path / "decisions.json"
    promoted = tmp_path / "reviewed.json"

    report = build_review_worksheet(profiles, worksheet)
    assert report["film_count"] == 9
    assert report["assignment_count"] == 45
    _approve_all(worksheet)

    compiled = compile_review(profiles, worksheet, decisions, reviewer="Daniel")
    assert compiled["approved"] == 45
    result = promote_reviewed_profiles(
        profiles, decisions, registry, promoted, next_version="1.1.0"
    )
    assert result["film_count"] == 9
    raw = json.loads(promoted.read_text(encoding="utf-8"))
    assert all(film["status"] == "reviewed" for film in raw["films"])
    assert all(
        trait["source"] == "human_authored"
        for film in raw["films"]
        for trait in film["traits"]
    )


def test_compile_rejects_incomplete_worksheet(tmp_path: Path):
    profiles, _ = _paths()
    worksheet = tmp_path / "review.csv"
    build_review_worksheet(profiles, worksheet)
    rows = list(csv.DictReader(worksheet.open(encoding="utf-8")))[:-1]
    for row in rows:
        row["decision"] = "approve"
    with worksheet.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ProfileReviewError, match="incomplete"):
        compile_review(profiles, worksheet, tmp_path / "decisions.json", reviewer="Daniel")


def test_edit_requires_values_and_note(tmp_path: Path):
    profiles, _ = _paths()
    worksheet = tmp_path / "review.csv"
    build_review_worksheet(profiles, worksheet)
    rows = list(csv.DictReader(worksheet.open(encoding="utf-8")))
    for row in rows:
        row["decision"] = "approve"
    rows[0]["decision"] = "edit"
    with worksheet.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ProfileReviewError, match="edit requires"):
        compile_review(profiles, worksheet, tmp_path / "decisions.json", reviewer="Daniel")


def test_rejection_removes_only_reviewed_assignment(tmp_path: Path):
    profiles, registry = _paths()
    worksheet = tmp_path / "review.csv"
    decisions = tmp_path / "decisions.json"
    promoted = tmp_path / "reviewed.json"
    build_review_worksheet(profiles, worksheet)
    rows = list(csv.DictReader(worksheet.open(encoding="utf-8")))
    for row in rows:
        row["decision"] = "approve"
    rows[0]["decision"] = "reject"
    rows[0]["review_note"] = "Not sufficiently supported for this film."
    with worksheet.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    compile_review(profiles, worksheet, decisions, reviewer="Daniel")
    result = promote_reviewed_profiles(profiles, decisions, registry, promoted, next_version="1.1.0")
    assert result["assignment_count"] == 44
