from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class FilmLookup:
    film_key: str
    title: str
    year: int | None = None


@dataclass(frozen=True)
class FilmMetadata:
    film_key: str
    title: str
    year: int | None
    provider: str
    confidence: float = 1.0
    genres: tuple[str, ...] = ()
    directors: tuple[str, ...] = ()
    cast: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    runtime_minutes: int | None = None
    keywords: tuple[str, ...] = ()
    retrieved_at: str = ""

    def validate(self) -> None:
        if not self.film_key or not self.title or not self.provider:
            raise ValueError("film_key, title, and provider are required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.runtime_minutes is not None and self.runtime_minutes <= 0:
            raise ValueError("runtime must be positive")


class MetadataProvider(Protocol):
    name: str

    def fetch(self, lookup: FilmLookup) -> FilmMetadata | None: ...


class MetadataCache:
    def __init__(self, root: Path):
        self.root = root

    def _path(self, provider: str, film_key: str) -> Path:
        digest = hashlib.sha256(film_key.encode()).hexdigest()
        return self.root / provider / digest[:2] / f"{digest}.json"

    def _quarantine(self, path: Path) -> None:
        """Move an unreadable cache entry aside so the provider can refetch it."""
        quarantine = path.with_suffix(path.suffix + ".corrupt")
        counter = 1
        while quarantine.exists():
            quarantine = path.with_suffix(path.suffix + f".corrupt.{counter}")
            counter += 1
        path.replace(quarantine)

    def get(self, provider: str, film_key: str) -> FilmMetadata | None:
        path = self._path(provider, film_key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for key in ("genres", "directors", "cast", "countries", "languages", "keywords"):
                data[key] = tuple(data.get(key, ()))
            item = FilmMetadata(**data)
            item.validate()
            return item
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError, KeyError):
            self._quarantine(path)
            return None

    def put(self, item: FilmMetadata) -> FilmMetadata:
        item.validate()
        canonical = item
        if not canonical.retrieved_at:
            canonical = replace(
                canonical,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
        path = self._path(canonical.provider, canonical.film_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(canonical), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return canonical


def fetch_with_cache(
    provider: MetadataProvider,
    lookup: FilmLookup,
    cache: MetadataCache,
    refresh: bool = False,
):
    if not refresh:
        cached = cache.get(provider.name, lookup.film_key)
        if cached:
            return cached, "cache"

    fetched = provider.fetch(lookup)
    if fetched is None:
        return None, "miss"
    if fetched.film_key != lookup.film_key or fetched.provider != provider.name:
        raise ValueError("metadata identity mismatch")

    canonical = cache.put(fetched)
    return canonical, "provider"
