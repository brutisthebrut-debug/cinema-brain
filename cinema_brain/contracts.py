from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


Polarity = Literal[-1, 0, 1]


@dataclass(frozen=True)
class ModelVersions:
    schema: str = "schema-0.1.0"
    importer: str = "importer-0.2.0"
    identity: str = "identity-0.2.0"
    taxonomy: str = "taxonomy-0.1.0"
    taste: str = "taste-0.2.0"
    request_parser: str = "request-0.1.0"
    ranker: str = "ranker-0.1.0"
    explanation: str = "explanation-0.1.0"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class TraitEvidence:
    film_key: str
    trait: str
    polarity: Polarity
    strength: float
    source_type: str
    source_text: str | None = None
    confidence: float = 1.0
    source_reference: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    model_version: str = "taste-0.2.0"

    def __post_init__(self) -> None:
        if self.polarity not in (-1, 0, 1):
            raise ValueError("polarity must be -1, 0, or 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.strength < 0:
            raise ValueError("strength must be non-negative; polarity stores direction")

    @property
    def signed_strength(self) -> float:
        return round(self.polarity * self.strength * self.confidence, 4)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["signed_strength"] = self.signed_strength
        return result


@dataclass(frozen=True)
class WatchRequest:
    genres: tuple[str, ...] = ()
    moods: tuple[str, ...] = ()
    desired_destination: tuple[str, ...] = ()
    max_runtime_minutes: int | None = None
    active_services: tuple[str, ...] = ()
    location: str = "US"
    exclude_watched: bool = True
    allow_rewatch: bool = False
    subtitles_ok: bool | None = None
    gore_tolerance: str | None = None
    ambiguity_tolerance: str | None = None
    attention: str | None = None
    company: str | None = None
    novelty: str = "new"

    def __post_init__(self) -> None:
        if self.max_runtime_minutes is not None and self.max_runtime_minutes <= 0:
            raise ValueError("max_runtime_minutes must be positive")
        if self.exclude_watched and self.allow_rewatch:
            raise ValueError("exclude_watched and allow_rewatch cannot both be true")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreComponents:
    taste_fit: float
    mood_fit: float
    context_fit: float
    novelty: float
    quality_floor: float
    watchlist_intent: float = 0.0
    underexplored_bonus: float = 0.0
    risk_penalty: float = 0.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if name == "risk_penalty":
                if not 0 <= value <= 1:
                    raise ValueError(f"{name} must be between 0 and 1")
            elif not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")

    def weighted_total(self) -> float:
        total = (
            self.taste_fit * 0.35
            + self.mood_fit * 0.20
            + self.context_fit * 0.15
            + self.novelty * 0.08
            + self.quality_floor * 0.10
            + self.watchlist_intent * 0.07
            + self.underexplored_bonus * 0.05
            - self.risk_penalty * 0.15
        )
        return round(max(0.0, min(1.0, total)), 4)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["weighted_total"] = self.weighted_total()
        return result


@dataclass(frozen=True)
class AvailabilityEvidence:
    service: str
    region: str
    verified_at: str
    source: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class RecommendationResult:
    film_key: str
    name: str
    year: int | None
    predicted_rating: float
    confidence: float
    score_components: ScoreComponents
    evidence: tuple[dict[str, Any], ...]
    caveat: str
    availability: AvailabilityEvidence | None
    versions: ModelVersions = field(default_factory=ModelVersions)

    def __post_init__(self) -> None:
        if not 0.5 <= self.predicted_rating <= 5.0:
            raise ValueError("predicted_rating must be between 0.5 and 5.0")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.caveat.strip():
            raise ValueError("every recommendation must include a meaningful caveat")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["score_components"] = self.score_components.to_dict()
        result["versions"] = self.versions.to_dict()
        return result
