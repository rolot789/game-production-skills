---
name: game-art-production-orchestrator
description: Orchestrate the AI-native game art production pipeline from locked game specification and art style through asset planning, grounded generation, normalization, contract-aware QC, and scene-context runtime validation. Enforce readiness gates, scoped reference authority, canonical delta-rework handoffs, dependency-aware invalidation, provenance, and coherent version lineage.
---

# Game Art Production Orchestrator

## Purpose

Coordinate routing, gates, handoffs, lifecycle state, rework scope, invalidation, and promotion without duplicating specialist work.

```text
game-spec-builder
→ art-style-builder
→ game-asset-planner
→ game-asset-generator
→ game-asset-normalizer
→ game-asset-qc
→ runtime-visual-validator
```

The orchestrator does not redesign art, write provider prompts, normalize pixels, perform QC, or visually approve scenes. It determines which specialist acts next, with which authoritative inputs, and what exact surface may change.

## Project path resolution

If `project.yaml` exists, its `paths` registry is the canonical artifact path map. Contract paths such as `specs/<asset-id>.yaml` are logical patterns. The orchestrator must resolve logical names through the registry before creating handoffs and must carry resolved paths in `authoritative_inputs` / `expected_outputs`.

## Core principles

1. Advance artifacts, not assumptions.
2. Preserve validated truth.
3. Search-derived references are evidence until explicitly approved as scoped anchors.
4. Rework uses canonical `change_scope / preserve_scope` from `contracts/rework-handoff-contract.yaml`.
5. Symptom location, root ownership, invalidation scope, and revalidation scope are separate decisions.
6. Invalidate the smallest descendant surface that can no longer be trusted.
7. `partial_validation_only` never promotes runtime readiness.
8. Provenance/history is append-only even when artifacts are superseded.
9. Descendant approvals cannot survive changed upstream identity unless effective input equivalence is proven.

## Source-of-truth hierarchy

1. LOCKED GameSpec
2. LOCKED ArtStyle
3. approved scoped Style Anchors
4. locked applicable Style Constraint Ledger
5. Asset Manifest / Asset Specs
6. Generation Contract + candidate/generation records
7. Normalization records / output hashes
8. QC reports / family summaries
9. Runtime reports / evidence / approved baselines

`reference-corpus.yaml` is evidence; `style-anchor-manifest.yaml` defines reference authority.

## Pipeline state

Maintain `.pipeline/game-art-production-state.yaml` as canonical orchestration state.

Stage states:

`NOT_STARTED`, `IN_PROGRESS`, `READY`, `BLOCKED`, `FAILED`, `INVALIDATED`, `COMPLETE`.

Asset lifecycle:

```text
PLANNED
→ READY_FOR_GENERATION
→ GENERATED
→ NORMALIZED
→ QC_APPROVED
→ RUNTIME_APPROVED
→ SHIPPABLE
```

Rework/failure states:

`GENERATION_REWORK`, `NORMALIZATION_BLOCKED`, `QC_REWORK`, `RUNTIME_REWORK`, `INVALIDATED`.

Track active version lineage for each asset/family:

```yaml
active_versions:
  asset_spec:
  generation_candidate:
  normalization_output:
  qc_report:
  runtime_report:
```

Use hashes/IDs when versions are not explicit.

## Canonical handoff envelope

Every external specialist transition follows `contracts/rework-handoff-contract.yaml` when rework is involved. Normal forward handoffs should use the same authority/version discipline.

```yaml
handoff_id: HND-0042
from: game-asset-qc
to: game-asset-generator
subject:
  type: asset
  id: AST-001
root_owner: game-asset-generator
reason_codes:
  - NEGATIVE_CONSTRAINT_VIOLATION

authoritative_inputs: []

change_scope:
  dimensions:
    - texture_density
  artifacts: []
  runtime_properties: []

preserve_scope:
  dimensions:
    - identity
    - silhouette
    - palette
  artifacts:
    - assets/specs/AST-001.yaml
  upstream_truth:
    - game_spec
    - art_style
    - approved_anchors

expected_outputs: []
invalidation_scope: LOCAL_ASSET
revalidation_scope:
  - normalization
  - asset_qc
  - affected_runtime_contexts
next_action: regenerate scoped dimension
```

Specialist-local aliases such as `change_dimensions`, `preserve_dimensions`, `change`, or `preserve` may appear inside specialist reports. Before routing, normalize them into canonical scope fields.

## Readiness / promotion

### GameSpec
Require the relevant readiness gate. Never promote inferred semantics as confirmed production truth.

### ArtStyle
Before mass generation require applicable locked rules, reference grounding, approved production-critical anchors, applicable negative constraints, and representative calibration approval.

### Generation
Require complete AssetSpec/style authority/family inputs. `generation-contract.yaml` is authoritative; `prompt.md` is serialized output.

### Normalization
Require exact candidate/spec lineage and mechanical policy. A normalization result applies only to the exact effective input it records.

### QC
Only normalized outputs with coherent generation/normalization lineage enter QC. `approved` / policy-allowed `approved_with_minor_findings` promote to `QC_APPROVED`.

### Runtime
Only executable rendered-context evidence may produce runtime approval. Partial/rework/blocked statuses never promote.

### SHIPPABLE
Require coherent current lineage from AssetSpec through integrated runtime approval.

## Failure routing

- undefined gameplay/state/screen meaning → `game-spec-builder`
- missing/contradictory style, scoped anchors, constraints → `art-style-builder`
- MRAU/family/state representation/runtime requirement → `game-asset-planner`
- malformed visual, identity/style/state drift, generation contract violation → `game-asset-generator`
- canvas/scale/trim/alpha/anchor/pivot/export processing → `game-asset-normalizer`
- missed/incorrect isolated contract classification/evidence → `game-asset-qc`
- runtime evidence planning/attribution → `runtime-visual-validator`
- z-order/layout/camera/shader/lighting/blend/mask/postprocess → runtime implementation owner

When ambiguous, request the smallest diagnostic step capable of separating root causes.

## Dependency-aware invalidation

Preserve unaffected locked truth by default. Invalidate descendants of changed authoritative input.

### Generator-local change

Correct behavior:

```text
new generation candidate
→ old normalization output/record becomes non-authoritative
→ old QC approval becomes non-authoritative
→ dependent runtime approval becomes non-authoritative
→ rerun normalization
→ rerun QC
→ rerun affected runtime contexts
```

Do **not** preserve an old normalization record for a changed candidate unless exact effective input equivalence is proven via hash/version and reuse is policy-permitted.

### Normalization-only change

```text
preserve generation candidate
→ invalidate normalization output/record
→ invalidate dependent QC/runtime
→ normalize → QC → affected runtime
```

### Runtime-integration-only change

```text
preserve generation / normalization / QC
→ change runtime integration
→ invalidate affected runtime contexts only
→ revalidate affected contexts
```

### Scoped ArtStyle change

```text
changed locked UI texture rule/anchor
→ invalidate only AssetSpecs/generation descendants governed by that changed authority
→ preserve unrelated categories/families
```

A reference merely added to `reference-corpus.yaml` causes no invalidation until production authority changes.

Record trigger artifact/version, root owner, changed truth, invalidated descendants, preserved siblings, and revalidation scope.

## Art-style loop orchestration

Respect:

- `L0_MICRO`
- `L1_RESELECT`
- `L2_DELTA_SEARCH`
- `L3_BRANCH_RESET`
- `L4_DIRECTION_RESET`

Do not escalate when a narrower loop is sufficient. Broad direction resets require explicit user intent.

## Generation rework orchestration

Respect:

- `G0_SAME_CONTRACT_RETRY`
- `G1_LOCAL_DIMENSION_DELTA`
- `G2_REDERIVE_FROM_CANONICAL_PARENT`
- `G3_CHANGE_GENERATION_STRATEGY`
- `G4_ESCALATE_UPSTREAM`

`G4` means contract insufficiency/contradiction, not generator permission to redesign ArtStyle.

## Family/batch orchestration

Prefer:

```text
canonical parent
→ representative derivatives
→ representative QC
→ representative runtime validation
→ remaining family
```

Canonical/systemic failure blocks dependent variants. Local derivative failure preserves passing siblings unless evidence shows family-wide cause.

Batch order:

- Tier 0 calibration/anchors
- Tier 1 P0 core gameplay
- Tier 2 P0 variants
- Tier 3 core UI
- Tier 4 secondary/progression
- Tier 5 decoration/FX/polish

Do not scale later tiers while representative earlier tiers expose systemic problems.

## Human checkpoints

Require explicit human approval for GameSpec lock, ArtStyle direction lock, calibration anchor approval, first P0 canonical family approval, broad L4 direction reset, and systemic runtime fixes that reopen locked upstream truth.

Do not interrupt for deterministic routine routing when contracts already determine the next action.

## Policy references

Use when needed:

- `references/orchestration-state-policy.md`
- `references/invalidation-routing-policy.md`
- `references/handoff-promotion-policy.md`
- `contracts/rework-handoff-contract.yaml`

## Completion

Production is complete only when required GameSpec/ArtStyle truth is locked, reference authority is approved, planned assets have authoritative generation and normalization versions, QC passes on those exact versions, executable runtime contexts pass for the integrated lineage, required assets are `SHIPPABLE`, and orchestration state points to the exact shipping versions with no unresolved blocker/systemic rework.
