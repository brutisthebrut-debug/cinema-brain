# Cinema Brain Roadmap Status

Updated: 2026-08-03

This file is the execution companion to `docs/ROADMAP.md`. The roadmap defines product direction; this file records what is implemented, validated, active, and deliberately parked.

## Canonical project references

- `docs/ROADMAP.md` — product and engineering sequence
- `README.md` — operator quick start and cross-agent resume point
- `docs/BRAIN_RELEASES.md` — current release milestone and dependency sequence
- `docs/VISION.md` — Daniel OS destination and Cinema Brain's role as reference implementation
- `docs/FOUNDING_PRINCIPLES.md` — permanent doctrine and architecture fitness checks
- `docs/ROADMAP_GOVERNANCE.md` — definitions of done and roadmap standards
- `docs/METADATA_INTELLIGENCE.md` — provider and enrichment architecture
- `docs/SOURCE_REGISTRY.md` — source capabilities, licensing, restrictions, and replacement plans
- `docs/GOLDEN_DATASET.md` — reviewed benchmark policy and quality gates
- `docs/DECISIONS.md` — chronological decisions
- `docs/RELEASE_NOTES.md` — shipped capabilities and lessons
- `docs/TECHNICAL_DEBT.md` — intentional deferrals and repayment triggers
- `docs/adr/` — architecture decision records

## Operating rules

- Build capabilities, not disconnected features.
- Reviewed truth outranks inferred truth.
- External providers contribute evidence; no provider is authoritative by itself.
- Canonical data and provenance must remain separate from raw provider payloads.
- Human review is required before benchmark or canonical-trait promotion.
- Workflows must be bounded, resumable, fault tolerant, and diagnostic when partially unsuccessful.
- Every subsystem remains replaceable behind typed, versioned contracts.
- Preserve disagreements and negative evidence rather than averaging them away.
- Engine and recommendation quality come before interface expansion.
- A feature enters the active roadmap only when it improves the Intelligence Graph, recommendation quality, or a measurable learning outcome.
- No milestone is complete until its real-data path is validated.
- After every two or three infrastructure slices, identify and build the user-visible intelligence the infrastructure unlocked.

## Foundation epic — complete

- Reliable Letterboxd ingestion, validation, watched exclusion, and manual watch logging
- CSV, RSS, and manual-source reconciliation with replay protection
- Safe live Letterboxd RSS synchronization for `dmarlin`
- Canonical SQLite film memory and provider-neutral metadata contracts
- Durable Evidence Graph with provenance, conflicts, deduplication, and model versions
- Evidence-backed Cinematic DNA and durable recommendation-outcome storage
- Replaceable Wikidata enrichment with cache, compression handling, retry, pacing, and rate-limit recovery
- Per-film failure isolation and diagnostic artifact preservation

## Metadata Intelligence Phase 1 — complete

The first bounded, real-data metadata system now works end to end:

```text
Letterboxd memory
  -> benchmark-driven film selection
  -> Wikidata candidate discovery
  -> strict local title/year/film validation
  -> canonical metadata persistence
  -> deterministic Evidence extraction
  -> human review worksheet
  -> version-bound decision packet
  -> guarded promotion candidate
  -> regression validation
```

Validated outcomes:

- nine watched horror benchmark films selected correctly
- nine of nine enriched successfully
- nine exact title/year matches at confidence 1.0
- zero provider misses and zero failed films in the successful run
- `[REC]` correctly remains absent rather than being replaced by an unrelated film
- the completed nine-film review worksheet is stored on `review/golden-horror-v1-approvals`
- the guarded candidate workflow successfully compiled decisions and generated the promotion artifact

## Brain v0.1 and v0.2 — complete foundations

The Golden Horror release, Canonical Trait Model v1, reviewed authoring workflow,
nine canonical horror profiles, and Personal Taste Graph are complete on `main`.
Calibration evidence remains an ongoing input, but no unfinished Golden Horror v2
release blocks current production.

## Brain v0.3 — active recommendation validation

The active goal is to measure a second frozen recommendation against Daniel's
actual reaction without allowing the outcome to rewrite its prediction.

### Completed — Canonical Trait Model v1

Design a bounded, reviewed vocabulary covering:

- emotional tone and emotional destination
- narrative structure
- fear mechanisms
- themes
- visual and sonic style
- pacing and intensity
- ending type
- realism and performance style
- rewatch value
- conversation value
- `watch when` and `avoid when` guidance

Definition of done:

- schema and validation rules are versioned
- trait families, aliases, polarity, confidence, and evidence classes are explicit
- ambiguous or overlapping traits have documented boundaries
- the nine approved horror films have complete reviewed profiles
- the v1 vocabulary is frozen before recommendation work depends on it

### Completed — Trait Authoring Pipeline

```text
Film facts and Evidence
  -> candidate traits
  -> reviewer worksheet
  -> approve / reject / quarantine
  -> canonical trait profile
  -> versioned promotion
  -> regression gate
```

The pipeline may suggest traits, but it cannot declare its own output reviewed truth.

Definition of done:

- authoring is reproducible and does not require hand-editing JSON
- every promoted trait retains evidence, reviewer, reason, timestamp, and model version
- negative and contradictory traits remain representable
- later taxonomy changes cannot silently rewrite historical profiles

### Completed — Taste Intelligence v1

Build Daniel's taste vector only after reviewed film traits exist.

Required distinctions:

- loved versus admired versus affected
- stable preference versus tonight's desired effect
- rating, like, rewatch, review, and explicit reaction as separate signals
- positive and negative evidence
- current taste versus era-specific taste
- confidence based on evidence diversity, not volume alone

Definition of done:

- a versioned Daniel taste profile is generated from canonical Evidence
- every affinity can explain its strongest supporting and contradicting films
- low-evidence traits remain explicitly uncertain
- profile regeneration is deterministic

### Completed through outcome capture — Explainable Recommendation Engine v1

Every recommendation must answer:

- Why this film?
- Why now?
- Which reviewed traits support it?
- What is the meaningful risk?
- Why did nearby alternatives rank lower?

Definition of done:

- watched films are excluded unless a rewatch is requested
- hard filters and soft preferences are visibly separated
- candidates receive auditable score components
- predictions, confidence, and explanations are frozen before outcomes are known
- the first live recommendations are evaluated against Daniel's actual reactions

### Next evidence-gated milestone — Horror benchmark expansion

Expand deliberately rather than opening multiple genre fronts:

```text
9 reviewed films
  -> 25
  -> 50
  -> measure gaps
  -> expand further only when new failure classes justify it
```

Prioritize diversity across found footage, psychological, folk, body, supernatural, creature, cosmic, slasher, international, archival, recent, loved, disliked, and contradictory examples.

The first real outcome is now reviewed. Noroi: The Curse succeeded on
completion, glad-watched, moment fit, explanation fit, and recommendation intent.
Its 3.5/5 actual rating is materially below the legacy score projection, so the
result creates a calibration review candidate rather than a recommendation-trust
failure. Daniel also reported some difficulty following the story; narrative
legibility remains a candidate dimension, not promoted taste truth.

Do not begin the 25-film expansion until a second frozen outcome shows whether
either gap repeats.

Noroi is now canonical watched memory through Outcome-to-Memory Promotion v1.
The next release excludes it and is frozen as
`recommendation-6852bacab2c7499e0a8c` from merge commit `72791d4`. Its slate is
The Dark and the Wicked, Possum, The Empty Man, A Dark Song, and Saint Maud. The
second watch must use this release's submission template so formal
Recommendation Trust begins from a real `release_id`.

## Later intelligence phases

- Taste drift and era snapshots
- Blind-spot and hidden-favorite discovery
- Contradiction and regret analysis
- Context and mood planning
- Live availability as expiring operational evidence
- Director, actor, country, language, decade, and thematic graphs

These begin only when the reviewed trait and recommendation foundations make them measurable.

## Deliberately parked

- Public profiles
- Social feeds and sharing
- Leaderboards
- Mobile application
- Browser extension
- Public API or marketplace
- Plugin ecosystem
- Broad multi-user architecture
- Dashboard-led development

These ideas remain valid future options, but they do not belong in the active sequence until the intelligence layer is mature.

## Engineering metrics

- canonical film and viewing-event counts
- source-reconciliation accuracy
- metadata coverage and field completeness
- false-positive, miss, quarantine, retry, and provider-failure rates
- reviewed benchmark size and regression count
- canonical trait coverage and reviewer disagreement
- Evidence count, diversity, conflict, and provenance completeness
- recommendation acceptance and completion
- predicted-versus-actual rating error
- confidence calibration
- explanation usefulness
- repeat-recommendation and stale-availability rates

## Current execution order

1. Preserve the merged Brain v0.1 canonical horror truth.
2. Preserve the merged Brain v0.2 Personal Taste Graph and calibration contracts.
3. Preserve Brain v0.3's corpus, raw ranker, and balanced slate through PR #60.
4. Preserve Recommendation Release Gates v1, Recommendation Audit v1, and the
   read-only Brain Health Dashboard through PRs #61–#63.
5. Preserve Post-watch Outcome Capture v1 through PR #64.
6. Preserve Unified Evaluation Experience v1 as the single human-facing loop over
   pre-watch evaluation, release-bound outcome capture, and manual fallback.
7. Preserve Manual Outcome Reconciliation v1 and the reviewed Noroi outcome.
8. Preserve Outcome-to-Memory Promotion v1 and the canonical Noroi watch.
9. Generate a post-Noroi frozen slate, capture its release-bound outcome, and
   compare calibration and narrative-legibility evidence.
10. Expand the reviewed horror benchmark to 25 and then 50 only when repeated gaps
   from real outcomes justify the added films.

No additional provider, workflow-governance, interface, or social work should
interrupt this sequence unless a real failure blocks it.
