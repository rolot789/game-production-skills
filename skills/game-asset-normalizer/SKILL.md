---
name: game-asset-normalizer
description: Normalize approved or selected game-art candidates into deterministic, engine-ready runtime assets while preserving visual truth. Apply explicit canvas, scale, bounds, padding, alpha, anchor, pivot, family-alignment, naming, export, version-lineage, and delta-rework rules without redrawing or restyling.
---

# Game Asset Normalizer

## Principle

**Normalize mechanics, not aesthetics.**

This stage may resize, pad, trim according to explicit policy, normalize alpha/canvas/scale, align families, attach anchor/pivot metadata, export formats, hash outputs, and validate deterministic geometry. It must not redraw, restyle, invent missing content, repair semantic generation failures, or silently crop required content.

```text
Selected Generation Candidate
+ AssetSpec
+ Normalization Policy
+ Optional Rework Scope
        ↓
Input / Version Validation
        ↓
Geometry / Alpha Inspection
        ↓
Trim / Scale / Canvas / Family Alignment
        ↓
Anchor / Pivot / Metadata Resolution
        ↓
Deterministic Export
        ↓
Normalization Record + Hashes
```

## Project path resolution

If `project.yaml` exists, treat its `paths` registry as canonical. Logical paths shown here such as `normalized/<asset-id>/...` must resolve through that registry when the project defines another root.

## Required inputs

At minimum:

- selected generation candidate,
- `specs/<asset-id>.yaml`,
- normalization policy declared by the AssetSpec/project.

When available, consume:

- candidate generation record,
- `generation-contract.yaml`,
- family/canonical-parent metadata,
- `project.yaml`,
- `change_scope` and `preserve_scope` for rework handoffs.

Do not normalize an asset when the candidate identity/version cannot be established well enough to preserve lineage.

## Input lineage

A normalization record must identify the exact candidate and specification it processed.

Record when available:

```yaml
input_candidate:
  id: <candidate-id>
  path: <resolved-path>
  hash: <content-hash>
  generation_job_version: <version>
  generation_record: <path-or-id>

asset_spec:
  path: <resolved-path>
  version: <version>
  hash: <hash>

normalization_policy:
  id: <policy-id>
  version: <version-or-unknown>
```

Never pretend an old normalization record applies to a newly generated candidate unless identity is proven through the recorded input hash/version.

## Mechanical process

```text
inspect geometry / alpha bounds
→ resolve normalization policy
→ trim decision
→ uniform scale
→ canvas placement / padding
→ family alignment
→ visual anchor + runtime pivot metadata
→ deterministic export
→ validation / report
```

Keep these concepts distinct:

- `visual_anchor`: perceptual alignment reference,
- `runtime_pivot`: transform/placement origin used by runtime,
- `collision_origin`: gameplay/physics origin when separately defined.

Do not collapse them into one point merely for convenience.

## Family normalization

Family variants should share the appropriate:

- canvas basis,
- scale basis,
- baseline,
- pixel density,
- coordinate system,
- declared anchor group,
- pivot policy.

Do not independently maximize each state or direction. A family should preserve relative scale and placement so downstream state switching does not jump.

If a derivative is normalized against a canonical parent, record that lineage.

## Delta rework contract

Canonical rework fields are:

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

The normalizer may change only mechanical surfaces it owns and that the handoff permits.

Examples:

### Pivot-only correction

```yaml
change_scope:
  runtime_properties:
    - runtime_pivot
preserve_scope:
  dimensions:
    - visual_content
    - palette
    - silhouette
  upstream_truth:
    - generation_candidate
    - art_style
```

Do not rescale, retrim, or alter the canvas unless the pivot correction requires it and the dependency is explicitly recorded.

### New generation candidate

A changed generation candidate normally invalidates the previous normalization result because the normalized output is a descendant of the candidate.

```text
new generation candidate
→ normalization required
→ QC approval invalidated
→ affected runtime approval invalidated
```

Only reuse a prior normalized output when the orchestrator can prove the effective normalization input is identical and the policy permits reuse.

## Allowed operations

Allowed when required by explicit policy:

- deterministic trim/padding,
- uniform resize,
- nearest/bilinear/etc. resampling only when specified,
- canvas placement,
- alpha cleanup limited to mechanical edge/format handling,
- family alignment,
- metadata attachment,
- file naming/format conversion,
- hash/report generation.

Forbidden:

- redraw missing limbs/details,
- restyle line/texture/palette,
- invent transparent content,
- reshape silhouette to make fitting easier,
- semantic state repair,
- visual beautification,
- independent per-variant scaling that violates family policy.

If a forbidden correction is needed, route upstream.

## Validation

Before promotion to QC verify:

- exact expected dimensions/canvas,
- alpha/background policy,
- no required content is clipped,
- trim/padding follows policy,
- scale basis is correct,
- family relative scale/alignment is preserved,
- anchor/pivot metadata is valid,
- file format/naming is correct,
- output hash exists when hashing is supported,
- record points to exact input candidate/spec versions,
- rework `preserve_scope` was not violated.

## Failure routing

- malformed/missing visual content → `game-asset-generator`
- contradictory runtime footprint/family/normalization constraints → `game-asset-planner`
- ambiguous visual style requirement → `art-style-builder` only when the normalization decision truly depends on unresolved style truth
- deterministic processing/export failure → `game-asset-normalizer`

Do not repair upstream failures locally.

## Outputs

Logical outputs:

```text
normalized/<asset-id>/
├── runtime/<asset-id>.<ext>
├── normalization-record.yaml
├── geometry-report.yaml
└── preview/
```

Resolve actual locations through `project.yaml` when present.

`normalization-record.yaml` should include:

```yaml
input_candidate:
asset_spec:
normalization_policy:
change_scope:
preserve_scope:
operations: []
family_lineage:
output:
  path:
  hash:
validation:
```

## Completion criteria

Ready for QC only when dimensions, alpha, clipping, scale, anchor/pivot, family invariants, record completeness, deterministic validation, exact input/output lineage, and applicable preserve/change constraints pass.
