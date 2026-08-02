from cinema_brain.metadata import FilmLookup, FilmMetadata, MetadataCache, fetch_with_cache

class FakeProvider:
    name = "fake"
    def __init__(self):
        self.calls = 0
    def fetch(self, lookup):
        self.calls += 1
        return FilmMetadata(
            film_key=lookup.film_key,
            title=lookup.title,
            year=lookup.year,
            provider=self.name,
            genres=("Horror",),
            directors=("Example Director",),
            runtime_minutes=98,
            keywords=("creeping dread",),
        )

def test_metadata_cache_is_stable(tmp_path):
    cache = MetadataCache(tmp_path / "cache")
    provider = FakeProvider()
    lookup = FilmLookup("title:vicious:2025", "Vicious", 2025)
    first, first_source = fetch_with_cache(provider, lookup, cache)
    second, second_source = fetch_with_cache(provider, lookup, cache)
    assert first_source == "provider"
    assert second_source == "cache"
    assert provider.calls == 1
    assert first == second

def test_metadata_rejects_bad_runtime():
    item = FilmMetadata("x", "Bad", 2025, "fake", runtime_minutes=0)
    try:
        item.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid runtime was accepted")

def test_provider_cannot_return_wrong_film(tmp_path):
    class WrongProvider:
        name = "wrong"
        def fetch(self, lookup):
            return FilmMetadata("different", "Different", 2024, "wrong")
    try:
        fetch_with_cache(WrongProvider(), FilmLookup("expected", "Expected", 2025), MetadataCache(tmp_path))
    except ValueError:
        pass
    else:
        raise AssertionError("identity mismatch was accepted")
