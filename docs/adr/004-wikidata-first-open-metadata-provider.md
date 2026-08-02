# ADR 004: Wikidata is the first open metadata provider

- Status: Accepted for bounded validation
- Date: 2026-08-02

## Context

Cinema Brain needs film facts that can safely support private AI-assisted analysis without locking the system to one commercial provider. The provider must fit the existing replaceable metadata contract, preserve provenance, avoid credentials where possible, and tolerate incomplete coverage without corrupting canonical film identity.

TMDB was rejected after terms review because its API terms create unacceptable uncertainty for this AI-assisted use case.

## Decision

Use Wikidata as the first live metadata provider.

The adapter is read-only and uses Wikidata structured data. It sends a descriptive User-Agent and observes conservative access behavior. Before storing a result, Cinema Brain requires:

1. strong normalized title similarity,
2. an exact release-year match when the canonical film has a year, and
3. a recognized film instance type.

The first mapped fields are genres, directors, principal cast, country of origin, original language, runtime, and main subjects. All facts remain tagged with `provider=wikidata`, retrieval time, and match confidence.

Enrichment is bounded, cached, resumable, and produces explicit misses and failures. A miss is preferable to a guessed match.

## Consequences

- No API key or secret is required.
- Structured data is compatible with the project's licensing requirements.
- Coverage will be uneven and must be measured rather than assumed.
- Some interpretive horror signals will require a later evidence-extraction layer; Wikidata facts are not treated as Daniel preference evidence by themselves.
- A second provider can be added later without changing metadata consumers.
- Whole-library enrichment is prohibited until a bounded horror sample is manually reviewed.

## Validation requirements

- Hermetic tests must cover title/year collisions, non-film entities, field mapping, User-Agent behavior, rate-limit retry, cache resume, and per-film failure isolation.
- The first real sample must publish a reviewable enrichment report before scaling.
