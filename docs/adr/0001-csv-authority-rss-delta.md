# ADR-001: CSV as historical authority and RSS as incremental delta

- Status: Accepted
- Date: 2026-08-02

## Context

Letterboxd exports provide broad historical account snapshots, while the public profile RSS feed provides timely but incomplete recent activity.

## Decision

Use CSV exports as the historical correction and reconciliation source. Use RSS as an incremental delta stream. Preserve raw records from both and reconcile them into canonical films and viewing events without allowing one source to erase another.

## Alternatives considered

- RSS as the sole source: rejected because it is incomplete and short-lived.
- Periodic CSV only: rejected because it cannot keep Cinema Brain current between exports.
- Committing SQLite as the durable state: rejected because it is opaque and merge-hostile.

## Consequences

The system stays current while remaining reproducible and auditable. Periodic CSV refreshes are still required to correct deletions and account changes RSS does not expose.
