from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .evidence import Evidence, EvidenceGraph, TraitRegistry
from .evidence.model import now_iso
from .metadata import FilmMetadata

MODEL_VERSION = "metadata-evidence-1.0.0"

# Deterministic vocabulary bridge. Provider labels remain facts; these mappings create
# explicitly versioned interpretive evidence without pretending the provider asserted it.
LABEL_TO_TRAITS: dict[str, tuple[str, ...]] = {
    "horror film": ("horror",),
    "psychological horror": ("horror", "psychological"),
    "found footage": ("found footage", "naturalistic realism"),
    "folk horror": ("folk horror", "isolation"),
    "supernatural horror": ("supernatural",),
    "body horror": ("body horror",),
    "cosmic horror": ("cosmic horror", "existential dread"),
    "slasher film": ("slasher",),
    "monster film": ("creature feature",),
    "ghost film": ("ghosts", "supernatural"),
    "haunted house film": ("haunted house", "isolation"),
    "survival film": ("survival", "isolation"),
    "thriller film": ("thriller",),
    "psychological thriller": ("psychological", "thriller"),
    "dark comedy": ("dark comedy",),
}


@dataclass(frozen=True)
class ExtractionReport:
    film_key: str
    emitted: int
    unmatched_labels: tuple[str, ...]
    confidence: float


def build_metadata_registry() -> TraitRegistry:
    registry = TraitRegistry()
    traits = sorted({trait for values in LABEL_TO_TRAITS.values() for trait in values})
    for trait in traits:
        registry.register(trait)
    return registry


def _normalized_labels(item: FilmMetadata) -> tuple[str, ...]:
    return tuple(sorted({value.strip().lower() for value in (*item.genres, *item.keywords) if value.strip()}))


def extract_metadata_evidence(
    item: FilmMetadata,
    *,
    observed_at: str | None = None,
    model_version: str = MODEL_VERSION,
) -> tuple[tuple[Evidence, ...], ExtractionReport]:
    item.validate()
    observed = observed_at or item.retrieved_at or now_iso()
    emitted: list[Evidence] = []
    unmatched: list[str] = []
    provider_confidence = max(0.0, min(1.0, item.confidence))

    for label in _normalized_labels(item):
        traits = LABEL_TO_TRAITS.get(label)
        if not traits:
            unmatched.append(label)
            continue
        for trait in traits:
            # Interpretive extraction cannot be more confident than the source fact.
            confidence = round(provider_confidence * 0.8, 4)
            emitted.append(Evidence(
                subject_key=item.film_key,
                trait=trait,
                weight=0.6,
                confidence=confidence,
                source_type="metadata_inference",
                source_ref=f"{item.provider}:{label}",
                model_version=model_version,
                observed_at=observed,
                polarity=1,
                note=f"Derived deterministically from provider label: {label}",
            ))

    return tuple(emitted), ExtractionReport(
        film_key=item.film_key,
        emitted=len(emitted),
        unmatched_labels=tuple(unmatched),
        confidence=provider_confidence,
    )


def add_metadata_evidence(graph: EvidenceGraph, evidence: Iterable[Evidence]) -> int:
    added = 0
    for item in evidence:
        graph.add(item)
        added += 1
    return added
