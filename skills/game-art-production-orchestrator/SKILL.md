---
name: game-art-production-orchestrator
description: Orchestrate the AI-native game art production pipeline from locked game specification and art style through asset planning, generation, normalization, QC, and runtime visual validation. Enforce readiness gates, artifact contracts, provenance, failure routing, and deterministic handoffs between specialized skills.
---

# Game Art Production Orchestrator

## Purpose

Coordinate the pipeline without duplicating specialist responsibilities. Decide current stage, authoritative artifacts, allowed next skill, readiness gate, failure owner, invalidation scope, and promotion state.

```text
game-spec-builder
→ art-style-builder
→ game-asset-planner
→ game-asset-generator
→ game-asset-normalizer
→ game-asset-qc
→ runtime-visual-validator
```

## Source-of-truth hierarchy

1. LOCKED GameSpec
2. LOCKED ArtStyle
3. Approved Style Anchors
4. Asset Manifest / Asset Specs
5. Generation records
6. Normalization records
7. QC reports
8. Runtime validation reports

Downstream artifacts never silently rewrite upstream sources.

## Pipeline state

Maintain `.pipeline/game-art-production-state.yaml` with stage statuses `NOT_STARTED`, `IN_PROGRESS`, `READY`, `BLOCKED`, `FAILED`, `INVALIDATED`, `COMPLETE`.

Asset lifecycle:

```text
PLANNED
→ READY_FOR_GENERATION
→ GENERATED
→ NORMALIZED
→ QC_APPROVED
→ RUNTIME_APPROVED
→ SHIPPABLE
```

Failure states: `GENERATION_REWORK`, `NORMALIZATION_BLOCKED`, `QC_REWORK`, `RUNTIME_REWORK`, `INVALIDATED`.

## Handoffs

Validate each input/output contract and readiness gate before advancing. Record artifact paths/hashes when available, readiness, scope, and provenance. Do not rerun completed earlier stages without cause.

## Failure routing

- semantics/screen flow/state behavior → game-spec-builder
- visual rules/anchors/readability policy → art-style-builder
- MRAU/variant/representation/runtime requirement → game-asset-planner
- wrong visual/state/identity/style output → game-asset-generator
- canvas/scale/alpha/anchor/pivot processing → game-asset-normalizer
- incorrect asset-level classification/evidence → game-asset-qc
- runtime evidence/test attribution → runtime-visual-validator or runtime integration

## Invalidation

When an upstream source changes, invalidate only dependent descendants. Preserve old provenance. Do not restart the entire pipeline for a narrow change.

## Batch order

Tier 0 calibration/anchors → Tier 1 P0 core gameplay → Tier 2 P0 variants → Tier 3 core UI → Tier 4 secondary/progression → Tier 5 decoration/FX. Do not scale a later tier while an earlier representative tier exposes systemic problems.

## Completion

Production is complete only when required specs/styles are locked, planned assets are generated and normalized, QC passes, runtime validation passes, required assets are SHIPPABLE, and no blocker remains.
