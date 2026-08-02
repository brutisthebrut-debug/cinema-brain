import sqlite3
from pathlib import Path

from cinema_brain.evidence import Evidence, EvidenceStore, TraitRegistry
from cinema_brain.schema import SCHEMA_SQL


def _db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT INTO films(film_key, name, year, watched) VALUES (?, ?, ?, 1)",
        ("title:undertone:2025", "Undertone", 2025),
    )
    conn.commit()
    conn.close()


def test_evidence_store_round_trip_and_deduplication(tmp_path):
    db = tmp_path / "cinema.db"
    _db(db)
    registry = TraitRegistry()
    registry.register("creeping dread", aliases=("slow dread",))
    store = EvidenceStore(db)
    item = Evidence(
        subject_key="title:undertone:2025",
        trait="slow dread",
        weight=0.9,
        confidence=0.95,
        source_type="manual_reaction",
        source_ref="undertone-2026-08-02",
        model_version="evidence-1.0.0",
        observed_at="2026-08-02T02:00:00-04:00",
        polarity=1,
        note="Blair Witch-like creeping unease",
    )

    assert store.save(item, registry) is True
    assert store.save(item, registry) is False
    assert store.count("evidence-1.0.0") == 1

    graph = store.load_graph(registry, subject_key="title:undertone:2025")
    loaded = graph.items("title:undertone:2025", "creeping dread")
    assert len(loaded) == 1
    assert loaded[0].trait == "creeping dread"
    assert loaded[0].note == "Blair Witch-like creeping unease"
    aggregate = graph.aggregate("title:undertone:2025", "creeping dread")
    assert aggregate.score > 0
    assert aggregate.evidence_count == 1
