# Cinema Brain

Cinema Brain is Daniel's private, local-first movie intelligence system. It turns
Letterboxd history, reviewed film traits, explicit reactions, current context, and
frozen recommendation outcomes into explainable recommendations that can improve
without rewriting history.

GitHub is the source of truth for code, contracts, roadmap state, and agent handoff.
Raw Letterboxd exports and private workflow artifacts remain local or in private
GitHub Actions artifacts unless Daniel intentionally promotes reviewed evidence.

## Resume here

| Handoff field | Current value |
| --- | --- |
| Release | Brain v0.3 — Recommendation Intelligence |
| State on `main` | Implemented through Post-watch Outcome Capture v1 and the Unified Evaluation Experience v1 |
| Current operation | Capture the first real outcome in the unified page, then verify and review it |
| Next implementation decision | Expand the horror benchmark only after the outcome and any regression fixture reveal a measured coverage gap |

Do not automatically change taste weights, promote a regression fixture, expand
the corpus, or begin a new UI/provider feature before that review.

Authoritative execution state:

- [`docs/BRAIN_RELEASES.md`](docs/BRAIN_RELEASES.md) — release milestones and active sequence
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — long-term product and engineering roadmap
- [`docs/ROADMAP_STATUS.md`](docs/ROADMAP_STATUS.md) — implemented, active, and parked work
- [`docs/POST_WATCH_OUTCOME_CAPTURE_V1.md`](docs/POST_WATCH_OUTCOME_CAPTURE_V1.md) — current operating contract
- [`docs/UNIFIED_EVALUATION_EXPERIENCE_V1.md`](docs/UNIFIED_EVALUATION_EXPERIENCE_V1.md) — human-facing evaluation and manual fallback

## What is production-ready

### Canonical memory

- Ingests complete Letterboxd CSV exports and manual watches.
- Reconciles CSV, RSS, and manual sources without losing viewing events or rewatches.
- Preserves provenance and detects duplicates, malformed records, and conflicts.
- Builds a normalized SQLite database with deterministic watched-film exclusion.
- Safely synchronizes Daniel's recent `dmarlin` Letterboxd RSS history.

### Reviewed film and taste intelligence

- Maintains a versioned canonical trait registry.
- Preserves nine human-reviewed horror profiles and 45 approved trait assignments.
- Builds a deterministic Personal Taste Graph with positive evidence, negative
  evidence, contradictions, uncertainty, and explicit preferences kept distinct.
- Validates predictions with abstention rather than manufacturing confidence from
  sparse evidence.

### Recommendation Intelligence v0.3

- Builds a versioned horror recommendation corpus.
- Excludes watched and ineligible films before ranking.
- Produces raw explainable rankings and a diversity-aware balanced top-five slate.
- Freezes every eligible recommendation release behind fail-closed integrity gates.
- Creates immutable prediction snapshots with SHA-256 tamper detection.
- Generates a read-only Recommendation Audit keyed by `release_id`.
- Packages a local Brain Health Dashboard that renders verified audit data only.
- Packages a release-bound post-watch submission template.
- Exposes one mobile-ready evaluation page for pre-watch fit, post-watch outcome,
  release-bound export, and explicit manual handoff.
- Records rating, reaction, completion, glad-watched, and moment-fit evidence
  append-only.
- Calculates Recommendation Trust and versioned prediction error.
- Creates an unpromoted deterministic regression fixture when a recommendation
  meaningfully misses.

The North Star is **Recommendation Trust**: if Cinema Brain recommends five films,
how many is Daniel genuinely glad he watched?

## System flow and invariants

```text
Sources
  -> Canonical Memory
  -> Metadata Evidence
  -> Reviewed Film Identity and Traits
  -> Personal Taste Graph
  -> Candidate Ranking
  -> Balanced Slate
  -> Release Gates and Frozen Prediction
  -> Read-only Audit and Health Dashboard
  -> Append-only Outcome
  -> Human-reviewed Learning
```

These rules are binding across agents and interfaces:

1. GitHub `main` is the source of truth; do not treat chat history as newer than the repository.
2. Memory precedes prediction; watched films remain excluded unless a rewatch is requested.
3. Reviewed truth outranks provider or model inference.
4. Predictions, explanations, versions, and release identity freeze before Daniel reacts.
5. Audit and dashboard layers are read-only and cannot rerank or learn.
6. Outcomes append to a frozen `release_id`; they never alter the original prediction.
7. A miss creates review evidence, not an automatic taste-weight change.
8. Context and moment fit do not silently become permanent taste.
9. Required tests have no network dependency.
10. New work must improve the Intelligence Graph, recommendation quality, or measurable learning.

## Setup and validation

Cinema Brain supports Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .
python -m pip install pytest

python -m pytest -q
python -m cinema_brain ingest
python -m cinema_brain validate
python -m cinema_brain report
python -m cinema_brain taste
```

The required pull-request workflow in `.github/workflows/tests.yml` runs the full
unit suite, complete ingestion, normalized-database validation, baseline reporting,
Daniel Cinematic DNA generation, and artifact upload.

## Generate a frozen recommendation release

The private GitHub Actions workflow
`.github/workflows/unwatched-horror-ranking.yml` performs the production path:

1. ingest and validate canonical history;
2. build the Personal Taste Graph and explicit preference corrections;
3. rank eligible unwatched horror candidates;
4. build the balanced top-five slate;
5. enforce release gates and freeze the manifest and prediction snapshot;
6. build the verified Recommendation Audit;
7. package the read-only Brain Health Dashboard;
8. package the release-bound post-watch submission template.

Its private artifact contains:

```text
personal_taste_graph_v1.json
unwatched_horror_ranking_v1.json
unwatched_horror_balanced_slate_v1.json
recommendation_release_manifest_v1.json
recommendation_prediction_snapshot_v1.json
recommendation_audit_v1.json
brain_health_dashboard_v1.html
post_watch_outcome_submission_v1.json
```

The manifest, prediction snapshot, and audit are immutable inputs. Only the empty
outcome fields in `post_watch_outcome_submission_v1.json` are filled after viewing.

## Record the first real outcome

Open the [live unified evaluation page](https://brutisthebrut-debug.github.io/cinema-brain/evaluate.html).

Preferred path: import `post_watch_outcome_submission_v1.json` from the private
recommendation artifact. The page preserves the frozen release identity, limits
the film picker to the released slate, collects the full pre-watch and post-watch
reaction, and exports the exact submission contract below.

Manual path: complete the same questions without an import and use **Copy for
chat**. The manual record remains useful evaluation evidence, but it cannot count
as formal Recommendation Trust unless an agent verifies that a matching frozen
release existed before the watch. Never create or backdate a release after seeing
the outcome.

In the release-bound submission, preserve `version`, `submission_type`,
`release_id`, `audit_id`, and `released_predictions`. Fill only:

- `film_key` from the released slate;
- `watched_at` and `recorded_at` timestamps;
- `actual_rating` from 0.5 to 5.0;
- a non-empty one-sentence `reaction_text`;
- `completed` as `true` or `false`;
- `glad_watched` as `true` or `false`;
- `fit_the_moment` as `true`, `false`, or `null`.

Then run:

```bash
python -m cinema_brain.cli record-recommendation-outcome \
  --manifest recommendation_release_manifest_v1.json \
  --snapshot recommendation_prediction_snapshot_v1.json \
  --audit recommendation_audit_v1.json \
  --submission post_watch_outcome_submission_v1.json \
  --output-dir outcomes
```

The command creates one append-only directory:

```text
outcomes/<release_id>/<outcome_id>/
  recommendation_outcome_v1.json
  recommendation_regression_fixture_v1.json  # only when a reviewable miss occurs
```

Review the outcome's Recommendation Trust, projected-versus-actual rating error,
completion, moment fit, and regression reasons. If a fixture exists, it must remain
`candidate_not_promoted` until Daniel and the implementing agent inspect the exact
miss together.

## Agent implementation and handoff protocol

Every implementation slice uses the same production process:

1. Read this README, `docs/BRAIN_RELEASES.md`, the active contract, and recent merged PRs.
2. Confirm `main` and the working tree before editing.
3. Keep the change bounded to the documented next dependency.
4. Create an `agent/<description>` branch.
5. Add deterministic regression coverage for behavior changes.
6. Run the focused tests and the full repository suite locally.
7. Commit only intended files with clear, small commit messages.
8. Open a real GitHub pull request with scope, rationale, impact, validation, and handoff.
9. Wait for CI on the exact head SHA; never merge an untested or moved head.
10. Merge only when required checks pass.
11. Update this README, `docs/BRAIN_RELEASES.md`, relevant roadmap/status text,
    release notes, and a permanent contract whenever the production boundary moves.
12. Stop at the documented review boundary; do not activate the following milestone silently.

If GitHub CLI authentication is unavailable but the connected GitHub app has
verified write access, repository mutations may use its content-addressed
branch/commit/PR APIs. The same branch, tests, exact-head CI, and merge requirements
still apply.

## Documentation map

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layer ownership and contracts
- [`docs/FOUNDING_PRINCIPLES.md`](docs/FOUNDING_PRINCIPLES.md) — permanent doctrine
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — chronological decisions
- [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md) — shipped capability history
- [`docs/TECHNICAL_DEBT.md`](docs/TECHNICAL_DEBT.md) — intentional deferrals and triggers
- [`docs/RECOMMENDATION_RELEASE_GATES_V1.md`](docs/RECOMMENDATION_RELEASE_GATES_V1.md) — frozen release boundary
- [`docs/RECOMMENDATION_AUDIT_V1.md`](docs/RECOMMENDATION_AUDIT_V1.md) — read-only diagnostic contract
- [`docs/BRAIN_HEALTH_DASHBOARD_V1.md`](docs/BRAIN_HEALTH_DASHBOARD_V1.md) — dashboard boundary
- [`docs/POST_WATCH_OUTCOME_CAPTURE_V1.md`](docs/POST_WATCH_OUTCOME_CAPTURE_V1.md) — append-only outcome contract
- [`docs/UNIFIED_EVALUATION_EXPERIENCE_V1.md`](docs/UNIFIED_EVALUATION_EXPERIENCE_V1.md) — unified evaluation UI contract

## Privacy

Raw Letterboxd exports remain local and are ignored by Git by default. Generated
recommendation packages can contain Daniel-specific taste and behavioral evidence;
keep them in private workflow artifacts or local storage. Do not commit private
exports, outcome packages, or generated profiles unless Daniel intentionally
approves the exact evidence for durable promotion.
