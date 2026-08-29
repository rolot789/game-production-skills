---
name: game-asset-qc
description: Use when a normalized asset must be judged against its production contract before it reaches the game — "check these assets", "is this on style", "did the regeneration fix it" — or after any regeneration or normalization change. Runs scripts/technical_check.py for measurable conformance and accessibility, then verifies scoped anchors, negative constraints, family coherence, and readability at intended display size. Never modifies assets. Problems that only appear in a real scene belong to runtime-visual-validator.
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

## Run the technical check first

QC has two halves. One is judgment: does this honor the art direction, does the state read, is the family coherent. The other is arithmetic: dimensions, colour mode, alpha, clipping, padding, hash lineage, contrast ratio, colour-vision separability.

Only the first needs an agent. Run the second:

```bash
python3 skills/game-asset-qc/scripts/technical_check.py \
    --asset normalized/AST-GATE-CLOSED/runtime/AST-GATE-CLOSED.png \
    --spec assets/specs/AST-GATE-CLOSED.yaml \
    --record normalized/AST-GATE-CLOSED/normalization-record.yaml \
    --sibling normalized/AST-GATE-OPEN/runtime/AST-GATE-OPEN.png \
    --background "#1B1F24" --background "#3A4149"
```

It emits the `technical` and `accessibility` blocks of the QC report directly, plus measured values. Paste that output into the report rather than re-deriving it by eye — a claim about dimensions or contrast that was eyeballed is not evidence.

Two checks it performs that are easy to miss manually:

- **`lineage_hash_matches`** — whether the asset on disk is actually the file the normalization record describes. A `FAIL` here means the QC run would judge a different file than the record claims, which invalidates the verdict before any visual work begins. Stop and resolve it.
- **`A11Y_COLOR_VISION`** — whether family states stay distinguishable under protanopia, deuteranopia, and tritanopia simulation. A hue-only state distinction fails for roughly one in twelve players, and it is invisible to unaided review.

Spend your attention on what the script cannot judge.

## Contract Compliance Matrix

Evaluate applicable dimensions only.

### Technical conformance

Produced by `scripts/technical_check.py`: file readability, format/colour/alpha mode, canvas, transparency, bounds/clipping, padding, and exact input/output lineage. Verify naming and export contract against the AssetSpec yourself where the script has no rule for it.

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

### Animation clips

Judge a clip as a clip before judging any single frame of it. The normalizer's frame continuity report is the input: a clip whose `pivot_stable` or `no_duplicate_frames` failed cannot be approved frame by frame, because every frame is individually fine and the sequence is not.

Readability is judged at the clip's `fps`. A frame that reads at leisure can be invisible for 83 ms, and `intended_display_size` alone does not capture that.

`poses_share_a_subject` arrives as `INSUFFICIENT_EVIDENCE` by design — deciding it is QC's job, not the script's. Compare the reported `delta_from_canonical` against the family's `must_preserve` list: a frame that changed something the family declared invariant is `IDENTITY_DRIFT`, routed to `game-asset-generator`.

### Gameplay readability

At `runtime.intended_display_size` — not at source resolution — verify silhouette recognition, state differentiation, important feature visibility, value/contrast hierarchy, clutter/noise, and distinction from neighboring gameplay categories when intrinsic to the asset.

Scene composition belongs to `runtime-visual-validator`.

### Accessibility conformance

When `project.yaml` declares an `accessibility` baseline, verify it. A declared baseline that no stage checks is a contract hole, and this is the stage that closes it.

`scripts/technical_check.py` measures three of the four checks:

- `A11Y_CONTRAST` — alpha-weighted mean colour against every declared background, versus the project's contrast floor.
- `A11Y_COLOR_VISION` — separation from sibling states under all three colour-vision simulations.
- `A11Y_NON_COLOR_CHANNEL` — whether `state.encoding_channels` declares anything other than `hue`.

`A11Y_RUNTIME_CONTRAST` belongs to `runtime-visual-validator`, because it needs the real scene background rather than a declared one.

A colour-vision failure is normally **not** a generator defect. If the AssetSpec specified a hue-only encoding, the root owner is `game-asset-planner`; if the locked style leaves no room for a second channel, it is `art-style-builder`. Route to the generator only when a valid non-colour channel was specified and the candidate failed to implement it. See `ACCESSIBILITY_FAILURE` in `references/routing.yaml`.

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

`preserve_dimensions` is a specialist-local diagnostic field inside a finding. When routing external rework, convert it to the canonical `preserve_scope.dimensions` field defined by `references/rework-handoff-contract.yaml`. A routed handoff carrying `preserve_dimensions` is malformed and `validate_project.py` rejects it.

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

Root ownership follows `references/routing-index.yaml` for the lookup, with the full `references/routing.yaml` as the single source of truth behind it. Do not restate either from memory; use `decision_procedure` in the index to pick the class, then take the owner and scopes from the row.

Every `BLOCKER` and `MAJOR` finding carries a `reason_code` naming its symptom class. An unknown reason code is a malformed report and `validate_project.py` rejects it.

Do not route isolated QC defects to runtime validation.

## Canonical rework handoff

External rework handoffs MUST follow `references/rework-handoff-contract.yaml` and validate against `references/schemas/rework-handoff.schema.json`.

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
