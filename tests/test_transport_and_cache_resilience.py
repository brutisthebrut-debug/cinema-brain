import gzip
import json
import zlib
from pathlib import Path

from cinema_brain.metadata import FilmLookup, FilmMetadata, MetadataCache, fetch_with_cache
from cinema_brain.wikidata_provider import _decode_response_body


def test_decode_gzip_by_header():
    payload = json.dumps({"ok": True}).encode("utf-8")
    assert json.loads(_decode_response_body(gzip.compress(payload), "gzip")) == {"ok": True}


def test_decode_gzip_by_magic_bytes_without_header():
    payload = json.dumps({"ok": True}).encode("utf-8")
    assert json.loads(_decode_response_body(gzip.compress(payload))) == {"ok": True}


def test_decode_deflate():
    payload = json.dumps({"ok": True}).encode("utf-8")
    assert json.loads(_decode_response_body(zlib.compress(payload), "deflate")) == {"ok": True}


class StubProvider:
    name = "stub"

    def __init__(self):
        self.calls = 0

    def fetch(self, lookup: FilmLookup):
        self.calls += 1
        return FilmMetadata(
            film_key=lookup.film_key,
            title=lookup.title,
            year=lookup.year,
            provider=self.name,
        )


def test_corrupt_cache_is_quarantined_and_refetched(tmp_path: Path):
    cache = MetadataCache(tmp_path / "cache")
    lookup = FilmLookup("film:1", "Example", 2026)
    provider = StubProvider()
    cache_path = cache._path(provider.name, lookup.film_key)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(b"\x1f\x8bnot-json")

    item, source = fetch_with_cache(provider, lookup, cache)

    assert source == "provider"
    assert item is not None
    assert provider.calls == 1
    assert cache_path.exists()
    assert list(cache_path.parent.glob(cache_path.name + ".corrupt*"))


def test_invalid_json_cache_is_quarantined(tmp_path: Path):
    cache = MetadataCache(tmp_path / "cache")
    path = cache._path("stub", "film:2")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken", encoding="utf-8")

    assert cache.get("stub", "film:2") is None
    assert not path.exists()
    assert list(path.parent.glob(path.name + ".corrupt*"))
