# Golden Benchmark Promotion

Promotion is the explicit boundary between a review decision and trusted benchmark truth.

## Rules

- Only `approved` decisions may promote a record.
- Approved decisions must retain an `exact` identity evaluation.
- Provider title must equal the canonical title or an accepted alias.
- Provider year must equal the benchmark release year.
- Rejected and quarantined decisions remain visible but never mark a record reviewed.
- Review packets are bound to one benchmark version and cannot be replayed against a changed dataset.
- Every successful promotion writes a new benchmark version and records its previous version.
- Promotion must produce at least one newly reviewed record; no-op releases are rejected.

## Workflow

1. Generate a bounded real-data sample review artifact.
2. Record approved, rejected, or quarantined decisions with reasons.
3. Validate the review packet against the exact source benchmark version.
4. Promote only approved exact matches.
5. Review the generated benchmark diff.
6. Run the complete CI and golden release gate.
7. Merge the new benchmark version.

No provider, workflow, or model may mark its own result as reviewed truth.
