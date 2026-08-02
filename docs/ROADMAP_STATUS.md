# Cinema Brain Roadmap Status

Updated: 2026-08-02

This file is the execution companion to `docs/ROADMAP.md`. The roadmap remains the product vision; this file records what is actually implemented and validated. Roadmap governance is defined in `docs/ROADMAP_GOVERNANCE.md`.

## Operating rules

- Build capabilities rather than isolated features.
- Build before expanding the plan; change the roadmap when implementation teaches us something.
- Every subsystem remains replaceable behind typed contracts.
- Engine quality comes before dashboard work.
- Every completed milestone records what was learned, which assumptions changed, and what duplicate work became unnecessary.
- Major architectural decisions are recorded under `docs/adr/`.
- Intentional deferrals are recorded in `docs/TECHNICAL_DEBT.md`.
- No item is marked complete until the full real-data validation pipeline passes.

## Foundation epic — complete

- Reliable Letterboxd memory, validation, watched exclusion, and manual watch log
- Taste-engine foundation and Evidence-backed Cinematic DNA
- Durable learning ledger and recommendation outcome storage
- Metadata contracts and canonical SQLite persistence
- Evidence Graph foundation, provenance, conflicts, and durable storage
- Letterboxd RSS raw delta ledger with parsing, deduplication, and edit detection
- Canonical CSV/RSS/manual reconciliation with source precedence and replay protection
- Safe live Letterboxd RSS synchronization command for `dmarlin`
- Controlled GitHub Actions workflow with durable JSON RSS state
- First successful live Letterboxd synchronization and private artifact generation

## Milestone: Cinema Brain became a living system

The first successful `dmarlin` RSS workflow established a continuously refreshable path from real-world viewing activity into durable memory, canonical reconciliation, validation, reports, and Cinematic DNA. CSV remains the historical authority; RSS provides incremental activity.

## Active epic — Metadata Intelligence

### Current production sequence

1. Select and implement a licensing-compatible open metadata provider.
2. Add retry, rate-limit, cache, safe-resume, and failure-report behavior.
3. Normalize genres, countries, languages, runtime, release facts, credits, and keywords.
4. Enrich a bounded horror sample and manually review film identity matches.
5. Convert selected facts and horror signals into provenance-aware Evidence records.
6. Generate Horror DNA from explicit reactions plus enriched film evidence.
7. Measure coverage, conflicts, stale records, evidence diversity, and pipeline reliability.

### Definition of done

Metadata Intelligence is complete when enrichment is replaceable, reproducible, cached, resumable, provenance-aware, confidence-aware, identity-safe, and capable of materially expanding the Horror DNA profile through the full real-data CI pipeline.

## Engineering metrics now tracked as first-class roadmap criteria

- canonical film and viewing-event counts
- metadata coverage and completeness
- unresolved identity, duplicate, stale, and conflict rates
- evidence count and source diversity
- sync reliability and duration
- test and regression coverage
- recommendation acceptance, completion, confidence calibration, and prediction error when ranking becomes active

## Learned / changed

- A workflow artifact alone is not durable state because artifacts expire.
- Committing a generated SQLite database would be opaque and merge-hostile.
- A small versioned JSON RSS ledger provides durable, reviewable, replayable state while the database remains reproducible.
- The first live workflow exposed missing test dependencies; the regression is now covered and the production sync passes.
- CSV exports remain the historical correction mechanism; RSS is the incremental delta stream.
- TMDB was rejected after terms review; metadata enrichment will use licensing-compatible open data behind the provider-neutral interface.
- Conversation, CLI, future dashboard, and other Daniel OS modules will consume one stable recommendation interface rather than duplicate ranking logic.

## Then

1. Add typed mood/request parsing and candidate rejection audits.
2. Build the first explainable ranking run against Daniel's watchlist.
3. Add recommendation evaluation and calibration against actual outcomes.
4. Add live availability verification only after ranking can operate independently of it.
5. Build discovery, contradiction, regret, and taste-evolution capabilities.
6. Delay dashboard work until recommendation and explanation quality are measurable.
