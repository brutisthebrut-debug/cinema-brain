from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .metadata import FilmMetadata


@dataclass(frozen=True)
class GoldenRecord:
    film_key: str
    canonical_title: str
    release_year: int
    accepted_titles: tuple[str, ...]
    entity_type: str
    hazards: tuple[str, ...]
    expected_traits: tuple[str, ...]
    reviewed: bool


@dataclass(frozen=True)
class IdentityEvaluation:
    film_key: str
    status: str
    title_match: bool
    year_match: bool
    reviewed: bool
    provider_title: str
    provider_year: int | None
    explanation: str

    @property
    def passes(self) -> bool:
        return self.title_match and self.year_match


def _normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def load_golden_dataset(path: Path) -> tuple[str, tuple[GoldenRecord, ...]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    version = str(payload.get("version", "")).strip()
    if not version:
        raise ValueError("golden dataset version is required")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("golden dataset records must be a non-empty list")

    records: list[GoldenRecord] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_records):
        if not isinstance(raw, dict):
            raise ValueError(f"record {index} must be an object")
        film_key = str(raw.get("film_key", "")).strip()
        title = str(raw.get("canonical_title", "")).strip()
        year = raw.get("release_year")
        entity_type = str(raw.get("entity_type", "")).strip()
        if not film_key or not title or not isinstance(year, int) or not entity_type:
            raise ValueError(f"record {index} is missing required identity fields")
        if film_key in seen:
            raise ValueError(f"duplicate golden film_key: {film_key}")
        if not 1870 <= year <= 2200:
            raise ValueError(f"invalid release year for {film_key}: {year}")
        seen.add(film_key)
        records.append(
            GoldenRecord(
                film_key=film_key,
                canonical_title=title,
                release_year=year,
                accepted_titles=tuple(str(v).strip() for v in raw.get("accepted_titles", []) if str(v).strip()),
                entity_type=entity_type,
                hazards=tuple(str(v).strip() for v in raw.get("hazards", []) if str(v).strip()),
                expected_traits=tuple(str(v).strip().lower() for v in raw.get("expected_traits", []) if str(v).strip()),
                reviewed=bool(raw.get("reviewed", False)),
            )
        )
    return version, tuple(records)


def evaluate_identity(record: GoldenRecord, metadata: FilmMetadata) -> IdentityEvaluation:
    accepted = {_normalize_title(record.canonical_title), *(_normalize_title(v) for v in record.accepted_titles)}
    provider_title = _normalize_title(metadata.title)
    title_match = provider_title in accepted
    year_match = metadata.year == record.release_year

    if title_match and year_match:
        status = "exact"
        explanation = "Provider title is canonical or an accepted alias and release year matches."
    elif title_match:
        status = "year_mismatch"
        explanation = f"Accepted title matched, but expected {record.release_year} and received {metadata.year}."
    elif year_match:
        status = "title_mismatch"
        explanation = "Release year matched, but provider title was not canonical or an accepted alias."
    else:
        status = "identity_mismatch"
        explanation = "Neither accepted title nor release year matched the reviewed identity."

    return IdentityEvaluation(
        film_key=record.film_key,
        status=status,
        title_match=title_match,
        year_match=year_match,
        reviewed=record.reviewed,
        provider_title=metadata.title,
        provider_year=metadata.year,
        explanation=explanation,
    )


def summarize_gate(evaluations: tuple[IdentityEvaluation, ...]) -> dict:
    reviewed = tuple(item for item in evaluations if item.reviewed)
    failures = tuple(item for item in reviewed if not item.passes)
    return {
        "evaluated": len(evaluations),
        "reviewed": len(reviewed),
        "seed_only": len(evaluations) - len(reviewed),
        "reviewed_failures": len(failures),
        "passes_release_gate": bool(reviewed) and not failures,
        "failure_keys": [item.film_key for item in failures],
    }
