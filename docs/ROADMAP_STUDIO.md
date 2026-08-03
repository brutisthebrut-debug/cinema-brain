# Cinema Brain Studio Roadmap

Status: companion roadmap

Owner: Cinema Brain

This roadmap captures the interface layer for building and inspecting Cinema Brain's intelligence. It is subordinate to `docs/ROADMAP.md` and must not interrupt the active sequence of canonical profile promotion, Taste Intelligence v1, and explainable recommendation validation.

## Position in the product

```text
Cinema Brain Engine
  -> typed intelligence contracts
  -> Cinema Brain Studio
  -> reviewer decisions and inspection
```

Studio is an internal operating surface, not a second source of truth.

## Completed — Studio Seed

- Dependency-free canonical trait review UI
- Mobile-first, one-assignment-at-a-time review
- Approve, edit, and reject controls
- Guarded validation for edits and rejections
- Local browser autosave
- Exact review CSV import and export
- No backend, network calls, or third-party framework
- CI contract tests
- GitHub Pages deployment path in progress

This is the first user-facing Cinema Brain surface and the first implementation of the Studio design language.

## Active bounded task — Publish the review UI

Definition of done:

1. GitHub Pages deployment workflow passes CI.
2. The deployment runs successfully from `main`.
3. The review interface is available at a stable HTTPS address.
4. The generated 45-row worksheet can be imported on mobile.
5. A partially completed review survives refresh in the same browser.
6. The exported CSV passes the existing guarded review compiler unchanged.

This task may complete in parallel with Daniel's current review because it does not alter candidate profiles or promotion logic.

## Next eligible Studio slice — Review Queue v1

This slice is not active until the current nine-film review is promoted or a real operational blocker proves it is needed sooner.

Scope:

- show imported worksheet name and version
- group progress by film
- jump to unresolved assignments
- identify edits and rejections
- show readiness summary before export
- preserve the exact CSV contract

Explicitly excluded:

- authentication
- database
- remote persistence
- multi-user review
- direct promotion
- generic dashboard navigation

## Later eligible slices

### Promotion Readiness

Expose compile and promotion prerequisites without bypassing GitHub or CLI safeguards.

### Intelligence Inspector

Inspect canonical film traits, evidence, confidence, reviewer history, and contradictions.

### Recommendation Audit

Display ranked candidates, hard-filter results, score components, evidence, caveats, and frozen predictions.

### Calibration Review

Compare predictions with actual outcomes and surface meaningful model errors.

### Expert Review

Support invited domain reviewers only after identity, permissions, disagreement resolution, and provenance contracts are designed.

## Sequencing rule

Studio work may enter active development only when one of these is true:

- it removes repeated manual friction from a workflow already in use
- it exposes intelligence needed to validate the current roadmap milestone
- it prevents review error or loss of provenance
- it is a very small usability layer that can ship without delaying engine work

## Parked Studio ideas

- public-facing Studio accounts
- community reviewer marketplace
- social review feeds
- leaderboards or reviewer scores
- broad content-management system
- real-time collaboration
- consumer discovery experience inside Studio
- native mobile application

## Current priority relationship

```text
1. Finish current canonical trait review
2. Compile and promote nine reviewed horror profiles
3. Build Taste Intelligence v1
4. Run first explainable recommendation validation
5. Improve Studio only where those steps reveal real friction
```

Studio is the beginning of the visible brain, but the intelligence remains the product foundation.
