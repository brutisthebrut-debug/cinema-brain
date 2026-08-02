# Founding Principles

1. **Build for decades, not demos.** Optimize for a system Daniel can still trust and use in ten years.
2. **Memory is sacred.** Never silently discard, rewrite, or merge personal history without provenance.
3. **Evidence before inference.** Every meaningful conclusion must be traceable to its supporting and contradicting evidence.
4. **Human judgment wins.** Daniel can correct any identity, fact, trait, prediction, or outcome without erasing the original record.
5. **Explainability is non-negotiable.** No recommendation may rely on “the AI thinks so.” It must identify why, confidence, and risk.
6. **Build capabilities, not isolated features.** Prefer one reusable layer over multiple special-purpose implementations.
7. **Simple systems should be allowed to evolve.** Avoid unnecessary complexity, provider lock-in, and premature abstraction.
8. **Measure quality, not activity.** Code volume, feature count, and velocity do not substitute for accuracy, reliability, and usefulness.
9. **Privacy by default.** Personal behavioral, health, journal, and relationship data require explicit boundaries and minimal exposure.
10. **Failures become evidence.** Bad matches, failed recommendations, sync errors, and wrong assumptions become regression tests and calibration data.
11. **Every brain is independently excellent and collectively smarter.** Shared intelligence travels through contracts and permissions, not hidden coupling.
12. **GitHub is the engineering source of truth.** Chat may generate ideas; implemented decisions, status, and doctrine must be recorded in the repository.

## The Forever Test

Before accepting a major capability, ask:

> Will we still be glad we built this in ten years?

A capability should normally pass at least four checks:

- It improves a real recurring decision.
- It strengthens or reuses the architecture.
- It remains understandable and replaceable.
- It respects privacy, provenance, and human correction.
- Its ongoing maintenance cost is justified.

Uncertain ideas are not rejected forever. They are deferred until evidence earns their complexity.

## Architecture fitness checks

After every 10–20 meaningful milestones, or sooner when complexity rises, pause feature work briefly and review:

- Is the architecture still coherent?
- Are concepts duplicated across layers?
- Has technical debt exceeded its justification?
- Are contracts still stable and appropriately narrow?
- Do tests protect the highest-risk paths?
- Can anything be deleted or simplified?
- Has implementation drifted from the vision?
- Are cross-brain boundaries still private and explicit?

The review should produce concrete deletions, migrations, debt updates, or an explicit decision that no change is needed.
