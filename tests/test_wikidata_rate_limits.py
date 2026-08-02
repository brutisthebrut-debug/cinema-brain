from __future__ import annotations

from urllib.error import HTTPError

import pytest

from cinema_brain.wikidata_provider import WikidataProvider


def test_provider_honors_retry_after_header(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    def requester(url: str) -> dict:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise HTTPError(url, 429, "rate limited", {"Retry-After": "3"}, None)
        return {"ok": True}

    monkeypatch.setattr("cinema_brain.wikidata_provider.time.sleep", sleeps.append)
    provider = WikidataProvider(
        requester=requester,
        retries=1,
        retry_delay=0.25,
        min_request_interval=0,
    )

    assert provider._request({"action": "test"}) == {"ok": True}
    assert calls == 2
    assert sleeps == [3.0]


def test_provider_paces_successive_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    moments = iter([10.0, 10.1, 10.1, 10.5])
    sleeps: list[float] = []

    monkeypatch.setattr("cinema_brain.wikidata_provider.time.monotonic", lambda: next(moments))
    monkeypatch.setattr("cinema_brain.wikidata_provider.time.sleep", sleeps.append)

    provider = WikidataProvider(
        requester=lambda url: {"ok": True},
        min_request_interval=0.4,
    )
    assert provider._request({"action": "first"}) == {"ok": True}
    assert provider._request({"action": "second"}) == {"ok": True}
    assert sleeps == [pytest.approx(0.3)]
