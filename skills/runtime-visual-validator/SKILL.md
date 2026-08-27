---
name: runtime-visual-validator
description: Use when approved assets must be checked inside the running game — "does this actually work in the game", "the icon is unreadable in that level", "the selected state stopped reading after the update" — or when a scene regression appears. Captures reproducible rendered evidence, separates integration failures from upstream asset failures, and never promotes partial evidence to approval. Defects visible without scene context belong to game-asset-qc; atlas and import problems belong to game-engine-integrator.
---

# Runtime Visual Validator

## Purpose

Determine whether a QC-approved asset actually works in the game context where the player sees and uses it.

```text
Game Asset QC
  "Is this asset valid against its production contract?"

Runtime Visual Validator
  "Does this valid asset still work when rendered in the actual game?"
```

A runtime symptom may originate from scene integration, normalization, generation, planning, art direction, or game semantics. Do not assume the visible symptom owns the root cause.

## Project path resolution

If `project.yaml` exists, its `paths` registry is canonical. Resolve logical runtime-validation paths through it rather than hard-coding repository roots.

## Core rules

1. Validate in actual rendered context.
2. Do not duplicate isolated QC unless runtime evidence exposes a missed/context-sensitive defect.
3. Record reproducible build/scene/viewport/camera/state/capture evidence.
4. Rendered evidence is mandatory for visual claims; DOM/code assertions are only supporting evidence for Canvas/WebGL.
5. Intended player scale is authoritative.
6. Protect semantics rather than brittle pixel identity.
7. Route to the root owner.
8. Preserve already-passing context dimensions.
9. Invalidate the smallest affected context/dependency surface.
10. No executable runtime means no full runtime approval.

## Inputs

Typical inputs:

```text
playable build / executable preview
QC-approved runtime asset/version
qc/<asset-id>/qc-report.yaml
engine-integration/<target-id>/integration-plan.yaml   when engine integration ran
specs/<asset-id>.yaml
normalization-record.yaml
art-style.yaml when context rules matter
style-anchor-manifest.yaml when scoped comparison matters
style-constraint-ledger.yaml when contextual constraints matter
family/state context
baseline captures or prior runtime report when regression testing
project.yaml
```

For revalidation/rework, consume canonical `change_scope / preserve_scope` from `references/rework-handoff-contract.yaml`.

## Preflight

Before full validation:

1. confirm executable target,
2. confirm exact target asset/version is integrated,
3. confirm acceptable QC status for that same lineage,
4. define contexts, states, viewport(s), camera, and capture points,
5. define expected player-visible behavior,
6. identify baseline evidence when relevant,
7. record limitations.

If only supplied captures are available, return `partial_validation_only`.

## Validation levels

- **Level 1 — Asset in scene:** size, placement, contrast, clipping, compositing, local overlap.
- **Level 2 — Family/state context:** state differentiation, family continuity, anchor stability, direction/transition consistency.
- **Level 3 — Full scene hierarchy:** focal hierarchy, world/UI separation, occlusion, lighting/post-process interaction, simultaneous gameplay readability.
- **Level 4 — Flow/regression context:** transitions, camera/viewports, feedback timing, semantic regressions.

Use the minimum level required by risk; P0 stateful gameplay assets generally require Level 2 or 3.

## Runtime dimensions

Evaluate only applicable dimensions:

- actual-scale readability,
- scene hierarchy,
- state differentiation,
- placement/alignment,
- occlusion/overlap,
- z-order/blend/opacity/masks/shaders/post-processing,
- animation/transition continuity,
- UI/world collisions,
- contextual style integrity,
- semantic visual regression.

Do not re-score isolated ArtStyle from scratch.

## Runtime evidence

For BLOCKER/MAJOR visual findings record, when available:

```text
build / commit identifier
scene / route / level
viewport / device class
camera state
game state
asset ID + runtime asset version
normalization/QC lineage
capture ID
screenshot/frame sequence
baseline capture ID
reproduction steps
```

For Canvas/WebGL, screenshot/rendered-frame evidence is required. Animation issues should use frame sequences or equivalent deterministic evidence where possible.

Use `references/runtime-evidence-policy.md`.

## Finding model

Separate symptom, root owner, and remediation scope.

```yaml
id: RTV-001
severity: MAJOR
context_id: CTX-003
capture_ids: [CAP-008]
dimension: state_differentiation
expected: current state remains clearly stronger at gameplay scale
observed: scene bloom erases the approved value hierarchy
root_owner: runtime_integration
root_reason: approved assets pass isolated QC; scene post-processing destroys contrast
required_action: reduce/scope bloom
```

Specialist-local diagnostic fields such as `change` or `preserve` may exist in the runtime report, but external routing must use canonical `change_scope / preserve_scope`.

## Root-cause routing

Root ownership follows `references/routing.yaml` — the single source of truth for symptom class, root owner, invalidation scope, and revalidation scope. Work its `decision_procedure` in order, then take the owner and both scopes from the matching row rather than deciding them independently.

Every `BLOCKER` and `MAJOR` finding carries a `reason_code` naming its class. An unknown code is a malformed report.

The two traps this stage falls into most often:

- **Assuming the symptom owns the cause.** A defect visible in a scene is not automatically an integration defect. Steps 2 through 4 of the decision procedure exist to separate them.
- **Sending an asset back to QC.** QC cannot edit assets. Route content rework to its producing owner and record `qc_escape: true` with the missed dimension separately.

Use `references/runtime-regression-routing-policy.md` for how to recognize each class in runtime evidence, and for regression classification and escalation.

## Canonical rework handoff

External rework MUST serialize through `references/rework-handoff-contract.yaml` and validate against `references/schemas/rework-handoff.schema.json`.

Example for runtime-integration-only failure:

```yaml
root_owner: runtime_integration
reason_codes:
  - SCENE_COMPOSITING_FAILURE

change_scope:
  dimensions: []
  artifacts: []
  runtime_properties:
    - scene_postprocess.bloom_intensity

preserve_scope:
  dimensions:
    - asset_palette
    - asset_silhouette
  artifacts:
    - normalized/AST-001/runtime/AST-001.png
    - qc/AST-001/qc-report.yaml
  upstream_truth:
    - game_spec
    - art_style
    - asset_spec
    - generation_candidate
    - normalization
    - qc_approval

invalidation_scope: SCENE_LOCAL
revalidation_scope:
  - affected_runtime_contexts
```

If root ownership is upstream, preserve only artifacts that remain valid descendants of unchanged inputs.

## Version-sensitive invalidation

Runtime approval is tied to the integrated lineage.

- New generation candidate → previous normalization/QC/runtime descendants are invalid unless effective input identity is proven unchanged.
- New normalized output → previous QC/runtime descendants are invalid.
- New QC decision on same normalized output → runtime approval may require revalidation according to changed findings/policy.
- Runtime-integration-only change → upstream generation/normalization/QC may remain valid; invalidate affected runtime contexts only.

Do not preserve descendant approval across changed upstream identity merely because the visual difference seems small.

## Coverage policy

Prioritize P0 assets, decision-changing states, difficult backgrounds/post-processing, minimum viewport/most constrained camera, canonical + representative derivatives, and known regression contexts. Expand only when representative failures suggest systemic risk.

Use `references/scene-context-validation-policy.md`.

## Accessibility in context

`game-asset-qc` verifies contrast against *declared* backgrounds. This stage verifies `A11Y_RUNTIME_CONTRAST` against the background the scene actually renders, which is the one that counts.

An asset can pass isolated contrast checks and still fail here — scene post-processing, an overlay, or a busier background than the spec anticipated will do it. That failure is usually `INTEGRATION_LOCAL` or `INTEGRATION_SYSTEMIC`, not an asset defect. Route it as `CONTEXT_SENSITIVE_ASSET_FAILURE` only when ordinary integration cannot fix it without violating a locked requirement.

## Status

- `runtime_approved`
- `runtime_approved_with_minor_findings`
- `runtime_rework_required`
- `runtime_blocked`
- `partial_validation_only`

Only the first two may promote to `RUNTIME_APPROVED`. `partial_validation_only` is evidence, never approval.

Three conditions force a non-promoting status, and `validate_project.py` enforces all three:

- `build.executable` is false — supplied captures never produce runtime approval,
- any `untested` context is marked `risk: high`,
- any `BLOCKER` or `MAJOR` finding lacks `capture_ids`.

The last one is not bookkeeping. A visual claim without rendered evidence cannot be reproduced by the person who has to fix it, which makes it an opinion rather than a finding.

## Outputs

Logical outputs:

```text
runtime-validation/<asset-id>/runtime-validation-plan.yaml
runtime-validation/<asset-id>/runtime-report.yaml
runtime-validation/<asset-id>/evidence-manifest.yaml
runtime-validation/<asset-id>/captures/*
runtime-validation/<asset-id>/regression-summary.yaml
runtime-validation/scenes/<scene-id>/scene-report.yaml
runtime-validation/<family-id>/family-runtime-summary.yaml
```

Resolve actual paths through `project.yaml` when present.

## Completion criteria

Runtime validation is complete only when required contexts are executed or explicitly unavailable, findings have reproducible evidence, root ownership is explicit, blocker/major findings are resolved for approval, untested risk is explicit, lineage matches the integrated asset/QC versions, and any rework routing uses the canonical handoff contract.
