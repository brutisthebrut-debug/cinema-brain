from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


MANUAL_WATCH_HEADERS = (
    "Date",
    "Name",
    "Year",
    "Letterboxd URI",
    "Rating",
    "Rewatch",
    "Tags",
    "Watched Date",
    "Source",
)


class OutcomeMemoryPromotionError(ValueError):
    """Raised when an outcome cannot safely become canonical watched memory."""


def _require_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise OutcomeMemoryPromotionError(f"{field} is required")
    return value.strip()


def _parse_watched_date(value: str, timezone_name: str) -> str:
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise OutcomeMemoryPromotionError(
            f"unknown IANA timezone: {timezone_name}"
        ) from error
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise OutcomeMemoryPromotionError("watched_at must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise OutcomeMemoryPromotionError("watched_at must include a timezone offset")
    return timestamp.astimezone(timezone).date().isoformat()


def _verified_watch(outcome: dict[str, Any], timezone_name: str) -> dict[str, Any]:
    if not isinstance(outcome, dict):
        raise OutcomeMemoryPromotionError("outcome must be a JSON object")

    outcome_type = outcome.get("outcome_type")
    outcome_id = _require_text(outcome, "outcome_id")
    provenance = outcome.get("provenance")
    if not isinstance(provenance, dict) or provenance.get(
        "prediction_frozen_before_outcome"
    ) is not True:
        raise OutcomeMemoryPromotionError(
            "outcome must prove the prediction was frozen before the watch"
        )

    if outcome_type == "verified_manual_recommendation_outcome":
        binding = outcome.get("binding")
        if not isinstance(binding, dict) or binding.get("status") != (
            "verified_legacy_frozen_prediction"
        ):
            raise OutcomeMemoryPromotionError("manual outcome binding is not verified")
        prediction = outcome.get("prediction")
        actual = outcome.get("actual")
        rating_field = "rating"
    elif outcome_type == "post_watch_recommendation_outcome":
        if not isinstance(outcome.get("release_id"), str) or not outcome["release_id"]:
            raise OutcomeMemoryPromotionError("release-bound outcome is missing release_id")
        prediction = outcome.get("prediction")
        actual = outcome.get("actual")
        rating_field = "rating"
    else:
        raise OutcomeMemoryPromotionError(
            "outcome_type must be verified_manual_recommendation_outcome or "
            "post_watch_recommendation_outcome"
        )

    if not isinstance(prediction, dict) or not isinstance(actual, dict):
        raise OutcomeMemoryPromotionError("outcome prediction and actual are required")
    if actual.get("completed") is not True:
        raise OutcomeMemoryPromotionError(
            "only completed outcomes may become a canonical manual watch"
        )

    film_key = _require_text(prediction, "film_key")
    title = _require_text(prediction, "title")
    year = prediction.get("year")
    if not isinstance(year, int) or isinstance(year, bool):
        raise OutcomeMemoryPromotionError("prediction.year must be an integer")
    rating = actual.get(rating_field)
    if not isinstance(rating, (int, float)) or isinstance(rating, bool):
        raise OutcomeMemoryPromotionError("actual.rating must be numeric")
    if not 0.5 <= float(rating) <= 5.0:
        raise OutcomeMemoryPromotionError("actual.rating must be between 0.5 and 5.0")

    watched_at = _require_text(actual, "watched_at") if outcome_type.startswith(
        "verified_manual"
    ) else _require_text(outcome, "watched_at")
    return {
        "outcome_id": outcome_id,
        "film_key": film_key,
        "title": title,
        "year": year,
        "rating": float(rating),
        "watched_date": _parse_watched_date(watched_at, timezone_name),
        "source": f"outcome:{outcome_id}",
    }


def promote_outcome_watch(
    outcome: dict[str, Any],
    manual_watches_path: Path,
    *,
    timezone_name: str,
) -> dict[str, Any]:
    """Append one verified completed outcome to canonical manual watch memory."""
    watch = _verified_watch(outcome, timezone_name)
    if not manual_watches_path.exists():
        raise OutcomeMemoryPromotionError("manual watches CSV does not exist")

    with manual_watches_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        rows = list(reader)
    if headers != MANUAL_WATCH_HEADERS:
        raise OutcomeMemoryPromotionError(
            "manual watches CSV headers do not match the canonical contract"
        )

    duplicate = next(
        (
            row
            for row in rows
            if row.get("Name") == watch["title"]
            and row.get("Year") == str(watch["year"])
            and row.get("Watched Date") == watch["watched_date"]
        ),
        None,
    )
    if duplicate is not None:
        return {**watch, "status": "already_present", "row_count": len(rows)}

    row = {
        "Date": watch["watched_date"],
        "Name": watch["title"],
        "Year": str(watch["year"]),
        "Letterboxd URI": "",
        "Rating": f"{watch['rating']:g}",
        "Rewatch": "No",
        "Tags": "",
        "Watched Date": watch["watched_date"],
        "Source": watch["source"],
    }
    with manual_watches_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANUAL_WATCH_HEADERS)
        writer.writerow(row)
    return {**watch, "status": "appended", "row_count": len(rows) + 1}


def promote_outcome_watch_file(
    outcome_path: Path,
    manual_watches_path: Path,
    *,
    timezone_name: str,
) -> dict[str, Any]:
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    return promote_outcome_watch(
        outcome,
        manual_watches_path,
        timezone_name=timezone_name,
    )
