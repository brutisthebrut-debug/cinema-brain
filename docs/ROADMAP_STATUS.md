# Cinema Brain Roadmap Status

Updated: 2026-08-02

This file is the execution companion to `docs/ROADMAP.md`. The roadmap remains the product vision; this file records what is actually implemented and validated.

## Canonical project references

- `docs/VISION.md` — Daniel OS destination and Cinema Brain's role as reference implementation
- `docs/FOUNDING_PRINCIPLES.md` — permanent doctrine, Forever Test, and architecture fitness checks
- `docs/ROADMAP_GOVERNANCE.md` — roadmap standards, definitions of done, and engineering metrics
- `docs/DECISIONS.md` — chronological product and operating decisions
- `docs/RELEASE_NOTES.md` — shipped capabilities, lessons, accepted debt, and version history
- `docs/TECHNICAL_DEBT.md` — intentional deferrals and repayment triggers
- `docs/adr/` — detailed architecture decision records

## Operating rules

- Build capabilities rather than isolated features.
- Build before expanding the plan; change the roadmap when implementation teaches us something.
- Apply the Forever Test before accepting major complexity.
- Every subsystem remains replaceable behind typed contracts.
- Every brain should be independently excellent but collectively smarter through explicit contracts and permissions.
- Explainability, provenance, privacy, and human correction are non-negotiable.
- Engine quality comes before dashboard work.
- Every completed milestone records what was learned, which assumptions changed, and what duplicate work became unnecessary.
- Major architectural decisions are recorded under `docs/adr/` and summarized in `docs/DECISIONS.md`.
- Intentional deferrals are recorded in `docs/TECHNICAL_DEBT.md`.
- Engineering releases are recorded in `docs/RELEASE_NOTES.md`.
- No item is marked complete until the full real-data validation pipeline passes.
- Run an architecture fitness check after roughly 10–20 meaningful milestones, or sooner when complexity warrants it.

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

This milestone is recorded as engineering release **v0.3 — Living Foundation**.

## Daniel OS reference architecture

Cinema Brain is the first complete implementation of the shared lifecycle:

```text
Source
  -> Canonical Identity
  -> Evidence
  -> Learning
  -> Prediction
  -> Outcome
  -> Calibration
```

Future modules may specialize their domain models, but should reuse these capabilities and preserve the same guarantees around provenance, explainability, correction, privacy, versioning, and validation.

## Active epic — Metadata Intelligence

### Active validation: Wikidata provider and bounded enrichment

The first licensing-compatible provider slice now includes:

- a read-only Wikidata adapter using CC0 structured data
- mandatory descriptive User-Agent headers and conservative request behavior
- exact title, release-year, and film-type identity gates
- retry/backoff for rate limits and transient Wikimedia failures
- normalized genres, directors, cast, countries, languages, runtime, and main subjects
- no API key or private credential requirement
- bounded enrichment by explicit canonical film keys or a recent-watch limit
- deterministic local metadata caching and canonical SQLite persistence
- per-film miss and failure reporting without abandoning the rest of a batch
- safe resume through the existing cache
- hermetic provider and enrichment tests with no network dependency
- a CLI command: `enrich-metadata`

### Current production sequence

1. Validate and merge the Wikidata provider and bounded enrichment service.
2. Run a small real horror sample and manually review every identity match.
3. Expand normalization and resolve any coverage gaps exposed by the sample.
4. Convert selected facts and horror signals into provenance-aware Evidence records.
5. Generate Horror DNA from explicit reactions plus enriched film evidence.
6. Measure coverage, conflicts, stale records, evidence diversity, and pipeline reliability.

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
- TMDB was rejected after terms review.
- Wikidata structured data is CC0 and requires responsible API use, including a descriptive User-Agent, bounded requests, and backoff after rate limits.
- Provider search cannot be trusted by title alone; exact release-year and film-type checks are mandatory before persistence.
- Conversation, CLI, future dashboard, and other Daniel OS modules will consume one stable recommendation interface rather than duplicate ranking logic.
- Durable vision, principles, decisions, release notes, debt, and ADRs now prevent important reasoning from living only in chat.

## Then

1. Add typed mood/request parsing and candidate rejection audits.
2. Build the first explainable ranking run against Daniel's watchlist.
3. Add recommendation evaluation and calibration against actual outcomes.
4. Add live availability verification only after ranking can operate independently of it.
5. Build discovery, contradiction, regret, and taste-evolution capabilities.
6. Delay dashboard work until recommendation and explanation quality are measurable.
