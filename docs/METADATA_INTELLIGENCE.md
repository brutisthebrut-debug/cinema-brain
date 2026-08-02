# Metadata Intelligence Blueprint

## Purpose

Metadata Intelligence turns a canonical film record into a durable, auditable bundle of facts, semantic signals, disagreements, and confidence. It exists to improve recommendation quality without creating provider lock-in or an untraceable data swamp.

## Core rule

No provider is the truth. Providers contribute evidence.

Every imported value must retain:
- provider
- source identifier
- source URL or dataset version when available
- license class
- retrieval timestamp
- matching method
- confidence
- field type: fact, interpretation, community signal, or Daniel signal
- extraction or normalization version

## Evidence classes

1. **Objective facts**
   - release date
   - runtime
   - country
   - language
   - credited cast and crew

2. **Provider interpretations**
   - genre
   - themes
   - tone
   - narrative form
   - horror mechanisms

3. **Community priors**
   - ratings
   - tags
   - popularity
   - consensus descriptors

4. **Daniel evidence**
   - ratings
   - likes
   - rewatches
   - reviews
   - chat reactions
   - completion and recommendation outcomes

Daniel evidence is the highest authority for Daniel's taste. External sources describe the film; they do not override his reaction.

## Planned source stack

### Tier 1 — canonical open facts
- Wikidata

### Tier 2 — optional factual reinforcement
- IMDb noncommercial datasets, behind a removable adapter and only while the project remains eligible
- Library of Congress for historical and authority records

### Tier 3 — semantic intelligence
- MovieLens Tag Genome or a similarly licensed tag source
- Wikipedia narrative extraction with revision and license provenance
- DBpedia only where it materially improves structured coverage

### Tier 4 — specialist archival coverage
- Internet Archive
- public-domain and archival catalogs

### Excluded by default
- providers whose terms conflict with AI-assisted recommendation use
- unofficial streaming APIs
- scraped review sites
- subtitle or review corpora with unclear rights
- anonymous third-party data dumps without lineage

## Provider registry requirements

Each provider must declare:
- capability and supported fields
- license and attribution requirements
- commercial compatibility
- redistribution limits
- rate limits and access policy
- refresh expectations
- identity strategy
- confidence policy
- retry and backoff behavior
- cache policy
- replacement strategy
- health metrics

## Identity confidence

A metadata match is never just matched or unmatched. It receives a confidence score and explanation.

Strong signals:
- exact normalized title
- exact release year
- confirmed film or television-film entity type
- runtime agreement
- director agreement
- external identifier agreement

Weakening signals:
- alternate title only
- missing year
- sequel or remake ambiguity
- conflicting runtime
- missing creator information

Low-confidence matches must be quarantined for review rather than silently persisted as canonical truth.

## Conflict policy

When providers disagree:
- retain each claim
- record source and confidence
- avoid destructive overwrite
- expose the disagreement in quality reports
- choose a preferred display value only through a documented field-level policy

## Time-awareness

Every fact and inference is time-stamped. Taste profiles also preserve era snapshots so changes in Daniel's preferences are not confused with model changes.

## Source health

Track for each provider:
- uptime
- latency
- success and failure rates
- 429 and retry counts
- coverage gained
- stale records
- schema drift
- identity-rejection rate
- average confidence

A provider that degrades must lower confidence or be disabled without breaking the rest of the engine.

## Golden dataset

Before whole-library enrichment, every provider and matcher must pass a manually reviewed benchmark of representative films, including:
- same-title collisions
- remakes
- sequels
- international and alternate titles
- obscure films
- recent releases
- horror subgenres
- Daniel favorites and dislikes

## Rollout order

1. Finish Wikidata provider and CI validation.
2. Add provider and licensing registry.
3. Build a 50-film manually reviewed horror-heavy golden dataset.
4. Run bounded Wikidata enrichment and review identity confidence.
5. Add optional IMDb dataset adapter for private factual reinforcement.
6. Add a semantic tag source such as MovieLens Tag Genome.
7. Measure incremental value before adding Wikipedia prose extraction.
8. Add specialist archival adapters only for unresolved records.
9. Expand to the full library only after benchmark thresholds pass.

## Definition of done

Metadata Intelligence is complete when:
- enrichment is replaceable and resumable
- all claims retain provenance and license class
- identity confidence is explainable
- conflicts remain visible
- provider health is measurable
- a golden dataset protects against regressions
- bounded enrichment materially improves Horror DNA
- full CI proves reproducibility
