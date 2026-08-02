# Metadata Golden Dataset

## Purpose

The golden dataset is the permanent human-reviewed benchmark for identity matching, metadata normalization, provenance, and semantic-signal extraction. Whole-library enrichment is blocked until the active provider stack passes this benchmark.

## Current executable seed

`config/golden_horror_v1.json` is the first machine-readable seed. It contains 10 deliberately hazardous horror identities, including remakes, generic titles, punctuation differences, international titles, and *Undertone*.

The seed is **not yet approved truth**. Every record begins with `reviewed: false`. CI validates its structure and identity rules, but the release gate remains closed until records are manually reviewed and promoted. This prevents an initial draft from quietly becoming authoritative.

`cinema_brain.golden_dataset` provides:
- strict versioned loading
- duplicate and malformed-record rejection
- canonical and accepted-title normalization
- exact title/year evaluation
- explicit mismatch explanations
- release-gate summaries that count only reviewed records

## Initial size

Start with 50 films. Expand toward 100 only when new failure classes appear. The first 10-record seed establishes the schema and regression machinery; the remaining records should be selected from Daniel's real library and review artifacts.

## Required coverage

### Identity hazards
- same title, different years
- remakes and reboots
- sequels with nearly identical names
- alternate and international titles
- punctuation and article differences
- films sharing names with books, songs, people, or television episodes
- missing or disputed release years

### Catalog diversity
- recent releases
- older and archival films
- independent and low-budget films
- international and non-English films
- animation
- documentaries
- television films where relevant
- obscure titles from Daniel's real history

### Horror emphasis
- atmospheric horror
- found footage
- psychological horror
- folk horror
- cosmic horror
- body horror
- slashers
- creature features
- possession and occult
- home invasion
- analog and liminal horror
- horror-comedy

### Personal relevance
- Daniel five-star favorites
- strong dislikes
- rewatches
- underseen favorites
- *Undertone* as the first explicit fear-evidence case
- films with contradictory rating and written reaction

## Human-reviewed truth fields

For every benchmark film record:
- canonical title
- release year
- accepted alternate titles
- entity type
- director
- runtime range
- countries
- languages
- broad genres
- known external identifiers
- expected identity hazards
- approved horror mechanisms where explicitly reviewed

The golden record does not pretend every interpretive trait is objective. Facts and human-reviewed semantic labels remain separate.

## Provider evaluation metrics

- exact identity accuracy
- false-positive rate
- false-negative rate
- low-confidence quarantine rate
- field coverage
- field disagreement rate
- provenance completeness
- cache reproducibility
- retry and failure isolation
- runtime per film

## Initial quality gates

Before whole-library enrichment:
- zero known false-positive identity matches
- at least one reviewed benchmark record; a seed-only dataset can never pass
- 100% provenance on persisted fields
- all low-confidence matches quarantined
- repeated runs produce the same canonical results from cache
- one provider failure does not stop the batch
- no external source overwrites Daniel evidence
- manually reviewed horror signals remain distinguishable from provider tags

Numerical thresholds should tighten as the dataset grows. False positives remain more costly than misses.

## Regression policy

Every real-world matching failure becomes:
1. a new benchmark case or fixture
2. a regression test
3. an identity-policy or normalization lesson
4. an entry in release notes when materially important

## Review workflow

1. Select films from the canonical database.
2. Generate provider candidates and confidence explanations.
3. Review facts and identity manually.
4. Approve, reject, or quarantine each match.
5. Set `reviewed: true` only after approval.
6. Freeze the benchmark record with a version.
7. Run it in CI for every provider or matching change.

## Versioning

The benchmark has its own version. Changing accepted truth requires a documented reason so provider improvements are not confused with moving the test target.
