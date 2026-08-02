# Metadata Source Registry

This registry is the approval gate for external data sources. A source is not production-ready until its license, operating constraints, identity method, provenance requirements, and replacement strategy are documented.

## Status values
- **active** — implemented and approved for production use
- **planned** — approved in principle; adapter not yet complete
- **research** — value or terms still being evaluated
- **restricted** — allowed only under a narrow private/noncommercial configuration
- **rejected** — must not be used

## Wikidata
- Status: active candidate in PR #16
- Role: canonical open factual backbone and identifier bridge
- Data class: objective facts and provider classifications
- License class: open structured data
- Access: read-only public endpoints
- Required controls: descriptive User-Agent, conservative traffic, caching, retry/backoff
- Identity policy: exact title/year/film-type gates; confidence reported
- Replacement strategy: provider-neutral `MetadataProvider` contract

## IMDb downloadable datasets
- Status: planned / restricted
- Role: alternate titles, title IDs, runtime, genres, credits, rating priors
- Data class: facts and community priors
- Constraint: private/noncommercial eligibility must be rechecked before activation
- Required controls: local dataset adapter, dataset-version provenance, no webpage scraping, removable feature flag
- Replacement strategy: disable adapter without altering canonical records from other sources

## MovieLens / Tag Genome
- Status: planned pending selected-release terms review
- Role: population-level semantic tags and relevance scores
- Data class: community semantic priors
- Required controls: dataset-version provenance, minimum derived-data retention, no silent redistribution
- Replacement strategy: semantic-signal adapter behind a stable contract

## Wikipedia
- Status: research
- Role: narrative, setting, production technique, themes, reception context
- Data class: attributed text-derived interpretation
- Required controls: page revision, license, attribution, extractor version, quotation limits, field-level provenance
- Activation gate: must prove measurable signal gain beyond structured sources

## DBpedia
- Status: research / fallback
- Role: normalized Wikipedia relationships and abstracts
- Data class: structured and text-derived facts
- Activation gate: only where it improves unresolved coverage or reduces extraction complexity

## Library of Congress
- Status: planned specialist source
- Role: historical films, authority records, alternate titles, subject headings
- Data class: archival facts and authority links
- Required controls: rate limiting, source identifiers, specialist-only routing

## Internet Archive
- Status: research specialist source
- Role: public-domain and archival cinema metadata
- Data class: archival facts
- Activation gate: unresolved or historical-film queue only

## Streaming availability sources
- Status: deferred
- Role: current regional availability
- Data class: expiring operational evidence
- Requirement: terms-compatible source with plan-tier, region, timestamp, and expiry
- Rule: availability never becomes permanent film metadata

## Rejected sources and methods
- TMDB under current AI-use restrictions
- unofficial JustWatch endpoints
- scraping IMDb webpages
- scraped reviews or subtitles without clear rights
- anonymous data dumps without provenance
- any provider that prevents explainable retention of source and license

## Approval checklist
A new provider must answer:
1. What unique capability does it add?
2. Is the license compatible with current and plausible future use?
3. What attribution or redistribution duties apply?
4. How are records identified and matched?
5. What confidence and conflict behavior is required?
6. How is it cached and refreshed?
7. How does it fail safely?
8. How is it disabled or replaced?
9. What benchmark proves it improves the engine?
10. What technical debt does it introduce?
