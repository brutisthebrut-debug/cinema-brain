import json
from pathlib import Path

from cinema_brain.golden_dataset import evaluate_identity, load_golden_dataset, summarize_gate
from cinema_brain.metadata import FilmMetadata


def _metadata(title: str, year: int) -> FilmMetadata:
    return FilmMetadata(
        film_key="title:rec:2007",
        title=title,
        year=year,
        provider="wikidata",
        confidence=0.9,
        retrieved_at="2026-08-02T12:00:00+00:00",
    )


def test_seed_dataset_loads_and_contains_undertone():
    version, records = load_golden_dataset(Path("config/golden_horror_v1.json"))
    assert version == "horror-identity-v1"
    assert len(records) == 10
    assert any(record.canonical_title == "Undertone" for record in records)
    assert all(not record.reviewed for record in records)


def test_punctuation_alias_matches_rec():
    _, records = load_golden_dataset(Path("config/golden_horror_v1.json"))
    record = next(item for item in records if item.canonical_title == "[REC]")
    result = evaluate_identity(record, _metadata("REC", 2007))
    assert result.passes
    assert result.status == "exact"


def test_same_title_wrong_year_is_rejected():
    _, records = load_golden_dataset(Path("config/golden_horror_v1.json"))
    record = next(item for item in records if item.canonical_title == "The Thing")
    metadata = FilmMetadata(
        film_key=record.film_key,
        title="The Thing",
        year=2011,
        provider="wikidata",
        confidence=0.95,
        retrieved_at="2026-08-02T12:00:00+00:00",
    )
    result = evaluate_identity(record, metadata)
    assert not result.passes
    assert result.status == "year_mismatch"


def test_seed_records_do_not_pretend_to_pass_release_gate():
    _, records = load_golden_dataset(Path("config/golden_horror_v1.json"))
    evaluations = tuple(evaluate_identity(record, FilmMetadata(
        film_key=record.film_key,
        title=record.canonical_title,
        year=record.release_year,
        provider="fixture",
        confidence=1.0,
        retrieved_at="2026-08-02T12:00:00+00:00",
    )) for record in records)
    summary = summarize_gate(evaluations)
    assert summary["reviewed"] == 0
    assert summary["seed_only"] == 10
    assert summary["passes_release_gate"] is False


def test_duplicate_keys_are_rejected(tmp_path: Path):
    path = tmp_path / "bad.json"
    record = {
        "film_key": "title:test:2000",
        "canonical_title": "Test",
        "release_year": 2000,
        "entity_type": "film"
    }
    path.write_text(json.dumps({"version": "v1", "records": [record, record]}), encoding="utf-8")
    try:
        load_golden_dataset(path)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("expected duplicate validation failure")
