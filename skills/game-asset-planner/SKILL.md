---
name: game-asset-planner
description: Compile locked game specification and art style into a production-ready asset manifest. Discover semantic visual entities, decompose them into minimum reusable asset units, expand required state/direction variants, choose representation strategies that remain compatible with locked style constraints, and emit traceable per-asset production specs with version lineage.
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
- If required semantics are unresolved or contradictory, block rather than invent.

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

## AssetSpec v2 contract

Each `specs/<asset-id>.yaml` should provide enough deterministic truth for generation, normalization, QC, runtime validation, and dependency-aware invalidation.

Recommended structure includes:

```yaml
asset_id: AST-001
family_id: FAM-001
category: interactive_object
purpose: <runtime semantic purpose>

source_versions:
  game_spec:
    version: <when available>
    hash: <when available>
  art_style:
    version: <when available>
    hash: <when available>

style_authority:
  anchor_ids: []
  constraint_ids: []
  category_overrides: []

state:
  id: <state-or-null>
orientation:
  id: <orientation-or-null>

family:
  canonical_parent: <asset-id-or-null>
  derivation_role: canonical_parent | derivative | independent
  shared_geometry_group: <id-or-null>
  shared_anchor_group: <id-or-null>

production:
  strategy: generated_raster
  derivation_mode: independent | parent_derived | reference_edit | procedural

normalization:
  canvas_policy: <policy-id-or-inline-contract>
  scale_policy: <policy-id-or-inline-contract>
  anchor_policy: <policy-id-or-inline-contract>
  pivot_policy: <policy-id-or-inline-contract>

runtime:
  footprint: <runtime size/grid footprint>
  background_policy: transparent | opaque | runtime_composited
  readability_requirements: []
  state_readability_requirements: []

qc_requirements: []

dependencies:
  upstream: []
  downstream_hints: []
```

Do not fabricate version/hash fields if they are unavailable; record `unknown` or omit according to project schema.

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

The planner normally creates authoritative specs rather than executing rework. When a planner-owned defect is routed back from QC/runtime, the handoff may contain canonical fields:

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
