# Cinema Brain Roadmap Status

Updated: 2026-08-02

This file is the execution companion to `docs/ROADMAP.md`. The roadmap remains the product vision; this file records what is actually implemented and validated.

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

## Active validation

Evidence-backed Cinematic DNA integration:
- explicit reaction phrases become persisted film-level Evidence records
- phrase matching remains many-to-many while trait IDs remain canonical
- profile generation reads only from the durable Evidence Graph
- evidence regeneration is idempotent by model version
- profile output exposes source references, model versions, conflicts, and persisted record counts
- regression test uses the Undertone / Blair Witch reaction pattern

## Active next milestone

Persist enriched film metadata into canonical SQLite tables and add coverage reporting, so the Evidence Graph can begin learning beyond manually written reactions.

## Then

1. Add a real metadata provider adapter behind the provider-neutral contract.
2. Enrich a bounded horror sample.
3. Convert metadata into provenance-aware evidence.
4. Generate Horror DNA from explicit reactions plus enriched metadata.
5. Add typed mood/request parsing and candidate rejection audits.
6. Build the first explainable ranking run against Daniel's watchlist.

## Guardrail

No roadmap item is marked complete until tests pass in the full GitHub Actions pipeline and the pull request is merged into `main`.
