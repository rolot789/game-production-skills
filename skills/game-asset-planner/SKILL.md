---
name: game-asset-planner
description: Compile locked game specification and art style into a production-ready asset manifest. Discover semantic visual entities, decompose them into minimum reusable asset units, expand required state/direction variants, select representation strategies, and emit traceable per-asset production specs.
---

# Game Asset Planner

## Purpose

Compile immutable `GameSpec + ArtStyle + approved anchors` into the complete set of visual production requirements. Do not generate images.

```text
Locked GameSpec + Locked ArtStyle
→ Semantic Visual Inventory
→ MRAU Decomposition
→ State / Direction / Variant Expansion
→ Representation Strategy
→ asset-manifest.yaml + specs/<asset-id>.yaml
```

## Principles

- Plan from runtime semantics, not screenshot crops.
- A Minimum Reusable Asset Unit (MRAU) is something that must be independently placed, swapped, animated, hidden, reused, or state-controlled.
- Convert game rules into visible states. Example: gate blocking/opening semantics may require closed/open/transition states and orientation variants.
- Expand only meaningful variant combinations; avoid blind Cartesian products.
- Choose representation deliberately: `generated_raster`, `generated_vector`, `generated_3d`, `procedural`, `runtime_primitive`, `runtime_text`, `shader_or_particle`, or `reuse_existing`.
- Do not turn runtime text, simple lines, or suitable procedural effects into PNGs without reason.
- Every asset must retain source traceability to GameSpec/ArtStyle paths and rationale.
- Define family/shared geometry/shared anchor groups for state/direction variants.
- Record runtime dimensions/footprint, background policy, anchor/pivot expectations, animation semantics, priority, and QC requirements.
- If required semantics are unresolved or contradictory, block rather than invent.

## Outputs

```text
asset-manifest.yaml
specs/<asset-id>.yaml
```

Each spec should identify asset_id, family/category, purpose, state/orientation, production strategy, source refs, style inheritance/overrides, dependencies, shared geometry/anchor groups, priority, runtime constraints, and QC requirements.
