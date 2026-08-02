# Cinema Brain Architecture

## Purpose

Cinema Brain is a private, explainable personal recommendation system. Its job is not to collect movie data for its own sake. Its job is to turn Daniel's durable viewing history, explicit reactions, current mood, and live availability into better decisions while preserving evidence and learning from mistakes.

## System rule

Every layer must consume a stable contract from the layer below it and produce a stable contract for the layer above it. No feature may bypass the memory layer, hide provenance, or write directly into another layer's internal tables.

## End-to-end flow

1. **Acquire** — untouched Letterboxd exports, manual watches, explicit reactions, and future recommendation outcomes.
2. **Normalize** — reconcile films and viewing events into canonical records without losing source identity.
3. **Enrich** — attach versioned metadata and traits with provider, retrieval date, and confidence.
4. **Model** — convert explicit and behavioral evidence into a versioned Cinematic DNA profile.
5. **Plan** — turn a natural-language request into explicit hard filters, preferences, and context.
6. **Rank** — score eligible unwatched candidates and retain component-level explanations.
7. **Verify** — check live availability separately from stable movie and taste data.
8. **Recommend** — return a small set of options with predicted score, confidence, evidence, and caveat.
9. **Learn** — log the recommendation, actual outcome, prediction error, and any durable lesson.

## Bounded contexts

### Memory
Owns source files, canonical films, viewing events, reviews, lists, likes, watchlist state, and manual watches.

### Metadata
Owns external factual attributes and provider provenance. It never declares whether Daniel likes a trait.

### Taste
Owns signal weights, trait evidence, affinity, confidence, and time-scoped profile snapshots. It never decides live availability.

### Context
Owns the current request: mood, desired destination, energy, company, runtime, subtitle tolerance, intensity, novelty, location, and active services.

### Recommendation
Owns candidate filtering, ranking, prediction, explanation, and risk. It reads from Memory, Metadata, Taste, Context, and Availability through contracts.

### Availability
Owns current service verification with location and timestamp. Availability is disposable cache, not permanent truth.

### Learning
Owns recommendation attempts, outcomes, prediction errors, explicit corrections, and calibration history.

## Canonical contracts

### Film identity

```json
{
  "film_key": "title:undertone:2025",
  "name": "Undertone",
  "year": 2025,
  "external_ids": {},
  "provenance": []
}
```

### Trait evidence

```json
{
  "film_key": "title:undertone:2025",
  "trait": "creeping_dread",
  "polarity": 1,
  "strength": 3.5,
  "source_type": "explicit_reaction",
  "source_text": "It honestly scared me like The Blair Witch.",
  "confidence": 1.0,
  "model_version": "taste-0.2.0"
}
```

### Watch request

```json
{
  "genres": ["horror"],
  "moods": ["creepy"],
  "desired_destination": ["genuinely_scared"],
  "max_runtime_minutes": 120,
  "active_services": ["max", "peacock", "paramount_plus"],
  "location": "US-NC-Charlotte",
  "exclude_watched": true,
  "novelty": "new"
}
```

### Recommendation result

```json
{
  "film_key": "title:example:2026",
  "predicted_rating": 4.2,
  "confidence": 0.78,
  "score_components": {
    "taste_fit": 0.82,
    "mood_fit": 0.91,
    "context_fit": 0.88,
    "novelty": 0.55,
    "quality_floor": 0.70
  },
  "evidence": [],
  "caveat": "May lean more psychological than supernatural.",
  "availability": {
    "service": "paramount_plus",
    "verified_at": "2026-08-02T00:00:00Z"
  }
}
```

## Versioning

The system uses independent versions for:

- database schema
- importer
- film identity policy
- metadata provider adapters
- trait taxonomy
- taste weights
- request parser
- ranking model
- explanation renderer

A generated profile or recommendation must record all relevant versions. This allows old predictions to be reproduced and compared fairly after the model improves.

## Provenance rules

1. Explicit Daniel feedback outranks inferred metadata.
2. Raw evidence is immutable; corrections create superseding evidence.
3. Every inferred trait records its source and confidence.
4. Third-party metadata cannot silently overwrite explicit labels.
5. Recommendations retain the exact model versions and evidence used.
6. Failed recommendations remain visible and become calibration data.

## Sustainability rules

- Pure scoring functions wherever possible.
- Typed domain objects at layer boundaries.
- Database access isolated in repositories rather than spread across scoring code.
- Provider adapters behind interfaces with cached responses.
- Deterministic tests for ingestion, filtering, scoring, and explanation.
- Golden integration scenarios for real user requests.
- No network dependency in unit tests.
- No dashboard logic inside the core engine.
- No secrets or raw personal exports in public artifacts.

## 10x review gate

Before adding or changing a feature, ask:

1. Does this improve a real decision Daniel makes?
2. Which layer owns it?
3. What stable input and output contract does it use?
4. How is provenance preserved?
5. How will it be tested independently and end-to-end?
6. How does it affect existing predictions and versioning?
7. Can Daniel correct it explicitly?
8. Does it create drift, duplication, or hidden coupling?
9. Is there a simpler implementation with equal user value?
10. What would make the feature ten times more useful without making the system ten times harder to maintain?

## Initial golden scenario

**Request:** Daniel is in Charlotte at 2 AM, watching with dogs, has Max, Peacock, and Paramount+, and wants a creepy horror film that feels genuinely unsettling.

**Known evidence:** *Undertone* received four stars and worked because of Blair Witch-like creeping dread and sustained uncertainty.

**Required behavior:**

- Exclude all watched films.
- Restrict to currently verified services.
- Favor creeping dread, realism, sustained uncertainty, isolation, and atmosphere.
- Penalize generic jump-scare dependence when evidence supports doing so.
- Return a predicted rating, confidence, strongest evidence, and one meaningful caveat.
- Log the prediction and compare it with the post-watch reaction.
