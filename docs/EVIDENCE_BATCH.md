# Bounded Metadata Evidence Batch

This milestone connects persisted provider metadata to the durable Evidence Graph without performing whole-library inference.

## Command

```bash
python -m cinema_brain --db cinema_brain.db extract-metadata-evidence \
  --film-key undertone-2025 \
  --output reports/metadata_evidence.json
```

When no film key is supplied, the command processes a bounded recent set using `--limit`.

## Guarantees

- reads only canonical persisted metadata
- uses the versioned deterministic extraction model
- persists evidence through `EvidenceStore`
- remains idempotent across repeated runs
- reports inserted and duplicate evidence separately
- reports unmapped provider labels for taxonomy review
- never converts film traits directly into Daniel preference
- supports explicit bounded film sets for golden-dataset review

## Next gate

Run enrichment and extraction on a small horror sample, inspect every identity match and unmapped label, then turn errors into regression fixtures before broadening the taxonomy or library scope.
