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
- Metadata foundation and persistence: provider-neutral contracts, deterministic cache, canonical SQLite facts, identity safety, coverage, and staleness reporting
- Evidence Graph foundation and persistence: canonical traits, immutable provenance, conflict preservation, durable storage, and model-version filtering
- Evidence-backed Cinematic DNA: explicit reactions persist as film-level evidence and profile generation uses the durable graph
- Letterboxd RSS delta ledger: feed parsing, raw event preservation, GUID deduplication, edit detection, and hermetic fixture tests

## Active validation

Canonical source reconciliation:
- promotes RSS diary/review deltas into canonical films, viewing events, ratings, and reviews
- matches existing CSV or manual viewing events by canonical film identity plus watched date
- enriches an existing event rather than counting the same watch again
- records every RSS-to-canonical match in a durable audit ledger
- keeps source precedence explicit: CSV/manual identity wins; RSS fills missing fields
- is idempotent when the same feed is processed repeatedly
- includes regressions for an existing Undertone export row and a new Vicious RSS-only row

## Learned / changed

- CSV exports remain the historical snapshot and correction mechanism.
- RSS is the near-real-time delta stream, not a complete account mirror.
- Manual chat updates remain the fastest source for private reactions and context.
- Source records should not overwrite one another; reconciliation links them to one canonical event.
- Same-film and same-day is the safe initial viewing-event match rule. Ambiguous no-date events remain auditable rather than guessed.
- RSS descriptions can create review records while still linking to the same canonical viewing event.
- TMDB was rejected after terms review; metadata enrichment will use licensing-compatible open data behind the provider-neutral interface.

## Active next milestone

Add a licensing-compatible open metadata provider, batch enrichment with safe resume and failure reporting, and a bounded horror sample before whole-library enrichment.

## Then

1. Convert selected metadata fields and horror signals into provenance-aware Evidence records.
2. Generate Horror DNA from explicit reactions plus enriched film evidence.
3. Add typed mood/request parsing and candidate rejection audits.
4. Build the first explainable ranking run against Daniel's watchlist.
5. Add live availability verification only after ranking can operate independently of it.
6. Delay dashboard work until recommendation and explanation quality are measurable.
