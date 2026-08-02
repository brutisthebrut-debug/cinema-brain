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
- Evidence Graph foundation and persistence
- Evidence-backed Cinematic DNA integration
- Metadata intelligence persistence:
  - canonical `film_metadata` records keyed by film and provider
  - full provider payload retained for auditability
  - deterministic upsert and exact reconstruction
  - coverage and staleness reporting
  - provider/cache-to-database sync

## Active validation

First real metadata provider adapter:
- TMDB v3 adapter behind the existing provider-neutral contract
- bearer-token authentication with no credential committed to GitHub
- guarded title/year matching
- deterministic mapping of genres, directors, cast, countries, languages, runtime, and keywords
- dependency-injected HTTP transport so CI never depends on the network
- regression tests for exact-year matching, missing results, and missing credentials

## Learned / changed

- Film facts and interpretive taste traits remain separate.
- Cache files are transport and recovery artifacts; SQLite is canonical metadata storage.
- External provider tests must be hermetic. Live API checks belong in an optional integration job, not the required unit-test gate.
- A provider credential is an operational dependency, not application data, and must remain outside the repository.
- Whole-library enrichment will not begin until a bounded horror sample reports identity mismatches, misses, latency, and metadata coverage.

## Active next milestone

Run a bounded horror enrichment command through TMDB, cache, and canonical metadata storage; produce a machine-readable coverage and failure report.

## Then

1. Convert selected metadata fields and horror signals into provenance-aware Evidence records.
2. Generate Horror DNA from explicit reactions plus enriched film evidence.
3. Add typed mood/request parsing and candidate rejection audits.
4. Build the first explainable ranking run against Daniel's watchlist.
5. Add live availability verification only after ranking can operate independently of it.
6. Delay dashboard work until recommendation quality and explanation quality are measurable.
