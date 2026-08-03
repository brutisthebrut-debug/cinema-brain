# Cinema Brain Releases

Updated: 2026-08-03

This companion roadmap tracks measurable increases in Cinema Brain intelligence. It does not replace `docs/ROADMAP.md`; it translates the active roadmap into release milestones.

## Brain v0.1 — Canonical Horror Foundation

Status: promotion in progress

Includes:

- canonical trait registry v1
- nine reviewed horror profiles
- 45 human-approved trait assignments
- immutable review decision packet
- guarded profile promotion
- canonical review UI
- Cinema Brain Studio foundation
- GitHub Pages deployment path

Definition of done:

- reviewed worksheet is committed
- decision packet is committed
- promoted profile dataset passes CI
- release PR is merged to `main`
- release is recorded in release notes

## Brain v0.2 — Personal Taste Graph

Status: next active release

Goal: convert Daniel's durable film evidence into a versioned, explainable taste model.

Deliverables:

1. Build a deterministic user-to-trait affinity model.
2. Keep positive evidence, negative evidence, contradictions, and uncertainty separate.
3. Weight explicit ratings, likes, written reactions, rewatches, and outcome evidence distinctly.
4. Produce supporting and contradicting films for every learned affinity.
5. Add model and taxonomy versions to every generated taste profile.
6. Add regression fixtures using Daniel's real history.
7. Expose the first taste profile through Cinema Brain Studio only after the engine output is stable.

Definition of done:

- the same frozen inputs reproduce the same taste profile
- every affinity has an inspectable evidence trail
- sparse traits remain uncertain rather than overfit
- Daniel-specific reactions remain distinguishable from general film truth
- the profile can score the nine canonical horror films without hidden prompt logic

## Brain v0.3 — Explainable Recommendations

Goal: rank eligible unwatched films using canonical traits and the personal taste graph.

Deliverables:

- typed request planning
- hard-filter and soft-preference separation
- trait-based film similarity
- personal-fit score components
- calibrated confidence
- why-this, why-now, caveat, and alternative explanations
- frozen prediction before outcome capture

## Brain v0.4 — Blind Spots and Calibration

Goal: identify likely hidden favorites and measure whether the brain is improving.

Deliverables:

- blind-spot discovery
- prediction error tracking
- confidence calibration
- recommendation regression
- taste drift snapshots
- regret and contradiction analysis

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
- trait coverage
- evidence diversity
- conflict rate
- explainability coverage
- recommendation acceptance and completion
- predicted-versus-actual error
- confidence calibration
- regression pass rate
- review backlog

## Anti-drift rule

A Studio or interface task may enter active work only when it:

- removes friction from the current release,
- exposes intelligence needed for validation, or
- remains a small bounded layer over an already-stable engine contract.

The active sequence is:

1. ship Brain v0.1
2. build Brain v0.2
3. validate the first explainable recommendation
4. expand the horror benchmark based on measured gaps
