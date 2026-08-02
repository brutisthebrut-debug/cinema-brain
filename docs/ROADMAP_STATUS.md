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

## Active validation

Letterboxd RSS incremental synchronization:
- official per-profile feed URL construction
- parsing of diary/review/list items and Letterboxd extension fields
- durable raw delta ledger with first-seen and last-seen timestamps
- GUID-based deduplication
- content-hash detection of edited feed items
- hermetic XML fixture tests with no dependency on Letterboxd uptime

## Learned / changed

- The CSV export remains the historical source of truth and reconciliation mechanism.
- The RSS feed is a low-friction delta stream for new diary entries, reviews, and lists; it is not a complete account mirror.
- RSS events must be stored before normalization so later parser improvements can be replayed without losing source history.
- Feed edits are tracked by content hash rather than creating duplicate watches.
- Likes, watchlist changes, deletions, old history, and some later edits still require periodic CSV reconciliation.
- TMDB was rejected after terms review because its current API restrictions create unacceptable risk for an AI-assisted recommendation project.
- Metadata enrichment will continue through licensing-compatible open data behind the existing provider-neutral interface.

## Active next milestone

Normalize RSS diary/review events into canonical films and viewing records, with reconciliation rules that prevent duplicates when the same activity later appears in a CSV export.

## Then

1. Add a licensing-compatible open metadata provider and enrich a bounded horror sample.
2. Convert selected metadata fields and horror signals into provenance-aware Evidence records.
3. Generate Horror DNA from explicit reactions plus enriched film evidence.
4. Add typed mood/request parsing and candidate rejection audits.
5. Build the first explainable ranking run against Daniel's watchlist.
6. Add live availability verification only after ranking can operate independently of it.
7. Delay dashboard work until recommendation and explanation quality are measurable.
