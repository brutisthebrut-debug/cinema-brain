# Cinema Brain Studio

## Purpose

Cinema Brain Studio is the internal operating surface for building, reviewing, validating, and promoting Cinema Brain's intelligence.

It is not the consumer movie-discovery product. It is the place where trusted cinematic knowledge is created and maintained.

The first working surface is the canonical trait review UI. That small tool establishes the core Studio pattern:

```text
Review queue
  -> inspect evidence
  -> approve / edit / reject
  -> preserve reviewer decisions
  -> export or promote through guarded contracts
  -> run regression checks
```

## Product boundary

Studio may simplify an existing trusted workflow, but it must not bypass it.

Studio does not own canonical truth. It is a client of the same typed, versioned review and promotion contracts used by the CLI and GitHub Actions.

The following remain authoritative:

- canonical film identity
- trait registry and schema versions
- candidate profile records
- reviewer decision packets
- promotion validators
- regression gates
- immutable provenance and history

A UI action must produce the same auditable record as the equivalent CLI or workflow action.

## Near-term surfaces

### 1. Canonical Trait Review

Current implementation:

- import the guarded CSV worksheet
- review one trait assignment at a time
- approve, edit, or reject
- validate required edit and rejection fields
- autosave locally
- export the exact guarded CSV schema
- operate without a backend or third-party dependencies

### 2. Review Queue

A future queue should show bounded work rather than a generic dashboard.

Example:

```text
Review Queue
────────────
Horror profiles       45 assignments
Identity exceptions    3 films
Recommendation audit   5 scenarios
```

Each queue item must identify:

- input version
- review contract
- progress
- unresolved conflicts
- definition of done
- next guarded action

### 3. Promotion Readiness

After review, Studio should show whether a dataset is ready to advance.

```text
Promotion Ready
45 / 45 decisions complete
0 invalid edits
0 missing notes
9 / 9 films retain approved traits
```

Actions such as compile, promote, and regression should remain explicit and gated. Studio may trigger them later, but must display the exact version and expected outputs before execution.

### 4. Intelligence Inspection

Once reviewed profiles and Taste Intelligence exist, Studio can expose:

- film trait profiles
- evidence supporting each trait
- reviewer history
- contradictions and quarantined claims
- Daniel's supporting and contradicting taste evidence
- recommendation score components
- prediction-versus-outcome errors

This is inspection of real intelligence, not dashboard decoration.

## Long-term capability map

Studio may eventually support:

- identity resolution
- canonical trait authoring
- expert review queues
- benchmark promotion
- regression inspection
- taxonomy migrations
- recommendation audits
- contradiction resolution
- taste-vector inspection
- outcome calibration
- source and provider diagnostics

Potential reviewers may include Daniel, trusted genre experts, critics, or invited collaborators. Multi-reviewer support does not enter the active roadmap until reviewer identity, disagreement handling, access control, and provenance are explicitly designed.

## Admission test

A proposed Studio feature must satisfy at least one:

1. It reduces friction in an existing reviewed workflow.
2. It makes evidence, uncertainty, disagreement, or provenance easier to inspect.
3. It improves the speed or quality of a measurable intelligence task.
4. It exposes a capability that already exists in the engine without duplicating business logic.

If it only makes the project look more complete, it is not active work.

## Anti-drift rules

- The Intelligence Graph remains the active product milestone.
- Studio cannot invent a second schema or workflow.
- No backend is added until local/static operation is genuinely insufficient.
- No broad admin dashboard is built ahead of specific review work.
- No public or multi-user architecture is implied by an internal tool.
- UI polish cannot delay canonical profile promotion, Taste Intelligence, or recommendation validation.
- A Studio slice should be small enough to ship and validate independently.

## Definition of success

Cinema Brain Studio succeeds when a reviewer can complete a trusted intelligence task faster and with fewer errors, while producing the exact same versioned and auditable records as the underlying engine.
