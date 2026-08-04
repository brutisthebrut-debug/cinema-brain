# Manual Outcome Reconciliation v1

## Purpose

The unified evaluation page can produce a manual post-watch handoff when Daniel
does not have the private release template. Manual Outcome Reconciliation v1
turns that handoff into verified evidence without weakening Recommendation
Release Gates v1 or inventing a historical `release_id`.

This is a transition contract for predictions frozen before release gates were
available. It is not a second recommendation system.

## Inputs

The reconciler accepts:

- the original `frozen_top_five` human-evaluation packet;
- one `post_watch_manual_intake` exported by the unified evaluation page.

The detailed files remain private. The repository stores the generic engine,
tests, contract, and safe aggregate handoff only.

## Verification boundary

The engine fails closed unless:

1. source artifact, film key, title, and year match exactly;
2. the frozen packet contains exactly five unique pre-watch predictions;
3. the matched film was explicitly unwatched;
4. the frozen record still says `watched_after_recommendation: not_yet`;
5. rating and sentiment are still empty in the frozen record;
6. predicted score and confidence are valid;
7. the manual handoff preserves its explicit unbound status;
8. the handoff confirms that the completed watch followed Cinema Brain's recommendation.

Differences in copied pre-watch answers are reported as field drift; they do not
rewrite the frozen values.

## Metric separation

A verified manual outcome may report:

- observed recommendation trust from `glad_watched`;
- completion and moment-fit evidence;
- a provisional rating-calibration comparison;
- an unpromoted review candidate when the result crosses an existing Outcome v1 threshold.

It must always report:

```text
formal_release_bound_trust_eligible: false
formal_release_bound_recommendation_trust: null
release_id: null
```

The observed result is useful historical evaluation evidence. It is never mixed
into the formal aggregate produced from content-addressed Post-watch Outcome v1
records.

## Calibration and review candidates

The frozen legacy `predicted_score` is projected onto the Letterboxd scale using
the same linear shape as Outcome Capture v1:

```text
2.75 + 2.25 × predicted_score
```

The method is named separately as
`legacy_linear_predicted_score_to_letterboxd_0.5_5.0_v1`. A review candidate is
created for the same observable conditions used by Outcome Capture v1, but it is
marked `formal_release_bound_fixture: false` and
`promotion_status: candidate_not_promoted`.

## Append-only CLI

```bash
python -m cinema_brain.cli reconcile-manual-outcome \
  --evaluation daniel_human_evaluation_top5_v1.json \
  --submission cinema_brain_manual_handoff_v1.json \
  --output-dir outcomes/manual
```

The command writes:

```text
outcomes/manual/<source_artifact>/<outcome_id>/
  manual_outcome_reconciliation_v1.json
  manual_outcome_regression_candidate_v1.json  # only when review is required
```

Exclusive directory creation prevents replay from replacing prior evidence.

## First production evidence

Noroi: The Curse (2005) is the first manual outcome to pass the identity and
pre-watch timing checks against `daniel-unwatched-horror-ranking-v2`.

Safe aggregate interpretation:

- Daniel completed it, was glad he watched, and said it fit the moment;
- actual rating was 3.5/5, sentiment was `like`, and recommendation intent was `yes`;
- the explanation fit was `nailed_it`;
- observed legacy trust is 1.0 for one verified manual outcome;
- formal release-bound Recommendation Trust remains unmeasured;
- the 0.888 legacy score projects to 4.748/5, producing a -1.248 signed error;
- calibration therefore creates an unpromoted review candidate for
  `rating_projection_miss` and `overconfident_miss`.

The recommendation succeeded behaviorally. The review candidate concerns score
calibration, not whether Noroi belonged on the slate.

## Handoff

Do not change taste weights, promote the candidate, or expand directly to 25
reviewed horror films from this one result. The next evidence operation is a
second watch from the already frozen top five or a newly generated release-bound
slate. Use it to determine whether the score calibration gap repeats and whether
narrative legibility is a durable taste dimension rather than a one-film note.
