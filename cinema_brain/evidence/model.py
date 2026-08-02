from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class Evidence:
    subject_key: str
    trait: str
    weight: float
    confidence: float
    source_type: str
    source_ref: str
    model_version: str
    observed_at: str
    polarity: int = 1
    note: str = ""

    def validate(self) -> None:
        if not self.subject_key or not self.trait:
            raise ValueError("subject_key and trait are required")
        if not -1.0 <= self.weight <= 1.0:
            raise ValueError("weight must be between -1 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.polarity not in (-1, 1):
            raise ValueError("polarity must be -1 or 1")
        if not self.source_type or not self.source_ref or not self.model_version:
            raise ValueError("source and model version are required")

    @property
    def signed_strength(self) -> float:
        return self.weight * self.confidence * self.polarity


@dataclass(frozen=True)
class EvidenceConflict:
    subject_key: str
    trait: str
    positive_strength: float
    negative_strength: float
    evidence_count: int


@dataclass(frozen=True)
class EvidenceAggregate:
    subject_key: str
    trait: str
    score: float
    confidence: float
    evidence_count: int
    positive_count: int
    negative_count: int
    strongest_sources: tuple[str, ...] = ()
    conflict: EvidenceConflict | None = None


@dataclass
class TraitRegistry:
    aliases: dict[str, str] = field(default_factory=dict)
    canonical_traits: set[str] = field(default_factory=set)

    def register(self, canonical: str, aliases: Iterable[str] = ()) -> None:
        canonical = canonical.strip().lower()
        if not canonical:
            raise ValueError("canonical trait is required")
        self.canonical_traits.add(canonical)
        self.aliases[canonical] = canonical
        for alias in aliases:
            alias = alias.strip().lower()
            if alias:
                existing = self.aliases.get(alias)
                if existing and existing != canonical:
                    raise ValueError(f"alias collision: {alias}")
                self.aliases[alias] = canonical

    def resolve(self, trait: str) -> str:
        key = trait.strip().lower()
        if key not in self.aliases:
            raise KeyError(f"unknown trait: {trait}")
        return self.aliases[key]


class EvidenceGraph:
    def __init__(self, registry: TraitRegistry):
        self.registry = registry
        self._items: list[Evidence] = []
        self._dedupe: set[tuple[str, str, str, str, str]] = set()

    def add(self, evidence: Evidence) -> None:
        evidence.validate()
        canonical = self.registry.resolve(evidence.trait)
        normalized = Evidence(
            subject_key=evidence.subject_key,
            trait=canonical,
            weight=evidence.weight,
            confidence=evidence.confidence,
            source_type=evidence.source_type,
            source_ref=evidence.source_ref,
            model_version=evidence.model_version,
            observed_at=evidence.observed_at,
            polarity=evidence.polarity,
            note=evidence.note,
        )
        identity = (
            normalized.subject_key,
            normalized.trait,
            normalized.source_type,
            normalized.source_ref,
            normalized.model_version,
        )
        if identity in self._dedupe:
            raise ValueError("duplicate evidence identity")
        self._dedupe.add(identity)
        self._items.append(normalized)

    def items(self, subject_key: str | None = None, trait: str | None = None) -> tuple[Evidence, ...]:
        canonical = self.registry.resolve(trait) if trait else None
        return tuple(
            item for item in self._items
            if (subject_key is None or item.subject_key == subject_key)
            and (canonical is None or item.trait == canonical)
        )

    def aggregate(self, subject_key: str, trait: str) -> EvidenceAggregate:
        canonical = self.registry.resolve(trait)
        items = self.items(subject_key, canonical)
        if not items:
            return EvidenceAggregate(subject_key, canonical, 0.0, 0.0, 0, 0, 0)

        positive = [i for i in items if i.signed_strength > 0]
        negative = [i for i in items if i.signed_strength < 0]
        positive_strength = sum(i.signed_strength for i in positive)
        negative_strength = abs(sum(i.signed_strength for i in negative))
        total = sum(i.signed_strength for i in items)
        denominator = sum(abs(i.signed_strength) for i in items) or 1.0
        agreement = abs(total) / denominator
        volume = min(len(items) / 6.0, 1.0)
        confidence = round(min(0.98, 0.25 + 0.45 * agreement + 0.28 * volume), 3)
        conflict = None
        if positive and negative:
            conflict = EvidenceConflict(
                subject_key=subject_key,
                trait=canonical,
                positive_strength=round(positive_strength, 4),
                negative_strength=round(negative_strength, 4),
                evidence_count=len(items),
            )
        strongest = tuple(
            i.source_ref for i in sorted(items, key=lambda x: abs(x.signed_strength), reverse=True)[:5]
        )
        return EvidenceAggregate(
            subject_key=subject_key,
            trait=canonical,
            score=round(total, 4),
            confidence=confidence,
            evidence_count=len(items),
            positive_count=len(positive),
            negative_count=len(negative),
            strongest_sources=strongest,
            conflict=conflict,
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
