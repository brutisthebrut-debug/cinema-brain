# Cinema Brain Roadmap Governance

Updated: 2026-08-02

This document governs how the product roadmap evolves. `docs/ROADMAP.md` remains the long-term product vision, while `docs/ROADMAP_STATUS.md` records validated execution status.

## Build capabilities, not isolated features

Cinema Brain is organized around reusable capabilities:

1. Canonical identity and durable memory
2. Metadata enrichment and normalization
3. Provenance-aware evidence extraction
4. Taste modeling and profile versioning
5. Context and request interpretation
6. Candidate generation and explainable ranking
7. Outcome capture and calibration
8. Discovery, contradiction, and taste evolution

A named experience such as Horror DNA, Comedy DNA, or a dashboard must consume these shared capabilities rather than create parallel logic.

## Active epic: Metadata Intelligence

The Foundation epic is complete enough to support live operation. Metadata Intelligence is now the active production epic.

### Scope

- licensing-compatible provider adapters
- retries, rate limiting, caching, and safe resume
- field-level provenance and confidence
- canonical genre, country, language, runtime, release, credit, and keyword normalization
- reusable signal extraction rather than genre-only labeling
- conversion of film signals into Evidence Graph records
- bounded horror enrichment before whole-library expansion

### Definition of done

Metadata Intelligence is complete when:

- a canonical film can be enriched through a replaceable provider interface
- each stored fact retains provider, retrieval time, confidence, and raw payload
- enrichment is cached, reproducible, resumable, and idempotent
- missing, stale, conflicting, and low-confidence metadata are visible
- selected facts and interpretive signals produce provenance-aware Evidence records
- a bounded horror sample passes identity review and regression tests
- the broader Horror DNA profile materially expands beyond manually written reactions
- the full real-data CI pipeline passes

## Stable recommendation interface

The recommendation engine is treated as a stable application interface even while Cinema Brain remains private.

Conversation, CLI, future dashboard, and future Daniel OS integrations must consume the same typed request and recommendation contracts. Interface layers must not contain independent ranking logic or query the database directly for recommendations.

## Engineering metrics

Every milestone must improve or protect at least one measurable property:

- canonical film count
- watched-event count
- metadata coverage and completeness
- stale or conflicting metadata count
- evidence count and evidence-source diversity
- duplicate and unresolved-identity rate
- sync reliability and duration
- recommendation acceptance, completion, and prediction error
- confidence calibration
- test count, regression coverage, and pipeline runtime

Metrics describe system health; they are not vanity targets. A larger evidence count is not automatically better if provenance or confidence declines.

## Technical debt policy

Intentional deferrals are recorded in `docs/TECHNICAL_DEBT.md` with:

- the deferred issue
- why it was deferred
- current risk
- trigger for reconsideration
- intended owner or epic

Nothing is silently postponed.

## Architecture Decision Records

Material architectural decisions are recorded under `docs/adr/`.

An ADR must capture:

- context
- decision
- alternatives considered
- consequences
- status

ADRs explain why the architecture exists; commit history explains how it changed.

## Major-merge definition of done

A major milestone is complete only when:

1. The capability works against realistic data.
2. Unit and integration tests pass.
3. Failure and replay behavior are defined.
4. Provenance and model/schema versions are preserved.
5. Documentation and roadmap status match the implementation.
6. The full real-data validation pipeline passes.
7. Any intentional deferral is added to the technical-debt register.

## Roadmap change discipline

Roadmap changes should be earned by implementation evidence, provider constraints, observed failures, or measured user value. New ideas are welcomed, but they do not automatically become active commitments.
