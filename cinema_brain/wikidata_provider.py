from __future__ import annotations

import gzip
import json
import re
import time
import zlib
from dataclasses import replace
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .metadata import FilmLookup, FilmMetadata

ACTION_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "CinemaBrain/0.1 (private personal movie intelligence; contact via GitHub brutisthebrut-debug/cinema-brain)"
FILM_TYPES = {"Q11424", "Q202866", "Q24869", "Q29168811"}


def _normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _decode_response_body(body: bytes, content_encoding: str = "") -> str:
    """Decode HTTP response bytes, including compressed payloads."""
    encoding = content_encoding.casefold().strip()
    if encoding == "gzip" or body.startswith(b"\x1f\x8b"):
        body = gzip.decompress(body)
    elif encoding == "deflate":
        try:
            body = zlib.decompress(body)
        except zlib.error:
            body = zlib.decompress(body, -zlib.MAX_WBITS)
    return body.decode("utf-8")


def _json_request(url: str, *, timeout: float = 15.0) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    with urlopen(request, timeout=timeout) as response:  # nosec: B310 - fixed Wikimedia endpoint
        body = response.read()
        headers = getattr(response, "headers", None)
        content_encoding = headers.get("Content-Encoding", "") if headers is not None else ""
        return json.loads(_decode_response_body(body, content_encoding))


def _claim_entity_ids(entity: dict, property_id: str) -> list[str]:
    values: list[str] = []
    for claim in entity.get("claims", {}).get(property_id, []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, dict) and value.get("entity-type") == "item" and value.get("id"):
            values.append(str(value["id"]))
    return values


def _claim_years(entity: dict) -> list[int]:
    years: list[int] = []
    for claim in entity.get("claims", {}).get("P577", []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not isinstance(value, dict):
            continue
        match = re.match(r"^[+-](\d{4,})-", str(value.get("time", "")))
        if match:
            years.append(int(match.group(1)))
    return years


def _runtime_minutes(entity: dict) -> int | None:
    for claim in entity.get("claims", {}).get("P2047", []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not isinstance(value, dict):
            continue
        try:
            amount = float(str(value["amount"]).lstrip("+"))
        except (KeyError, TypeError, ValueError):
            continue
        unit = str(value.get("unit", ""))
        if unit.endswith("/Q7727") or unit == "1":
            return max(1, round(amount))
        if unit.endswith("/Q11574"):
            return max(1, round(amount / 60))
        if unit.endswith("/Q25235"):
            return max(1, round(amount * 60))
    return None


def _labels(payload: dict, entity_ids: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    entities = payload.get("entities", {})
    for entity_id in entity_ids:
        entity = entities.get(entity_id, {})
        labels = entity.get("labels", {})
        label = labels.get("en", {}).get("value")
        if label:
            result[entity_id] = str(label)
    return result


class WikidataProvider:
    """Read-only CC0 film metadata provider backed by Wikidata's Action API."""

    name = "wikidata"

    def __init__(
        self,
        *,
        requester: Callable[[str], dict] = _json_request,
        retries: int = 2,
        retry_delay: float = 0.5,
    ):
        self.requester = requester
        self.retries = max(0, retries)
        self.retry_delay = max(0.0, retry_delay)

    def _request(self, params: dict[str, str]) -> dict:
        url = f"{ACTION_API}?{urlencode(params)}"
        for attempt in range(self.retries + 1):
            try:
                return self.requester(url)
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt >= self.retries:
                    raise
            except URLError:
                if attempt >= self.retries:
                    raise
            time.sleep(self.retry_delay * (2**attempt))
        raise RuntimeError("unreachable")

    def _search_query(self, query: str) -> list[dict]:
        payload = self._request(
            {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "type": "item",
                "limit": "20",
                "format": "json",
                "maxlag": "5",
            }
        )
        return list(payload.get("search", []))

    def _search(self, lookup: FilmLookup) -> list[dict]:
        """Search narrowly first, then broaden without weakening local validation."""
        queries = []
        if lookup.year is not None:
            queries.append(f"{lookup.title} {lookup.year}")
        queries.append(lookup.title)

        results: list[dict] = []
        seen: set[str] = set()
        for query in queries:
            for item in self._search_query(query):
                entity_id = str(item.get("id", ""))
                if entity_id and entity_id not in seen:
                    seen.add(entity_id)
                    results.append(item)
        return results

    def _entities(self, entity_ids: list[str]) -> dict:
        if not entity_ids:
            return {"entities": {}}
        return self._request(
            {
                "action": "wbgetentities",
                "ids": "|".join(entity_ids),
                "props": "labels|claims",
                "languages": "en",
                "languagefallback": "1",
                "format": "json",
                "maxlag": "5",
            }
        )

    def _select(self, lookup: FilmLookup, search: list[dict]) -> tuple[dict, float] | None:
        candidate_ids = [str(item.get("id")) for item in search if item.get("id")]
        payload = self._entities(candidate_ids)
        best: tuple[dict, float] | None = None
        expected = _normalize_title(lookup.title)
        for entity_id in candidate_ids:
            entity = payload.get("entities", {}).get(entity_id, {})
            label = entity.get("labels", {}).get("en", {}).get("value", "")
            title_similarity = SequenceMatcher(None, expected, _normalize_title(str(label))).ratio()
            years = _claim_years(entity)
            year_match = lookup.year is None or lookup.year in years
            types = set(_claim_entity_ids(entity, "P31"))
            film_type = bool(types & FILM_TYPES)
            if title_similarity < 0.88 or not year_match or not film_type:
                continue
            confidence = 0.72 + (0.18 * title_similarity) + (0.08 if year_match else 0) + (0.02 if film_type else 0)
            confidence = min(1.0, confidence)
            if best is None or confidence > best[1]:
                best = (entity, confidence)
        return best

    def fetch(self, lookup: FilmLookup) -> FilmMetadata | None:
        selected = self._select(lookup, self._search(lookup))
        if selected is None:
            return None
        entity, confidence = selected

        properties = {
            "genres": "P136",
            "directors": "P57",
            "cast": "P161",
            "countries": "P495",
            "languages": "P364",
            "keywords": "P921",
        }
        ids_by_field = {name: _claim_entity_ids(entity, prop) for name, prop in properties.items()}
        all_ids = list(dict.fromkeys(entity_id for ids in ids_by_field.values() for entity_id in ids))
        label_map = _labels(self._entities(all_ids), all_ids)

        years = _claim_years(entity)
        item = FilmMetadata(
            film_key=lookup.film_key,
            title=str(entity.get("labels", {}).get("en", {}).get("value", lookup.title)),
            year=lookup.year if lookup.year in years else (years[0] if years else lookup.year),
            provider=self.name,
            confidence=round(confidence, 4),
            genres=tuple(label_map[item] for item in ids_by_field["genres"] if item in label_map),
            directors=tuple(label_map[item] for item in ids_by_field["directors"] if item in label_map),
            cast=tuple(label_map[item] for item in ids_by_field["cast"][:20] if item in label_map),
            countries=tuple(label_map[item] for item in ids_by_field["countries"] if item in label_map),
            languages=tuple(label_map[item] for item in ids_by_field["languages"] if item in label_map),
            runtime_minutes=_runtime_minutes(entity),
            keywords=tuple(label_map[item] for item in ids_by_field["keywords"] if item in label_map),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
        item.validate()
        return item
