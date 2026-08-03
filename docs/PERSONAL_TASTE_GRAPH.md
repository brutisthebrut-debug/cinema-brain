# Personal Taste Graph v1

Brain v0.2 converts reviewed film traits and Daniel's persisted viewing history into an explainable user-to-trait graph.

## Inputs

- `config/canonical_horror_profiles_v1_reviewed.json`
- watched film rows from the canonical SQLite database
- ratings
- likes
- rewatches
- review and list presence
- recommendation outcomes when available

Only films present in the reviewed profile set contribute trait evidence. Unknown or unreviewed films are ignored until they have canonical traits.

## Output

Run:

```bash
python -m cinema_brain.cli --db cinema_brain.db personal-taste-graph \
  --profiles config/canonical_horror_profiles_v1_reviewed.json \
  --output profiles/personal_taste_graph_v1.json
```

The output records:

- model, profile, and registry versions
- trait affinity
- confidence
- evidence count
- positive and negative evidence counts
- conflict state
- supporting films
- contradicting films
- provisional versus learned status

## Guardrails

- reviewed film truth and personal taste remain separate
- sparse evidence remains provisional
- positive and negative signals are not averaged away without exposing conflict
- the same database and profile versions produce deterministic output
- no prompt or network call is involved

## Next slice

Generate the first bounded real-data artifact from Daniel's canonical database, inspect coverage and uncertainty, then add scoring of the nine reviewed horror profiles against the taste graph.
