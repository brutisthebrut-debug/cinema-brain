from cinema_brain.metadata import FilmLookup
from cinema_brain.providers import TMDBProvider


def test_tmdb_provider_selects_exact_title_and_year_and_maps_details():
    calls = []

    def fake_get(url, headers):
        calls.append((url, headers))
        if "/search/movie" in url:
            return {
                "results": [
                    {"id": 1, "title": "Undertone", "release_date": "2024-01-01", "popularity": 99},
                    {"id": 2, "title": "Undertone", "release_date": "2025-03-13", "popularity": 10},
                ]
            }
        return {
            "id": 2,
            "title": "Undertone",
            "release_date": "2025-03-13",
            "runtime": 98,
            "genres": [{"name": "Horror"}],
            "production_countries": [{"name": "Canada"}],
            "spoken_languages": [{"english_name": "English"}],
            "credits": {
                "crew": [{"job": "Director", "name": "Ian Tuason"}],
                "cast": [{"name": "Actor One"}, {"name": "Actor Two"}],
            },
            "keywords": {"keywords": [{"name": "isolation"}, {"name": "sound recording"}]},
        }

    provider = TMDBProvider("token", get_json=fake_get)
    item = provider.fetch(FilmLookup("title:undertone:2025", "Undertone", 2025))

    assert item is not None
    assert item.film_key == "title:undertone:2025"
    assert item.year == 2025
    assert item.runtime_minutes == 98
    assert item.genres == ("Horror",)
    assert item.directors == ("Ian Tuason",)
    assert item.countries == ("Canada",)
    assert item.keywords == ("isolation", "sound recording")
    assert item.confidence == 1.0
    assert len(calls) == 2
    assert calls[0][1]["Authorization"] == "Bearer token"


def test_tmdb_provider_returns_none_for_no_match():
    provider = TMDBProvider("token", get_json=lambda url, headers: {"results": []})
    assert provider.fetch(FilmLookup("title:missing:2020", "Missing", 2020)) is None


def test_tmdb_provider_requires_token():
    provider = TMDBProvider("", get_json=lambda url, headers: {})
    try:
        provider.fetch(FilmLookup("title:test:2020", "Test", 2020))
    except ValueError as exc:
        assert "token" in str(exc).lower()
    else:
        raise AssertionError("expected missing-token error")
