import csv
from pathlib import Path

from cinema_brain.cli import main, parser


def test_profile_review_commands_are_registered():
    commands = parser()._subparsers._group_actions[0].choices
    assert "profile-review-template" in commands
    assert "profile-review-compile" in commands
    assert "profile-review-promote" in commands


def test_profile_review_template_cli_generates_real_candidate_shape(tmp_path: Path, monkeypatch):
    output = tmp_path / "review.csv"
    monkeypatch.setattr(
        "sys.argv",
        [
            "cinema-brain",
            "profile-review-template",
            "--profiles",
            "config/canonical_horror_profiles_v1.json",
            "--output",
            str(output),
        ],
    )
    assert main() == 0
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 45
    assert len({row["film_key"] for row in rows}) == 9
    assert all(row["decision"] == "" for row in rows)
