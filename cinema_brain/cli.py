from __future__ import annotations
import argparse
import json
from pathlib import Path

from .ingest import ingest
from .validate import validate
from .report import build_report
from .recommend import recommend
from .taste import build_taste_profile


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cinema-brain")
    p.add_argument("--db", default="cinema_brain.db")
    sub = p.add_subparsers(dest="command", required=True)

    i = sub.add_parser("ingest")
    i.add_argument("--data-dir", "--raw-dir", dest="data_dir", default="data")

    sub.add_parser("validate")

    r = sub.add_parser("report")
    r.add_argument("--output", default="reports/baseline_analysis.md")

    taste = sub.add_parser("taste")
    taste.add_argument("--taxonomy", default="config/traits.json")
    taste.add_argument("--output", default="profiles/taste_profile.json")

    rec = sub.add_parser("recommend")
    rec.add_argument("--limit", type=int, default=10)
    rec.add_argument("--min-rating", type=float, default=0.0)
    rec.add_argument("--genre", help="Reserved for future metadata enrichment.")
    return p


def main() -> int:
    args = parser().parse_args()
    db = Path(args.db)
    if args.command == "ingest":
        print(json.dumps(ingest(Path(args.data_dir), db), indent=2))
        return 0
    if args.command == "validate":
        errors, warnings = validate(db)
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
        return 1 if errors else 0
    if args.command == "report":
        print(build_report(db, Path(args.output)))
        return 0
    if args.command == "taste":
        profile = build_taste_profile(db, Path(args.taxonomy), Path(args.output))
        print(json.dumps(profile, indent=2, ensure_ascii=False))
        return 0
    if args.command == "recommend":
        print(json.dumps(recommend(db, args.limit, args.min_rating), indent=2))
        return 0
    return 2
