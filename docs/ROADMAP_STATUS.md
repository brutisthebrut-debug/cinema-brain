# Cinema Brain Roadmap Status

Updated: 2026-08-02

This file is the execution companion to `docs/ROADMAP.md`. The roadmap remains the product vision; this file records what is actually implemented and validated.

## Operating rules

- Build before expanding the plan; change the roadmap when implementation teaches us something.
- Every subsystem remains replaceable behind typed contracts.
- Engine quality comes before dashboard work.
- Every completed milestone records what was learned, which assumptions changed, and what duplicate work became unnecessary.
- No item is marked complete until the full real-data GitHub Actions pipeline passes and the pull request is merged into `main`.

## Completed

- Phase 0: reliable Letterboxd memory, validation, watched exclusion, and manual watch log
- Taste-engine foundation: versioned weights, trait taxonomy, reaction parsing, profile generation
- Integrated architecture: typed cross-layer contracts and 10x review gates
- Durable learning ledger: frozen recommendations, score components, availability snapshots, outcomes, and prediction error
- Metadata foundation: provider-neutral contract, deterministic local cache, identity checks, and refresh behavior
- Evidence Graph foundation:
  - canonical trait registry with alias collision protection
  - immutable provenance-aware evidence records
  - duplicate-evidence rejection
  - positive and negative evidence aggregation
  - preserved conflicts rather than silent averaging
  - confidence based on agreement and evidence volume
  - strongest-source traceability
- Evidence persistence:
  - SQLite adapter for canonical Evidence records
  - deterministic duplicate protection
  - round-trip graph reconstruction
  - model-version filtering and evidence counts
- Evidence-backed Cinematic DNA integration:
  - explicit reaction phrases persist as film-level Evidence records
  - phrase matching remains many-to-many while trait IDs remain canonical
  - profile generation reads from the durable Evidence Graph
  - evidence regeneration is idempotent by model version
  - profile output exposes provenance, model versions, conflicts, and record counts

## Active validation

Metadata intelligence persistence:
- canonical `film_metadata` records keyed by film and provider
- full provider payload retained for auditability
- deterministic upsert and exact round-trip reconstruction
- foreign-key protection against orphan metadata
- coverage, missing-data, and staleness reporting
- provider-to-database sync that preserves canonical identity

## Learned / changed

- Film facts and interpretive taste traits must remain separate. Metadata storage owns facts; Evidence Graph owns claims about Daniel's preferences.
- Cache files are useful transport and recovery artifacts, but SQLite is the queryable canonical metadata layer.
- Staleness belongs to metadata and availability, not to Daniel's stable personal history.
- Many descriptive signals are more useful than broad genres, but objective provider facts must remain distinguishable from inferred signals.
- The old parallel taste aggregation path is gone; future explanations and recommendations consume persisted evidence.

## Active next milestone

Add the first real metadata provider adapter, enrich a bounded horror sample, and generate a coverage report before attempting whole-library enrichment.

## Then

1. Convert selected metadata fields and horror signals into provenance-aware Evidence records.
2. Generate Horror DNA from explicit reactions plus enriched film evidence.
3. Add typed mood/request parsing and candidate rejection audits.
4. Build the first explainable ranking run against Daniel's watchlist.
5. Add live availability verification only after ranking can operate independently of it.
6. Delay dashboard work until recommendation quality and explanation quality are measurable.
