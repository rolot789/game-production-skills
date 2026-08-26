---
name: game-asset-normalizer
description: Normalize approved or candidate game art outputs into deterministic, engine-ready runtime assets by applying explicit canvas, scale, bounds, padding, alpha, anchor, pivot, family-alignment, naming, and export rules. Use after generation and before asset QC.
---

# Game Asset Normalizer

## Principle

**Normalize mechanics, not aesthetics.** This stage may resize, pad, trim according to explicit policy, normalize alpha/canvas/scale, align families, attach anchor/pivot metadata, export formats, hash and validate. It must not redraw, restyle, invent missing content, repair semantic generation failures, or silently crop required content.

## Process

```text
inspect geometry/alpha bounds
→ resolve normalization policy
→ trim decision
→ uniform scale
→ canvas placement / padding
→ family alignment
→ visual anchor + runtime pivot metadata
→ deterministic export
→ validation/report
```

Keep `visual_anchor`, `runtime_pivot`, and `collision_origin` distinct. Family variants should share appropriate canvas, scale basis, anchor, baseline, pixel density, and coordinate system; do not independently maximize each state.

Use scripts/deterministic operations for pixel mechanics. Model judgment is limited to selecting explicitly allowed branches and routing failures.

## Failure routing

- malformed/missing visual content → `game-asset-generator`
- contradictory runtime constraints → `game-asset-planner`
- processing failure → `game-asset-normalizer`

## Outputs

```text
normalized/<asset-id>/
├── runtime/<asset-id>.<ext>
├── normalization-record.yaml
├── geometry-report.yaml
└── preview/
```

Ready for QC only when dimensions, alpha, clipping, scale, anchor/pivot, family invariants, record completeness, and deterministic validation pass.
