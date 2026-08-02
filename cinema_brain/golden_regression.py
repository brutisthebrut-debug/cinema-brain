from __future__ import annotations

import json
import re
from pathlib import Path

from .golden_dataset import load_golden_dataset


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def evaluate_reviewed_benchmark(benchmark_path: Path, sample_path: Path) -> dict:
    version, records = load_golden_dataset(benchmark_path)
    sample = json.loads(Path(sample_path).read_text(encoding="utf-8"))
    films = {item["film_key"]: item for item in sample.get("films", [])}

    results = []
    for record in records:
        if not record.reviewed:
            continue
        film = films.get(record.film_key)
        if film is None:
            results.append({
                "film_key": record.film_key,
                "identity_pass": False,
                "traits_pass": False,
                "missing_traits": list(record.expected_traits),
                "error": "reviewed film missing from sample",
            })
            continue

        accepted = {_norm(record.canonical_title), *(_norm(v) for v in record.accepted_titles)}
        provider_title = _norm(str(film.get("provider_title", "")))
        provider_year = film.get("provider_year")
        identity_pass = provider_title in accepted and provider_year == record.release_year

        observed = {
            _norm(str(value))
            for field in ("genres", "keywords", "traits")
            for value in film.get(field, [])
            if str(value).strip()
        }
        missing_traits = [trait for trait in record.expected_traits if _norm(trait) not in observed]
        results.append({
            "film_key": record.film_key,
            "identity_pass": identity_pass,
            "traits_pass": not missing_traits,
            "missing_traits": missing_traits,
            "error": None,
        })

    failures = [item for item in results if not item["identity_pass"] or not item["traits_pass"]]
    return {
        "benchmark_version": version,
        "reviewed_records": len(results),
        "passed_records": len(results) - len(failures),
        "failed_records": len(failures),
        "passes": bool(results) and not failures,
        "results": results,
    }


def write_regression_report(benchmark_path: Path, sample_path: Path, output_path: Path) -> dict:
    report = evaluate_reviewed_benchmark(benchmark_path, sample_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
