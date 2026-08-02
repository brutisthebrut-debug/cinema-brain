import csv
import json
from pathlib import Path

import pytest

from cinema_brain.golden_review_workflow import build_review_template, compile_review_decisions


def benchmark(path: Path) -> Path:
    path.write_text(json.dumps({
        "version": "v1",
        "records": [{
            "film_key": "title:undertone:2025",
            "canonical_title": "Undertone",
            "release_year": 2025,
            "accepted_titles": [],
            "entity_type": "film",
            "hazards": ["recent obscure title"],
            "expected_traits": ["psychological"],
            "reviewed": False,
        }],
    }), encoding="utf-8")
    return path


def sample(path: Path) -> Path:
    path.write_text(json.dumps({
        "films": [{
            "film_key": "title:undertone:2025",
            "provider_title": "Undertone",
            "provider_year": 2025,
            "provider": "wikidata",
            "confidence": 0.95,
            "identity_exact": True,
        }],
    }), encoding="utf-8")
    return path


def test_template_to_approved_packet(tmp_path: Path):
    bench = benchmark(tmp_path / "golden.json")
    template = tmp_path / "review.csv"
    build_review_template(bench, sample(tmp_path / "sample.json"), template)
    rows = list(csv.DictReader(template.open(encoding="utf-8")))
    rows[0]["decision"] = "approved"
    rows[0]["reason"] = "Verified title and year."
    with template.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    output = tmp_path / "decisions.json"
    summary = compile_review_decisions(bench, template, output, reviewer="Daniel")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert summary["approved"] == 1
    assert payload["benchmark_version"] == "v1"
    assert payload["decisions"][0]["identity_status"] == "exact"


def test_mismatch_cannot_be_approved(tmp_path: Path):
    bench = benchmark(tmp_path / "golden.json")
    template = tmp_path / "review.csv"
    build_review_template(bench, sample(tmp_path / "sample.json"), template)
    rows = list(csv.DictReader(template.open(encoding="utf-8")))
    rows[0]["provider_year"] = "2024"
    rows[0]["decision"] = "approved"
    rows[0]["reason"] = "Incorrect approval."
    with template.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    with pytest.raises(ValueError, match="only exact identity matches"):
        compile_review_decisions(bench, template, tmp_path / "out.json", reviewer="Daniel")


def test_reason_is_required(tmp_path: Path):
    bench = benchmark(tmp_path / "golden.json")
    template = tmp_path / "review.csv"
    build_review_template(bench, sample(tmp_path / "sample.json"), template)
    rows = list(csv.DictReader(template.open(encoding="utf-8")))
    rows[0]["decision"] = "quarantined"
    with template.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    with pytest.raises(ValueError, match="requires a review reason"):
        compile_review_decisions(bench, template, tmp_path / "out.json", reviewer="Daniel")
