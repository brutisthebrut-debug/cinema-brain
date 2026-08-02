# ADR-003: Stable, explainable recommendation interface

- Status: Accepted
- Date: 2026-08-02

## Context

Cinema Brain may be accessed through conversation, CLI, a future dashboard, or other Daniel OS modules. Independent ranking logic in each interface would drift and become impossible to calibrate.

## Decision

Expose recommendation behavior through one stable typed interface. Every result must include score components, confidence, evidence, caveats, model versions, and candidate rejection reasons when requested. Interfaces remain thin clients and do not own ranking logic.

## Alternatives considered

- Direct database queries from each interface: rejected because behavior would diverge.
- Opaque model-only recommendations: rejected because failures could not be debugged or trusted.

## Consequences

New interfaces require less duplicated work, and every recommendation can be traced, evaluated, and improved through the same learning ledger.
