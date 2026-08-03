from __future__ import annotations

import json
from pathlib import Path

from cinema_brain.production_balanced_slate import (
    build_production_balanced_slate,
    build_production_balanced_slate_file,
)


def _film(key: str, title: str, score: float, confidence: float, traits: list[str]) -> dict:
    return {
        "film_key": key,
        "title": title,
        "taste_score": score,
        "confidence": confidence,
        "traits": traits,
    }


def test_build_production_balanced_slate_preserves_audit_views() -> None:
    ranking = {
        "version": "0.3.0",
        "model_version": "model-v1",
        "taste_model_version": "taste-v1",
        "corpus_version": "corpus-v1",
        "recommendations": [
            _film("a", "A", 0.95, 0.8, ["dread", "isolation"]),
            _film("b", "B", 0.94, 0.8, ["dread", "isolation"]),
            _film("c", "C", 0.90, 0.4, ["practical_effects", "body_horror"]),
        ],
        "abstentions": [{"film_key": "x"}],
        "watched_exclusions": [{"film_key": "w"}],
    }

    result = build_production_balanced_slate(ranking, slate_size=2)

    assert result["raw_recommendations"] == ranking["recommendations"]
    assert len(result["balanced_slate"]) == 2
    assert result["balanced_slate"][0]["film_key"] == "a"
    assert result["balanced_slate"][1]["film_key"] == "c"
    assert result["balanced_slate"][1]["slate_role"] == "discovery"
    assert result["abstentions"] == ranking["abstentions"]
    assert result["watched_exclusions"] == ranking["watched_exclusions"]
    assert result["slate_metrics"]["discovery_count"] == 1


def test_build_production_balanced_slate_file_writes_json(tmp_path: Path) -> None:
    ranking_path = tmp_path / "ranking.json"
    output_path = tmp_path / "balanced.json"
    ranking_path.write_text(
        json.dumps(
            {
                "version": "0.3.0",
                "recommendations": [
                    _film("a", "A", 0.9, 0.7, ["dread"]),
                    _film("b", "B", 0.8, 0.3, ["practical_effects"]),
                ],
                "abstentions": [],
                "watched_exclusions": [],
            }
        ),
        encoding="utf-8",
    )

    result = build_production_balanced_slate_file(ranking_path, output_path, slate_size=2)

    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == result
