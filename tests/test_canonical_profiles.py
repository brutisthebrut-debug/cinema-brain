import json
from pathlib import Path

import pytest

from cinema_brain.canonical_profiles import CanonicalProfileError, load_profiles, profile_report
from cinema_brain.trait_registry import load_trait_registry


REGISTRY = Path("config/trait_registry_v1.json")
PROFILES = Path("config/canonical_horror_profiles_v1.json")


def test_seed_profiles_validate_against_registry():
    profiles = load_profiles(PROFILES, REGISTRY)
    assert len(profiles) == 9
    assert all(profile.status == "candidate_review" for profile in profiles)
    assert all(profile.registry_version == "1.0.0" for profile in profiles)
    assert sum(len(profile.assignments) for profile in profiles) == 45


def test_profile_report_exposes_review_boundary():
    report = profile_report(PROFILES, REGISTRY)
    assert report == {
        "valid": True,
        "profile_version": "1.0.0-candidate",
        "registry_version": "1.0.0",
        "film_count": 9,
        "reviewed_count": 0,
        "candidate_count": 9,
        "assignment_count": 45,
    }


def test_unknown_trait_is_rejected(tmp_path: Path):
    raw = json.loads(PROFILES.read_text(encoding="utf-8"))
    raw["films"][0]["traits"][0]["trait_id"] = "made_up_trait"
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(CanonicalProfileError, match="unknown"):
        load_profiles(broken, REGISTRY)


def test_duplicate_film_identity_is_rejected(tmp_path: Path):
    raw = json.loads(PROFILES.read_text(encoding="utf-8"))
    raw["films"].append(raw["films"][0])
    broken = tmp_path / "duplicate.json"
    broken.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(CanonicalProfileError, match="duplicate film_key"):
        load_profiles(broken, REGISTRY)


def test_every_assignment_resolves_to_canonical_definition():
    registry = load_trait_registry(REGISTRY)
    for profile in load_profiles(PROFILES, REGISTRY):
        for assignment in profile.assignments:
            assert registry.get(assignment.trait_id).trait_id == assignment.trait_id
