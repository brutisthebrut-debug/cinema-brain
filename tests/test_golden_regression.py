import json
from pathlib import Path

from cinema_brain.golden_regression import evaluate_reviewed_benchmark


def write_benchmark(path: Path, *, reviewed: bool = True) -> None:
    path.write_text(json.dumps({
        "version": "horror-v2",
        "records": [{
            "film_key": "title:rec:2007",
            "canonical_title": "[REC]",
            "release_year": 2007,
            "accepted_titles": ["REC"],
            "entity_type": "film",
            "hazards": ["punctuation"],
            "expected_traits": ["found footage", "isolation"],
            "reviewed": reviewed,
        }],
    }), encoding="utf-8")


def write_sample(path: Path, *, title: str = "REC", year: int = 2007, keywords=None) -> None:
    path.write_text(json.dumps({
        "films": [{
            "film_key": "title:rec:2007",
            "provider_title": title,
            "provider_year": year,
            "genres": ["horror"],
            "keywords": keywords or ["found footage", "isolation"],
        }],
    }), encoding="utf-8")


def test_reviewed_alias_and_traits_pass(tmp_path: Path):
    benchmark = tmp_path / "benchmark.json"
    sample = tmp_path / "sample.json"
    write_benchmark(benchmark)
    write_sample(sample)
    report = evaluate_reviewed_benchmark(benchmark, sample)
    assert report["passes"] is True
    assert report["failed_records"] == 0


def test_identity_regression_fails(tmp_path: Path):
    benchmark = tmp_path / "benchmark.json"
    sample = tmp_path / "sample.json"
    write_benchmark(benchmark)
    write_sample(sample, year=2008)
    report = evaluate_reviewed_benchmark(benchmark, sample)
    assert report["passes"] is False
    assert report["results"][0]["identity_pass"] is False


def test_trait_regression_fails_with_missing_traits(tmp_path: Path):
    benchmark = tmp_path / "benchmark.json"
    sample = tmp_path / "sample.json"
    write_benchmark(benchmark)
    write_sample(sample, keywords=["found footage"])
    report = evaluate_reviewed_benchmark(benchmark, sample)
    assert report["passes"] is False
    assert report["results"][0]["missing_traits"] == ["isolation"]


def test_unreviewed_seed_is_not_treated_as_truth(tmp_path: Path):
    benchmark = tmp_path / "benchmark.json"
    sample = tmp_path / "sample.json"
    write_benchmark(benchmark, reviewed=False)
    write_sample(sample)
    report = evaluate_reviewed_benchmark(benchmark, sample)
    assert report["reviewed_records"] == 0
    assert report["passes"] is False
