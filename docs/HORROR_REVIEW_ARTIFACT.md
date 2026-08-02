# Horror Review Artifact Bundle

The manual `cinema-brain-horror-sample-review` workflow is the operating bridge between real provider enrichment and human benchmark decisions.

## Bundle contents

Each bounded run uploads one private 30-day artifact containing:

- the exact benchmark version used
- provider enrichment output
- persisted metadata-Evidence output
- the human-readable sample review JSON
- an editable CSV decision worksheet
- review instructions
- SHA-256 checksums
- the reconstructed SQLite database used for the run

## Safety boundary

The workflow does not approve, reject, quarantine, compile, promote, commit, or merge any benchmark record. It only prepares a reviewable evidence bundle.

Daniel remains the explicit reviewer. Completed CSV decisions must still pass compilation safeguards, benchmark-version checks, exact identity evaluation, guarded promotion, CI, and pull-request review.

## Operating sequence

1. Run the workflow with a bounded limit.
2. Download the generated artifact.
3. Review the JSON evidence and edit only the decision and reason columns in the CSV.
4. Compile the completed worksheet into a version-bound decision packet.
5. Promote approved exact matches into a new benchmark file.
6. Review the generated diff and run CI before merge.

Checksums make accidental file drift visible between generation and review. They are integrity evidence, not a cryptographic signature or proof of human approval.
