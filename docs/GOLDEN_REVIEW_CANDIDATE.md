# Golden Review Candidate Workflow

This workflow converts a completed human review worksheet into a reviewable benchmark candidate without granting automation permission to modify the repository.

## Inputs

- `review_ref`: branch or commit containing the completed CSV worksheet
- `worksheet_path`: repository-relative worksheet path
- `reviewer`: human reviewer recorded in the decision packet
- `next_version`: proposed benchmark version

## Trust boundary

The workflow checks out two separate trees:

1. trusted Cinema Brain code and benchmark from `main`
2. only the requested worksheet from the review ref

The review branch's Python code and workflows are never executed. The worksheet path is resolved and rejected if it escapes the isolated review-input directory.

## Output bundle

- completed review worksheet
- compiled decision packet
- exact source benchmark
- promoted benchmark candidate
- unified benchmark patch
- SHA-256 manifest
- reviewer instructions

## Deliberate limitations

The workflow has `contents: read` permission only. It cannot commit changes, open or approve a pull request, promote a benchmark in place, or merge anything.

A human must inspect the candidate bundle and explicitly place the candidate benchmark into a normal pull request. CI then evaluates that pull request before merge.
