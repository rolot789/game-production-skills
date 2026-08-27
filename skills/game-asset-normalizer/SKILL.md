---
name: game-asset-normalizer
description: Use when generated candidates must become engine-ready files with predictable size, canvas, alpha, anchor, and pivot — "clean these up for the engine", "the sprites are all different sizes", "the character jumps when the state changes" — or after any regeneration. Runs scripts/normalize.py for the deterministic geometry and records exact input and output hashes. Never redraws, restyles, or repairs content; those route to game-asset-generator.
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

A normalization record must identify the exact candidate and specification it processed, and must validate against `references/schemas/normalization-record.schema.json`.

```yaml
input_candidate:
  id: v1-c2
  path: generation/AST-GATE-CLOSED/candidates/v1-c2.png
  content_hash: <sha256 of those exact bytes>
  generation_job_version: v1
  generation_record: generation/AST-GATE-CLOSED/records/v1-c2.yaml

asset_spec:
  path: assets/specs/AST-GATE-CLOSED.yaml
  version: v3
  content_hash: <sha256>

normalization_policy:
  id: default-raster-v1
  version: v1
```

These fields are required, not best-effort. `normalize.py` computes them; do not hand-write them. A record whose `content_hash` does not match the bytes on disk is worse than no record, because it looks authoritative while describing a different file — `validate_project.py` fails on exactly this.

Never treat an old normalization record as applying to a newly generated candidate. Effective input equivalence is proven by identical `content_hash` on every declared input plus an identical policy version. Visual similarity, file size, and timestamps prove nothing.

## Run the script; do not do this by eye

Every operation in this stage is arithmetic — alpha bounds, trim, uniform scale, canvas placement, anchor and pivot derivation, hashing. Performing it by visual judgment is neither reproducible nor checkable, and the toolkit's entire invalidation model depends on `content_hash` being a real measurement rather than an assertion.

So this skill does not perform the geometry. It runs the tool and judges the result:

```bash
python3 skills/game-asset-normalizer/scripts/normalize.py \
    --candidate generation/AST-GATE-CLOSED/candidates/v1-c2.png \
    --spec assets/specs/AST-GATE-CLOSED.yaml \
    --project-root . \
    --out normalized/AST-GATE-CLOSED
```

The script reads the AssetSpec's `normalization` block, applies the operations in order, writes the runtime asset, and emits `normalization-record.yaml` and `geometry-report.yaml` with real sha256 hashes for the input candidate, the AssetSpec, and the output.

Add `--shared-scale <factor>` to force family members onto one scale basis. Add `--dry-run` to inspect the geometry before writing anything.

Exit code 0 means every validation check passed. Exit code 1 means at least one failed, and the record names which.

**What the agent decides, and the script cannot:** whether the numeric result honors the AssetSpec's intent, whether a failure is normalizer-owned or belongs upstream, and which family members share a scale basis. The script refuses to invent a missing `target_canvas` and refuses to process a fully transparent candidate — both are routed, not guessed.

## Mechanical process

The script performs this sequence; the record lists exactly which steps ran.

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

Root ownership follows `references/routing.yaml`; do not restate the table from memory. The classes this stage owns are `MECHANICAL_PROCESSING_DEFECT` and `FAMILY_ALIGNMENT_DEFECT`.

The failures that surface here but belong elsewhere:

- malformed or missing visual content → `CONTENT_ERROR`, owner `game-asset-generator`
- contradictory runtime footprint, family, or normalization constraints → `DECOMPOSITION_DEFECT`, owner `game-asset-planner`
- a missing `target_canvas` or undefined pivot semantics → `DECOMPOSITION_DEFECT`, owner `game-asset-planner`
- a normalization decision that genuinely depends on unresolved style truth → `STYLE_AUTHORITY_CONFLICT`, owner `art-style-builder`

Do not repair upstream failures locally. External handoffs serialize through `references/rework-handoff-contract.yaml`.

## Reference policy

`references/geometry-semantics-policy.md` covers what visual anchor, runtime pivot, and collision origin actually mean, why collapsing them causes animation jitter, and how family alignment is chosen.

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
