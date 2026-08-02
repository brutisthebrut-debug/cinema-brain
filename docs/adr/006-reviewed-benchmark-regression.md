# ADR 006: Reviewed records become executable regression truth

## Decision

Only human-reviewed golden records may gate live metadata identity and trait extraction. Seed records remain informative but non-gating.

## Consequences

- A release cannot claim benchmark protection until at least one record is reviewed.
- Accepted aliases and exact release years protect canonical identity.
- Expected traits protect deterministic extraction behavior.
- Missing reviewed films fail visibly rather than being skipped.
- Provider or taxonomy changes must preserve reviewed outcomes or receive an explicit benchmark review.