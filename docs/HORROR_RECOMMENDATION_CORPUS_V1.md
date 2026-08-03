# Horror Recommendation Corpus v1

This is the first bounded candidate corpus for Brain v0.3. It is deliberately small and frozen so ranking behavior can be inspected before Cinema Brain searches a broad catalog.

## Contract

Every film must have:

- a stable `film_key`
- title and release year
- at least three canonical trait assignments
- values and confidence between 0 and 1
- a written rationale for every assignment
- no duplicate film identity
- no watched-film overlap at ranking time

The corpus is validated against `config/trait_registry_v1.json`. Unknown traits fail closed.

## Seed batch

The candidate release contains 12 horror films and 48 trait assignments. The batch intentionally covers atmospheric dread, found footage, occult and cosmic horror, grief, loneliness, psychological destabilization, practical effects, and visual craft.

This is not yet a claim that every film is unwatched by Daniel. The production pipeline must compare corpus identities against the canonical viewing history and exclude watched films before scoring.

## Release gate

The next slice may rank this corpus only after:

1. corpus validation passes;
2. watched-film exclusion runs against the canonical database;
3. every surviving candidate has sufficient active taste-trait overlap;
4. low-evidence candidates are allowed to abstain;
5. score explanations preserve positive drivers, negative drivers, confidence, and coverage.

The first output is a frozen inspection batch, not a consumer recommendation feed.
