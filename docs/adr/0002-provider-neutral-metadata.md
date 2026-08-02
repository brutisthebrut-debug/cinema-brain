# ADR-002: Provider-neutral metadata and licensing compatibility

- Status: Accepted
- Date: 2026-08-02

## Context

Cinema Brain needs film facts and interpretive signals, but third-party providers differ in licensing, reliability, coverage, and identity quality. TMDB was rejected after its terms created unacceptable risk for an AI-assisted recommendation project.

## Decision

Keep metadata adapters replaceable behind typed contracts. Accept only providers whose licensing is compatible with the project. Preserve provider, retrieval time, confidence, and raw payload for every enrichment record.

## Alternatives considered

- Couple directly to one commercial provider: rejected because it creates licensing and migration risk.
- Skip metadata enrichment: rejected because recommendations would remain overly dependent on ratings and written reactions.

## Consequences

Initial implementation may take longer, but future providers can be replaced or combined without rewriting taste and recommendation layers.
