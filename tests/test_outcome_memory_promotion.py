from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path

import pytest

from cinema_brain.outcome_memory_promotion import (
    MANUAL_WATCH_HEADERS,
    OutcomeMemoryPromotionError,
    promote_outcome_watch,
)


def _manual_outcome() -> dict:
    return {
        "version": "1.0.0",
        "outcome_type": "verified_manual_recommendation_outcome",
        "outcome_id": "manual-outcome-noroi",
        "binding": {"status": "verified_legacy_frozen_prediction"},
        "prediction": {
            "film_key": "title:noroi-the-curse:2005",
            "title": "Noroi: The Curse",
            "year": 2005,
        },
        "actual": {
            "watched_at": "2026-08-04T01:09:00Z",
            "rating": 3.5,
            "completed": True,
        },
        "provenance": {"prediction_frozen_before_outcome": True},
    }


def _release_outcome() -> dict:
    return {
        "version": "1.0.0",
        "outcome_type": "post_watch_recommendation_outcome",
        "outcome_id": "recommendation-outcome-dark-wicked",
        "release_id": "recommendation-release-example",
        "watched_at": "2026-08-05T03:30:00Z",
        "prediction": {
            "film_key": "title:the-dark-and-the-wicked:2020",
            "title": "The Dark and the Wicked",
            "year": 2020,
        },
        "actual": {"rating": 4.0, "completed": True},
        "provenance": {"prediction_frozen_before_outcome": True},
    }


def _csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANUAL_WATCH_HEADERS)
        writer.writeheader()


def test_promotes_verified_manual_outcome_using_local_watch_date(tmp_path: Path) -> None:
    path = tmp_path / "manual_watches.csv"
    _csv(path)

    result = promote_outcome_watch(
        _manual_outcome(), path, timezone_name="America/New_York"
    )

    assert result["status"] == "appended"
    assert result["watched_date"] == "2026-08-03"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            "Date": "2026-08-03",
            "Name": "Noroi: The Curse",
            "Year": "2005",
            "Letterboxd URI": "",
            "Rating": "3.5",
            "Rewatch": "No",
            "Tags": "",
            "Watched Date": "2026-08-03",
            "Source": "outcome:manual-outcome-noroi",
        }
    ]


def test_promotes_release_bound_outcome_and_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "manual_watches.csv"
    _csv(path)
    outcome = _release_outcome()

    first = promote_outcome_watch(outcome, path, timezone_name="America/New_York")
    second = promote_outcome_watch(outcome, path, timezone_name="America/New_York")

    assert first["status"] == "appended"
    assert second["status"] == "already_present"
    assert second["row_count"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["binding"].update(status="unverified"),
        lambda payload: payload["actual"].update(completed=False),
        lambda payload: payload["provenance"].update(
            prediction_frozen_before_outcome=False
        ),
    ],
)
def test_rejects_unverified_or_incomplete_manual_outcome(
    tmp_path: Path, mutation
) -> None:
    path = tmp_path / "manual_watches.csv"
    _csv(path)
    outcome = deepcopy(_manual_outcome())
    mutation(outcome)

    with pytest.raises(OutcomeMemoryPromotionError):
        promote_outcome_watch(outcome, path, timezone_name="America/New_York")
