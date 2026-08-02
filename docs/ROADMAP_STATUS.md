# Cinema Brain Roadmap Status

Updated: 2026-08-02

This file is the execution companion to `docs/ROADMAP.md`. The roadmap remains the product vision; this file records what is actually implemented and validated.

## Operating rules

- Build before expanding the plan; change the roadmap when implementation teaches us something.
- Every subsystem remains replaceable behind typed contracts.
- Engine quality comes before dashboard work.
- Every completed milestone records what was learned, which assumptions changed, and what duplicate work became unnecessary.
- No item is marked complete until the full real-data validation pipeline passes.

## Completed

- Phase 0: reliable Letterboxd memory, validation, watched exclusion, and manual watch log
- Taste-engine foundation and Evidence-backed Cinematic DNA
- Durable learning ledger and recommendation outcome storage
- Metadata foundation and canonical SQLite persistence
- Evidence Graph foundation, provenance, conflicts, and durable storage
- Letterboxd RSS raw delta ledger with parsing, deduplication, and edit detection
- Canonical CSV/RSS/manual reconciliation with source precedence and replay protection
- Safe live Letterboxd RSS synchronization command for `dmarlin`

## Active validation

Controlled RSS automation:
- manual GitHub Actions workflow for `dmarlin`
- full unit tests before any live state mutation
- canonical database rebuilt from CSV/manual sources on every run
- versioned JSON RSS ledger restored before synchronization
- live feed fetch, reconciliation, and database validation
- baseline report and Cinematic DNA regeneration
- only the auditable RSS ledger is committed; SQLite remains a private artifact
- concurrency protection and no state commit after a failed step
- RSS state import/export round-trip tests

## Learned / changed

- A workflow artifact alone is not durable state because artifacts expire.
- Committing a generated SQLite database would be opaque and merge-hostile.
- A small versioned JSON RSS ledger provides durable, reviewable, replayable state while the database remains reproducible.
- Automatic scheduling should wait until the first manual live sync and state diff are reviewed.
- CSV exports remain the historical correction mechanism; RSS is the incremental delta stream.
- TMDB was rejected after terms review; metadata enrichment will use licensing-compatible open data behind the provider-neutral interface.

## Active next milestone

Run and review the first live `dmarlin` RSS synchronization. After validation, add a conservative recurring schedule and failure visibility.

## Then

1. Add a licensing-compatible open metadata provider and enrich a bounded horror sample.
2. Convert selected metadata fields and horror signals into provenance-aware Evidence records.
3. Generate Horror DNA from explicit reactions plus enriched film evidence.
4. Add typed mood/request parsing and candidate rejection audits.
5. Build the first explainable ranking run against Daniel's watchlist.
6. Add live availability verification only after ranking can operate independently of it.
7. Delay dashboard work until recommendation and explanation quality are measurable.
