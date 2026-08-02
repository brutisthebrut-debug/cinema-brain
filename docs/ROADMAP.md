# Cinema Brain Roadmap

## North Star

Build a private, durable, explainable model of Daniel's cinematic taste that becomes more accurate after every watch, recommendation, rating, review, and conversation.

Cinema Brain is not a generic movie database and not a startup requirement. It is the movie module of Daniel OS: a lifelong personal system that remembers what Daniel has seen, understands why particular films work or fail for him, and uses that evidence to make better choices in the moment.

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

---

# Architecture

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

The engine converts that into an explicit query plan rather than relying on freeform guessing.

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

## 6. Recommendation and feedback loop

Store:
- recommendation timestamp
- prompt/context
- candidates considered
- selected recommendation
- predicted score and confidence
- whether Daniel started and completed it
- actual rating
- one-sentence reaction
- whether it scared, moved, comforted, bored, or surprised him
- prediction error
- lessons applied to future weights

A recommendation that fails is useful training data, not a hidden embarrassment.

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

## 9. Regret and contradiction engine

Two valuable categories:
- **Predicted love, actual dislike**
- **Predicted dislike, actual love**

These reveal missing variables and prevent the system from becoming a taste echo chamber.

## 10. Streaming availability

Availability is queried live for the United States and never treated as permanent metadata.

Maintain Daniel's current service profile separately, including temporary travel contexts such as Charlotte access versus home access.

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

## Phase 2 — Metadata enrichment
- Provider adapter and cache
- Core film metadata
- Horror, style, emotion, and theme traits
- Provenance and confidence

## Phase 3 — Explainable recommendations
- Query constraints
- Candidate ranking
- Predicted Daniel score
- Evidence-based explanations
- Watchlist and discovery modes

## Phase 4 — Live availability
- Service profile
- Current U.S. availability checks
- Travel-context service overrides

## Phase 5 — Feedback learning
- Recommendation log
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

1. Generate `profiles/taste_profile.json` from current ratings, likes, rewatches, reviews, lists, and manual reactions.
2. Establish a controlled trait taxonomy in `config/traits.json`.
3. Add an explicit film-trait evidence table with provenance.
4. Add recommendation-outcome storage.
5. Implement metadata-provider abstraction and local cache.
6. Create first horror-focused profile using explicit evidence from *Undertone*.
7. Test a recommendation against Daniel's live response to *Vicious*.

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

After watching, Daniel can provide a rating and one sentence, and the system immediately updates its durable profile without requiring a full Letterboxd export.
