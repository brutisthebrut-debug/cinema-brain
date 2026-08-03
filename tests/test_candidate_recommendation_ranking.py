from __future__ import annotations

import sqlite3
from pathlib import Path

from cinema_brain.candidate_recommendation_ranking import (
    load_watched_film_keys,
    rank_eligible_candidates,
)


def _graph() -> dict:
    return {
        "model_version": "test-graph",
        "traits": {
            "creeping_dread": {"affinity": 0.9, "confidence": 0.9, "status": "stable"},
            "isolation": {"affinity": 0.8, "confidence": 0.8, "status": "stable"},
            "practical_effects": {"affinity": 0.7, "confidence": 0.9, "status": "explicit"},
        },
    }


def _corpus() -> dict:
    def trait(trait_id: str, value: float = 0.9) -> dict:
        return {"trait_id": trait_id, "value": value, "confidence": 0.9, "rationale": "test"}

    return {
        "version": "test-corpus",
        "registry_version": "test-registry",
        "films": [
            {
                "film_key": "title:watched-film:2020",
                "title": "Watched Film",
                "year": 2020,
                "traits": [trait("creeping_dread"), trait("isolation")],
            },
            {
                "film_key": "title:strong-film:2021",
                "title": "Strong Film",
                "year": 2021,
                "traits": [trait("creeping_dread"), trait("isolation"), trait("practical_effects")],
            },
            {
                "film_key": "title:sparse-film:2022",
                "title": "Sparse Film",
                "year": 2022,
                "traits": [trait("unknown_one"), trait("unknown_two"), trait("creeping_dread")],
            },
        ],
    }


def test_filters_watched_and_abstains_on_sparse_evidence() -> None:
    result = rank_eligible_candidates(
        _corpus(),
        _graph(),
        watched_film_keys={"title:watched-film:2020"},
    )

    assert result["candidate_count"] == 3
    assert result["watched_excluded_count"] == 1
    assert result["eligible_count"] == 2
    assert [film["title"] for film in result["recommendations"]] == ["Strong Film"]
    assert result["recommendations"][0]["recommendation_rank"] == 1
    assert result["abstentions"][0]["title"] == "Sparse Film"
    assert "too_few_active_traits" in result["abstentions"][0]["abstention_reasons"]


def test_load_watched_film_keys_from_canonical_database(tmp_path: Path) -> None:
    db_path = tmp_path / "cinema.db"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE films (name TEXT, year INTEGER, watched INTEGER)")
    connection.executemany(
        "INSERT INTO films VALUES (?, ?, ?)",
        [("The Empty Man", 2020, 1), ("Unwatched", 2021, 0)],
    )
    connection.commit()
    connection.close()

    assert load_watched_film_keys(db_path) == {"title:the-empty-man:2020"}
