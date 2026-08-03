from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cinema_brain.diversity_aware_ranking import build_diverse_slate


def build_production_balanced_slate(
    ranking: dict[str, Any],
    *,
    slate_size: int = 5,
) -> dict[str, Any]:
    """Build an auditable production artifact with raw and balanced recommendation views."""
    slate = build_diverse_slate(ranking, slate_size=slate_size)
    return {
        "version": "0.3.0",
        "source_ranking_version": ranking.get("version"),
        "model_version": ranking.get("model_version"),
        "taste_model_version": ranking.get("taste_model_version"),
        "corpus_version": ranking.get("corpus_version"),
        "raw_recommendations": ranking.get("recommendations", []),
        "balanced_slate": slate["slate"],
        "slate_metrics": slate["slate_metrics"],
        "raw_top": slate["raw_top"],
        "abstentions": ranking.get("abstentions", []),
        "watched_exclusions": ranking.get("watched_exclusions", []),
    }


def build_production_balanced_slate_file(
    ranking_path: Path,
    output_path: Path,
    *,
    slate_size: int = 5,
) -> dict[str, Any]:
    ranking = json.loads(ranking_path.read_text(encoding="utf-8"))
    result = build_production_balanced_slate(ranking, slate_size=slate_size)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result
