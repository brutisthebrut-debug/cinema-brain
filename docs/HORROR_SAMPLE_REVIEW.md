# Bounded Horror Sample Review

This milestone is the quality gate between provider/evidence plumbing and broad library enrichment.

The manual `cinema-brain-horror-sample-review` workflow:

1. rebuilds the canonical database from Daniel's committed Letterboxd sources;
2. runs the complete regression suite;
3. enriches only a bounded recent sample through Wikidata;
4. converts supported metadata labels into versioned film-level Evidence;
5. validates the resulting database; and
6. uploads private JSON reports plus the reproducible SQLite database for human review.

The review packet shows Letterboxd identity beside provider identity, exact title/year status, provider confidence, normalized genres and keywords, directors, runtime, and emitted Evidence count.

A mismatch is reported rather than silently accepted. The workflow remains informational so review artifacts are preserved even when a provider identity needs correction. Whole-library enrichment stays blocked until the bounded sample demonstrates acceptable identity accuracy and useful trait coverage.
