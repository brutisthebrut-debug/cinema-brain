# Letterboxd RSS Automation

Cinema Brain uses `dmarlin`'s public Letterboxd RSS feed as an incremental delta stream. The CSV export remains the historical source of truth.

## Workflow

The manual GitHub Actions workflow `.github/workflows/rss-sync.yml`:

1. runs all unit tests;
2. rebuilds the canonical SQLite database from committed CSV/manual sources;
3. restores the versioned RSS ledger from `data/rss/dmarlin-state.json`;
4. fetches and reconciles `https://letterboxd.com/dmarlin/rss/`;
5. validates the database and regenerates reports;
6. exports the updated RSS ledger;
7. commits only the small JSON ledger when it changes; and
8. uploads the database and reports as private workflow artifacts for 30 days.

## Safety properties

- No API key or secret is required.
- The SQLite database is not committed.
- RSS items remain auditable and replayable.
- Repeated runs are idempotent.
- A failed test, fetch, reconciliation, or validation prevents state from being committed.
- Workflow concurrency prevents overlapping syncs.

## Recovery

Delete or repair an invalid state item in `data/rss/dmarlin-state.json`, then manually rerun the workflow. A periodic full Letterboxd CSV export remains the correction mechanism for deletions, likes, watchlist changes, older history, and feed items that have aged out of RSS.

## Initial operating mode

The workflow is manual-only until the first live run is reviewed. A schedule should be added only after the first artifact and state diff are confirmed correct.
