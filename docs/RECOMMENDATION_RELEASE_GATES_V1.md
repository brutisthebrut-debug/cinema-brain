# Recommendation Release Gates v1

Recommendation Release Gates v1 is the Brain v0.3 boundary between generating a ranked slate and presenting a frozen prediction for private evaluation.

The gate is intentionally fail-closed. A workflow may generate ranking artifacts that remain useful for diagnosis, but it may not call them a recommendation release unless every required check passes.

## Production inputs

The gate consumes the two artifacts produced by the unwatched-horror workflow:

- `unwatched_horror_ranking_v1.json`
- `unwatched_horror_balanced_slate_v1.json`

The raw ranking remains the audit view. The balanced slate remains the presentation view. Release gating does not recalculate either one.

## Required checks

The stable gate identifiers are:

1. `version_traceability` — ranking, model, taste-model, corpus, registry, and slate versions are present and agree.
2. `candidate_accounting` — candidate, watched-exclusion, eligible, recommendation, and abstention counts reconcile with their records.
3. `ranking_integrity` — recommendation identities are unique and ranks are contiguous.
4. `slate_integrity` — the release contains exactly five unique predictions, preserves the raw ranking, and preserves abstentions and watched exclusions.
5. `watched_exclusion` — no watched identity appears in either recommendation view.
6. `prediction_quality` — every released prediction retains its score, confidence, evidence components, coverage, novelty, and slate role and has passed the ranking abstention policy.
7. `slate_metrics` — diversity, novelty, and discovery metrics are valid and reconcile with the released slate.

Any failure makes `eligible` false and prevents creation of a release package.

## Release outputs

An eligible run creates two additional private artifacts:

### Recommendation manifest

`recommendation_release_manifest_v1.json` records:

- deterministic release identity
- source revision and generation time
- input SHA-256 digests
- prediction-snapshot SHA-256 digest
- candidate and release counts
- every gate result and failure reason
- the create-before-outcome immutability policy

Its release status is `eligible_for_private_evaluation`. That status is deliberately narrower than a claim of production recommendation accuracy.

### Immutable prediction snapshot

`recommendation_prediction_snapshot_v1.json` freezes:

- raw recommendations
- the balanced top five
- score components and explanation evidence
- slate metrics
- abstentions
- watched exclusions
- every relevant model and data version

The snapshot is content-addressed and written with exclusive file creation. A second write to the same release output fails instead of silently replacing the original prediction. Outcome records must reference the manifest `release_id`; they must never edit the snapshot.

## Determinism and audit behavior

The release ID is derived from canonical SHA-256 digests of the frozen ranking and balanced-slate inputs plus the gate-contract version. Re-running the same frozen inputs produces the same release identity and prediction snapshot even when the manifest generation time changes.

The workflow verifies the manifest against the snapshot immediately after writing it. Any later mutation changes the snapshot digest and fails verification.

## Workflow integration

`.github/workflows/unwatched-horror-ranking.yml` now performs the release gate after ranking and slate construction. The uploaded private artifact contains the taste graph, raw ranking, balanced slate, release manifest, and immutable prediction snapshot.

Required unit tests cover:

- an eligible deterministic top-five release
- fail-closed watched-film overlap
- post-release tamper detection
- create-once output behavior

## Handoff state

After this gate is merged and CI is green, Brain v0.3 has a trustworthy prediction-freeze boundary. The next implementation should consume the manifest and snapshot without modifying them:

1. Recommendation Audit v1 — inspect gate outcomes, rank movement, abstentions, evidence coverage, and later prediction error by `release_id`.
2. Brain Health Dashboard v1 — a thin read-only view over versioned audit and health contracts; it must not own scoring or release logic.
3. Post-watch outcome capture — append Daniel's rating and one-sentence reaction against the frozen release, then calculate Recommendation Trust and calibration evidence.

No corpus expansion or broad catalog search should interrupt this sequence until the first frozen release has human outcome evidence.
