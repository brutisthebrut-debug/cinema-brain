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

## Active validation

Evidence persistence integration:
- SQLite adapter for canonical Evidence records
- deterministic duplicate protection using the existing schema constraint
- round-trip reconstruction of an Evidence Graph from durable storage
- model-version filtering and evidence counts
- real Undertone-style provenance test

## Active next milestone

Route existing taste-profile generation through the durable Evidence Graph so profile JSON, explanations, and later recommendations consume one aggregation path.

## Then

1. Persist enriched metadata into canonical tables.
2. Add a real metadata provider adapter behind the provider-neutral contract.
3. Enrich a bounded horror sample.
4. Convert metadata into provenance-aware evidence.
5. Generate Horror DNA from explicit reactions plus enriched metadata.
6. Add typed mood/request parsing and candidate rejection audits.

## Guardrail

No roadmap item is marked complete until tests pass in the full GitHub Actions pipeline and the pull request is merged into `main`.
