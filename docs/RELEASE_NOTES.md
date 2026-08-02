# Engineering Release Notes

These notes record capabilities shipped, architectural changes, lessons, accepted debt, and the next production milestone. They are not marketing notes.

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
