# Invalidation and Root-Routing Policy

## Purpose

Define how the orchestrator determines root ownership and invalidation scope after a failure or upstream change.

## Three separate questions

Never collapse these into one:

1. **Where was the symptom observed?**
2. **Who owns the root cause?**
3. **Which artifacts/contexts can no longer be trusted?**

Example:

```text
Symptom observed: runtime scene
Root cause: normalization pivot
Invalidation: normalization → QC → affected runtime contexts
Preserve: generation contract + generated visual
```

## Root-owner decision order

Prefer the earliest authoritative layer that contains the defective decision or transformation.

### game-spec-builder

Route here when expected gameplay semantics are undefined, contradictory, or changed.

Examples:
- unclear state meaning,
- ambiguous interaction feedback requirement,
- contradictory screen-flow behavior.

### art-style-builder

Route here when the locked visual system itself is incomplete or contradictory.

Examples:
- two approved anchors govern the same dimension incompatibly,
- category hierarchy rule is missing,
- a locked negative constraint conflicts with a locked positive rule,
- runtime readability requires reopening a style branch rather than fixing one asset.

### game-asset-planner

Route here when decomposition or representation is wrong.

Examples:
- one MRAU should have been multiple runtime-controllable assets,
- state family topology is wrong,
- required state/direction variant was omitted,
- runtime sizing/output requirement was specified incorrectly.

### game-asset-generator

Route here when the production contract is sound but the visual candidate violates it.

Examples:
- identity drift,
- style-anchor drift,
- state visual mismatch,
- forbidden glossy rendering,
- excessive micro-detail,
- family derivative no longer resembles canonical parent.

### game-asset-normalizer

Route here for mechanical runtime preparation defects.

Examples:
- trim/canvas clipping,
- alpha artifact introduced in processing,
- wrong scale/export size,
- anchor/pivot misalignment,
- inconsistent family canvas.

### game-asset-qc

Route here only when QC classification/evidence was wrong or an isolated defect should have been caught before runtime.

Do not route every runtime-discovered asset defect to QC; identify the actual producing owner as primary and record QC escape separately when useful.

### runtime-visual-validator

Route here when the validation plan, evidence coverage, comparison logic, or attribution is defective.

### runtime integration

Route here for implementation context defects such as:
- z-order,
- UI layout,
- camera transform,
- shader/blend/mask,
- lighting/post-processing,
- animation wiring/state transition implementation.

## Invalidation propagation

Invalidate descendants of the changed or defective authority, not unrelated siblings.

### ArtStyle dimension change

```text
changed UI texture rule
→ dependent UI anchors/constraints
→ UI generation contracts
→ dependent generated candidates
→ normalization
→ QC
→ runtime contexts
```

Preserve unrelated character/environment families.

### AssetSpec change

Determine which downstream surfaces depend on the changed field.

Examples:

```text
visual semantic/state change
→ generation + all descendants invalid
```

```text
pivot/export-only requirement change
→ generated visual may remain valid
→ normalization + QC + runtime invalid
```

### Generation candidate change

```text
new active generated visual
→ normalization + QC + runtime invalid
```

Do not invalidate GameSpec, ArtStyle, or planning unless the generator escalated because those inputs were defective.

### Normalization change

```text
normalization version changes
→ QC + affected runtime invalid
→ generation preserved
```

### QC report correction

If the asset itself did not change, only downstream promotion/runtime validation may need reconsideration. Do not regenerate by default.

### Runtime integration change

If upstream asset truth is unaffected:

```text
runtime context/baseline invalid
→ rerun affected runtime validation only
```

## Local vs systemic findings

Classify scope before invalidation:

- `LOCAL_ASSET`
- `LOCAL_DERIVATIVE`
- `FAMILY_SYSTEMIC`
- `CATEGORY_SYSTEMIC`
- `GLOBAL_SYSTEMIC`
- `SCENE_LOCAL`
- `RUNTIME_SYSTEMIC`

A local derivative defect should not invalidate its canonical parent or siblings.

A canonical-parent defect may invalidate derivatives that inherit the failing dimension.

## Preserve/change envelope

Every rework route should include:

```yaml
change_scope:
  - failing_dimension_or_runtime_surface
preserve_scope:
  - confirmed_passing_dimension
  - unrelated_authoritative_artifact
```

If `preserve_scope` is empty for a narrow failure, reconsider whether the route is too broad.

## Escalation discipline

Escalate upstream only when the downstream specialist cannot fix the defect without inventing or changing upstream truth.

Examples:

- generator cannot infer missing character identity rule → art-style-builder
- normalizer cannot choose a pivot because spec never defines semantics → planner/spec owner
- runtime validator observes poor readability caused by one asset's forbidden glow → generator, not art-style reset
- multiple categories fail because global value hierarchy is contradictory → art-style-builder

## Invalidation ledger

The orchestrator should preserve a machine-readable history conceptually equivalent to:

```yaml
- invalidation_id: INV-0031
  trigger:
    artifact: art/style-constraint-ledger.yaml
    from_version: v3
    to_version: v4
    changed_fields:
      - ui.texture_density.max
  affected:
    - family:UI-PRIMARY-BUTTONS
    - family:UI-ICONS
  preserved:
    - family:PLAYER
    - family:ENV-WALLS
  rerun_from: generation
  reason: category-scoped locked constraint changed
```

The ledger may be embedded in pipeline state or stored separately, but the history must be reconstructable.
