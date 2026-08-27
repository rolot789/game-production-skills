# Scene Context Validation Policy

## Purpose

Runtime validation should cover the contexts that can materially change player-visible meaning without exploding into an exhaustive Cartesian product of every asset, scene, viewport, state, and camera.

This policy defines risk-based context selection.

## Context model

A runtime validation context is the combination of conditions that can change how an asset is perceived or used.

Typical context dimensions:

```text
scene / route / level
viewport / device class
camera / zoom / framing
gameplay or UI state
background value/color density
lighting / post-processing
neighboring assets
UI overlays
animation / transition phase
input / interaction state
```

Do not include dimensions that cannot change the visual outcome for the target asset.

## Risk-first selection

Prioritize contexts using four signals:

1. **Gameplay criticality** — would a visual failure cause a wrong player decision?
2. **Context sensitivity** — how much can background/camera/UI/post-processing alter the asset?
3. **Variation surface** — how many meaningful states/viewports/scenes exist?
4. **Regression history** — has this context broken before or changed recently?

A high-risk context should receive broader coverage than decorative or low-interaction content.

## Recommended coverage tiers

### Tier P0 — Gameplay critical

Examples:

- player,
- goal/exit,
- hazards,
- interactable state indicators,
- puzzle state blocks,
- current/locked/available progression state.

Validate at least:

- intended runtime scale,
- representative full scene,
- all decision-critical states,
- worst-case or constrained viewport/camera when applicable.

### Tier P1 — Important interaction / navigation

Examples:

- chapter selection,
- main UI controls,
- inventory/action states,
- tutorial prompts.

Validate representative normal + stressed contexts.

### Tier P2 — Secondary / decorative

Examples:

- noninteractive decoration,
- low-priority environmental props,
- polish-only FX.

A representative context may be sufficient unless the asset affects hierarchy or performance-sensitive compositing.

## Context matrix

For a target family, build a compact matrix rather than brute-force combinations.

Example:

```yaml
contexts:
  - id: CTX-DESKTOP-NORMAL
    viewport: 1920x1080
    scene_density: normal
    states: [current, available, locked]

  - id: CTX-DESKTOP-HIGH-DENSITY
    viewport: 1920x1080
    scene_density: high
    states: [current, available]

  - id: CTX-MIN-VIEWPORT
    viewport: 1280x720
    scene_density: normal
    states: [current, locked]
```

Choose combinations because they test a specific risk.

## Worst-case contexts

When multiple contexts exist, explicitly include contexts likely to suppress readability:

- smallest supported viewport,
- greatest camera distance,
- busiest background,
- strongest allowed post-processing,
- highest overlapping-instance count,
- lowest intended value/color contrast,
- most crowded UI state.

Do not rely only on showcase scenes.

## State-family coverage

For stateful families:

1. validate the canonical/default state,
2. validate every player-decision-critical state,
3. sample low-risk cosmetic variants,
4. expand to all variants only when a systemic defect is suspected.

Examples where all states often matter:

- locked / available / current / completed,
- open / closed when traversability depends on the distinction,
- dangerous / safe,
- selected / unselected when input focus depends on it.

Examples where sampling may be enough:

- cosmetic recolors,
- purely decorative direction variants with identical readability role.

## Responsive / viewport coverage

Do not assume desktop validation proves smaller viewports.

At minimum, test:

- the primary supported viewport,
- the minimum supported viewport when layout can compress,
- any materially different aspect-ratio class.

If the project explicitly targets only one fixed viewport, do not invent responsive coverage requirements.

## Camera coverage

Camera can change scale and overlap dramatically.

Test camera states that materially affect:

- projected asset size,
- occlusion,
- screen-edge clipping,
- perspective/angle,
- hierarchy.

Do not capture arbitrary camera positions with no production relevance.

## Repeated-instance coverage

Some effects are safe for one asset but fail with many instances.

Use density/stress contexts for:

- glow/bloom,
- particles,
- transparent overlays,
- outlines,
- repeated icons,
- dense stage nodes,
- stacked UI badges.

Check whether aggregate effects destroy hierarchy or create visual noise.

## Background / lighting coverage

If assets can appear across different background or lighting classes, sample classes that materially alter contrast.

Example classification:

```text
BG-LIGHT
BG-MID
BG-DARK
BG-HIGH-DETAIL
```

Do not test every level if they share the same relevant visual conditions.

## Flow coverage

Use Level 4 flow validation when state meaning depends on transition timing or previous/next context.

Examples:

- button hover/pressed/disabled,
- gate opening,
- stage clear transition,
- tutorial reveal,
- selected node changing to completed,
- scene transition that changes camera/layout.

Validate the transition, not just the endpoints, when the transition communicates gameplay meaning.

## Regression-sensitive coverage

Prefer re-running contexts when:

- asset version changed,
- normalization metadata changed,
- scene layout changed,
- camera changed,
- post-processing changed,
- shared UI container changed,
- a systemic style/category rule changed.

Do not re-run unrelated contexts solely because another asset changed.

## Coverage expansion rule

Start with representative contexts.

Expand coverage when:

- a systemic failure is found,
- one failure may affect siblings,
- the cause depends on an untested context dimension,
- a high-risk requirement remains uncertain.

Example:

```text
Representative locked-state failure
→ determine whether cause is state asset or scene treatment
→ if scene treatment is shared, test current/available/completed
→ if shared failure confirmed, invalidate affected scene family only
```

## Coverage stopping rule

Stop expanding when:

- required high-risk contexts have passed,
- sampled lower-risk contexts provide enough evidence for the family rule,
- no unresolved systemic failure remains,
- further combinations would not test a new hypothesis.

The goal is confidence, not exhaustive screenshot count.

## Untested-context disclosure

Every runtime report should state material untested contexts.

Example:

```yaml
untested:
  - context: ultrawide viewport
    reason: runtime environment unavailable
    risk: low

  - context: mobile portrait
    reason: required target but unavailable
    risk: high
```

A required high-risk untested context may force `partial_validation_only` or `runtime_blocked` depending on project policy.
