---
name: art-style-builder
description: Build and lock a production-usable game art style through adaptive interviews, structured visual requirements, calibration asset planning, reference comparison, and approved style anchors. Emit ArtStyle.md, art-style.yaml, and style-anchor-manifest.yaml for downstream asset production.
---

# Art Style Builder

## Purpose

Convert incomplete visual intent into an explicit, production-usable art system. A usable style is not a mood phrase or one long prompt; it is **structured visual invariants + approved visual anchors**.

```text
GameSpec + Art Intent / References
→ Visual Requirement Graph
→ Adaptive Questions
→ Draft Art Style
→ Calibration Set
→ Candidate Comparison
→ Approved Anchors
→ STYLE LOCK
```

## Rules

- Read GameSpec first when available; derive visual constraints but never modify game semantics.
- Track `UNSEEN`, `UNRESOLVED`, `INFERRED`, `PROPOSED`, `CONFIRMED`, `CONFLICT`, `LOCKED`, `NOT_APPLICABLE`.
- Ask 1–3 high-impact visual questions at a time; prioritize gameplay readability, dimensionality/camera, shape language, line/rendering medium, color/value, texture, lighting, then decoration.
- Separate GLOBAL STYLE from CATEGORY OVERRIDES for character, environment, interactive_object, UI, icon, FX, and background.
- Treat negative constraints as first-class `forbidden` rules.
- Never silently merge conflicting references; declare which dimensions each reference governs.
- Do not start mass production before calibration.

## Calibration

Use a representative minimal set such as character, structural environment, interactive object, UI button/panel, icon, background fragment, and FX. Create A/B/C only when a decision dimension is genuinely unresolved. Convert feedback such as “line from B, color from A, less texture” into structured rules before regenerating.

Approved anchors must declare roles such as `style_anchor`, `identity_anchor`, `palette_anchor`, `geometry_anchor`, or `category_anchor`, plus the fields they govern.

## Readiness

- `STYLE_DIRECTION_READY`: emotional tone, dimensionality, shape language, line/rendering approach, color/value, texture, major forbidden rules.
- `CALIBRATION_READY`: direction ready + category rules + calibration set + output constraints.
- `ASSET_GENERATION_READY`: global/category rules locked, production-critical anchors approved, forbidden rules locked, no blocker conflicts.
- `STYLE_PRODUCTION_READY`: generation ready + runtime readability/state visualization/output consistency rules.

## Outputs

```text
ArtStyle.md
art-style.yaml
style-requirement-state.yaml
style-decision-log.md
style-anchor-manifest.yaml
calibration-plan.yaml
```

Downstream asset generation must consume the locked structured style and scoped anchors without inventing new art direction.
