# Reviewed Benchmark Regression Gate

This gate turns promoted human-reviewed records into executable truth.

It compares each reviewed golden record against a fresh bounded sample and fails when:

- the provider title is no longer canonical or an accepted alias;
- the provider year changes;
- a reviewed film is missing from the sample;
- an expected trait disappears from the observed genres, keywords, or extracted traits.

Unreviewed seed records are never treated as release-gating truth. A benchmark with zero reviewed records cannot pass.

The report records benchmark version, reviewed count, pass/fail totals, per-film identity status, and missing traits. This is the first point where the golden dataset protects live metadata and Evidence behavior rather than only its own file integrity.

The next production step is to wire this evaluator into the bounded real-data workflow after the first records are explicitly reviewed and promoted.