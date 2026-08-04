# Post-watch Outcome Capture v1

Post-watch Outcome Capture v1 is the append-only Learning-layer contract that connects Daniel's explicit reaction to one immutable recommendation release. It measures the first real Recommendation Trust evidence without rewriting the manifest, prediction snapshot, Recommendation Audit v1 record, or Brain Health Dashboard input.

## Inputs

The production workflow now adds `post_watch_outcome_submission_v1.json` to each private recommendation artifact. Its immutable fields bind the submission to the verified `release_id` and `audit_id`; its released-prediction list limits `film_key` to the exact balanced slate.

Daniel fills:

- the released `film_key`;
- `watched_at` and `recorded_at` timestamps;
- a Letterboxd-style rating from 0.5 to 5.0;
- a non-empty one-sentence reaction;
- whether he completed the film;
- whether he is genuinely glad he watched it;
- whether it fit the moment, or `null` when that question is not applicable.

## Verification boundary

Before accepting evidence, the engine:

1. rebuilds Recommendation Audit v1 from the manifest and snapshot;
2. requires the supplied audit to match that deterministic pre-outcome record exactly;
3. requires the audit to remain in `awaiting_outcome` state;
4. matches `release_id` and `audit_id` exactly;
5. requires `film_key` to identify exactly one frozen balanced-slate prediction;
6. validates every explicit outcome field.

Any mismatch fails closed. The release package and audit are read only.

## Recommendation Trust and calibration

The roadmap defines Recommendation Trust as: “If Cinema Brain recommends five films, how many is Daniel genuinely glad he watched?” Outcome v1 therefore records one binary trust observation:

- `1.0` when `glad_watched` is true;
- `0.0` when `glad_watched` is false.

Aggregate trust is the mean across unique Outcome v1 records. Completion rate and moment-fit rate remain separate so they cannot silently redefine the north-star metric.

The frozen release contains a `taste_score` on `[-1, 1]`, not a direct Letterboxd forecast. Calibration v1 projects that score linearly onto `[0.5, 5.0]` using `2.75 + 2.25 × taste_score`, records the method name, and reports signed and absolute rating error. The mapping is versioned and may be replaced later without rewriting historical outcomes.

## Regression fixtures

A deterministic regression fixture is created when any of these occur:

- Daniel is not glad he watched;
- he did not complete the film;
- the film was wrong for the moment;
- projected-versus-actual rating error is at least one star;
- that rating miss was paired with confidence of at least 0.6.

The fixture preserves frozen score drivers, actual reaction, calibration evidence, and explicit failure reasons. It remains `candidate_not_promoted`; a miss does not automatically change taste weights, canonical profiles, or future ranking.

## Append-only storage and CLI

Each accepted submission creates a unique directory:

```text
outcomes/<release_id>/<outcome_id>/
  recommendation_outcome_v1.json
  recommendation_regression_fixture_v1.json  # only when required
```

The outcome directory uses exclusive creation, so replaying the same deterministic submission cannot replace prior evidence.

Run capture with:

```bash
python -m cinema_brain.cli record-recommendation-outcome \
  --manifest recommendation_release_manifest_v1.json \
  --snapshot recommendation_prediction_snapshot_v1.json \
  --audit recommendation_audit_v1.json \
  --submission post_watch_outcome_submission_v1.json \
  --output-dir outcomes
```

## Regression contract

Required coverage proves:

- deterministic, immutable release linkage;
- template restriction to the released slate;
- correct trust and rating-error calculation;
- fail-closed release, audit, and film mismatches;
- append-only duplicate rejection;
- deterministic fixture creation for meaningful misses;
- aggregate trust and calibration summaries.

## Handoff

After Outcome Capture v1 is merged and CI is green, do not promote a regression fixture or update taste weights automatically. The next operation is to capture one real outcome from a frozen release, inspect the resulting trust and calibration evidence, and review any fixture. Corpus growth to 25 and then 50 follows only when measured gaps justify it.
