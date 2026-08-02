from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from cinema_brain.metadata import FilmLookup, FilmMetadata


JsonGetter = Callable[[str, dict[str, str]], dict[str, Any]]


def _default_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:  # nosec B310 - fixed HTTPS host
        return json.loads(response.read().decode("utf-8"))


@dataclass
class TMDBProvider:
    """TMDB v3 adapter with dependency injection for deterministic tests.

    The provider performs a title/year search, selects a guarded best match,
    then fetches details and credits. Network access is never required by unit
    tests; callers may inject get_json.
    """

    api_token: str
    get_json: JsonGetter = _default_get_json
    name: str = "tmdb"
    base_url: str = "https://api.themoviedb.org/3"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_token.strip():
            raise ValueError("TMDB API token is required")
        query = urllib.parse.urlencode(params or {})
        url = f"{self.base_url}{path}" + (f"?{query}" if query else "")
        return self.get_json(
            url,
            {
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "User-Agent": "cinema-brain/1.0",
            },
        )

    @staticmethod
    def _year(value: str | None) -> int | None:
        if not value or len(value) < 4:
            return None
        try:
            return int(value[:4])
        except ValueError:
            return None

    def _select_match(self, lookup: FilmLookup, results: list[dict[str, Any]]) -> dict[str, Any] | None:
        wanted = lookup.title.casefold().strip()
        exact = [item for item in results if str(item.get("title", "")).casefold().strip() == wanted]
        candidates = exact or results
        if lookup.year is not None:
            year_matches = [item for item in candidates if self._year(item.get("release_date")) == lookup.year]
            if year_matches:
                candidates = year_matches
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: float(item.get("popularity") or 0), reverse=True)[0]

    def fetch(self, lookup: FilmLookup) -> FilmMetadata | None:
        search = self._get(
            "/search/movie",
            {"query": lookup.title, "year": lookup.year} if lookup.year else {"query": lookup.title},
        )
        match = self._select_match(lookup, list(search.get("results") or []))
        if match is None or match.get("id") is None:
            return None

        movie_id = int(match["id"])
        details = self._get(f"/movie/{movie_id}", {"append_to_response": "credits,keywords"})
        credits = details.get("credits") or {}
        crew = credits.get("crew") or []
        cast = credits.get("cast") or []
        keywords_node = details.get("keywords") or {}
        keywords = keywords_node.get("keywords") or keywords_node.get("results") or []

        directors = tuple(
            str(person.get("name")) for person in crew
            if person.get("job") == "Director" and person.get("name")
        )
        top_cast = tuple(str(person.get("name")) for person in cast[:12] if person.get("name"))
        genres = tuple(str(item.get("name")) for item in details.get("genres") or [] if item.get("name"))
        countries = tuple(
            str(item.get("name")) for item in details.get("production_countries") or [] if item.get("name")
        )
        languages = tuple(
            str(item.get("english_name") or item.get("name"))
            for item in details.get("spoken_languages") or []
            if item.get("english_name") or item.get("name")
        )
        keyword_names = tuple(str(item.get("name")) for item in keywords if item.get("name"))

        resolved_year = self._year(details.get("release_date")) or lookup.year
        title = str(details.get("title") or lookup.title)
        confidence = 1.0 if title.casefold().strip() == lookup.title.casefold().strip() else 0.82
        if lookup.year is not None and resolved_year != lookup.year:
            confidence = min(confidence, 0.72)

        item = FilmMetadata(
            film_key=lookup.film_key,
            title=title,
            year=resolved_year,
            provider=self.name,
            confidence=confidence,
            genres=genres,
            directors=directors,
            cast=top_cast,
            countries=countries,
            languages=languages,
            runtime_minutes=details.get("runtime"),
            keywords=keyword_names,
        )
        item.validate()
        return item
