# Orchestration State Policy

## Purpose

Define the minimum state needed for deterministic routing across the game art production pipeline. State exists to answer five questions without reconstructing history from chat:

1. What is authoritative now?
2. What stage/lifecycle is each subject in?
3. What failed and who owns the root cause?
4. What must change and what must be preserved?
5. What is the next legal specialist action?

## Canonical state file

Maintain:

```text
.pipeline/game-art-production-state.yaml
```

The state file is not a duplicate of all production artifacts. It is an index over authoritative versions, readiness, dependencies, and routing.

Recommended top-level structure:

```yaml
version: 2
project:
  id: game-project
  pipeline_status: IN_PROGRESS

authoritative:
  game_spec:
    path: spec/game-spec.yaml
    version: v7
    gate: ASSET_PLANNING_READY
  art_style:
    path: art/art-style.yaml
    version: v5
    gate: ASSET_GENERATION_READY
  style_anchor_manifest:
    path: art/style-anchor-manifest.yaml
    version: v4
  style_constraint_ledger:
    path: art/style-constraint-ledger.yaml
    version: v3

stages:
  game_spec: COMPLETE
  art_style: COMPLETE
  asset_planning: COMPLETE
  generation: IN_PROGRESS
  normalization: IN_PROGRESS
  asset_qc: IN_PROGRESS
  runtime_validation: IN_PROGRESS

subjects: {}
active_rework: []
open_blockers: []
```

## Subject state

A subject may be an asset, family, scene, or cross-cutting style branch.

Example asset state:

```yaml
subjects:
  AST-PLAYER-IDLE:
    type: asset
    family_id: FAM-PLAYER
    priority: P0
    lifecycle: RUNTIME_REWORK
    active_versions:
      spec: v3
      generation_contract: v6
      generated_candidate: v6-c2
      normalization: v6-n1
      qc: v6-q1
      runtime: v6-r2
    root_owner: runtime_integration
    change_scope:
      - z_order
    preserve_scope:
      - generated_visual
      - normalization
      - qc_approval
    next_skill: runtime-visual-validator
    next_action: revalidate affected scene after integration fix
```

## Authority rules

- The state file points to authority; it does not create authority.
- Locked upstream artifacts remain authoritative until explicitly revised.
- A newer artifact is not automatically authoritative if it has not passed the required gate.
- Search-discovered reference evidence is not production authority unless represented by an approved scoped anchor.
- Superseded versions remain in history/provenance but should not be selected for downstream handoffs.

## Rework entries

Track active rework as a scoped transaction:

```yaml
active_rework:
  - id: RWK-0042
    subject: AST-PLAYER-IDLE
    observed_at: runtime_validation
    root_owner: game-asset-normalizer
    reason_codes:
      - PIVOT_MISALIGNMENT
    change_scope:
      - runtime_pivot
    preserve_scope:
      - generated_visual
      - style_contract
      - asset_spec
    invalidates:
      - normalization
      - asset_qc
      - runtime_validation
    preserves:
      - generation
    status: OPEN
```

Close a rework entry only when the required descendant revalidation is complete.

## Version-sensitive promotion

Promotion applies to exact active versions.

Example:

```text
candidate v5-c1
→ normalized v5-n1
→ QC approved v5-q1
→ runtime approved v5-r1
```

If candidate v6 becomes active, v5-r1 remains historical evidence but must not be treated as runtime approval for v6.

## Partial validation

`partial_validation_only` may be recorded as evidence status but never as lifecycle promotion.

```yaml
runtime_evidence:
  status: partial_validation_only
lifecycle: QC_APPROVED
```

Do not set `RUNTIME_APPROVED` until executable runtime coverage passes.

## Family state

Track canonical parent authority separately from derivatives.

```yaml
families:
  FAM-NPC-01:
    canonical_asset: NPC-01-IDLE
    canonical_status: QC_APPROVED
    systemic_blocker: null
    derivatives:
      NPC-01-NORTH: QC_APPROVED
      NPC-01-SOUTH: GENERATION_REWORK
      NPC-01-EAST: QC_APPROVED
```

A local derivative failure must not demote passing siblings unless the finding is systemic.

## State mutation discipline

Whenever state changes, record:

- triggering evidence/artifact,
- previous state,
- new state,
- root owner when failure-related,
- change scope,
- preserve scope,
- invalidated descendants,
- next legal action.

Do not overwrite the reason for an invalidation with the later symptom produced by that invalidation.
