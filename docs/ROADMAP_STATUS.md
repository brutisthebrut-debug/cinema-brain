# Cinema Brain Roadmap Status

Updated: 2026-08-02

This file is the execution companion to `docs/ROADMAP.md`. The roadmap remains the product vision; this file records what is actually implemented and validated.

## Canonical project references

- `docs/VISION.md` — Daniel OS destination and Cinema Brain's role as reference implementation
- `docs/FOUNDING_PRINCIPLES.md` — permanent doctrine, Forever Test, and architecture fitness checks
- `docs/ROADMAP_GOVERNANCE.md` — roadmap standards, definitions of done, and engineering metrics
- `docs/METADATA_INTELLIGENCE.md` — multi-source enrichment architecture and rollout blueprint
- `docs/SOURCE_REGISTRY.md` — provider capabilities, licensing, restrictions, and replacement plans
- `docs/GOLDEN_DATASET.md` — human-reviewed metadata benchmark and quality gates
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
- External providers contribute evidence; no provider is treated as truth.
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

- a read-only Wikidata adapter using open structured data
- mandatory descriptive User-Agent headers and conservative request behavior
- exact title, release-year, and film-type identity gates
- retry/backoff for rate limits and transient failures
- normalized genres, directors, cast, countries, languages, runtime, and main subjects
- no API key or private credential requirement
- bounded enrichment by explicit canonical film keys or a recent-watch limit
- deterministic local metadata caching and canonical SQLite persistence
- per-film miss and failure reporting without abandoning the rest of a batch
- safe resume through the existing cache
- hermetic provider and enrichment tests with no network dependency
- a CLI command: `enrich-metadata`

### Multi-source target architecture

Metadata Intelligence will use narrow, replaceable source roles rather than one dominant provider:

1. **Wikidata** for canonical open facts and identifier bridging.
2. **Optional IMDb downloadable datasets** for private factual reinforcement, alternate titles, credits, runtime, and rating priors, gated by current eligibility and a removable adapter.
3. **MovieLens Tag Genome or an equivalent approved source** for semantic community priors.
4. **Wikipedia** only after structured sources are measured, for narrative, theme, setting, and production-technique extraction with revision and license provenance.
5. **DBpedia** only where it materially improves structured coverage.
6. **Library of Congress and Internet Archive** as specialist historical and archival sources.
7. **Live availability providers** remain a separate expiring evidence layer, not permanent film metadata.

Rejected or quarantined sources include providers with conflicting AI-use terms, unofficial streaming endpoints, scraped reviews or subtitles with unclear rights, and anonymous dumps without lineage.

### Current production sequence

1. Validate and merge the Wikidata provider and bounded enrichment service.
2. Add the provider/licensing registry to executable configuration.
3. Build the first 50-film horror-heavy golden dataset.
4. Run a small real horror sample and manually review every identity match and confidence explanation.
5. Turn every discovered mismatch into a regression fixture.
6. Expand normalization only where the sample proves a real gap.
7. Add optional private factual reinforcement behind a removable adapter.
8. Add a semantic tag layer and measure its incremental value.
9. Evaluate narrative extraction only after structured and semantic sources are measured.
10. Convert selected facts and horror signals into provenance-aware Evidence records.
11. Generate Horror DNA from explicit reactions plus enriched film evidence.
12. Expand to the full library only after golden-dataset quality gates pass.

### Required capabilities

- provider and licensing registry
- field-level provenance and source identifiers
- fact versus interpretation versus community-prior versus Daniel-evidence classification
- explainable identity confidence
- quarantine for low-confidence matches
- preserved provider disagreements
- provider health metrics and schema-drift visibility
- time-aware retrieval and taste-era snapshots
- safe resume, retry queues, and bounded batches
- benchmark-driven quality gates before broad enrichment

### Definition of done

Metadata Intelligence is complete when enrichment is replaceable, reproducible, cached, resumable, provenance-aware, license-aware, confidence-aware, identity-safe, conflict-visible, provider-health measurable, protected by a human-reviewed golden dataset, and capable of materially expanding the Horror DNA profile through the full real-data CI pipeline.

## Engineering metrics now tracked as first-class roadmap criteria

- canonical film and viewing-event counts
- metadata coverage and field completeness
- unresolved identity, false-positive, duplicate, stale, and conflict rates
- low-confidence quarantine rate
- provider success, latency, retry, and schema-drift signals
- evidence count, class, and source diversity
- sync reliability and duration
- golden-dataset accuracy and regression count
- test and regression coverage
- recommendation acceptance, completion, confidence calibration, and prediction error when ranking becomes active

## Learned / changed

- A workflow artifact alone is not durable state because artifacts expire.
- Committing a generated SQLite database would be opaque and merge-hostile.
- A small versioned JSON RSS ledger provides durable, reviewable, replayable state while the database remains reproducible.
- The first live workflow exposed missing test dependencies; the regression is now covered and the production sync passes.
- CSV exports remain the historical correction mechanism; RSS is the incremental delta stream.
- TMDB was rejected after terms review.
- Provider search cannot be trusted by title alone; exact release-year and film-type checks are mandatory before persistence.
- False-positive identity matches are more damaging than metadata misses.
- Community tags are priors, not Daniel preferences.
- External facts, interpretations, community opinions, and Daniel evidence must remain separate evidence classes.
- Conversation, CLI, future dashboard, and other Daniel OS modules will consume one stable recommendation interface rather than duplicate ranking logic.
- Durable vision, principles, decisions, release notes, debt, registries, benchmarks, and ADRs prevent important reasoning from living only in chat.

## Then

1. Add typed mood/request parsing and candidate rejection audits.
2. Build the first explainable ranking run against Daniel's watchlist.
3. Add recommendation evaluation and calibration against actual outcomes.
4. Add live availability verification only after ranking can operate independently of it.
5. Build discovery, contradiction, regret, and taste-evolution capabilities.
6. Delay dashboard work until recommendation and explanation quality are measurable.
