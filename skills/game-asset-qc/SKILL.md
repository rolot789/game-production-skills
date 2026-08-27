---
name: game-asset-qc
description: Evaluate normalized game assets against production contracts, scoped visual anchors, persistent style constraints, family lineage, and runtime-readability requirements. Produce evidence-backed findings, pass/fail status, and canonical delta-rework handoffs without modifying assets.
---

# Game Asset QC

## Purpose

Judge whether a normalized asset satisfies the production contract it was supposed to implement. Do not judge isolated attractiveness and do not redesign the asset during QC.

```text
Normalized Asset
+ AssetSpec
+ Generation Contract / Record
+ Locked ArtStyle
+ Scoped Anchors
+ Style Constraint Ledger
+ Family / State Context
        ↓
Contract Resolution
        ↓
Technical + Visual Verification
        ↓
Finding Classification
        ↓
Root-owner Routing
        ↓
APPROVED / REWORK_REQUIRED / BLOCKED
```

## Project path resolution

If `project.yaml` exists, its `paths` registry is canonical. Logical output patterns in this skill resolve through that registry.

## Required inputs

Use the strongest available explicit evidence:

- normalized runtime asset,
- normalization record,
- AssetSpec,
- `generation-contract.yaml`,
- selected candidate generation record,
- locked `art-style.yaml`,
- `style-anchor-manifest.yaml`,
- `style-constraint-ledger.yaml` when applicable,
- canonical parent/sibling variants when applicable,
- gameplay/state semantics from GameSpec or AssetSpec when needed.

If production-critical truth is missing or contradictory, block and route upstream rather than inventing it.

## Core rules

1. Contract first, taste second.
2. Verify anchors only on dimensions they govern.
3. Enforce locked negative constraints as actual QC rules.
4. Inspect both source scale and intended runtime display size.
5. Evaluate families comparatively.
6. Separate symptom from root cause.
7. Never modify/repaint/crop/normalize/regenerate in QC.
8. Treat repeated systemic failures as systemic even if individual instances look superficially usable.

## Contract Compliance Matrix

Evaluate applicable dimensions only.

### Technical conformance

Check file readability, format/color/alpha mode, canvas, transparency, bounds/clipping, naming/export contract, normalization metadata, anchor/pivot consistency, and exact input/output lineage.

### Semantic conformance

Check identity/category/state/direction/pose, gameplay-significant features, absence of invented semantics, and intrinsic state distinguishability.

### Positive style conformance

Resolve global/category rules for shape, line, palette/value, texture, lighting, material, composition, detail density, readability, and overrides.

### Scoped anchor conformance

For each anchor record `anchor_id`, role, governed dimensions, applicability, and result: `PASS`, `FAIL`, `NOT_APPLICABLE`, or `INSUFFICIENT_EVIDENCE`.

### Negative constraint conformance

Apply inheritance:

```text
Global → Category → Family → Asset Override
```

Evaluate `HARD_FORBIDDEN`, `SOFT_AVOID`, `BOUNDED`, and `ANTI_REFERENCE`. Convert vague feedback such as `looks AI-generated` into observable contract violations before using it as evidence.

### Family coherence

Compare identity, silhouette/proportion, projection, relative scale, palette/material family, line/texture treatment, shared geometry, intended state difference, and direction consistency.

### Gameplay readability

At intended runtime size verify silhouette recognition, state differentiation, important feature visibility, value/contrast hierarchy, clutter/noise, and distinction from neighboring gameplay categories when intrinsic to the asset.

Scene composition belongs to `runtime-visual-validator`.

## Evidence model

Every `BLOCKER` or `MAJOR` finding must include concrete evidence.

```yaml
id:
severity:
dimension:
contract_source:
expected:
observed:
evidence:
root_cause_class:
owner:
required_action:
preserve_dimensions: []
```

`preserve_dimensions` is a specialist-local diagnostic field. When routing external rework, convert it to the canonical `preserve_scope.dimensions` field defined by `contracts/rework-handoff-contract.yaml`.

## Severity and status

Severity:

- `BLOCKER`: unusable, wrong semantics/identity, missing critical contract, hard forbidden violation with production impact, invalid runtime asset, or contradiction preventing evaluation.
- `MAJOR`: clear locked requirement/anchor/family/bounded/readability violation; rework required.
- `MINOR`: localized defect without material identity/style/state/runtime impact; may ship only if policy allows.
- `NOTE`: non-blocking observation.

Status:

- `approved`
- `approved_with_minor_findings`
- `rework_required`
- `blocked`

## Root-cause routing

- visual/style/identity/state/family generation defect → `game-asset-generator`
- clipping/canvas/alpha/trim/padding/scale/anchor/pivot/export defect → `game-asset-normalizer`
- missing/incorrect variant, AssetSpec, family relation, runtime footprint → `game-asset-planner`
- contradictory/scoped style/anchor/constraint truth → `art-style-builder`
- contradictory gameplay/state semantics → `game-spec-builder`

Do not route isolated QC defects to runtime validation.

## Canonical rework handoff

External rework handoffs MUST follow `contracts/rework-handoff-contract.yaml`.

Example:

```yaml
root_owner: game-asset-generator
reason_codes:
  - NEGATIVE_CONSTRAINT_VIOLATION

change_scope:
  dimensions:
    - texture_density
    - highlight_treatment
  artifacts: []
  runtime_properties: []

preserve_scope:
  dimensions:
    - identity
    - silhouette
    - palette
    - line_weight
  artifacts:
    - specs/AST-001.yaml
  upstream_truth:
    - game_spec
    - art_style
    - approved_anchors

invalidation_scope: LOCAL_ASSET
revalidation_scope:
  - normalization
  - asset_qc
  - affected_runtime_contexts
```

Internal fields such as `change_dimensions` / `preserve_dimensions` may be used inside the QC report, but must not replace canonical external fields.

## Family and batch policy

Validate canonical parent first, representative derivatives second, then the remaining family. A canonical/systemic failure blocks dependent derivatives. A local derivative failure preserves passing siblings unless evidence proves family-wide impact.

Use `references/contract-verification-policy.md`, `references/failure-routing-policy.md`, and `references/family-batch-qc-policy.md` when needed.

## Version lineage

The QC report must identify the exact upstream versions/IDs it evaluated, including normalized output hash/version, AssetSpec version/hash, generation contract/candidate lineage, ArtStyle version when available, anchor IDs, and active constraint IDs.

A changed generation candidate or normalized output normally invalidates the previous QC approval unless effective input identity is proven unchanged.

## Outputs

Logical outputs:

```text
qc/<asset-id>/qc-report.yaml
qc/<family-id>/family-qc-summary.yaml   # when family/batch QC is used
```

Resolve actual paths through `project.yaml` when present.

## Completion criteria

QC is complete only when applicable contracts are resolved, technical/visual checks are complete at intended scale, findings have evidence/severity, blocker/major findings have root owners/actions, passing dimensions are captured for preservation, final status is explicit, evaluated versions are recorded, and any external rework request uses the canonical handoff envelope.
