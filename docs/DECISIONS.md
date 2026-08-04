# Decision Log

This file records major product and operating decisions in chronological form. Detailed architectural reasoning may also live in `docs/adr/`.

## 2026-08-02

### Cinema Brain is the Daniel OS reference implementation
Future brains should reuse the lifecycle Source → Canonical Identity → Evidence → Learning → Prediction → Outcome → Calibration.

### Build capabilities, not isolated features
Work should strengthen reusable ingestion, identity, evidence, metadata, ranking, learning, and interface capabilities.

### CSV is the historical authority; RSS is the delta stream
Letterboxd exports reconcile and correct history. RSS keeps recent activity current between exports. Manual updates provide immediate private context.

### Evidence must preserve provenance and contradiction
The system does not silently average away disagreement or erase the source of a conclusion.

### Recommendations must be explainable
Every recommendation must identify supporting evidence, confidence, meaningful risk, and relevant model versions.

### One stable recommendation interface
Conversation, CLI, dashboards, and future Daniel OS modules consume the same recommendation contract and ranking engine.

### Metadata providers remain replaceable and licensing-compatible
Provider facts are cached with source, retrieval time, and confidence. No provider may overwrite Daniel's explicit labels.

### GitHub is the engineering source of truth
Chat is a design and operating interface. Repository documents and code are the canonical record of implementation, status, decisions, debt, and doctrine.

### Engine quality precedes dashboard work
A dashboard remains a thin client and is deferred until recommendation quality and explanations are measurable.

### The Forever Test governs major additions
Before accepting significant complexity, ask whether the system will still benefit from it in ten years.

### Architecture fitness checks are recurring maintenance
After roughly 10–20 meaningful milestones, pause to inspect coherence, duplication, debt, tests, simplification opportunities, and vision drift.

### Every brain is independently excellent and collectively smarter
Cross-brain intelligence must use explicit contracts, permissions, and inspectable evidence rather than hidden implementation coupling.

## 2026-08-03

### Human evaluation and release-bound outcomes are one experience

The original top-five evaluation UI and the later Post-watch Outcome Capture v1
contract are complementary, not competing flows. The UI must preserve pre-watch
interest and explanation evidence while collecting the release-bound post-watch
outcome on the same film card.

When a release template is unavailable, manual intake remains valuable human
evidence but cannot count as Recommendation Trust unless a matching release frozen
before the watch is verified. Cinema Brain never invents or backdates release
identity to rescue an outcome.
