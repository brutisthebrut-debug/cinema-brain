# Cinema Brain Releases

Updated: 2026-08-03

This companion roadmap tracks measurable increases in Cinema Brain intelligence. It does not replace `docs/ROADMAP.md`; it translates the active roadmap into release milestones.

## Brain v0.1 — Canonical Horror Foundation

Status: complete and merged to `main`

Includes:

- canonical trait registry v1
- nine reviewed horror profiles
- 45 human-approved trait assignments
- immutable review decision packet
- guarded profile promotion
- canonical review UI
- Cinema Brain Studio foundation
- optional GitHub Pages deployment path

Definition of done:

- reviewed worksheet is committed
- decision packet is committed
- promoted profile dataset passes CI
- release PR is merged to `main`
- release is recorded in release notes

## Brain v0.2 — Personal Taste Graph

Status: engine complete; calibration evidence remains an ongoing input

Goal: convert Daniel's durable film evidence into a versioned, explainable taste model.

Shipped:

1. Deterministic user-to-trait affinity model.
2. Separate positive evidence, negative evidence, contradictions, and uncertainty.
3. Distinct weighting for ratings, likes, rewatches, written reactions, outcomes, and explicit preferences.
4. Supporting and contradicting films for learned affinities.
5. Versioned personal taste graph artifacts generated from persisted history.
6. Explainable scoring of the nine canonical horror films.
7. Leave-one-film-out validation with positive, neutral, and negative outcomes.
8. Abstention when coverage or active evidence is too thin.
9. Single-trait dominance detection.
10. Explicit preference correction that preserves provenance.
11. Benchmark reaction calibration that separates overall film enjoyment from admiration of individual craft traits.
12. Internal calibration Studio tooling, intentionally paused as optional tooling rather than a production dependency.

Evidence from the first production validation:

- nine benchmark folds
- five eligible predictions
- four abstentions
- two correct eligible classifications
- calibrated mean absolute error of 0.602
- four single-trait-dominated predictions

Interpretation:

The engine is deterministic, explainable, and appropriately willing to abstain. The current benchmark remains too small and several imported watch records lack strong reaction evidence. Brain v0.3 must therefore preserve confidence limits and avoid presenting sparse predictions as certainty.

Definition of done:

- the same frozen inputs reproduce the same taste profile
- every affinity has an inspectable evidence trail
- sparse traits remain uncertain rather than overfit
- Daniel-specific reactions remain distinguishable from general film truth
- the profile can score canonical films without hidden prompt logic
- validation can abstain instead of manufacturing confidence

## Brain v0.3 — Recommendation Intelligence

Status: active production validation; corpus and ranking are complete through PR
#60, and release gates, audit, health inspection, and post-watch outcome capture are
complete through PR #64. The original evaluation UI and the release-bound outcome
contract are unified in Unified Evaluation Experience v1. The first real outcome
has been reviewed through Manual Outcome Reconciliation v1.

Goal: produce bounded, explainable recommendations for eligible unwatched films while measuring whether Daniel would actually be glad he watched them.

### Milestone 1 — Versioned recommendation corpus

Build a curated horror-first candidate pool before attempting broad catalog search.

Deliverables:

- versioned candidate corpus contract
- canonical identity and duplicate validation
- watched and already-known exclusion
- required metadata and trait coverage report
- provenance for every candidate trait profile
- deterministic corpus build
- initial small evaluation corpus before expansion to hundreds of films

Definition of done:

- every candidate has one canonical film identity
- every scored trait resolves to the canonical registry
- invalid or insufficiently covered films are quarantined rather than silently scored
- corpus builds are reproducible from frozen inputs

### Milestone 2 — Explainable recommendation ranking

Deliverables:

- typed request planning
- hard-filter and soft-preference separation
- candidate retrieval from the versioned corpus
- trait-based film similarity
- personal-fit score components
- confidence and coverage reported separately
- diversity and novelty controls
- why-this, why-now, caveat, and alternative explanations
- frozen prediction record before outcome capture
- abstention when evidence is insufficient

Production state: complete through the raw-ranking and diversity-aware balanced-slate production artifacts merged in PR #60.

A recommendation must distinguish:

- liking a craft element from liking the whole film
- strong learned evidence from provisional evidence
- positive fit from uncertainty
- close similarity from useful discovery

### Milestone 3 — Recommendation validation

Primary metrics:

- Precision@5
- Precision@10
- recommendation acceptance
- recommendation completion
- predicted-versus-actual error
- confidence calibration
- diversity
- novelty
- explanation coverage
- abstention quality

North-star metric: **Recommendation Trust**

> If Cinema Brain recommends five films, how many is Daniel genuinely glad he watched?

Initial release gate:

- run a small, frozen unwatched candidate batch
- preserve predictions before Daniel reacts
- collect outcomes without rewriting the original prediction
- inspect every miss and overconfident recommendation
- do not claim production-quality recommendation accuracy from the nine-film training benchmark

#### Recommendation Release Gates v1

Status: implemented as the active Brain v0.3 release boundary.

Shipped:

- fail-closed version, accounting, ranking, slate, watched-exclusion, prediction-quality, and slate-metric checks
- a versioned recommendation manifest with complete gate results and input digests
- a create-once prediction snapshot frozen before human outcome capture
- content-addressed release identity and tamper verification
- production workflow upload of the manifest and snapshot beside the raw and balanced artifacts
- regression coverage for eligible release, watched overlap, tampering, and overwrite prevention
- permanent contract and agent handoff in `docs/RECOMMENDATION_RELEASE_GATES_V1.md`

#### Recommendation Audit v1

Status: implemented as the active read-only diagnostic contract over frozen releases.

Shipped:

- fail-closed manifest-to-snapshot cross-link verification
- deterministic audit identity keyed to `release_id` and the frozen snapshot digest
- complete release-gate and count reconciliation
- raw-to-balanced rank movement inspection
- abstention reason and rate inspection
- released-prediction evidence coverage
- read-only Brain health metrics and an explicit awaiting-outcome state
- create-once audit output and regression coverage
- permanent contract and agent handoff in `docs/RECOMMENDATION_AUDIT_V1.md`

#### Brain Health Dashboard v1

Status: implemented as the thin read-only Studio surface over Recommendation Audit v1.

Shipped:

- local import of the verified `recommendation_audit_v1.json` artifact
- release identity, integrity, gate, count, rank-movement, abstention, and evidence-coverage views
- explicit awaiting-outcome boundary keyed by `release_id`
- dependency-free, mobile-ready, private operation with no network or browser storage
- fail-closed rejection of wrong-version, unverified, failed-gate, or post-outcome audit records
- production artifact packaging and regression coverage
- permanent contract and agent handoff in `docs/BRAIN_HEALTH_DASHBOARD_V1.md`

#### Post-watch Outcome Capture v1

Status: implemented as the append-only Learning-layer contract over frozen releases.

Shipped:

- a release-bound submission template containing only the eligible balanced slate
- fail-closed manifest, snapshot, audit, `release_id`, `audit_id`, and `film_key` verification
- explicit rating, one-sentence reaction, completion, glad-watched, and moment-fit evidence
- deterministic prediction error using a versioned taste-score-to-rating projection
- Recommendation Trust measured directly from whether Daniel is genuinely glad he watched
- append-only outcome directories and deterministic regression fixtures for misses
- aggregate Recommendation Trust, completion, moment-fit, and calibration summaries
- production artifact packaging, CLI capture, regression coverage, and a permanent handoff

#### Unified Evaluation Experience v1

Status: implemented as the single thin client over original human evaluation and
Post-watch Outcome Capture v1.

Shipped:

- one mobile page for pre-watch fit and post-watch outcome evidence;
- local import of the release-bound submission template;
- exact Outcome Capture v1 export without changing immutable identity fields;
- a copyable manual handoff when the private artifact is unavailable;
- explicit exclusion of unverified manual intake from Recommendation Trust;
- migration of existing Human Evaluation Pack v1 browser answers by `film_key`;
- no network requests, ranking logic, trust calculation, or taste mutation.

#### Manual Outcome Reconciliation v1

Status: implemented as the fail-closed transition contract for manual outcomes
from predictions frozen before Recommendation Release Gates v1.

Shipped:

- exact source-artifact, film-identity, and pre-watch timing verification;
- explicit separation of observed legacy trust from formal release-bound trust;
- no invented or backdated `release_id`;
- provisional rating calibration with a separately named projection method;
- deterministic, unpromoted review candidates for meaningful misses;
- append-only private outcome storage and a CLI workflow;
- first-outcome review for Noroi: The Curse (2005).

First evidence:

- completed, glad watched, fit the moment, 3.5/5, `like`, and would recommend;
- observed legacy trust 1.0 from one verified manual outcome;
- formal release-bound Recommendation Trust remains unmeasured;
- the 0.888 legacy score projected to 4.748/5, creating an unpromoted
  calibration candidate for a 1.248-star absolute error and confidence 0.678.

Next validation work:

1. Capture a second outcome from the already frozen top five or a new
   release-bound slate and compare its calibration evidence with Noroi.
2. Decide whether narrative legibility is a durable missing dimension only after
   repeated evidence, not from one note.
3. Expand the horror benchmark only when measured outcome gaps justify the next films.

### Milestone 4 — Continuous learning

Deliverables:

- recommendation outcome capture
- focused post-watch questions
- graph updates from overall enjoyment and trait-specific reactions
- preference drift snapshots
- contradiction and regret analysis
- confidence recalibration
- deterministic recommendation regression fixtures

## Brain v0.4 — Blind Spots and Calibration

Goal: identify likely hidden favorites and measure whether the brain is improving over time.

Deliverables:

- blind-spot discovery
- prediction error tracking
- confidence calibration
- recommendation regression
- taste drift snapshots
- regret and contradiction analysis
- cross-cluster discovery without collapsing into popularity ranking

## Brain v1.0 — Cross-Genre Cinema Intelligence

Definition of done:

- trusted cross-genre canonical coverage
- measurable recommendation quality
- durable continuous learning
- explainable personal recommendations
- Cinema Brain Studio supports review, inspection, and promotion without bypassing engine contracts

## Brain health metrics

Track intelligence quality rather than code volume:

- canonical film count
- reviewed trait assignments
- candidate corpus size
- trait coverage
- evidence diversity
- conflict rate
- explainability coverage
- recommendation acceptance and completion
- Recommendation Trust
- predicted-versus-actual error
- confidence calibration
- abstention rate and abstention quality
- diversity and novelty
- regression pass rate
- release-gate pass and failure reasons
- prediction-snapshot integrity
- frozen releases awaiting outcome evidence
- review backlog

## UI and Studio boundary

The internal review and calibration interfaces remain useful prototypes and future Studio foundations, but they are not required for Brain v0.3 production.

New UI work is paused unless it:

- renders the stable Recommendation Audit and Brain Health contracts without owning engine logic,
- removes friction from an active intelligence validation task,
- exposes evidence required to diagnose a recommendation,
- or remains a small bounded layer over an already-stable engine contract.

The private engine repository will not be made public merely to host internal static tooling. Hosting may be revisited after recommendation quality earns a visible product surface.

## Anti-drift rule

A task enters active production only when it strengthens the current release's definition of done or records a necessary future dependency without activating it.

The active sequence is:

1. preserve Brain v0.1 canonical truth
2. use Brain v0.2 taste and calibration contracts as the scoring foundation
3. preserve the merged versioned recommendation corpus
4. preserve the merged raw ranking and diversity-aware balanced slate
5. enforce Recommendation Release Gates v1 and freeze the prediction manifest and snapshot
6. preserve Recommendation Audit v1 as the read-only diagnostic contract
7. preserve Brain Health Dashboard v1 as the thin read-only audit surface
8. collect post-watch outcomes through the unified evaluation experience, binding
   them by `release_id` when verified and reconciling pre-gate manual evidence
   without mixing the two trust populations
9. preserve the reviewed Noroi outcome and its unpromoted calibration candidate
10. collect a second frozen outcome before changing calibration or taste dimensions
11. expand corpus and confidence only when repeated outcome evidence supports it
