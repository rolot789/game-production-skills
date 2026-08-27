---
name: game-asset-planner
description: Use when a locked game spec and art style must become a concrete asset list — "what assets do I need", "break this down into sprites", "how many states does the gate need" — or before any generation begins. Discovers semantic entities, decomposes them into minimum reusable units, expands state and direction variants, picks representation strategies compatible with locked style truth, and emits asset-manifest.yaml plus per-asset specs. Does not generate images (use game-asset-generator) or change art direction (use art-style-builder).
---

# Game Asset Planner

## Purpose

Compile immutable `GameSpec + ArtStyle + approved scoped anchors + applicable style constraints` into the complete set of visual production requirements. Do not generate images.

```text
Locked GameSpec
+ Locked ArtStyle
+ Scoped Style Anchors
+ Applicable Style Constraints
        ↓
Semantic Visual Inventory
        ↓
MRAU Decomposition
        ↓
State / Direction / Variant Expansion
        ↓
Representation Strategy
        ↓
Runtime / Family / Lineage Contracts
        ↓
asset-manifest.yaml + specs/<asset-id>.yaml
```

## Project path resolution

If `project.yaml` exists, treat its `paths` registry as the canonical mapping from logical artifact names to project paths. Paths shown in this skill such as `asset-manifest.yaml` or `specs/<asset-id>.yaml` are logical artifact patterns, not permission to ignore the project registry.

When no project registry exists, use the current repository/toolkit convention consistently and record the resolved output paths in the handoff.

## Principles

- Plan from runtime semantics, not screenshot crops.
- A Minimum Reusable Asset Unit (MRAU) is something that must be independently placed, swapped, animated, hidden, reused, or state-controlled.
- Convert game rules into visible states. Example: gate blocking/opening semantics may require closed/open/transition states and orientation variants.
- Expand only meaningful variant combinations; avoid blind Cartesian products.
- Choose representation deliberately: `generated_raster`, `generated_vector`, `generated_3d`, `procedural`, `runtime_primitive`, `runtime_text`, `shader_or_particle`, or `reuse_existing`.
- Representation strategy must remain compatible with locked visual truth. Do not select a runtime primitive when the required scoped style constraints depend on authored texture, irregular contour behavior, or another feature the primitive cannot reproduce.
- Do not turn runtime text, simple lines, or suitable procedural effects into PNGs without reason.
- Every asset must retain source traceability to GameSpec/ArtStyle paths, versions/hashes when available, approved anchor IDs, applicable constraint IDs, and planning rationale.
- Define family/shared geometry/shared anchor groups for state/direction variants.
- Record canonical parent and derivative topology for families that should not be generated independently.
- Record runtime dimensions/footprint, background policy, visual anchor, runtime pivot, collision-origin expectations when relevant, animation semantics, priority, and QC requirements.
- Encode every gameplay-critical state in at least one non-hue channel. Colour-only state encoding is a planning defect, not a generation defect.
- If required semantics are unresolved or contradictory, block rather than invent.

## Reference policies

- `references/mrau-decomposition-policy.md` — how to find the seam between one asset and two, and the failure modes on each side of it.
- `references/representation-strategy-policy.md` — choosing between generated raster, procedural, runtime primitive, shader, and reuse, and what each choice costs downstream.
- `references/routing.yaml` — the canonical failure routing table.
- `references/rework-handoff-contract.yaml` — the canonical rework envelope.

## Required inputs

At minimum:

```text
game-spec.yaml
art-style.yaml
style-anchor-manifest.yaml
```

When present and applicable, also consume:

```text
style-constraint-ledger.yaml
style-loop-state.yaml
project.yaml
```

The planner does not need the entire reference corpus to choose asset decomposition. It should rely on approved production authority in ArtStyle, scoped anchors, and the constraint ledger. Use reference metadata only when an AssetSpec must preserve a named approved identity/geometry source.

## Style-aware representation strategy

Before selecting representation, determine which style dimensions materially depend on authored media.

Examples:

```text
runtime_text
→ suitable when typography is explicitly runtime-rendered and no authored lettering texture is required

runtime_primitive
→ suitable for simple geometric UI separators only when locked style rules permit mechanical geometry

generated_raster
→ appropriate when handmade contour irregularity / tactile texture / painterly fill is production-critical

shader_or_particle
→ appropriate when behavior is procedural and the locked style is expressed through shader/particle parameters rather than a static sprite
```

If the chosen strategy cannot satisfy a locked `HARD_FORBIDDEN`, `BOUNDED`, anchor, or category rule, the plan is invalid and must be revised before generation.

## AssetSpec contract

Each `specs/<asset-id>.yaml` must validate against `references/schemas/asset-spec.schema.json`. That schema is the authority; the shape below is the readable version of it.

```yaml
schema_version: 3
asset_id: AST-GATE-CLOSED
family_id: FAM-GATE
category: interactive_object
purpose: blocks the corridor until the player solves the adjacent switch
priority: P0

# Required. Dependency-aware invalidation cannot run without these.
source_versions:
  game_spec:
    path: spec/game-spec.yaml
    version: v7
    content_hash: <sha256 of that exact file>
  art_style:
    path: art/art-style.yaml
    version: v5
    content_hash: <sha256>

style_authority:
  anchor_ids: [REF-017]
  constraint_ids: [NEG-LINE-001]
  category_overrides: [interactive_object.contour_weight]

state:
  id: closed
  gameplay_meaning: traversal blocked
  encoding_channels: [shape, value]      # a gameplay-critical state needs a non-hue channel

orientation:
  id: null

family:
  canonical_parent: null                  # this asset is the parent
  derivation_role: canonical_parent
  must_preserve: [outer_frame_geometry, top_view_projection, palette_family]
  must_change: []
  may_vary: []
  must_not_introduce: [new_ornament]

production:
  strategy: generated_raster
  derivation_mode: independent
  strategy_rationale: locked style requires authored contour irregularity a primitive cannot reproduce

normalization:
  canvas_policy: fixed
  scale_policy: fit_content
  anchor_policy: content_center
  pivot_policy: bottom_center
  target_canvas: { width: 256, height: 256 }
  padding: 8
  trim: true
  resample: lanczos

runtime:
  footprint: 1x1 tile
  intended_display_size: { width: 64, height: 64 }
  background_policy: transparent
  readability_requirements: [silhouette readable at 64 px]
  state_readability_requirements: [closed vs open distinguishable at 64 px]
  backgrounds_encountered: ["#1B1F24", "#3A4149"]

accessibility:
  gameplay_critical: true
  required_checks: [A11Y_CONTRAST, A11Y_COLOR_VISION, A11Y_NON_COLOR_CHANNEL]

qc_requirements: [family_state_comparison_at_display_size]

dependencies:
  upstream: [spec/game-spec.yaml, art/art-style.yaml]
  downstream_hints: [AST-GATE-OPEN, AST-GATE-TRANSITION]
```

### Fields the normalizer and QC cannot work without

Three of these are load-bearing in a way that is easy to miss:

- `normalization.target_canvas` — the normalizer refuses to invent a canvas. Omitting it produces a blocker routed straight back here.
- `runtime.intended_display_size` — readability is judged at this size, not at source resolution. A detail that is clean at 256 px can destroy state distinction at 64 px.
- `state.encoding_channels` — for any gameplay-critical state, at least one channel must be something other than `hue`. Colour-only state encoding fails for roughly one in twelve players, and it is the planner's decision to prevent, not the generator's to rescue.

### Version and hash fields are required, not optional

`source_versions` entries need `path`, `version`, and `content_hash`. Compute the hash from the exact bytes of the file being referenced:

```bash
sha256sum spec/game-spec.yaml
```

If a required version or hash cannot be produced, emit a blocker and stop. `unknown` is not an acceptable lineage value: every invalidation decision downstream depends on being able to prove whether an input changed, and a record that cannot support that decision is worse than no record because it looks authoritative.

## Family topology

For related assets, plan a canonical parent whenever identity or geometry should remain stable across variants.

Examples:

```text
closed gate
→ transition
→ open gate

character neutral
→ directions
→ actions

base UI icon
→ active / disabled / selected
```

A derivative spec should explicitly say what may change and what remains invariant. This makes downstream `change_scope / preserve_scope` rework deterministic.

## Change/preserve compatibility

The planner normally creates authoritative specs rather than executing rework. When a planner-owned defect is routed back from QC/runtime, the handoff carries the canonical fields defined in `references/rework-handoff-contract.yaml`:

```yaml
change_scope:
  dimensions: []
  artifacts: []
  runtime_properties: []

preserve_scope:
  dimensions: []
  artifacts: []
  upstream_truth: []
```

Revise only the planner-owned surface identified in `change_scope`. Do not reopen preserved GameSpec/ArtStyle truth unless the handoff explicitly routes ownership upstream.

## Outputs

Logical outputs:

```text
asset-manifest.yaml
specs/<asset-id>.yaml
```

Resolve their actual locations through `project.yaml` when present.

The manifest should index assets/families, resolved spec paths, priority/tier, production strategy, lifecycle readiness, canonical-parent relations, and source-version lineage.

## Completion criteria

Asset planning is complete for a requested scope only when:

- required semantic visual entities are represented,
- MRAU decomposition matches runtime responsibility,
- meaningful state/direction families are complete,
- representation strategies can satisfy locked style/constraint truth,
- canonical family topology is explicit where required,
- normalization/runtime/QC requirements are defined enough for downstream execution,
- source versions and style authorities are traceable,
- downstream generation can proceed without inventing semantics, representation, or family relationships.
