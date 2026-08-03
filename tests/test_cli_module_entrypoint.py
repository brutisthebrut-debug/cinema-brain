import csv
import subprocess
import sys
from pathlib import Path


def test_python_m_cli_executes_and_writes_review_template(tmp_path: Path):
    output = tmp_path / "review.csv"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cinema_brain.cli",
            "profile-review-template",
            "--profiles",
            "config/canonical_horror_profiles_v1.json",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 45
    assert len({row["film_key"] for row in rows}) == 9
