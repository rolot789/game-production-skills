---
name: runtime-visual-validator
description: Validate approved game assets inside actual playable game contexts. Capture runtime evidence, inspect scene-level readability, state differentiation, visual hierarchy, placement, occlusion, UI overlap, animation/state transitions, and visual regressions; attribute failures to the correct upstream owner.
---

# Runtime Visual Validator

## Principle

A game asset is not finished until it works in context. Asset QC asks whether an asset is valid in isolation; runtime validation asks whether it remains valid against the real background, camera, scale, UI, neighbors, lighting, compositing, animation, and post-processing.

## Validate

- contextual readability
- visual hierarchy
- state differentiation
- placement/alignment
- occlusion/overlap
- actual rendered scale
- z-order/blend/opacity/masking/compositing
- animation/transition clarity and anchor jitter
- semantic visual regression
- style in context

Define a deterministic validation plan before capture: scene, viewport, camera, target assets/families, states, entry steps, capture points, expected behavior, baseline.

For Canvas/WebGL, screenshots/frame evidence are mandatory; DOM assertions alone are insufficient. If no executable runtime is available, validate supplied captures but return `partial_validation_only`, not full runtime approval.

## Levels

1. Single asset in scene
2. Family/state validation
3. Full scene validation

P0 gameplay assets should reach level 2 or 3 before shipping.

## Root-cause routing

A runtime symptom is not automatically a runtime asset problem. Route undefined behavior to game spec; incompatible style/hierarchy to art style; wrong decomposition/state representation to planner; malformed visual to generator; transform/anchor/canvas issue to normalizer; missed isolated issue to QC; z-index/layout/camera/lighting/blend implementation to runtime integration.

## Status

`runtime_approved`, `runtime_approved_with_minor_findings`, `runtime_rework_required`, `runtime_blocked`, `partial_validation_only`.

Only project-allowed approved statuses may promote to SHIPPABLE.
