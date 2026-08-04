# Outcome-to-Memory Promotion v1

## Purpose

Post-watch evidence and canonical watched memory are different records. The
outcome preserves what Cinema Brain predicted and how Daniel reacted. Canonical
memory ensures a completed film cannot be recommended again as unwatched.

Outcome-to-Memory Promotion v1 closes that loop without turning an outcome into
automatic taste learning.

## Accepted evidence

The promotion command accepts exactly one of:

- a `verified_manual_recommendation_outcome` produced by Manual Outcome
  Reconciliation v1; or
- a release-bound `post_watch_recommendation_outcome` containing a real
  `release_id`.

Both must prove that the prediction was frozen before the outcome. The watch
must be complete, the film identity and year must be present, the rating must be
valid, and `watched_at` must include a timezone offset.

Incomplete outcomes remain outcome evidence but require a human decision before
they can become canonical watched memory.

## Promotion behavior

The command converts `watched_at` into the operator-supplied IANA timezone and
appends one row to `data/manual/manual_watches.csv`. It records only:

- canonical title and year;
- local watched date;
- rating;
- non-rewatch status; and
- the verified `outcome_id` as source provenance.

Reaction text, notes, sentiment, trust, calibration, and regression evidence
remain in the private outcome package. They are not copied into the public
manual-watch ledger.

Promotion is idempotent by title, year, and local watched date. It never
overwrites an existing row. A later Letterboxd RSS event for the same film and
date links to the canonical event instead of creating a second watch.

## CLI

```bash
python -m cinema_brain.cli promote-outcome-watch \
  --outcome outcomes/manual/<source>/<outcome>/manual_outcome_reconciliation_v1.json \
  --manual-watches data/manual/manual_watches.csv \
  --timezone America/New_York
```

The timezone is required because the outcome timestamp may be UTC while the
Letterboxd watched date is the local viewing day.

## First production promotion

Noroi: The Curse (2005) was completed at `2026-08-04T01:09:00Z`, which is
August 3 in `America/New_York`. Its verified legacy outcome is now canonical
watched memory at 3.5/5. The next release must exclude
`title:noroi-the-curse:2005` before ranking.

Production validation exposed and corrected an older exclusion defect: the
ranker had maintained a second title normalizer, while canonical ingestion did
not consistently treat apostrophes as part of a word. Punctuated titles such as
`Noroi: The Curse` and `The Blackcoat's Daughter` could therefore disagree with
corpus identity even when memory was correct. Ingestion and watched exclusion
now reuse one canonical identity policy with punctuation regressions.

## Boundaries

Promotion changes watched memory only. It does not:

- modify the frozen prediction or outcome;
- count legacy evidence as formal release-bound Recommendation Trust;
- change taste weights or canonical traits;
- promote a calibration or regression candidate; or
- copy private reaction text into GitHub.

## Handoff

Generate a new frozen recommendation release from the main revision containing
the Noroi memory row. Verify Noroi appears in `watched_exclusions`, import that
release's `post_watch_outcome_submission_v1.json` into the unified evaluation
page, and capture the second outcome against the real `release_id`.
