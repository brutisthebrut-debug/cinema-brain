# Golden Review Decisions

The executable golden dataset is seeded separately from human approval. A provider result becomes reviewed truth only through an explicit decision.

## Decision states

- `approved` — the provider identity is an exact accepted-title and release-year match, and the reviewer verified it.
- `rejected` — the provider selected the wrong entity or supplied materially incorrect identity data.
- `quarantined` — the result is plausible but requires more evidence, an alternate title, or another provider before approval.

## Safety rules

- Only an `exact` identity evaluation can be approved.
- Every decision records reviewer, timestamp, reason, expected identity, provider identity, and evaluation status.
- Duplicate decisions for the same benchmark record are rejected in one decision packet.
- Rejected or quarantined records block benchmark promotion.
- The seed benchmark remains unreviewed until a separate promotion step applies approved decisions.

## Workflow

1. Run the bounded real-data sample workflow.
2. Inspect the private sample review artifact.
3. Create one explicit decision per reviewed film.
4. Preserve rejected and quarantined cases as regression evidence.
5. Promote only approved records into the reviewed golden benchmark.
6. Run the release gate again before broadening enrichment.

This split prevents automation from silently declaring provider output to be human-reviewed truth.
