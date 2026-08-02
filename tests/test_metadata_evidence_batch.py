from pathlib import Path

from cinema_brain.db import connect, init_schema
from cinema_brain.metadata import FilmMetadata
from cinema_brain.metadata_store import MetadataStore
from cinema_brain.metadata_evidence import MODEL_VERSION
from cinema_brain.metadata_evidence_batch import extract_and_persist_metadata_evidence
from cinema_brain.evidence import EvidenceStore


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "brain.db"
    conn = connect(path)
    init_schema(conn)
    conn.execute(
        "INSERT INTO films (film_key, title, year, last_watched) VALUES (?, ?, ?, ?)",
        ("undertone-2025", "Undertone", 2025, "2026-08-01"),
    )
    conn.commit()
    conn.close()
    return path


def test_batch_persists_and_replays_idempotently(tmp_path: Path):
    db = _db(tmp_path)
    MetadataStore(db).save(FilmMetadata(
        film_key="undertone-2025",
        title="Undertone",
        year=2025,
        provider="wikidata",
        confidence=0.9,
        genres=("psychological horror",),
        keywords=("found footage", "unknown label"),
        retrieved_at="2026-08-02T12:00:00+00:00",
    ))

    first = extract_and_persist_metadata_evidence(db, film_keys=["undertone-2025"])
    assert first.processed == 1
    assert first.inserted == 4
    assert first.duplicates == 0
    assert first.unmatched_labels == ("unknown label",)
    assert EvidenceStore(db).count(MODEL_VERSION) == 4

    second = extract_and_persist_metadata_evidence(db, film_keys=["undertone-2025"])
    assert second.inserted == 0
    assert second.duplicates == 4
    assert EvidenceStore(db).count(MODEL_VERSION) == 4


def test_batch_rejects_nonpositive_limit(tmp_path: Path):
    db = _db(tmp_path)
    try:
        extract_and_persist_metadata_evidence(db, limit=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
