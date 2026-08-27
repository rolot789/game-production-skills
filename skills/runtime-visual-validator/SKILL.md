---
name: runtime-visual-validator
description: Validate QC-approved game assets inside actual playable contexts. Use reproducible runtime evidence to verify scene-level readability, hierarchy, state differentiation, placement, occlusion, compositing, animation continuity, and semantic visual regressions; distinguish integration failures from upstream asset failures and route rework to the smallest correct owner.
---

# Runtime Visual Validator

## Purpose

Determine whether a QC-approved asset actually works in the game context where the player sees and uses it.

Asset QC and runtime validation have different responsibilities:

```text
Game Asset QC
  "Is this asset valid against its production contract?"

Runtime Visual Validator
  "Does this valid asset still work when rendered in the actual game?"
```

A runtime failure may come from the asset, normalization, scene integration, camera, background, UI, lighting, post-processing, animation, or an upstream design contradiction. Do not assume the visible symptom owns the root cause.

The runtime validator does **not** redesign assets, silently revise ArtStyle, or approve a visual without runtime evidence.

## Core principles

1. **Validate in context, not in a vacuum.** Runtime approval requires evidence from the intended rendered context.
2. **Do not duplicate isolated QC.** Re-open isolated asset quality only when runtime evidence reveals a missed or context-sensitive problem.
3. **Use reproducible captures.** Record build, scene, viewport, camera, state, steps, asset version, and capture point.
4. **Visual evidence is mandatory for visual claims.** DOM/layout assertions and code inspection may support a finding but cannot replace rendered evidence for Canvas/WebGL or other visual output.
5. **Validate at actual player scale.** Zoomed source art is supplementary; intended display size is authoritative for readability.
6. **Compare semantics, not pixels.** Visual regression checks should protect hierarchy, state readability, placement, identity, and interaction feedback rather than require brittle pixel-perfect equality.
7. **Route to the root owner.** A z-order issue belongs to runtime integration; a pivot error may belong to normalization; a malformed asset may belong to generation.
8. **Preserve passing context dimensions.** Runtime rework should not destabilize scene properties that already pass.
9. **Do not over-invalidate.** A local scene failure should not invalidate unrelated scenes or asset-family members.
10. **No executable runtime means no full runtime approval.** Supplied screenshots can support partial validation only.

## Inputs

Use the strongest available production truth. Typical inputs are:

```text
playable build or executable preview
runtime validation plan
QC-approved runtime asset
qc/<asset-id>/qc-report.yaml
specs/<asset-id>.yaml
normalization record
art-style.yaml
style-anchor-manifest.yaml
style-constraint-ledger.yaml when relevant
family/state context when applicable
scene/camera/viewport configuration
approved baseline captures or prior runtime report when regression testing
```

Do not require every upstream artifact for every validation run. Require only the artifacts needed to explain the expected runtime behavior and route failures correctly.

## Preflight

Before declaring a run eligible for full validation:

1. Confirm the target build or preview is executable.
2. Confirm the target asset/version is actually present in the build.
3. Confirm required QC status is acceptable under project policy.
4. Define the scenes, states, viewport(s), camera, and capture points.
5. Define expected player-visible behavior for each capture point.
6. Identify baseline evidence when the task includes regression validation.
7. Record known limitations such as unavailable platforms, inaccessible states, or nondeterministic effects.

If the runtime cannot be executed but trustworthy captures are supplied, continue only with the evidence that exists and return `partial_validation_only`.

## Runtime validation plan

Create or consume a deterministic `runtime-validation-plan.yaml` before broad capture.

The plan should identify:

```yaml
build:
  id: <build-or-commit-id>
  launch_target: <url-command-or-preview>

contexts:
  - id: CTX-001
    scene: <scene-id>
    viewport: <width>x<height>
    camera: <camera/state>
    target_assets:
      - <asset-id>
    game_state: <state>
    entry_steps:
      - <deterministic step>
    capture_points:
      - id: CAP-001
        expected:
          - <player-visible expectation>
```

Do not produce a large capture set before deciding which contexts are actually decision-relevant.

## Validation levels

Use the minimum level sufficient for the asset risk and shipping stage.

### Level 1 — Asset in scene

Validate one asset in its intended context:

- actual rendered size,
- placement,
- contrast against background,
- clipping,
- compositing,
- basic hierarchy,
- local overlap.

Useful for early integration and low-risk decorative assets.

### Level 2 — Family / state context

Validate related states, directions, variants, or animation states together:

- state differentiation,
- family identity continuity,
- transition continuity,
- anchor stability,
- direction consistency,
- active/inactive/locked/readability relationships.

Gameplay-critical stateful assets should normally reach at least this level.

### Level 3 — Full scene hierarchy

Validate the asset inside a representative complete scene:

- focal hierarchy,
- foreground/background competition,
- player/enemy/object readability,
- UI/world separation,
- overlap and occlusion,
- scene lighting/post-processing effects,
- simultaneous gameplay-state readability.

### Level 4 — Flow / regression context

Validate transitions across meaningful gameplay or UI flow and compare with approved baselines when available:

- scene transitions,
- animation/state transitions,
- camera changes,
- responsive viewport changes,
- visual feedback timing,
- semantic visual regressions.

Do not require Level 4 universally. Use it for high-risk flows, animation-heavy families, cross-scene assets, or regression-sensitive releases.

## Runtime validation dimensions

Evaluate only dimensions that are meaningful in the current context.

### 1. Actual-scale readability

Check whether the asset remains legible and identifiable at intended runtime size and camera distance.

Examples of failures:

- silhouette collapses at gameplay scale,
- important internal marks disappear,
- line weight becomes visually dominant,
- state marker is only visible when zoomed.

### 2. Scene hierarchy

Check whether the asset receives the intended amount of visual attention relative to other elements.

Possible problems:

- decorative element dominates a gameplay target,
- UI panel competes with critical world state,
- active state is weaker than inactive state,
- background contrast obscures the player.

A hierarchy failure may belong to runtime integration or ArtStyle depending on whether the problem is scene implementation or the locked hierarchy rules themselves.

### 3. State differentiation

Validate states under actual scene conditions, not on transparent backgrounds only.

Check:

- active vs inactive,
- enabled vs disabled,
- current vs completed vs locked,
- open vs closed,
- selected vs unselected,
- damaged vs normal,
- interaction feedback states.

The player must be able to distinguish states through the intended visual channel at runtime scale.

### 4. Placement and alignment

Check:

- screen/world position,
- baseline alignment,
- anchor behavior,
- tile/grid registration,
- camera-relative alignment,
- UI safe areas,
- responsive positioning.

### 5. Occlusion and overlap

Check whether nearby world objects, UI, particles, labels, masks, or camera framing hide critical visual information.

Differentiate intentional occlusion from accidental readability loss.

### 6. Compositing and render behavior

Check:

- z-order,
- blend mode,
- opacity,
- alpha edges,
- masks,
- clipping containers,
- shader effects,
- color modulation,
- post-processing interaction,
- lighting interaction where applicable.

### 7. Animation and transition continuity

Check rendered continuity rather than single-frame quality only.

Look for:

- anchor jitter,
- scale popping,
- unintended silhouette changes,
- frame-to-frame identity drift,
- state transition ambiguity,
- feedback that appears too late or too briefly to read.

### 8. UI / world collisions

Check whether UI and world-space elements compete or overlap in unintended ways across target viewports.

### 9. Contextual style integrity

Use this only for context-sensitive style failures.

Examples:

- approved texture becomes too noisy after scene post-processing,
- palette relationship loses hierarchy under scene lighting,
- approved glow becomes excessive when multiple instances overlap.

Do not re-score isolated art style from scratch.

### 10. Semantic visual regression

When a baseline exists, ask whether player-relevant visual meaning changed unexpectedly.

Protect things such as:

- which object reads as interactive,
- which state reads as active,
- target visibility,
- ordering/hierarchy,
- placement,
- family identity,
- transition clarity.

Avoid using raw pixel difference alone as the regression decision.

## Runtime evidence

For any `BLOCKER` or `MAJOR` visual finding, capture sufficient evidence to let another agent reproduce the observation.

Evidence should include when available:

```text
build / commit identifier
scene / route / level
viewport and device class
camera state
game state
asset ID + runtime asset version
capture ID
screenshot or frame sequence
baseline capture ID when comparing regressions
reproduction steps
```

For Canvas/WebGL, a screenshot or rendered frame is required for visual findings. DOM assertions alone are not enough.

For animation/transition findings, use a frame sequence, video-equivalent evidence, or multiple deterministic captures where the runtime/tooling supports it.

Read `references/runtime-evidence-policy.md` for detailed evidence rules.

## Finding model

A runtime finding must separate symptom from root cause.

Preferred structure:

```yaml
id: RTV-001
severity: MAJOR
context_id: CTX-003
capture_ids:
  - CAP-008

dimension: state_differentiation

expected:
  current stage remains clearly stronger than available stages at gameplay scale

observed:
  bloom and background star density reduce the value difference until current and available states read equivalently

root_owner: runtime_integration
root_reason:
  the approved assets pass isolated QC; scene bloom and compositing erase their designed contrast hierarchy

affected_scope:
  scenes:
    - chapter-stage-select
  assets:
    - stage-star-current
    - stage-star-available

required_action:
  reduce or scope scene bloom so the approved state hierarchy remains visible

preserve:
  - asset palette
  - asset silhouettes
  - state geometry
```

Do not write findings such as `looks bad in the game` without expected behavior, observed evidence, and routing.

## Root-cause routing

Use the smallest correct owner.

### `runtime_integration`

Use when the asset contract is valid but the scene implementation breaks it:

- z-order,
- layout,
- transforms,
- camera,
- viewport handling,
- scene lighting,
- blend/opacity,
- shaders,
- masks,
- post-processing,
- animation wiring,
- UI/world composition.

### `game-asset-normalizer`

Use when runtime evidence reveals a mechanical asset-preparation defect:

- wrong pivot,
- bad trim/padding,
- clipping from normalized bounds,
- canvas inconsistency,
- incorrect anchor metadata.

### `game-asset-generator`

Use when the actual visual content is malformed and the failure survives independently of the runtime integration:

- identity drift,
- wrong state depiction,
- malformed silhouette,
- generated visual artifact.

If QC should reasonably have caught the same isolated defect, also mark it as a QC escape.

### `game-asset-qc`

Use for a missed isolated-contract defect or insufficient QC coverage, not as the visual-content rework owner.

### `game-asset-planner`

Use when runtime integration exposes the wrong decomposition, missing state, wrong orientation family, or asset/runtime responsibility split.

### `art-style-builder`

Use when the locked art system itself creates a contextual contradiction that cannot be solved by ordinary scene implementation without violating approved style truth.

### `game-spec-builder`

Use when the expected gameplay/UI meaning is undefined or contradictory.

Read `references/runtime-regression-routing-policy.md` for escalation and invalidation rules.

## Rework preservation

Runtime rework instructions should declare what may change and what must remain stable.

Example:

```yaml
change:
  - scene_postprocess.bloom_intensity

preserve:
  - asset files
  - approved palette
  - asset scale
  - camera framing
  - UI layout
```

If the issue is local to one scene or viewport, do not reopen unrelated assets, scenes, or style dimensions.

## Scene and family coverage

Do not validate every asset in every possible scene by default. Use risk-based representative coverage.

Prioritize:

1. P0 gameplay-critical assets,
2. states that change player decisions,
3. high-contrast or post-processing-heavy scenes,
4. smallest supported viewport / most constrained camera,
5. family canonical state plus representative derivatives,
6. known regression-prone contexts.

If a representative failure suggests a systemic issue, expand coverage deliberately.

Read `references/scene-context-validation-policy.md` for coverage selection.

## Status

Allowed statuses:

- `runtime_approved`
- `runtime_approved_with_minor_findings`
- `runtime_rework_required`
- `runtime_blocked`
- `partial_validation_only`

### `runtime_approved`

All required validation contexts pass and no unresolved BLOCKER/MAJOR finding remains.

### `runtime_approved_with_minor_findings`

Required contexts pass and only project-acceptable MINOR/NOTE findings remain.

### `runtime_rework_required`

At least one required context has a resolvable visual/integration failure.

### `runtime_blocked`

Validation cannot proceed because a required runtime, state, build, dependency, or expectation is unavailable or contradictory.

### `partial_validation_only`

Some evidence was reviewed, but full executable runtime coverage was unavailable. This status does not promote an asset to `RUNTIME_APPROVED`.

## Shipping gate

Only project-allowed runtime-approved statuses can promote:

```text
QC_APPROVED
→ RUNTIME_APPROVED
→ SHIPPABLE
```

A partial capture review cannot substitute for runtime approval of a production-critical asset.

## Outputs

Typical outputs:

```text
runtime-validation/<asset-id>/
├── runtime-validation-plan.yaml
├── runtime-report.yaml
├── evidence-manifest.yaml
├── captures/
└── regression-summary.yaml        # when baseline comparison is used
```

For broader scene/family validation, optionally emit:

```text
runtime-validation/scenes/<scene-id>/scene-report.yaml
runtime-validation/<family-id>/family-runtime-summary.yaml
```

The report should include validation level, tested contexts, untested required contexts, evidence references, findings, root owners, preserve/change scopes, and final status.

## Completion criteria

Runtime validation is complete only when:

1. all required contexts in the validation plan were executed or explicitly marked unavailable,
2. required visual findings have reproducible evidence,
3. root ownership is assigned without conflating symptom and cause,
4. no unresolved BLOCKER/MAJOR remains for an approved status,
5. untested context risk is explicit,
6. the result can be consumed by the orchestrator without guessing whether the asset may advance to `RUNTIME_APPROVED`.
