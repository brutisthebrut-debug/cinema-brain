# ADR 005: Metadata signals become versioned Evidence records

Status: Accepted

## Context

Provider metadata contains facts and labels, while Cinema Brain needs reusable interpretive traits. Treating provider labels as Daniel preferences would collapse distinct evidence classes and overstate certainty.

## Decision

- Provider metadata remains a factual snapshot.
- A deterministic, versioned extraction layer maps selected labels into film-level Evidence records.
- Extracted evidence is marked `metadata_inference`, retains provider/label provenance, and cannot be more confident than its source metadata.
- Unmapped labels are reported rather than silently discarded.
- Conflicting evidence is preserved by the Evidence Graph.
- LLM-generated traits and embeddings remain deferred until deterministic extraction is measurable against the golden dataset.
- Taste recency and evidence decay will be applied later at ranking/profile time; historical evidence is never deleted or mutated.

## Consequences

The same extraction contract can support horror, comedy, romance, and other domains. Taxonomy changes are model-version changes, and profiles can be regenerated reproducibly without rewriting source metadata.
