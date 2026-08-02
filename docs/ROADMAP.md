# Cinema Brain Roadmap

## North Star

Build a private, durable, explainable model of Daniel's cinematic taste that becomes more accurate after every watch, recommendation, rating, review, and conversation.

Cinema Brain is not a generic movie database and not a startup requirement. It is the movie module of Daniel OS: a lifelong personal system that remembers what Daniel has seen, understands why particular films work or fail for him, and uses that evidence to make better choices in the moment.

The roadmap is governed by `docs/ARCHITECTURE.md`. Every feature must have one owning layer, a stable contract, preserved provenance, versioning, independent tests, and an end-to-end reason it improves a real decision.

## Product principles

1. **Memory before prediction.** Never recommend a watched film unless a rewatch is requested.
2. **Why matters more than stars.** A one-sentence reaction can carry more useful taste evidence than a rating alone.
3. **Explain every recommendation.** Confidence must be tied to actual evidence, not vague AI language.
4. **Stable history, live availability.** Personal taste data is durable; streaming catalogs must be checked live.
5. **Positive and negative taste are separate.** Disliking jump-scare spam is not the same as loving slow burns.
6. **Mood is first-class data.** “Creepy,” “nostalgic,” “beautifully devastating,” and “background-friendly” matter as much as genre.
7. **Human correction wins.** Daniel can override any inferred trait or recommendation outcome.
8. **No silent data loss.** Raw exports, manual watches, reviews, list rankings, and recommendation outcomes retain provenance.
9. **Private by default.** This is personal behavioral data and stays in a private repository.
10. **Useful beats elaborate.** Every layer must improve an actual question Daniel asks.
11. **Contracts before coupling.** Layers exchange typed, versioned records rather than reaching into one another’s internals.
12. **Failures become evidence.** A poor recommendation is recorded and used to calibrate the model.

## The 10x standard

Every roadmap item must be reviewed with these questions before implementation:

- What real decision does this improve?
- Which layer owns it?
- What are its stable inputs and outputs?
- How is provenance retained?
- How can Daniel correct it?
- How is it independently tested?
- How is it tested in the full pipeline?
- What model or schema version changes?
- Does it duplicate another feature or create hidden coupling?
- How can it become ten times more useful without becoming ten times harder to maintain?

---

# Architecture and dependency order

The system flows in one direction:

```text
Sources
  -> Memory
  -> Metadata
  -> Taste
  -> Context planning
  -> Candidate filtering and ranking
  -> Live availability verification
  -> Recommendation explanation
  -> Outcome logging
  -> Calibration and evolution
```

The dashboard and conversational interface sit above this pipeline. They do not own business logic.

## 1. Memory layer — established

### Inputs
- Letterboxd watched history
- Ratings
- Diary entries and rewatches
- Watchlist
- Likes
- Written reviews
- Custom and festival lists
- Manual chat watch log

### Guarantees
- Deterministic watched exclusion
- Title/year reconciliation across Letterboxd URL types
- Full source row counts and checksums
- Manual entries merge safely with later Letterboxd refreshes
- Validation detects malformed data and contradictions

### 10x expansion
- Add immutable source-event identifiers.
- Add superseding corrections rather than destructive edits.
- Add explicit reconciliation reports during each Letterboxd refresh.
- Add schema migrations so future changes never require rebuilding by hand.
- Add a personal-data retention policy before additional Daniel OS modules share infrastructure.

## 2. Metadata layer

Enrich each canonical film with:
- genres and subgenres
- directors, writers, and principal cast
- countries and languages
- runtime and release decade
- production companies
- franchise and sequel relationships
- content descriptors
- horror mechanisms: found footage, occult, home invasion, folk horror, cosmic horror, body horror, creature feature, slasher, possession, analog horror, liminal horror
- formal traits: slow burn, nonlinear, ambiguous ending, minimal dialogue, long takes, dream logic, practical effects, naturalistic acting
- emotional traits: dread, wonder, grief, loneliness, warmth, nostalgia, melancholy, catharsis, chaos, awe

### Requirements
- Cache enriched metadata locally
- Preserve provider, retrieval date, and confidence
- Never overwrite explicit Daniel labels with third-party metadata
- Allow multiple values and weighted traits
- Keep provider adapters replaceable
- Make enrichment resumable and idempotent

### 10x expansion
- Separate objective facts from interpretive traits.
- Support competing metadata claims with confidence rather than choosing silently.
- Track coverage so recommendation confidence drops when candidate metadata is thin.
- Build reusable film embeddings only after explicit metadata and provenance are stable.
- Add franchise, creative-collaborator, and thematic-neighborhood graphs from the same canonical records.

## 3. Cinematic DNA / taste engine

The taste engine models evidence at several levels.

### Explicit signals
- rating
- like
- written review
- one-sentence chat reaction
- “actually scared me” / “did not scare me”
- favorite or ranked-list placement
- manual trait corrections

### Behavioral signals
- rewatches
- repeated franchise viewing
- watchlist age and eventual conversion
- recommendation acceptance or rejection
- completion and abandonment when available
- clusters watched during particular periods

### Initial signal weights
- 5-star rating: +4.0
- 4.5 stars: +3.4
- 4 stars: +2.6
- 3.5 stars: +1.4
- 3 stars: +0.3
- 2.5 stars: -0.6
- 2 stars: -1.6
- 1.5 stars: -2.6
- 1 star: -3.4
- 0.5 stars: -4.0
- liked: +1.5
- each rewatch beyond first: +0.8, capped
- written review: evidence-strength multiplier, not automatic positivity
- top-ten ranked-list placement: +2.0 to +0.5 by rank
- explicit chat reaction: ±1 to ±4 depending on language and confidence

Weights remain versioned and testable. They are starting assumptions, not permanent truth.

### Trait profile outputs
For each trait:
- affinity score
- confidence
- positive evidence count
- negative evidence count
- strongest supporting films
- strongest contradicting films
- trend over time
- explicit vs inferred status

### Separate profiles
- Fear DNA
- Emotional DNA
- Style DNA
- Story/theme DNA
- Comedy DNA
- Romance DNA
- Comfort/nostalgia DNA
- Director graph
- Actor graph
- Country/language graph
- Decade graph

### 10x expansion
- Store every trait contribution as a first-class evidence record.
- Distinguish “I admire this” from “I enjoyed this” and “this affected me.”
- Model desired effect separately from general preference; wanting to be scared tonight is contextual, not permanent taste.
- Build profile snapshots so model changes and taste evolution are not conflated.
- Calibrate confidence by evidence diversity, not only evidence volume.
- Detect conflicts such as high rating plus negative reaction rather than averaging them away.

## 4. Mood and context engine

Inputs can include:
- current mood
- desired emotional destination
- energy and attention level
- alone / dogs / friends / date
- time available
- time of day
- tolerance for sadness, gore, subtitles, ambiguity, or intensity
- current streaming services
- novelty vs comfort

Example request:

> Creepy but not bleak, under two hours, full attention, on Max or Peacock, and definitely unwatched.

The engine converts that into an explicit typed query plan rather than relying on freeform guessing.

### 10x expansion
- Separate current state from desired destination.
- Remember temporary contexts without turning them into permanent preferences.
- Support “surprise me” while still honoring hard boundaries.
- Let Daniel save named modes such as late-night dogs, Sunday comfort, full-attention cinema, and group chaos.
- Explain which constraints were hard filters versus soft preferences.

## 5. Recommendation engine

### Hard filters
- exclude watched unless rewatch requested
- service availability
- runtime constraints
- language/subtitle constraints
- release-year constraints
- content exclusions

### Scoring components
- trait affinity
- similarity to high-confidence favorites
- dissimilarity from strong dislikes
- mood fit
- context fit
- novelty bonus
- underexplored-interest bonus
- watchlist intent
- critic/audience quality floor when useful
- availability confidence

### Output contract
Every recommendation includes:
- predicted Daniel score
- confidence
- why it fits tonight
- strongest evidence films
- meaningful risk or caveat
- streaming service and verification date
- whether it came from watchlist or outside discovery
- model versions and score components

### 10x expansion
- Produce a candidate audit showing why films were rejected.
- Generate intentionally diverse finalists rather than near-duplicates.
- Distinguish safest pick, bold pick, and comfort pick.
- Add counterfactual explanations: what missing evidence keeps confidence from being higher?
- Prevent repetitive recommendation loops through recommendation-history penalties.

## 6. Recommendation and feedback loop

Store:
- recommendation timestamp
- prompt/context
- candidates considered
- selected recommendation
- predicted score and confidence
- model versions
- whether Daniel started and completed it
- actual rating
- one-sentence reaction
- whether it scared, moved, comforted, bored, or surprised him
- prediction error
- lessons applied to future weights

A recommendation that fails is useful training data, not a hidden embarrassment.

### 10x expansion
- Track recommendation acceptance separately from movie enjoyment.
- Track whether the movie fit the moment even when the film itself was only average.
- Preserve frozen prediction snapshots before learning from the outcome.
- Require enough evidence before automatically changing global weights.
- Surface proposed calibrations for human approval when they materially change the profile.

## 7. Taste evolution

Generate snapshots by year or era:
- 2014 Daniel
- festival years
- grief periods
- relationship periods
- recovery and rebuilding periods
- current era

Track:
- genres rising or falling
- tolerance for ambiguity and bleakness
- changing rating generosity
- comfort rewatches
- directors or countries discovered late
- traits that remain stable across life changes

This layer should observe patterns without pretending correlation proves causation.

### 10x expansion
- Separate genuine taste drift from changes in rating behavior.
- Let Daniel define eras rather than having the system impose personal narratives.
- Compare first-watch and rewatch reactions.
- Detect rediscovery cycles and dormant interests.
- Add uncertainty language around any life-context correlation.

## 8. Discovery intelligence

Surface:
- favorite director Daniel may not realize is a favorite
- actors associated with unusually high ratings
- countries/languages with strong fit
- neglected decades
- hidden gems near favorite trait clusters
- watchlist items with highest predicted score
- movies Daniel “should” love but has not seen
- productive contradictions: films he should have hated but loved, and vice versa

### 10x expansion
- Balance similarity with genuine expansion.
- Create exploration budgets so novelty does not overwhelm fit.
- Track underexplored interests only when enough positive evidence exists.
- Build thematic bridges between genres rather than relying solely on genre similarity.
- Explain why a discovery broadens the profile instead of merely repeating it.

## 9. Regret and contradiction engine

Two valuable categories:
- **Predicted love, actual dislike**
- **Predicted dislike, actual love**

These reveal missing variables and prevent the system from becoming a taste echo chamber.

### 10x expansion
- Separate model failure, mood mismatch, availability compromise, and misleading metadata.
- Detect films Daniel respects but would not recommend to himself.
- Identify traits that only work in specific combinations.
- Create contradiction clusters that suggest new hidden variables.

## 10. Streaming availability

Availability is queried live for the United States and never treated as permanent metadata.

Maintain Daniel's current service profile separately, including temporary travel contexts such as Charlotte access versus home access.

### 10x expansion
- Record region, plan tier, verification source, and timestamp.
- Distinguish included subscription, ads, rental, purchase, and free-library access.
- Expire availability evidence automatically.
- Never let stale availability lower trust in the stable taste model.

## 11. Interfaces

### Conversational interface
Primary experience. Daniel asks naturally and receives grounded recommendations.

### Command-line interface
For ingestion, validation, profile generation, testing, and reproducible queries.

### Personal dashboard — later
Potential views:
- cinematic DNA radar and trait cards
- recent watches
- recommendation accuracy
- watchlist priority
- directors and countries
- taste evolution timeline
- “what should I watch tonight?” control panel

The dashboard is optional. The data model and conversational intelligence come first.

### 10x expansion
- Dashboard remains a thin client over the same contracts used by conversation and CLI.
- Every recommendation can expose its evidence trail on demand.
- Fast mobile workflow: log watch, rate, one sentence, done.
- Add exports so Daniel remains able to leave the system with all derived data.

---

# Cross-cutting foundations

These are not separate shiny features. They are required infrastructure across every phase.

## Provenance
Every fact, trait, prediction, correction, and outcome records where it came from.

## Versioning
Schema, importer, identity policy, metadata providers, taxonomy, taste model, request parser, ranker, and explanation renderer evolve independently.

## Data contracts
Typed contracts define trait evidence, watch requests, score components, availability evidence, and recommendation results.

## Testing
- Unit tests for pure functions and contracts
- Integration tests for ingestion through profile generation
- Golden scenarios based on real requests
- Regression tests for every discovered failure
- No network dependency in unit tests

## Observability
Generated runs report coverage, warnings, confidence gaps, candidate counts, rejection reasons, and prediction errors.

## Human control
Explicit Daniel corrections always supersede inference without erasing the original evidence.

---

# Delivery phases

## Phase 0 — Reliable memory ✅
- Full export ingestion
- Validation
- Watched exclusion
- Manual watch log

## Phase 1 — Taste engine foundation (active)
- Versioned signal weights
- Explicit trait vocabulary
- Film-level evidence scoring
- Profile JSON generation
- Initial reaction parser for manual notes
- Tests for positive, negative, and rewatch weighting
- Typed cross-layer contracts
- Integrated architecture and 10x review gate

## Phase 2 — Metadata enrichment
- Provider adapter and cache
- Core film metadata
- Horror, style, emotion, and theme traits
- Provenance and confidence
- Coverage reporting and resumable enrichment

## Phase 3 — Explainable recommendations
- Typed query constraints
- Candidate audit and hard-filter reasons
- Candidate ranking
- Predicted Daniel score
- Evidence-based explanations
- Watchlist and discovery modes

## Phase 4 — Live availability
- Service profile
- Current U.S. availability checks
- Travel-context service overrides
- Expiring verification records

## Phase 5 — Feedback learning
- Recommendation log
- Frozen prediction snapshots
- Prediction-versus-actual analysis
- Weight calibration
- Explicit corrections

## Phase 6 — Graphs and evolution
- Director and actor graphs
- Country/language and decade graphs
- Annual taste snapshots
- contradictions and regret

## Phase 7 — Dashboard
- Read-only first
- Private deployment
- Fast “tonight” workflow
- Visual exploration without replacing conversation

---

# Immediate build queue

1. Convert inferred trait contributions into durable evidence records with provenance.
2. Add recommendation-outcome and frozen-prediction storage.
3. Implement metadata-provider abstraction and local cache.
4. Add a typed request parser and candidate audit.
5. Create first horror-focused profile using explicit evidence from *Undertone*.
6. Test a recommendation against Daniel's live response to *Vicious*.
7. Add the Charlotte late-night dogs golden integration scenario.

---

# First explicit live evidence

## Undertone (2025)
- Watched: August 2, 2026
- Rating: 4 stars
- Reaction: genuinely scary; created a Blair Witch-like sense of creeping dread and unease
- Initial traits:
  - creeping dread: strong positive
  - found-footage-like realism: positive
  - sustained uncertainty: positive
  - atmosphere: strong positive
  - genuine fear response: confirmed

This is the first manually captured example of the system learning *why* a movie worked, not merely that it received four stars.

---

# Definition of done for Cinema Brain v1

Cinema Brain v1 is complete when Daniel can ask for a movie using mood, context, runtime, and active services, and receive only unwatched candidates with:
- current availability
- predicted personal score
- confidence
- evidence-based explanation
- a meaningful caveat
- model-version traceability

After watching, Daniel can provide a rating and one sentence, and the system immediately updates its durable profile without requiring a full Letterboxd export.
