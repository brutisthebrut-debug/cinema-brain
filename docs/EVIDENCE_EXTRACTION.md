# Evidence Extraction Engine

## Purpose

Convert provider metadata into reproducible film-level signals without confusing external facts with Daniel's preferences.

## Pipeline

```text
Provider metadata fact
  -> normalized label
  -> versioned deterministic mapping
  -> film-level Evidence record
  -> Evidence Graph
  -> later profile and ranking aggregation
```

## Guarantees

- Metadata facts remain unchanged in canonical storage.
- Every inferred signal retains provider and source-label provenance.
- Downstream confidence never exceeds source confidence.
- Unmapped labels are reported for taxonomy review.
- Contradictions are preserved, not overwritten.
- Extraction is deterministic, idempotent by Evidence identity, and model-versioned.
- Human reactions remain a separate, higher-authority evidence class.
- Historical evidence is never deleted; future recency weighting occurs during aggregation or ranking.

## Initial horror vocabulary

The first mapping covers broad horror, psychological horror, found footage, folk horror, supernatural horror, body horror, cosmic horror, slashers, creature features, ghosts, haunted houses, survival, thrillers, and dark comedy. This is deliberately bounded. The golden dataset will determine which additional traits earn inclusion.

## Deferred

- LLM-generated traits
- embeddings
- automatic evidence decay
- whole-library extraction

These remain deferred until deterministic extraction is validated against the horror-heavy golden dataset.
