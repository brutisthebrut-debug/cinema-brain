import json
from pathlib import Path

import pytest

from cinema_brain.trait_registry import (
    TraitRegistryError,
    load_trait_registry,
    registry_report,
    validate_trait_registry,
)


def test_loads_canonical_registry_and_resolves_aliases():
    registry = load_trait_registry(Path("config/trait_registry_v1.json"))

    assert registry.version == "1.0.0"
    assert len(registry.traits) >= 50
    assert registry.get("creeping_dread").family == "fear_mechanism"
    assert [trait.trait_id for trait in registry.resolve("actually scary")] == ["genuine_fear_response"]
    assert any(trait.trait_id == "slow_burn" for trait in registry.family("pacing"))


def test_registry_converts_to_legacy_taxonomy_contract():
    registry = load_trait_registry(Path("config/trait_registry_v1.json"))
    taxonomy = registry.to_taxonomy()

    assert taxonomy["version"] == "1.0.0"
    assert "creeping_dread" in taxonomy["families"]["fear_mechanism"]
    assert taxonomy["aliases"]["scared me"] == ["genuine_fear_response"]


def test_validation_rejects_duplicate_ids_and_ambiguous_aliases():
    raw = {
        "version": "test",
        "traits": [
            {
                "id": "slow_burn",
                "label": "Slow burn",
                "family": "pacing",
                "description": "Patient pacing.",
                "kind": "interpretation",
                "aliases": ["patient"],
            },
            {
                "id": "slow_burn",
                "label": "Another",
                "family": "pacing",
                "description": "Duplicate.",
                "kind": "interpretation",
                "aliases": ["patient"],
            },
        ],
    }

    errors = validate_trait_registry(raw)
    assert any("duplicate trait id" in error for error in errors)


def test_load_rejects_invalid_registry(tmp_path: Path):
    path = tmp_path / "traits.json"
    path.write_text(json.dumps({"version": "", "traits": []}), encoding="utf-8")

    with pytest.raises(TraitRegistryError):
        load_trait_registry(path)


def test_registry_report_is_stable():
    report = registry_report(Path("config/trait_registry_v1.json"))

    assert report["valid"] is True
    assert report["trait_count"] >= 50
    assert report["family_counts"]["personal_response"] >= 3
    assert report["deprecated_count"] == 0
