from __future__ import annotations

import sqlite3
from pathlib import Path

from .model import Evidence, EvidenceGraph, TraitRegistry


class EvidenceStore:
    """Durable SQLite adapter for the canonical Evidence Graph."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def save(self, evidence: Evidence, registry: TraitRegistry) -> bool:
        evidence.validate()
        trait = registry.resolve(evidence.trait)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO trait_evidence
                (film_key, trait_id, polarity, strength, confidence, source_type,
                 source_ref, evidence_text, model_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.subject_key,
                    trait,
                    float(evidence.polarity),
                    abs(float(evidence.weight)),
                    float(evidence.confidence),
                    evidence.source_type,
                    evidence.source_ref,
                    evidence.note,
                    evidence.model_version,
                    evidence.observed_at,
                ),
            )
            conn.commit()
            return cursor.rowcount == 1
        finally:
            conn.close()

    def load_graph(
        self,
        registry: TraitRegistry,
        subject_key: str | None = None,
        model_version: str | None = None,
    ) -> EvidenceGraph:
        graph = EvidenceGraph(registry)
        clauses: list[str] = []
        params: list[str] = []
        if subject_key is not None:
            clauses.append("film_key=?")
            params.append(subject_key)
        if model_version is not None:
            clauses.append("model_version=?")
            params.append(model_version)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT film_key, trait_id, polarity, strength, confidence,
                       source_type, source_ref, evidence_text, model_version, created_at
                FROM trait_evidence
                """ + where + " ORDER BY id",
                params,
            ).fetchall()
        finally:
            conn.close()

        for row in rows:
            graph.add(
                Evidence(
                    subject_key=row["film_key"],
                    trait=row["trait_id"],
                    weight=float(row["strength"]),
                    confidence=float(row["confidence"]),
                    source_type=row["source_type"],
                    source_ref=row["source_ref"],
                    model_version=row["model_version"],
                    observed_at=row["created_at"],
                    polarity=1 if float(row["polarity"]) >= 0 else -1,
                    note=row["evidence_text"] or "",
                )
            )
        return graph

    def count(self, model_version: str | None = None) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            if model_version is None:
                return int(conn.execute("SELECT COUNT(*) FROM trait_evidence").fetchone()[0])
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM trait_evidence WHERE model_version=?",
                    (model_version,),
                ).fetchone()[0]
            )
        finally:
            conn.close()
