# Cinema Brain Roadmap

## North Star

Build a private, durable, explainable model of Daniel's cinematic taste that becomes more accurate after every watch, rating, review, recommendation, and conversation.

Cinema Brain is the movie intelligence module of Daniel OS. It should remember what Daniel has seen, understand why films work or fail for him, recommend the right unwatched film for the moment, and learn from the outcome without rewriting history.

## Product doctrine

1. **Memory before prediction.** Never recommend a watched film unless a rewatch is requested.
2. **Reviewed truth before scale.** Provider or model output is evidence until a human-approved process promotes it.
3. **Why matters more than stars.** Reactions, effects, and contradictions carry more information than ratings alone.
4. **Explain every recommendation.** Confidence must connect to real evidence and reviewed traits.
5. **Positive and negative taste remain separate.** Disliking one mechanism is not the same as loving its opposite.
6. **Context is not permanent taste.** Tonight's mood and desired effect must not silently rewrite Daniel's long-term profile.
7. **Preserve provenance and disagreement.** Raw sources, provider claims, inferences, corrections, and outcomes remain distinguishable.
8. **Human correction wins.** Daniel can override inference without erasing the original evidence.
9. **Private by default.** Personal behavioral and preference data stays under Daniel's control.
10. **Intelligence before interface.** Dashboards and public features wait until recommendation quality is measurable.
11. **Contracts before coupling.** Layers exchange typed, versioned records.
12. **Failures become fixtures.** Every real failure should improve the benchmark, tests, or policy.

## Roadmap admission test

A proposed active feature must answer at least one of these:

- Does it improve the Intelligence Graph?
- Does it improve recommendation quality?
- Does it create a measurable learning or validation signal?

If not, it belongs in the ideas backlog rather than the active roadmap.

---

# System flow

```text
Sources
  -> Canonical Memory
  -> Metadata Evidence
  -> Reviewed Film Identity
  -> Canonical Trait Graph
  -> Daniel Taste Vector
  -> Context and Request Plan
  -> Candidate Filtering and Ranking
  -> Live Availability Verification
  -> Recommendation Explanation
  -> Outcome Logging
  -> Calibration and Taste Evolution
```

Conversation, CLI, and any future dashboard are clients of this pipeline. They do not own intelligence logic.

---

# Completed foundation

## Reliable memory

- Full Letterboxd export ingestion and validation
- Canonical film identity and watched exclusion
- Diary, ratings, reviews, likes, watchlist, and lists
- Manual updates
- Letterboxd RSS delta ingestion
- CSV/RSS/manual reconciliation with replay protection
- Safe live RSS synchronization for `dmarlin`

## Durable evidence and learning

- Canonical Evidence Graph
- Immutable provenance-aware evidence
- Positive and negative aggregation
- Conflict preservation
- Model-version filtering
- Evidence-backed Cinematic DNA
- Frozen recommendation and outcome ledgers

## Metadata Intelligence Phase 1

- Replaceable provider contract and canonical metadata storage
- Wikidata enrichment with strict title/year/film-type validation
- Deterministic cache and safe resume
- Compression and corrupt-cache recovery
- Retry, pacing, rate-limit backoff, and `Retry-After` support
- Per-film failure isolation
- Deterministic metadata-to-Evidence extraction
- Versioned horror benchmark seed
- Human review worksheet and decision packet
- Guarded benchmark candidate generation
- Candidate validation and reviewed-regression gates
- Successful real-data run with nine exact horror-film matches

Metadata Intelligence Phase 1 was formally released into Brain v0.1. Its reviewed
canonical truth remains protected while Brain v0.3 validates real recommendations.

---

# Active Phase — Intelligence Graph

The active work is no longer more provider plumbing. It is creating a trustworthy semantic model of what films are and how Daniel experiences them.

## Phase 1A — Canonical Trait Model v1

Create a bounded vocabulary with explicit definitions and boundaries.

### Trait families

- **Emotional tone:** dread, warmth, melancholy, grief, awe, wonder, loneliness, catharsis, chaos
- **Desired effect:** scared, comforted, moved, energized, unsettled, amused, intellectually engaged
- **Fear mechanisms:** creeping dread, jump scares, isolation, loss of control, body violation, occult threat, uncanny realism, pursuit, confinement, contamination
- **Narrative form:** linear, nonlinear, mystery-box, dream logic, procedural, episodic, ambiguous reality
- **Pacing and intensity:** slow burn, escalating, relentless, quiet, meditative, uneven, front-loaded
- **Visual and sonic style:** naturalistic, expressionistic, practical-effects-forward, long takes, handheld, found footage, sound-driven, minimal dialogue
- **Themes:** grief, identity, intimacy, family, faith, alienation, obsession, mortality, transformation, social collapse
- **Ending type:** closed, open, ambiguous, bleak, cathartic, twist-dependent, unresolved
- **Viewing value:** rewatchability, conversation value, background suitability, full-attention demand
- **Guidance:** watch when, avoid when, audience fit, tolerance requirements

### Requirements

- canonical IDs and aliases
- family ownership and definitions
- polarity and confidence
- fact, provider interpretation, model inference, community prior, and Daniel evidence kept separate
- contradictions allowed
- versioned schema and migrations
- human correction and review provenance

### Definition of done

- Trait Model v1 validates deterministically.
- Ambiguous overlaps have documented rules.
- The nine reviewed horror films receive complete canonical trait profiles.
- The schema is frozen before the recommendation engine depends on it.

## Phase 1B — Trait Authoring and Promotion

```text
Canonical film
  -> facts and existing Evidence
  -> candidate trait profile
  -> review worksheet
  -> approve / reject / quarantine
  -> promoted canonical profile
  -> regression gate
```

### Requirements

- no hand-authored JSON required for routine review
- every promoted trait records reviewer, reason, evidence, timestamp, and version
- candidate generation can assist but cannot approve itself
- rejected and quarantined traits remain auditable
- profile history is append-only or superseded, never silently rewritten
- failures produce regression fixtures

### Definition of done

- All nine benchmark films pass the authoring and promotion workflow.
- Re-running the workflow produces the same candidate from the same inputs.
- A taxonomy change cannot silently change reviewed historical truth.

---

# Next Phase — Taste Intelligence v1

Taste Intelligence maps reviewed film traits and Daniel's behavior into a personal preference model.

## Evidence classes

### Explicit

- rating
- like
- written review
- one-sentence reaction
- manual correction
- favorite or ranked-list placement
- specific effect confirmation such as “actually scared me”

### Behavioral

- rewatches
- recommendation acceptance or rejection
- started, completed, or abandoned
- watchlist conversion
- repeated creators, countries, eras, and trait clusters

### Contextual

- current mood
- desired emotional destination
- attention and energy
- alone, dogs, friends, or date
- time available
- subtitle, gore, sadness, ambiguity, and intensity tolerance
- novelty versus comfort

Contextual evidence expires or remains session-bound unless Daniel explicitly promotes it to stable preference.

## Required distinctions

- loved versus admired versus affected
- enjoyed film versus fit the moment
- stable preference versus growth edge
- strong dislike versus insufficient evidence
- current taste versus historical era
- model uncertainty versus true contradiction

## Profile outputs

For every trait:

- affinity
- confidence
- positive and negative evidence counts
- strongest supporting films
- strongest contradicting films
- explicit versus inferred status
- trend over time
- conflict state
- model and taxonomy versions

## Definition of done

- Daniel's profile is regenerated from durable canonical Evidence.
- Every learned trait can explain its evidence trail.
- Confidence depends on evidence diversity and agreement, not volume alone.
- Sparse traits remain explicitly uncertain.
- Taste snapshots can distinguish model changes from real taste drift.

---

# Explainable Recommendation Engine v1

## Typed request plan

A natural-language request becomes explicit hard filters and soft preferences.

Example:

> Creepy but not bleak, under two hours, full attention, on Max or Peacock, and definitely unwatched.

## Hard filters

- watched status
- runtime
- language or subtitle requirements
- content exclusions
- release constraints
- verified service availability when required

## Scoring components

- reviewed trait affinity
- similarity to high-confidence favorites
- distance from strong dislikes
- desired-effect fit
- mood and context fit
- novelty and exploration value
- watchlist intent
- quality floor
- risk penalty
- metadata and trait coverage confidence

## Output contract

Every recommendation includes:

- predicted Daniel score
- confidence
- why this film
- why now
- strongest supporting evidence
- meaningful caveat
- hard-filter and soft-score audit
- why nearby alternatives ranked lower
- service, region, and verification time
- model and taxonomy versions

## Definition of done

- only eligible unwatched films are returned by default
- recommendations are reproducible from frozen inputs
- candidate rejection reasons are inspectable
- prediction and explanation are frozen before the outcome
- Daniel can record rating and one sentence afterward
- prediction error and context fit update the learning ledger

---

# Benchmark growth strategy

Do not open multiple genre fronts until the horror benchmark is useful and stable.

```text
9 reviewed horror films
  -> 25
  -> 50
  -> measure remaining failure classes
  -> expand only when new evidence justifies it
```

Coverage should include:

- found footage
- psychological horror
- folk horror
- body horror
- supernatural and occult
- creature features
- cosmic horror
- slashers
- horror comedy
- international and non-English films
- archival and recent releases
- favorites, dislikes, rewatches, and contradictory reactions

After horror reaches maturity, expand through shared trait neighborhoods rather than arbitrary genre order.

---

# Later Intelligence Capabilities

## Context planning

- temporary mood and desired destination
- named modes such as late-night dogs, Sunday comfort, group chaos, and full-attention cinema
- hard versus soft constraints

## Taste evolution

- year and era snapshots
- first-watch versus rewatch changes
- stable preferences versus temporary life-period clusters
- uncertainty around personal-context correlations

## Blind-spot discovery

- hidden favorites outside obvious genres
- neglected decades, countries, languages, and creators
- thematic bridges
- exploration budgets that balance novelty and fit

## Contradiction and regret

- predicted love, actual dislike
- predicted dislike, actual love
- admired but not enjoyed
- good film, wrong moment
- misleading metadata versus missing trait

## Creator and cultural graphs

- directors
- writers
- actors
- countries and languages
- decades
- franchises
- creative collaborators
- thematic neighborhoods

## Live availability

Availability remains expiring operational evidence, not permanent film truth.

Store:

- provider
- region
- plan tier
- subscription, ads, rental, purchase, or free access
- verification timestamp
- expiration

---

# Deliberately Parked

These remain future options, not active work:

- public profiles
- social sharing and feeds
- leaderboards
- multi-user architecture
- mobile application
- browser extension
- public API
- marketplace
- plugin ecosystem
- dashboard-owned intelligence logic; the active Brain Health Dashboard is limited to a thin read-only audit surface

They return only after the intelligence layer produces consistently useful, measurable recommendations.

---

# Cross-cutting requirements

## Provenance

Every fact, trait, inference, correction, prediction, and outcome records its source.

## Versioning

Schema, importers, identity policy, providers, taxonomy, authoring model, taste model, request parser, ranker, and explanation renderer evolve independently.

## Fault tolerance

- bounded work
- retry and backoff
- safe resume
- partial-result preservation
- diagnostic artifacts
- corrupt-cache quarantine
- no single record aborts a recoverable batch

## Testing

- unit tests for pure rules
- integration tests across layers
- real-data bounded workflows
- golden scenarios based on Daniel's actual requests
- regression tests for every discovered failure
- no network dependency in required unit tests

## Human control

Explicit corrections supersede inference while preserving the original evidence and review history.

---

# Current execution queue

The release-level execution state is maintained in `docs/BRAIN_RELEASES.md`. The current dependency order is:

1. Preserve the merged Brain v0.1 canonical horror truth.
2. Preserve the merged Brain v0.2 taste and calibration contracts.
3. Preserve Brain v0.3's versioned corpus, raw ranking, and balanced top-five slate through PR #60.
4. Preserve Recommendation Release Gates v1 and its frozen manifest and prediction snapshot.
5. Preserve Recommendation Audit v1 as the verified read-only contract over those immutable records.
6. Preserve Brain Health Dashboard v1 as the thin read-only audit surface.
7. Preserve Post-watch Outcome Capture v1 as the append-only Learning contract keyed by `release_id`.
8. Preserve Unified Evaluation Experience v1 and Manual Outcome Reconciliation v1.
9. Preserve the reviewed Noroi outcome and its unpromoted calibration candidate.
10. Preserve Outcome-to-Memory Promotion v1 and the canonical Noroi watch.
11. Generate a post-Noroi release and capture its release-bound outcome before
    changing calibration or taste dimensions.
12. Expand the horror benchmark to 25 and then 50 only when repeated measured gaps justify it.

No additional provider, governance, social, marketplace, or dashboard-owned intelligence work should interrupt this sequence unless a real blocker requires it.

---

# First explicit live evidence

## Noroi: The Curse (2005)

- Watched: August 3, 2026 (completed at August 4, 01:09 UTC)
- Rating: 3.5 stars
- Outcome: glad watched, fit the moment, liked, would recommend to similar taste
- Recommendation explanation: nailed it
- What landed: pacing, buildup, uncertainty, supernatural material, and eerie dread
- Friction: some difficulty following the story
- Binding: verified against the pre-gate frozen top-five prediction; not eligible
  for formal release-bound Recommendation Trust
- Calibration: the 0.888 legacy score projected to 4.748/5, creating an
  unpromoted rating-projection and overconfidence review candidate

This is the first verified recommendation outcome. It supports the slate decision
while challenging score calibration. Narrative legibility remains a candidate
dimension until another outcome shows the same pattern.

The completed outcome is also canonical watched memory. Future rankings must
exclude Noroi before freezing the next slate.

## Undertone (2025)

- Watched: August 2, 2026
- Rating: 4 stars
- Reaction: genuinely scary; created a Blair Witch-like sense of creeping dread and unease
- Initial evidence:
  - creeping dread: strong positive
  - found-footage-like realism: positive
  - sustained uncertainty: positive
  - atmosphere: strong positive
  - genuine fear response: confirmed

This remains the first manually captured example of Cinema Brain learning why a film worked rather than merely storing its rating.

---

# Definition of done for Cinema Brain v1

Cinema Brain v1 is complete when Daniel can ask naturally for a film using mood, desired effect, context, runtime, and active services, and receive eligible unwatched candidates with:

- current availability
- predicted personal score
- calibrated confidence
- reviewed-trait explanation
- a meaningful caveat
- candidate audit and score components
- model-version traceability

After watching, Daniel can provide a rating and one sentence. Cinema Brain records the result, updates durable Evidence, measures prediction error, and improves future recommendations without requiring a full Letterboxd export.
