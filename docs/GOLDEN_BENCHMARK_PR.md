# Golden Benchmark Pull Request Gate

A generated benchmark candidate is not trusted merely because the review and promotion workflows completed. The final pull request is a separate release boundary.

## Required files

A benchmark release pull request must contain:

- the unchanged source benchmark for comparison or an unambiguous link to its version
- the compiled review decision packet
- the promoted candidate benchmark
- the generated source-versus-candidate patch
- the integrity manifest from the candidate workflow

## Automated invariants

The candidate validator enforces:

- `previous_version` equals the source benchmark version
- the candidate version is new
- the review packet targets the source version
- no benchmark records are added or removed during promotion
- titles, years, aliases, entity types, hazards, and expected traits remain unchanged
- reviewed records never regress to unreviewed
- every new `reviewed=true` transition has an approved exact decision
- provider title and year still match the accepted benchmark identity
- at least one record is newly promoted

## Human review checklist

Before merge, confirm:

- the reviewer identity and reasons are credible
- every approved film was actually inspected
- rejected and quarantined rows remain unreviewed
- the candidate diff changes only version lineage and approved `reviewed` flags
- the integrity manifest matches the downloaded candidate bundle
- the full regression suite and candidate validator are green

No workflow may approve or merge a benchmark release automatically.
