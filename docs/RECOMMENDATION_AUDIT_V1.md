# Recommendation Audit v1

Recommendation Audit v1 is the stable, read-only diagnostic contract over an immutable Brain v0.3 recommendation release. It consumes the manifest and prediction snapshot created by Recommendation Release Gates v1. It never recalculates ranking, rewrites the release, or records a human outcome.

## Inputs

- `recommendation_release_manifest_v1.json`
- `recommendation_prediction_snapshot_v1.json`

The audit fails closed before producing output unless the package passes all release verification and cross-link checks.

## Integrity boundary

Audit v1 verifies:

1. the manifest and snapshot share a `release_id`;
2. the snapshot SHA-256 digest matches the manifest;
3. source revision and frozen input digests agree;
4. the `release_id` is reproducible from the release-gate version and frozen input digests;
5. manifest candidate, watched, eligible, recommended, abstained, and released counts reconcile with the snapshot;
6. raw and balanced ranks can be joined by canonical `film_key` without contradiction.

This closes the consumer-side boundary around the immutable release. A dashboard or later outcome evaluator must consume the verified audit contract rather than independently interpreting release files.

## Output

`recommendation_audit_v1.json` contains:

- deterministic `audit_id` and source `release_id`;
- snapshot and input integrity evidence;
- every release-gate result and failure count;
- reconciled release counts;
- raw-to-balanced rank movement for every released film;
- abstention records and reason frequencies;
- released-prediction evidence coverage;
- diversity, novelty, gate, abstention, and integrity health metrics;
- an explicit `awaiting_outcome` state.

Positive `rank_delta` means the diversity-aware slate promoted a film relative to its raw relevance rank. Negative `rank_delta` means it was demoted. The audit records movement and slate role but does not reinterpret or rerun the slate algorithm.

Evidence coverage reports whether each released prediction retained positive drivers, negative-driver accounting, and complete score components. It measures explanation readiness; it does not invent explanation prose.

## Determinism and immutability

The audit has no generation timestamp. Its identity is derived from the audit-contract version, `release_id`, and frozen prediction-snapshot digest. The same verified inputs produce the same audit byte-for-byte.

The file writer uses exclusive creation. Existing audit output is never silently replaced, and neither input file is modified.

## Outcome boundary

Audit v1 deliberately does not accept ratings, reactions, or post-watch evidence. It exposes:

- `outcome_status.status = awaiting_outcome`
- `release_id_required = true`
- null Recommendation Trust and prediction-error values

The later outcome contract must append evidence keyed by `release_id` and compare it with this frozen prediction. It must not edit the manifest, snapshot, or original audit.

## Workflow integration

`.github/workflows/unwatched-horror-ranking.yml` builds and verifies the audit immediately after the release package. The private workflow artifact contains the taste graph, raw ranking, balanced slate, manifest, prediction snapshot, and audit.

Required regression coverage includes:

- deterministic output with unchanged frozen inputs;
- rank movement, abstention, and evidence-coverage reporting;
- fail-closed manifest/snapshot count mismatch;
- fail-closed inconsistent raw-rank linkage;
- create-once audit output.

## Handoff

After Audit v1 is merged and CI is green, the next implementation is Brain Health Dashboard v1 as a thin read-only view over `recommendation_audit_v1.json`. The dashboard must not own ranking, release, audit, or outcome logic. Post-watch outcome capture by `release_id` follows that surface.
