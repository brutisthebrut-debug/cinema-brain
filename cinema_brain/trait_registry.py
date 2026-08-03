from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

TRAIT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
ALLOWED_KINDS = {"fact", "interpretation", "community_prior", "daniel_evidence", "context"}
ALLOWED_VALUE_TYPES = {"continuous", "binary", "categorical"}
ALLOWED_POLARITIES = {"positive", "negative", "neutral", "contextual"}


class TraitRegistryError(ValueError):
    """Raised when the canonical trait registry violates its contract."""


@dataclass(frozen=True)
class TraitDefinition:
    trait_id: str
    label: str
    family: str
    description: str
    kind: str
    value_type: str
    polarity: str
    aliases: tuple[str, ...] = ()
    antonyms: tuple[str, ...] = ()
    deprecated: bool = False
    replaced_by: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TraitDefinition":
        return cls(
            trait_id=str(raw["id"]),
            label=str(raw["label"]),
            family=str(raw["family"]),
            description=str(raw["description"]),
            kind=str(raw["kind"]),
            value_type=str(raw.get("value_type", "continuous")),
            polarity=str(raw.get("polarity", "neutral")),
            aliases=tuple(str(x) for x in raw.get("aliases", [])),
            antonyms=tuple(str(x) for x in raw.get("antonyms", [])),
            deprecated=bool(raw.get("deprecated", False)),
            replaced_by=str(raw["replaced_by"]) if raw.get("replaced_by") else None,
        )


class CanonicalTraitRegistry:
    def __init__(self, version: str, traits: Iterable[TraitDefinition]) -> None:
        self.version = version
        self._traits = {trait.trait_id: trait for trait in traits}
        self._alias_index: dict[str, set[str]] = {}
        for trait in self._traits.values():
            for alias in (trait.trait_id, trait.label, *trait.aliases):
                normalized = normalize_phrase(alias)
                self._alias_index.setdefault(normalized, set()).add(trait.trait_id)

    @property
    def traits(self) -> tuple[TraitDefinition, ...]:
        return tuple(self._traits[key] for key in sorted(self._traits))

    def get(self, trait_id: str) -> TraitDefinition:
        try:
            return self._traits[trait_id]
        except KeyError as exc:
            raise KeyError(f"unknown canonical trait: {trait_id}") from exc

    def resolve(self, phrase: str) -> tuple[TraitDefinition, ...]:
        ids = sorted(self._alias_index.get(normalize_phrase(phrase), set()))
        return tuple(self._traits[trait_id] for trait_id in ids)

    def family(self, family: str) -> tuple[TraitDefinition, ...]:
        return tuple(trait for trait in self.traits if trait.family == family)

    def to_taxonomy(self) -> dict[str, Any]:
        families: dict[str, list[str]] = {}
        aliases: dict[str, list[str]] = {}
        for trait in self.traits:
            if trait.deprecated:
                continue
            families.setdefault(trait.family, []).append(trait.trait_id)
            for alias in trait.aliases:
                aliases.setdefault(alias, []).append(trait.trait_id)
        return {"version": self.version, "families": families, "aliases": aliases}


def normalize_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def load_trait_registry(path: Path) -> CanonicalTraitRegistry:
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_trait_registry(raw)
    if errors:
        raise TraitRegistryError("invalid trait registry:\n- " + "\n- ".join(errors))
    return CanonicalTraitRegistry(
        version=str(raw["version"]),
        traits=(TraitDefinition.from_dict(item) for item in raw["traits"]),
    )


def validate_trait_registry(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["registry root must be an object"]
    if not str(raw.get("version", "")).strip():
        errors.append("version is required")
    traits = raw.get("traits")
    if not isinstance(traits, list) or not traits:
        errors.append("traits must be a non-empty list")
        return errors

    ids: set[str] = set()
    aliases: dict[str, set[str]] = {}
    for index, item in enumerate(traits):
        prefix = f"traits[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        trait_id = str(item.get("id", ""))
        if not TRAIT_ID_PATTERN.fullmatch(trait_id):
            errors.append(f"{prefix}.id must be snake_case: {trait_id!r}")
        if trait_id in ids:
            errors.append(f"duplicate trait id: {trait_id}")
        ids.add(trait_id)
        for field in ("label", "family", "description", "kind"):
            if not str(item.get(field, "")).strip():
                errors.append(f"{prefix}.{field} is required")
        if item.get("kind") not in ALLOWED_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(ALLOWED_KINDS)}")
        if item.get("value_type", "continuous") not in ALLOWED_VALUE_TYPES:
            errors.append(f"{prefix}.value_type must be one of {sorted(ALLOWED_VALUE_TYPES)}")
        if item.get("polarity", "neutral") not in ALLOWED_POLARITIES:
            errors.append(f"{prefix}.polarity must be one of {sorted(ALLOWED_POLARITIES)}")
        if item.get("deprecated") and not item.get("replaced_by"):
            errors.append(f"{prefix}.replaced_by is required when deprecated is true")
        for alias in item.get("aliases", []):
            normalized = normalize_phrase(str(alias))
            if not normalized:
                errors.append(f"{prefix}.aliases cannot contain blank values")
                continue
            aliases.setdefault(normalized, set()).add(trait_id)

    for item in traits:
        replacement = item.get("replaced_by") if isinstance(item, dict) else None
        if replacement and replacement not in ids:
            errors.append(f"replacement trait does not exist: {replacement}")

    for alias, trait_ids in aliases.items():
        if len(trait_ids) > 1:
            errors.append(f"ambiguous alias {alias!r} maps to {sorted(trait_ids)}")
    return errors


def registry_report(path: Path) -> dict[str, Any]:
    registry = load_trait_registry(path)
    families: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for trait in registry.traits:
        families[trait.family] = families.get(trait.family, 0) + 1
        kinds[trait.kind] = kinds.get(trait.kind, 0) + 1
    return {
        "valid": True,
        "version": registry.version,
        "trait_count": len(registry.traits),
        "family_counts": dict(sorted(families.items())),
        "kind_counts": dict(sorted(kinds.items())),
        "deprecated_count": sum(trait.deprecated for trait in registry.traits),
    }
