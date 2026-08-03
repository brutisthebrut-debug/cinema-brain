# Canonical Trait Registry v1

The canonical trait registry is the shared language for authored film meaning, Daniel-specific evidence, taste profiles, and recommendation explanations.

## Source of truth

`config/trait_registry_v1.json` is the authoritative registry. Trait IDs are stable API identifiers. Labels and descriptions may improve without changing an ID's meaning.

Each trait declares:

- `id` — stable snake-case identifier
- `label` — human-readable name
- `family` — one owning conceptual group
- `description` — boundary of the trait's meaning
- `kind` — `fact`, `interpretation`, `community_prior`, `daniel_evidence`, or `context`
- `value_type` — `continuous`, `binary`, or `categorical`
- `polarity` — `positive`, `negative`, `neutral`, or `contextual`
- `aliases` — phrases that resolve to the canonical ID
- optional deprecation and replacement metadata

## Architectural rules

1. Provider facts never become Daniel preferences automatically.
2. Interpretive film traits and Daniel's personal responses remain separate evidence classes.
3. Context traits describe suitability for a moment, not permanent quality.
4. Aliases may improve recall but may not ambiguously resolve to multiple canonical traits.
5. A trait ID is never silently repurposed. Meaningful replacement requires deprecation and `replaced_by`.
6. Every authored trait value must eventually carry source, author or model, confidence, observed time, and registry version.

## Current scope

The v1 seed emphasizes the approved horror benchmark and contains more than 50 traits across:

- fear mechanisms and horror modes
- pacing, narrative form, endings, performance, and craft
- emotional tone, themes, and effects
- viewing context and experience
- explicit Daniel responses

This is intentionally smaller than the eventual registry. New traits should be added only when benchmark authoring proves that an existing trait cannot express a meaningful distinction.

## Python contract

`cinema_brain.trait_registry` provides:

- strict registry validation
- immutable typed trait definitions
- canonical lookup
- alias resolution
- family grouping
- a compatibility projection for the existing taste taxonomy
- a deterministic registry report

## Definition of done for the next slice

The registry becomes active production infrastructure when:

1. the existing taste profile loads its families and aliases from the canonical registry;
2. nine approved horror benchmark films have versioned authored trait profiles;
3. authored values retain reviewer, confidence, evidence note, and registry version;
4. a review and promotion gate protects canonical film-trait profiles;
5. recommendation explanations can cite authored traits and Daniel evidence independently.
