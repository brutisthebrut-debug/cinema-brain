from cinema_brain.evidence import Evidence, EvidenceGraph
from cinema_brain.metadata import FilmMetadata
from cinema_brain.metadata_evidence import (
    MODEL_VERSION,
    add_metadata_evidence,
    build_metadata_registry,
    extract_metadata_evidence,
)


def metadata(**overrides):
    values = dict(
        film_key="undertone-2025",
        title="Undertone",
        year=2025,
        provider="wikidata",
        confidence=0.9,
        genres=("psychological horror",),
        keywords=("found footage", "unknown label"),
        retrieved_at="2026-08-02T12:00:00+00:00",
    )
    values.update(overrides)
    return FilmMetadata(**values)


def test_extracts_versioned_provenance_aware_traits():
    evidence, report = extract_metadata_evidence(metadata())
    traits = {item.trait for item in evidence}
    assert traits == {"horror", "psychological", "found footage", "naturalistic realism"}
    assert report.emitted == 4
    assert report.unmatched_labels == ("unknown label",)
    assert all(item.model_version == MODEL_VERSION for item in evidence)
    assert all(item.source_type == "metadata_inference" for item in evidence)
    assert all(item.confidence == 0.72 for item in evidence)


def test_confidence_never_exceeds_provider_confidence():
    evidence, _ = extract_metadata_evidence(metadata(confidence=0.25, keywords=()))
    assert evidence
    assert max(item.confidence for item in evidence) <= 0.25


def test_preserves_conflicting_evidence_in_graph():
    registry = build_metadata_registry()
    graph = EvidenceGraph(registry)
    extracted, _ = extract_metadata_evidence(metadata(genres=("psychological horror",), keywords=()))
    add_metadata_evidence(graph, extracted)
    graph.add(Evidence(
        subject_key="undertone-2025",
        trait="psychological",
        weight=0.8,
        confidence=1.0,
        source_type="daniel_reaction",
        source_ref="manual:undertone",
        model_version="manual-1",
        observed_at="2026-08-02T12:00:00+00:00",
        polarity=-1,
    ))
    aggregate = graph.aggregate("undertone-2025", "psychological")
    assert aggregate.conflict is not None
    assert aggregate.positive_count == 1
    assert aggregate.negative_count == 1


def test_extraction_is_deterministic():
    first, first_report = extract_metadata_evidence(metadata())
    second, second_report = extract_metadata_evidence(metadata())
    assert first == second
    assert first_report == second_report
