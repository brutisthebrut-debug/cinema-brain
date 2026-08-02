import pytest

from cinema_brain.evidence import Evidence, EvidenceGraph, TraitRegistry


def registry():
    r = TraitRegistry()
    r.register("creeping dread", ["slow unease", "sustained dread"])
    r.register("jump scares", ["jump scare"])
    return r


def item(*, trait="creeping dread", weight=1.0, confidence=1.0, polarity=1, ref="undertone"):
    return Evidence(
        subject_key="daniel",
        trait=trait,
        weight=weight,
        confidence=confidence,
        polarity=polarity,
        source_type="manual_reaction",
        source_ref=ref,
        model_version="evidence-1.0.0",
        observed_at="2026-08-02T02:00:00-04:00",
    )


def test_aliases_normalize_to_one_trait():
    graph = EvidenceGraph(registry())
    graph.add(item(trait="slow unease"))
    assert graph.items("daniel", "creeping dread")[0].trait == "creeping dread"


def test_aggregate_preserves_conflict():
    graph = EvidenceGraph(registry())
    graph.add(item(weight=0.9, confidence=0.9, ref="undertone"))
    graph.add(item(weight=0.6, confidence=0.8, polarity=-1, ref="example-failure"))
    result = graph.aggregate("daniel", "creeping dread")
    assert result.score == pytest.approx(0.33)
    assert result.positive_count == 1
    assert result.negative_count == 1
    assert result.conflict is not None
    assert result.confidence < 0.8


def test_duplicate_provenance_is_rejected():
    graph = EvidenceGraph(registry())
    evidence = item()
    graph.add(evidence)
    with pytest.raises(ValueError, match="duplicate evidence"):
        graph.add(evidence)


def test_unknown_traits_fail_loudly():
    graph = EvidenceGraph(registry())
    with pytest.raises(KeyError, match="unknown trait"):
        graph.add(item(trait="mystery soup"))
