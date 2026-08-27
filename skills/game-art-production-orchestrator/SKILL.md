---
name: game-art-production-orchestrator
description: Orchestrate the AI-native game art production pipeline from locked game specification and art style through asset planning, grounded generation, normalization, contract-aware QC, and scene-context runtime validation. Enforce readiness gates, scoped reference authority, delta rework, preserve/change contracts, dependency-aware invalidation, provenance, and deterministic handoffs between specialist skills.
---

# Game Art Production Orchestrator

## Purpose

Coordinate the pipeline without duplicating specialist responsibilities. The orchestrator owns **routing, gates, handoffs, lifecycle state, rework scope, invalidation, and promotion**. Specialist skills own their domain decisions and evidence.

```text
game-spec-builder
→ art-style-builder
→ game-asset-planner
→ game-asset-generator
→ game-asset-normalizer
→ game-asset-qc
→ runtime-visual-validator
```

The orchestrator must not redesign art, rewrite prompts, normalize files, perform QC, or visually approve runtime scenes itself. It determines **which specialist should act next and with what exact scope**.

## Core orchestration principles

1. **Advance artifacts, not assumptions.** Every handoff names authoritative inputs and expected outputs.
2. **Preserve validated truth.** A narrow failure must not reopen unrelated locked decisions or passing dimensions.
3. **Search-derived references are not authorities by discovery alone.** Only explicitly approved scoped anchors may govern production.
4. **Rework is delta-based.** Carry `change_scope` and `preserve_scope` through generator, normalization, QC, and runtime loops.
5. **Symptom location is not root ownership.** Route to the skill or runtime layer that owns the cause.
6. **Invalidation is dependency-aware.** Invalidate the smallest descendant surface that can no longer be trusted.
7. **Partial evidence never upgrades readiness.** `partial_validation_only` cannot promote an asset to `RUNTIME_APPROVED`.
8. **Provenance is append-only history.** Superseded artifacts remain traceable even when no longer authoritative.

## Source-of-truth hierarchy

1. LOCKED GameSpec
2. LOCKED ArtStyle
3. Approved scoped Style Anchors
4. Locked Style Constraint Ledger
5. Asset Manifest / Asset Specs
6. Generation Contract + generation records
7. Normalization records
8. QC reports / family QC summaries
9. Runtime validation reports / evidence manifests / approved baselines

`reference-corpus.yaml` is evidence. `style-anchor-manifest.yaml` defines production authority. A discovered reference must not bypass anchor approval.

Downstream artifacts never silently rewrite upstream sources.

## Pipeline state

Maintain `.pipeline/game-art-production-state.yaml` as the canonical orchestration state.

Pipeline stage statuses:

- `NOT_STARTED`
- `IN_PROGRESS`
- `READY`
- `BLOCKED`
- `FAILED`
- `INVALIDATED`
- `COMPLETE`

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

Failure/rework states:

- `GENERATION_REWORK`
- `NORMALIZATION_BLOCKED`
- `QC_REWORK`
- `RUNTIME_REWORK`
- `INVALIDATED`

Each asset/family state entry should track at minimum:

```yaml
asset_id: AST-001
stage: asset_qc
lifecycle: QC_REWORK
active_version: v4
root_owner: game-asset-generator
change_scope:
  - texture_density
preserve_scope:
  - identity
  - silhouette
  - palette
  - line_weight
invalidated_artifacts:
  - generation/AST-001/candidates/v4.png
preserved_artifacts:
  - specs/AST-001.yaml
  - normalized/AST-001/normalization-record.yaml
next_skill: game-asset-generator
reason: NEG-TEXTURE-004 violated at runtime display scale
```

## Readiness and promotion gates

Do not advance merely because files exist.

### Game specification

- Require the relevant GameSpec readiness gate before art-style work that depends on it.
- Do not convert `INFERRED` gameplay semantics into production truth.

### Art style

Before mass generation, require:

- locked production-relevant style rules,
- `REFERENCE_GROUNDED` where reference grounding is required,
- approved scoped anchors for production-critical dimensions,
- locked applicable negative constraints,
- calibration approval for representative P0 families.

### Generation

Before generation, require a complete scoped input set. `generation-contract.yaml` is the generation-stage source of truth; `prompt.md` is only a serialized provider-facing representation.

### Asset QC

Only normalized runtime candidates with sufficient generation and normalization provenance enter QC. `approved` or `approved_with_minor_findings` may promote to `QC_APPROVED` according to project policy.

### Runtime validation

Only executable rendered-context validation may produce `RUNTIME_APPROVED`. `partial_validation_only`, `runtime_rework_required`, and `runtime_blocked` never promote.

### Shipping

An asset is `SHIPPABLE` only when all required upstream versions remain authoritative and runtime approval applies to the currently integrated version/context.

## Handoff envelope

Every specialist transition should preserve a structured handoff envelope conceptually equivalent to:

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
change_scope:
  - texture_density
preserve_scope:
  - identity
  - silhouette
  - palette
required_inputs:
  - specs/AST-001.yaml
  - generation/AST-001/generation-contract.yaml
  - qc/AST-001/qc-report.yaml
expected_outputs:
  - generation/AST-001/generation-contract.yaml
  - generation/AST-001/records/*.yaml
revalidate:
  - normalization
  - asset_qc
  - runtime_validation
preserve:
  - game_spec
  - art_style
  - asset_planning
```

The exact storage format may vary, but the information must not be lost across handoffs.

## Failure routing

Route by root cause, not by where the failure was observed.

- undefined gameplay semantics, state behavior, screen-flow meaning → `game-spec-builder`
- contradictory/missing art direction, scoped anchor authority, contextual style policy → `art-style-builder`
- wrong MRAU decomposition, family topology, state/direction representation, runtime requirement → `game-asset-planner`
- malformed visual, identity/style/state drift, negative-constraint violation, failed generation contract → `game-asset-generator`
- canvas/scale/trim/alpha/anchor/pivot/export processing → `game-asset-normalizer`
- incorrect isolated classification, missing contract violation, insufficient QC evidence → `game-asset-qc`
- scene/context evidence planning or attribution error → `runtime-visual-validator`
- z-order/layout/camera/shader/lighting/blend/mask/post-processing integration → runtime implementation owner

If ownership is ambiguous, do not launch broad rework. Request the smallest diagnostic step that can separate competing root causes.

## Delta rework policy

Every rework loop should explicitly classify:

```text
WHAT CHANGES?
WHAT MUST NOT CHANGE?
WHAT EVIDENCE CAUSED THE REWORK?
WHICH ARTIFACTS ARE NOW UNTRUSTWORTHY?
WHICH DOWNSTREAM CHECKS MUST RUN AGAIN?
```

Examples:

### Generator-local visual defect

```text
QC detects excessive texture density
→ preserve GameSpec / ArtStyle / anchors / identity / palette
→ regenerate texture dimension only
→ rerun normalization if output geometry/canvas may differ
→ rerun QC
→ rerun affected runtime contexts only
```

### Normalization-only defect

```text
Runtime detects pivot offset
→ preserve generated visual candidate
→ invalidate normalization record + QC approval + affected runtime approval
→ rerun normalizer
→ QC
→ affected runtime contexts
```

### Runtime-integration-only defect

```text
Asset is valid but z-order hides it
→ preserve generation / normalization / QC
→ fix runtime integration
→ invalidate affected runtime evidence only
→ rerun affected scene validation
```

### Art-direction change

```text
User unlocks UI texture direction
→ invalidate dependent UI anchors/constraints
→ invalidate only asset families governed by those changed dimensions
→ preserve unrelated character/environment families
```

## Reference-grounding orchestration

When `art-style-builder` uses search:

1. preserve user-provided references as primary evidence in `REFERENCE_ANCHORED` mode,
2. allow search results into `reference-corpus.yaml` as evidence,
3. require accessibility/role resolution before candidate presentation,
4. require explicit user approval before a search-derived item becomes a production anchor,
5. preserve the corpus across feedback loops,
6. prefer corpus reselection before delta search,
7. invalidate downstream assets only when an authoritative anchor or locked style rule changes.

A new search result that is merely added to the corpus does **not** invalidate downstream assets.

## Art-style feedback loop orchestration

Respect the art-style loop escalation model:

- `L0_MICRO`: parameter/intensity refinement; no search by default
- `L1_RESELECT`: reuse/re-rank current corpus
- `L2_DELTA_SEARCH`: targeted search for uncovered dimension
- `L3_BRANCH_RESET`: reopen one category/domain branch
- `L4_DIRECTION_RESET`: reopen broad art direction only with explicit user intent

The orchestrator must not escalate to a broader loop when a narrower loop can resolve the issue.

## Generation rework orchestration

Respect generator escalation:

- `G0`: same-contract retry
- `G1`: local dimension delta
- `G2`: rederive from canonical family parent
- `G3`: change generation strategy/provider approach while preserving upstream truth
- `G4`: escalate upstream because the contract itself is insufficient or contradictory

Do not reinterpret `G4` as permission for the generator to redesign art direction.

## Family and batch orchestration

Prefer family-first progression:

```text
canonical parent
→ representative state/direction variants
→ QC representative subset
→ runtime representative subset
→ expand remaining family
```

If the canonical parent fails systemically, block dependent variants. If one derivative fails locally, rework only that derivative unless evidence indicates a family-level defect.

Batch order:

- Tier 0: calibration / anchors
- Tier 1: P0 core gameplay
- Tier 2: P0 state/direction variants
- Tier 3: core UI
- Tier 4: secondary / progression
- Tier 5: decoration / FX / polish

Do not scale a later tier while an earlier representative tier exposes systemic problems.

## Runtime approval and regression

Runtime approval is version- and context-sensitive.

- `partial_validation_only` is evidence, never approval.
- A new integrated asset version invalidates runtime approval for contexts that depend on the changed visual/runtime surface.
- A scene integration-only change invalidates only affected runtime contexts when upstream asset contracts remain valid.
- Approved runtime captures may become baselines only when their version/context provenance is recorded.
- Semantic regression matters more than pixel identity.

## Invalidation model

Use dependency-aware invalidation.

### Preserve by default

Unaffected locked GameSpec, ArtStyle dimensions, anchors, asset specs, passing generation dimensions, and unrelated families remain authoritative.

### Invalidate only descendants of changed truth

Examples:

```text
Style texture constraint changes for UI only
→ UI generation contracts invalid
→ UI generated candidates invalid
→ UI normalization/QC/runtime descendants invalid
→ character/environment assets preserved
```

```text
Runtime camera zoom changes
→ generation/QC preserved
→ runtime validation contexts depending on that camera invalidated
```

```text
AssetSpec collision-independent pivot rule changes
→ generation may remain valid
→ normalization and downstream QC/runtime invalidated
```

Record invalidation reason, triggering artifact/version, affected descendants, preserved siblings, and required revalidation.

## Human checkpoints

Require explicit human approval for:

- GameSpec lock,
- ArtStyle direction lock,
- calibration anchor approval,
- first P0 canonical family approval,
- broad `L4_DIRECTION_RESET`,
- major systemic runtime regression when the proposed fix would reopen locked upstream truth.

Do not interrupt the user for routine deterministic routing when the existing contracts already determine the next action.

## Completion

Production is complete only when:

- required GameSpec and ArtStyle truth is locked,
- required reference grounding/anchors are approved,
- planned required assets have authoritative generated and normalized versions,
- contract-aware QC passes,
- required executable runtime contexts pass,
- all required assets are `SHIPPABLE`,
- no blocker or unresolved systemic rework remains,
- orchestration state points to the exact authoritative versions used for shipping.

## Policy references

Read when needed:

- `references/orchestration-state-policy.md`
- `references/invalidation-routing-policy.md`
- `references/handoff-promotion-policy.md`
