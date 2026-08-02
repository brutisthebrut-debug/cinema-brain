from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .golden_dataset import GoldenRecord, IdentityEvaluation

ReviewStatus = Literal["approved", "rejected", "quarantined"]


@dataclass(frozen=True)
class GoldenReviewDecision:
    film_key: str
    status: ReviewStatus
    reviewer: str
    reviewed_at: str
    reason: str
    expected_title: str
    expected_year: int
    provider_title: str
    provider_year: int | None
    identity_status: str

    def validate(self) -> None:
        if not self.film_key.strip():
            raise ValueError("film_key is required")
        if self.status not in {"approved", "rejected", "quarantined"}:
            raise ValueError(f"invalid review status: {self.status}")
        if not self.reviewer.strip():
            raise ValueError("reviewer is required")
        if not self.reason.strip():
            raise ValueError("review reason is required")
        if self.status == "approved" and self.identity_status != "exact":
            raise ValueError("only exact identity matches may be approved")


def decide_review(
    record: GoldenRecord,
    evaluation: IdentityEvaluation,
    *,
    status: ReviewStatus,
    reviewer: str,
    reason: str,
    reviewed_at: str | None = None,
) -> GoldenReviewDecision:
    if record.film_key != evaluation.film_key:
        raise ValueError("record and evaluation film_key mismatch")
    decision = GoldenReviewDecision(
        film_key=record.film_key,
        status=status,
        reviewer=reviewer,
        reviewed_at=reviewed_at or datetime.now(timezone.utc).isoformat(),
        reason=reason,
        expected_title=record.canonical_title,
        expected_year=record.release_year,
        provider_title=evaluation.provider_title,
        provider_year=evaluation.provider_year,
        identity_status=evaluation.status,
    )
    decision.validate()
    return decision


def write_review_decisions(
    decisions: tuple[GoldenReviewDecision, ...],
    output: Path,
    *,
    benchmark_version: str,
) -> Path:
    seen: set[str] = set()
    for decision in decisions:
        decision.validate()
        if decision.film_key in seen:
            raise ValueError(f"duplicate review decision: {decision.film_key}")
        seen.add(decision.film_key)
    payload = {
        "benchmark_version": benchmark_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decisions": [asdict(item) for item in decisions],
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def summarize_review_decisions(decisions: tuple[GoldenReviewDecision, ...]) -> dict:
    counts = {"approved": 0, "rejected": 0, "quarantined": 0}
    for decision in decisions:
        decision.validate()
        counts[decision.status] += 1
    return {
        "total": len(decisions),
        **counts,
        "ready_for_promotion": bool(decisions) and counts["rejected"] == 0 and counts["quarantined"] == 0,
    }
