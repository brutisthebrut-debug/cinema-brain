from __future__ import annotations

import csv
import json
from pathlib import Path

from .golden_dataset import evaluate_identity, load_golden_dataset
from .golden_review import decide_review, write_review_decisions
from .metadata import FilmMetadata

_ALLOWED = {"approved", "rejected", "quarantined"}


def build_review_template(benchmark_path: Path, sample_path: Path, output_path: Path) -> dict:
    version, records = load_golden_dataset(benchmark_path)
    sample = json.loads(Path(sample_path).read_text(encoding="utf-8"))
    films = {item["film_key"]: item for item in sample.get("films", [])}
    rows = []
    for record in records:
        film = films.get(record.film_key)
        if film is None:
            continue
        rows.append({
            "film_key": record.film_key,
            "canonical_title": record.canonical_title,
            "release_year": record.release_year,
            "provider_title": film["provider_title"],
            "provider_year": film["provider_year"],
            "provider": film["provider"],
            "confidence": film["confidence"],
            "identity_exact": film["identity_exact"],
            "hazards": " | ".join(record.hazards),
            "decision": "",
            "reason": "",
        })
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "film_key", "canonical_title", "release_year", "provider_title",
        "provider_year", "provider", "confidence", "identity_exact",
        "hazards", "decision", "reason",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {"benchmark_version": version, "rows": len(rows), "output": str(output_path)}


def compile_review_decisions(
    benchmark_path: Path,
    template_path: Path,
    output_path: Path,
    *,
    reviewer: str,
) -> dict:
    version, records = load_golden_dataset(benchmark_path)
    by_key = {record.film_key: record for record in records}
    decisions = []
    with Path(template_path).open("r", encoding="utf-8-sig", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=2):
            status = (row.get("decision") or "").strip().lower()
            if not status:
                continue
            if status not in _ALLOWED:
                raise ValueError(f"row {index} has invalid decision: {status}")
            reason = (row.get("reason") or "").strip()
            if not reason:
                raise ValueError(f"row {index} requires a review reason")
            film_key = (row.get("film_key") or "").strip()
            record = by_key.get(film_key)
            if record is None:
                raise ValueError(f"row {index} references unknown film_key: {film_key}")
            provider_year_text = (row.get("provider_year") or "").strip()
            metadata = FilmMetadata(
                film_key=film_key,
                title=(row.get("provider_title") or "").strip(),
                year=int(provider_year_text) if provider_year_text else None,
                provider=(row.get("provider") or "review-template").strip(),
                confidence=float((row.get("confidence") or "0").strip()),
            )
            evaluation = evaluate_identity(record, metadata)
            decisions.append(decide_review(
                record,
                evaluation,
                status=status,
                reviewer=reviewer,
                reason=reason,
            ))
    if not decisions:
        raise ValueError("review template contains no completed decisions")
    write_review_decisions(tuple(decisions), output_path, benchmark_version=version)
    counts = {name: sum(1 for item in decisions if item.status == name) for name in sorted(_ALLOWED)}
    return {"benchmark_version": version, "total": len(decisions), **counts, "output": str(output_path)}
