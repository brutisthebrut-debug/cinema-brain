# Cinema Brain Technical Debt Register

Updated: 2026-08-02

This register records intentional deferrals. An entry is not necessarily a defect; it is a decision future work should not have to rediscover.

## TD-001 — GitHub Actions workflow versions

- **Status:** Open
- **Deferred issue:** Official `actions/checkout@v4` and `actions/setup-python@v5` currently emit Node.js deprecation warnings on GitHub-hosted runners.
- **Reason deferred:** The actions still execute successfully and the warning does not affect Cinema Brain results.
- **Risk:** Future GitHub runner changes may require upgrading action versions.
- **Reconsider when:** New stable major versions are available or warnings become failures.
- **Epic:** Operations / CI

## TD-002 — RSS is not a complete Letterboxd mirror

- **Status:** Accepted limitation
- **Deferred issue:** RSS does not guarantee complete coverage of deletions, likes, watchlist edits, historical entries, or all later account changes.
- **Reason deferred:** CSV export plus RSS delta reconciliation is the most legitimate and reliable available integration.
- **Risk:** Cinema Brain can temporarily differ from Letterboxd until the next export reconciliation.
- **Reconsider when:** Letterboxd offers a compatible personal API or additional export mechanisms.
- **Epic:** Memory

## TD-003 — Automatic RSS schedule

- **Status:** Open
- **Deferred issue:** RSS synchronization is manual rather than scheduled.
- **Reason deferred:** The first live workflow needed successful validation and review before recurring writes were enabled.
- **Risk:** New watches are not imported until the workflow runs.
- **Reconsider when:** At least several manual runs complete without identity or state-regression issues.
- **Epic:** Operations / Memory

## TD-004 — Open metadata provider selection

- **Status:** Active investigation
- **Deferred issue:** The first licensing-compatible production metadata provider has not been selected and implemented.
- **Reason deferred:** TMDB was rejected after terms review; provider licensing and identity quality must be verified before integration.
- **Risk:** Horror DNA and explainable ranking remain limited by sparse film-level signals.
- **Reconsider when:** During the active Metadata Intelligence epic.
- **Epic:** Metadata Intelligence

## TD-005 — Database migrations

- **Status:** Open
- **Deferred issue:** The current pipeline can rebuild SQLite from durable sources, but a formal migration framework is not yet implemented.
- **Reason deferred:** Reproducible rebuilds currently reduce migration urgency.
- **Risk:** Long-lived runtime databases will become harder to upgrade safely as schemas evolve.
- **Reconsider when:** The database begins retaining state that cannot be recreated from source ledgers or before external deployment.
- **Epic:** Core architecture

## TD-006 — Dashboard

- **Status:** Intentionally parked
- **Deferred issue:** No production dashboard exists.
- **Reason deferred:** Recommendation quality, evidence, and learning infrastructure have priority over presentation.
- **Risk:** Exploration is less visual in the short term.
- **Reconsider when:** Explainable recommendations and quality metrics are consistently useful.
- **Epic:** Interfaces
