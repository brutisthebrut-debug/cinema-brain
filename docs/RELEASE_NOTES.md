# Engineering Release Notes

These notes record capabilities shipped, architectural changes, lessons, accepted debt, and the next production milestone. They are not marketing notes.

## Brain v0.3 — Recommendation Intelligence validation

**Date:** 2026-08-03

### Shipped

- Versioned horror recommendation corpus with watched and known-film exclusion
- Explainable Daniel-specific candidate ranking and abstention
- Diversity-aware balanced top-five production slate through PR #60
- Fail-closed Recommendation Release Gates v1 and immutable prediction snapshots through PR #61
- Read-only Recommendation Audit v1 through PR #62
- Local Brain Health Dashboard v1 through PR #63
- Append-only Post-watch Outcome Capture v1 through PR #64
- Recommendation Trust, versioned projected-rating error, and deterministic unpromoted regression fixtures

### Architectural change

Recommendation output is now a content-addressed release rather than an ephemeral
list. The manifest, prediction snapshot, audit, dashboard, and outcome submission
share a verified `release_id` boundary. Post-watch evidence appends to that boundary
without mutating the prediction or silently changing taste truth.

### Validation

- PR #61 CI passed the release-gate implementation.
- PR #62 CI passed the audit implementation.
- PR #63 CI passed the dashboard implementation and all 143 repository tests.
- PR #64 CI passed outcome capture and all 152 repository tests.
- Release identity, tamper detection, audit cross-links, append-only outcomes, and
  regression-fixture thresholds have deterministic regression coverage.

### Learned

- A useful recommendation system needs a frozen prediction before it needs more candidates.
- Trust, completion, moment fit, and rating calibration must remain separate metrics.
- A failed recommendation is review evidence; it must not automatically retrain the model.
- Cross-agent continuity requires the root README to carry the live resume point,
  not only historical setup instructions.

### Intentionally deferred

- Automatic taste-weight or canonical-profile updates from one outcome
- Corpus expansion to 25 or 50 before the first real outcome is inspected
- Dashboard-owned ranking or learning logic
- New provider, public, social, marketplace, or multi-user work

### Next production operation

Capture the first real release-bound outcome, review Recommendation Trust and
prediction error, and inspect any generated regression fixture before promoting
learning evidence or expanding the horror corpus.

## v0.3 — Living Foundation

**Date:** 2026-08-02

### Shipped

- Full Letterboxd CSV ingestion and normalized memory
- Manual watch ingestion
- Canonical film and viewing-event reconciliation
- Durable Evidence Graph with provenance and contradiction preservation
- Evidence-backed Cinematic DNA profile generation
- Durable recommendation and outcome ledger
- Provider-neutral metadata contracts, cache, and canonical persistence
- Letterboxd RSS parsing, raw event ledger, edit detection, and replay protection
- Live `dmarlin` RSS synchronization through GitHub Actions
- Durable JSON RSS state with reproducible SQLite/database artifacts
- Full validation pipeline and regression tests

### Architectural change

Cinema Brain moved from a static personal database to a continuously refreshable personal intelligence system. It is now the reference implementation for the Daniel OS lifecycle:

```text
Source -> Canonical Identity -> Evidence -> Learning -> Prediction -> Outcome -> Calibration
```

### Learned

- Temporary workflow artifacts are not durable state.
- Committing generated SQLite files is opaque and merge-hostile; a versioned JSON delta ledger is safer.
- CI must install test dependencies explicitly rather than relying on undeclared package extras.
- Source reconciliation is safer than allowing CSV, RSS, and manual records to overwrite one another.
- Provider licensing is an architectural requirement, not a later legal cleanup.

### Intentionally deferred

- Automatic RSS scheduling until manual runs demonstrate stable behavior
- Whole-library metadata enrichment until a bounded sample is identity-reviewed
- Dashboard work until ranking and explanation quality are measurable
- Cross-brain data sharing until shared contracts and privacy boundaries are formalized

### Next production milestone

Metadata Intelligence: select a licensing-compatible provider, add resilient bounded enrichment, normalize film facts, derive provenance-aware horror signals, and generate Horror DNA from both explicit reactions and enriched evidence.

## Release-note template

Each future release should record:

- capabilities shipped
- architectural changes
- tests and validation evidence
- what was learned
- assumptions changed
- complexity removed
- technical debt accepted or retired
- metrics affected
- next production milestone
