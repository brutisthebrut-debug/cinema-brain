from __future__ import annotations
import argparse
import json
from pathlib import Path

from .ingest import ingest
from .validate import validate
from .report import build_report
from .recommend import recommend
from .taste import build_taste_profile
from .rss_sync import sync_rss, write_report
from .metadata_enrichment import enrich_films, write_enrichment_report
from .metadata_evidence_batch import extract_and_persist_metadata_evidence, write_batch_report
from .sample_review import build_sample_review
from .wikidata_provider import WikidataProvider


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cinema-brain")
    p.add_argument("--db", default="cinema_brain.db")
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("ingest"); i.add_argument("--data-dir", "--raw-dir", dest="data_dir", default="data")
    sub.add_parser("validate")
    r = sub.add_parser("report"); r.add_argument("--output", default="reports/baseline_analysis.md")
    taste = sub.add_parser("taste"); taste.add_argument("--taxonomy", default="config/traits.json"); taste.add_argument("--output", default="profiles/taste_profile.json")
    rec = sub.add_parser("recommend"); rec.add_argument("--limit", type=int, default=10); rec.add_argument("--min-rating", type=float, default=0.0); rec.add_argument("--genre")
    rss = sub.add_parser("sync-rss"); rss.add_argument("--username"); rss.add_argument("--feed-url"); rss.add_argument("--dry-run", action="store_true"); rss.add_argument("--output", default="reports/rss_sync.json")
    enrich = sub.add_parser("enrich-metadata"); enrich.add_argument("--provider", choices=("wikidata",), default="wikidata"); enrich.add_argument("--film-key", action="append", dest="film_keys"); enrich.add_argument("--limit", type=int, default=10); enrich.add_argument("--cache-dir", default="data/cache/metadata"); enrich.add_argument("--refresh", action="store_true"); enrich.add_argument("--output", default="reports/metadata_enrichment.json")
    evidence = sub.add_parser("extract-metadata-evidence"); evidence.add_argument("--film-key", action="append", dest="film_keys"); evidence.add_argument("--limit", type=int, default=10); evidence.add_argument("--output", default="reports/metadata_evidence.json")
    review = sub.add_parser("sample-review"); review.add_argument("--limit", type=int, default=10); review.add_argument("--output", default="reports/sample_review.json")
    return p


def main() -> int:
    args = parser().parse_args(); db = Path(args.db)
    if args.command == "ingest": print(json.dumps(ingest(Path(args.data_dir), db), indent=2)); return 0
    if args.command == "validate":
        errors, warnings = validate(db); print(json.dumps({"errors": errors, "warnings": warnings}, indent=2)); return 1 if errors else 0
    if args.command == "report": print(build_report(db, Path(args.output))); return 0
    if args.command == "taste": print(json.dumps(build_taste_profile(db, Path(args.taxonomy), Path(args.output)), indent=2, ensure_ascii=False)); return 0
    if args.command == "recommend": print(json.dumps(recommend(db, args.limit, args.min_rating), indent=2)); return 0
    if args.command == "sync-rss":
        report = sync_rss(db, username=args.username, feed_url=args.feed_url, dry_run=args.dry_run); write_report(report, Path(args.output) if args.output else None); print(json.dumps(report.to_dict(), indent=2)); return 0
    if args.command == "enrich-metadata":
        report = enrich_films(db, WikidataProvider(), Path(args.cache_dir), film_keys=args.film_keys, limit=args.limit, refresh=args.refresh)
        if args.output: write_enrichment_report(report, Path(args.output))
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False)); return 1 if report.failed else 0
    if args.command == "extract-metadata-evidence":
        report = extract_and_persist_metadata_evidence(db, film_keys=args.film_keys, limit=args.limit)
        if args.output: write_batch_report(report, Path(args.output))
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False)); return 0
    if args.command == "sample-review":
        report = build_sample_review(db, Path(args.output), args.limit); print(json.dumps(report, indent=2, ensure_ascii=False)); return 0
    return 2
