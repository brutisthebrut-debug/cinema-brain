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
- Taste-engine foundation and Evidence-backed Cinematic DNA
- Durable learning ledger and recommendation outcome storage
- Metadata foundation and canonical SQLite persistence
- Evidence Graph foundation, provenance, conflicts, and durable storage
- Letterboxd RSS raw delta ledger with parsing, deduplication, and edit detection
- Canonical CSV/RSS/manual reconciliation with source precedence and replay protection

## Active validation

Safe live Letterboxd RSS synchronization:
- `sync-rss` CLI command
- configuration through username, exact feed URL, or environment variables
- dry-run mode that fetches and parses without database writes
- explicit rejection of non-Letterboxd feed URLs
- durable JSON sync reports
- raw ingestion followed by canonical reconciliation in one operation
- missing-database protection
- idempotency regression coverage

## Learned / changed

- CSV exports remain the historical snapshot and correction mechanism.
- RSS is the near-real-time delta stream, not a complete account mirror.
- Manual chat updates remain the fastest source for private reactions and context.
- Feed configuration belongs outside committed code; a public Letterboxd username is sufficient for standard profile feeds.
- Dry-run and structured reports are required before any recurring automation is introduced.
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
