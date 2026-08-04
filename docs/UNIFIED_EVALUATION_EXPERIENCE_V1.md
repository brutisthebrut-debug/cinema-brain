# Unified Evaluation Experience v1

## Purpose

Cinema Brain originally exposed a friendly, mobile-ready top-five evaluation page.
Post-watch Outcome Capture v1 later added the stronger frozen `release_id`, audit,
Recommendation Trust, and regression-fixture contracts. The backend contract was
correct, but the public evaluation page was not migrated with it.

Unified Evaluation Experience v1 restores one human journey over both generations:

```text
Recommendation explanation
  -> pre-watch reaction
  -> watched outcome
  -> release-bound export or explicit manual handoff
  -> verified append-only capture
```

The implementation remains a thin client. It does not rank films, calculate trust,
change taste weights, verify releases, or write outcomes.

## Live entrypoint

GitHub Pages deploys `tools/canonical-review` at:

`https://brutisthebrut-debug.github.io/cinema-brain/evaluate.html`

The same URL that hosted Human Evaluation Pack v1 now hosts the unified experience.

## Preserved pre-watch evidence

The page retains the original evaluation signals:

- whether Daniel had already seen the film;
- interest created by the recommendation;
- whether the explanation sounded wrong, partly right, or exactly right;
- whether Daniel watched because Cinema Brain recommended it;
- actual sentiment and recommendation-to-similar-taste judgment;
- free-form nuance.

Existing Human Evaluation Pack v1 browser data is migrated by `film_key` when
present.

## Added post-watch evidence

The same film card now captures all Outcome Capture v1 fields:

- rating from 0.5 to 5.0;
- one honest immediate reaction sentence;
- completed or not completed;
- genuinely glad watched or not;
- fit the moment, missed the moment, or unknown;
- watched and recorded timestamps.

## Release-bound mode

Import `post_watch_outcome_submission_v1.json` from the private recommendation
artifact. The page validates the template version, submission type, `release_id`,
`audit_id`, and non-empty released slate. It then limits evaluation to that slate
and exports an exact Post-watch Outcome Submission v1 record.

The imported immutable identity fields are copied, not regenerated. Final release,
snapshot, and audit verification still belongs to
`cinema_brain.post_watch_outcomes`; browser output is never trusted by itself.

## Manual mode

Manual mode preserves tonight's real human reaction when the release template is
not conveniently available. It exports `post_watch_manual_intake` and produces a
copyable chat handoff containing the same answers.

Manual records carry:

`manual_unbound_do_not_count_as_recommendation_trust_until_verified`

An agent may later bind the intake only when it can prove a qualifying frozen
release existed before the watch and contained the same `film_key`. Otherwise the
record remains useful human-evaluation evidence but must not be counted as formal
Recommendation Trust. The system never backdates or invents a release identity.

## Privacy and storage

- The page makes no network requests.
- Draft answers and an imported template are stored only in the current browser's
  local storage so mobile progress survives refreshes.
- Export happens by local download or clipboard copy.
- Reset clears both v1 and unified evaluation browser records.

## Regression boundary

`tests/test_unified_evaluation_ui.py` prevents later UI changes from:

- dropping either the pre-watch or post-watch phase;
- omitting a required Outcome Capture v1 field;
- treating manual intake as verified trust evidence;
- or adding a network-owned submission path.

## Resume point

After deployment, Daniel can use the live page immediately. The next production
operation remains first-outcome review. No taste-weight change, regression
promotion, or corpus expansion is authorized until that evidence is inspected.

