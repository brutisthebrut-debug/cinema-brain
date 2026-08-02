from __future__ import annotations

from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from cinema_brain.metadata import FilmLookup
from cinema_brain.wikidata_provider import USER_AGENT, WikidataProvider, _json_request


def _entity(title: str, year: int, *, entity_id: str = "Q1") -> dict:
    return {
        "id": entity_id,
        "labels": {"en": {"language": "en", "value": title}},
        "claims": {
            "P31": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "Q11424"}}}}],
            "P577": [{"mainsnak": {"datavalue": {"value": {"time": f"+{year:04d}-01-01T00:00:00Z"}}}}],
            "P136": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "Q200092"}}}}],
            "P57": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "QDIRECTOR"}}}}],
            "P161": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "QACTOR"}}}}],
            "P495": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "Q30"}}}}],
            "P364": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "Q1860"}}}}],
            "P921": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "QFEAR"}}}}],
            "P2047": [{"mainsnak": {"datavalue": {"value": {"amount": "+95", "unit": "http://www.wikidata.org/entity/Q7727"}}}}],
        },
    }


def test_provider_maps_exact_title_and_year() -> None:
    film = _entity("Undertone", 2025)
    labels = {
        "Q200092": "horror film",
        "QDIRECTOR": "Ian Tuason",
        "QACTOR": "Nina Kiri",
        "Q30": "United States of America",
        "Q1860": "English",
        "QFEAR": "fear",
    }

    def requester(url: str) -> dict:
        params = parse_qs(urlparse(url).query)
        action = params["action"][0]
        if action == "wbsearchentities":
            return {"search": [{"id": "Q1", "label": "Undertone"}]}
        ids = params["ids"][0].split("|")
        if ids == ["Q1"]:
            return {"entities": {"Q1": film}}
        return {"entities": {entity_id: {"labels": {"en": {"value": labels[entity_id]}}} for entity_id in ids}}

    item = WikidataProvider(requester=requester).fetch(FilmLookup("undertone-2025", "Undertone", 2025))
    assert item is not None
    assert item.film_key == "undertone-2025"
    assert item.year == 2025
    assert item.genres == ("horror film",)
    assert item.directors == ("Ian Tuason",)
    assert item.cast == ("Nina Kiri",)
    assert item.countries == ("United States of America",)
    assert item.languages == ("English",)
    assert item.runtime_minutes == 95
    assert item.keywords == ("fear",)
    assert item.confidence >= 0.98


def test_provider_falls_back_to_title_only_search() -> None:
    film = _entity("The Thing", 1982)
    searches = []

    def requester(url: str) -> dict:
        params = parse_qs(urlparse(url).query)
        if params["action"][0] == "wbsearchentities":
            query = params["search"][0]
            searches.append(query)
            return {"search": [] if query.endswith("1982") else [{"id": "Q1", "label": "The Thing"}]}
        ids = params["ids"][0].split("|")
        if ids == ["Q1"]:
            return {"entities": {"Q1": film}}
        return {"entities": {}}

    item = WikidataProvider(requester=requester).fetch(FilmLookup("the-thing-1982", "The Thing", 1982))
    assert item is not None
    assert searches == ["The Thing 1982", "The Thing"]


def test_provider_rejects_same_title_wrong_year() -> None:
    wrong = _entity("The Thing", 2011)

    def requester(url: str) -> dict:
        params = parse_qs(urlparse(url).query)
        if params["action"][0] == "wbsearchentities":
            return {"search": [{"id": "Q1", "label": "The Thing"}]}
        return {"entities": {"Q1": wrong}}

    item = WikidataProvider(requester=requester).fetch(FilmLookup("the-thing-1982", "The Thing", 1982))
    assert item is None


def test_provider_rejects_nonfilm_entity() -> None:
    entity = _entity("Us", 2019)
    entity["claims"]["P31"][0]["mainsnak"]["datavalue"]["value"]["id"] = "Q5"

    def requester(url: str) -> dict:
        params = parse_qs(urlparse(url).query)
        if params["action"][0] == "wbsearchentities":
            return {"search": [{"id": "Q1", "label": "Us"}]}
        return {"entities": {"Q1": entity}}

    assert WikidataProvider(requester=requester).fetch(FilmLookup("us-2019", "Us", 2019)) is None


def test_provider_retries_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def requester(url: str) -> dict:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HTTPError(url, 429, "rate limited", {}, None)
        return {"search": []}

    monkeypatch.setattr("cinema_brain.wikidata_provider.time.sleep", lambda _: None)
    assert WikidataProvider(requester=requester, retries=1).fetch(FilmLookup("x", "X", 2000)) is None
    assert calls == 3


def test_default_requester_declares_project_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        captured["user_agent"] = request.get_header("User-agent")
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("cinema_brain.wikidata_provider.urlopen", fake_urlopen)
    assert _json_request("https://www.wikidata.org/w/api.php") == {}
    assert captured["user_agent"] == USER_AGENT
    assert captured["timeout"] == 15.0
