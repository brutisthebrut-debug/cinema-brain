from __future__ import annotations
import argparse
import json
from pathlib import Path

from .golden_candidate_validation import validate_candidate, write_validation_report
from .golden_promotion import write_promoted_dataset
from .golden_review_workflow import build_review_template, compile_review_decisions
from .ingest import ingest
from .metadata_enrichment import enrich_films, write_enrichment_report
from .metadata_evidence_batch import extract_and_persist_metadata_evidence, write_batch_report
from .persisted_taste_signals import build_persisted_personal_taste_graph
from .profile_review_workflow import build_review_worksheet, compile_review, promote_reviewed_profiles
from .recommend import recommend
from .report import build_report
from .rss_sync import sync_rss, write_report
from .sample_review import build_sample_review
from .taste import build_taste_profile
from .validate import validate
from .wikidata_provider import WikidataProvider


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cinema-brain")
    p.add_argument("--db", default="cinema_brain.db")
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("ingest"); i.add_argument("--data-dir", "--raw-dir", dest="data_dir", default="data")
    sub.add_parser("validate")
    r = sub.add_parser("report"); r.add_argument("--output", default="reports/baseline_analysis.md")
    taste = sub.add_parser("taste"); taste.add_argument("--taxonomy", default="config/traits.json"); taste.add_argument("--output", default="profiles/taste_profile.json")
    personal_taste = sub.add_parser("personal-taste-graph"); personal_taste.add_argument("--profiles", default="config/canonical_horror_profiles_v1_reviewed.json"); personal_taste.add_argument("--output", default="profiles/personal_taste_graph_v1.json")
    rec = sub.add_parser("recommend"); rec.add_argument("--limit", type=int, default=10); rec.add_argument("--min-rating", type=float, default=0.0); rec.add_argument("--genre")
    rss = sub.add_parser("sync-rss"); rss.add_argument("--username"); rss.add_argument("--feed-url"); rss.add_argument("--dry-run", action="store_true"); rss.add_argument("--output", default="reports/rss_sync.json")
    enrich = sub.add_parser("enrich-metadata"); enrich.add_argument("--provider", choices=("wikidata",), default="wikidata"); enrich.add_argument("--film-key", action="append", dest="film_keys"); enrich.add_argument("--limit", type=int, default=10); enrich.add_argument("--cache-dir", default="data/cache/metadata"); enrich.add_argument("--refresh", action="store_true"); enrich.add_argument("--output", default="reports/metadata_enrichment.json")
    evidence = sub.add_parser("extract-metadata-evidence"); evidence.add_argument("--film-key", action="append", dest="film_keys"); evidence.add_argument("--limit", type=int, default=10); evidence.add_argument("--output", default="reports/metadata_evidence.json")
    review = sub.add_parser("sample-review"); review.add_argument("--film-key", action="append", dest="film_keys"); review.add_argument("--limit", type=int, default=10); review.add_argument("--output", default="reports/sample_review.json")
    template = sub.add_parser("golden-review-template"); template.add_argument("--benchmark", default="config/golden_horror_v1.json"); template.add_argument("--sample", default="reports/sample_review.json"); template.add_argument("--output", default="reports/golden_review.csv")
    compile_cmd = sub.add_parser("golden-review-compile"); compile_cmd.add_argument("--benchmark", default="config/golden_horror_v1.json"); compile_cmd.add_argument("--template", default="reports/golden_review.csv"); compile_cmd.add_argument("--reviewer", required=True); compile_cmd.add_argument("--output", default="reports/golden_review_decisions.json")
    promote = sub.add_parser("golden-promote"); promote.add_argument("--benchmark", default="config/golden_horror_v1.json"); promote.add_argument("--decisions", default="reports/golden_review_decisions.json"); promote.add_argument("--next-version", required=True); promote.add_argument("--output", required=True)
    candidate = sub.add_parser("golden-candidate-validate"); candidate.add_argument("--source", required=True); candidate.add_argument("--candidate", required=True); candidate.add_argument("--decisions", required=True); candidate.add_argument("--output", default="reports/golden_candidate_validation.json")
    profile_template = sub.add_parser("profile-review-template"); profile_template.add_argument("--profiles", default="config/canonical_horror_profiles_v1.json"); profile_template.add_argument("--output", default="reports/canonical_horror_profile_review.csv")
    profile_compile = sub.add_parser("profile-review-compile"); profile_compile.add_argument("--profiles", default="config/canonical_horror_profiles_v1.json"); profile_compile.add_argument("--worksheet", default="reports/canonical_horror_profile_review.csv"); profile_compile.add_argument("--reviewer", required=True); profile_compile.add_argument("--output", default="reports/canonical_horror_profile_decisions.json")
    profile_promote = sub.add_parser("profile-review-promote"); profile_promote.add_argument("--profiles", default="config/canonical_horror_profiles_v1.json"); profile_promote.add_argument("--decisions", default="reports/canonical_horror_profile_decisions.json"); profile_promote.add_argument("--registry", default="config/trait_registry_v1.json"); profile_promote.add_argument("--next-version", required=True); profile_promote.add_argument("--output", required=True)
    return p


def main() -> int:
    args = parser().parse_args(); db = Path(args.db)
    if args.command == "ingest": print(json.dumps(ingest(Path(args.data_dir), db), indent=2)); return 0
    if args.command == "validate":
        errors, warnings = validate(db); print(json.dumps({"errors": errors, "warnings": warnings}, indent=2)); return 1 if errors else 0
    if args.command == "report": print(build_report(db, Path(args.output))); return 0
    if args.command == "taste": print(json.dumps(build_taste_profile(db, Path(args.taxonomy), Path(args.output)), indent=2, ensure_ascii=False)); return 0
    if args.command == "personal-taste-graph": print(json.dumps(build_persisted_personal_taste_graph(db, Path(args.profiles), Path(args.output)), indent=2, ensure_ascii=False)); return 0
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
    if args.command == "sample-review": print(json.dumps(build_sample_review(db, Path(args.output), args.limit, args.film_keys), indent=2, ensure_ascii=False)); return 0
    if args.command == "golden-review-template": print(json.dumps(build_review_template(Path(args.benchmark), Path(args.sample), Path(args.output)), indent=2)); return 0
    if args.command == "golden-review-compile": print(json.dumps(compile_review_decisions(Path(args.benchmark), Path(args.template), Path(args.output), reviewer=args.reviewer), indent=2)); return 0
    if args.command == "golden-promote": print(json.dumps(write_promoted_dataset(Path(args.benchmark), Path(args.decisions), Path(args.output), next_version=args.next_version), indent=2)); return 0
    if args.command == "golden-candidate-validate":
        report = validate_candidate(Path(args.source), Path(args.candidate), Path(args.decisions)); write_validation_report(report, Path(args.output)); print(json.dumps(report, indent=2)); return 0 if report["valid"] else 1
    if args.command == "profile-review-template": print(json.dumps(build_review_worksheet(Path(args.profiles), Path(args.output)), indent=2)); return 0
    if args.command == "profile-review-compile": print(json.dumps(compile_review(Path(args.profiles), Path(args.worksheet), Path(args.output), reviewer=args.reviewer), indent=2)); return 0
    if args.command == "profile-review-promote": print(json.dumps(promote_reviewed_profiles(Path(args.profiles), Path(args.decisions), Path(args.registry), Path(args.output), next_version=args.next_version), indent=2)); return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
