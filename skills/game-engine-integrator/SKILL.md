---
name: game-engine-integrator
description: Use when QC-approved assets must be packed and configured for a specific engine — "set up the atlas", "these import wrong in Unity", "why is the build so big", "are we over budget" — or before a build is cut. Runs scripts/budget_check.py to measure texture memory, atlas dimensions, and file sizes against declared budgets, then emits import settings and an atlas manifest. Does not judge how assets look (game-asset-qc) or validate them in real scenes (runtime-visual-validator).
---

# Game Engine Integrator

## Purpose

Turn a set of QC-approved normalized assets into something a specific engine can load correctly and afford to load at all.

```text
Game Asset QC
  "Does this asset satisfy its production contract?"

Game Engine Integrator
  "Can this engine load it correctly, and can the build afford it?"

Runtime Visual Validator
  "Does it still work once the player sees it?"
```

This stage exists because two whole classes of failure live between QC and runtime, and neither is visible to either neighbour: an asset that is visually perfect but imports with the wrong pivot or filter mode, and an asset set that is individually fine but collectively blows the memory budget.

## Project path resolution

If `project.yaml` exists, its `paths` registry is canonical. Resolve logical paths such as `engine-integration/<target-id>/...` through it rather than hard-coding repository roots. The engine target and the budgets both come from `project.yaml` (`engine` and `budgets`); this skill never invents either.

## Core rules

1. **Measure, do not estimate.** Budget claims come from `scripts/budget_check.py`, never from judgment.
2. An undeclared budget is a blocker, not a pass. `integration_blocked` is the correct status when `project.yaml` declares no budgets.
3. Import settings are derived from the normalization record, not re-decided here. Pivot comes from `geometry.runtime_pivot`; pixels-per-unit comes from `project.yaml`.
4. Never re-encode, resize, or recompress an asset to fit a budget. That changes the QC-approved bytes and invalidates the approval. Route the reduction upstream instead.
5. Atlas membership follows draw-order and lifetime, not alphabetical convenience.
6. A budget that cannot be met without changing asset content is not this stage's defect. Route it per `references/routing.yaml`.

## Required inputs

```text
QC-approved normalized runtime assets
qc/<asset-id>/qc-report.yaml          # status must be a promoting status
normalized/<asset-id>/normalization-record.yaml
specs/<asset-id>.yaml
project.yaml                          # engine target + budgets
```

Do not integrate an asset whose QC report is bound to a different `content_hash` than the file on disk. That is a lineage break, and it means the QC verdict does not describe this asset.

## Deterministic step first

Run the measurement before forming any opinion:

```bash
python3 scripts/budget_check.py --project-root . --target-id <target>
```

The script emits the `budget-report.yaml` body: measured totals, the declared budgets it compared against, per-check results, and findings. Read that output. Your job is what the script cannot do — decide whether a `FAIL` is an integration defect, a planning defect, or a budget that was set wrong.

## Import settings

Emit `import-settings.yaml` derived from recorded truth, one entry per asset:

```yaml
schema_version: 3
target:
  id: web-main
  engine: unity
  pixels_per_unit: 100
  color_space: linear
assets:
  AST-GATE-CLOSED:
    source: normalized/AST-GATE-CLOSED/runtime/AST-GATE-CLOSED.png
    content_hash: <sha256 of that exact file>
    pivot: [0.5, 1.0]          # from normalization-record geometry.runtime_pivot
    pixels_per_unit: 100
    filter_mode: point          # point for pixel art, bilinear otherwise
    compression: none
    generate_mipmaps: false
    wrap_mode: clamp
```

Rules that are not negotiable per engine:

- **Pivot** must equal the normalization record's `runtime_pivot`. If the engine cannot express it, record the limitation and route to `game-asset-normalizer` rather than silently rounding it.
- **Filter mode** follows the locked art style. Point filtering on non-pixel art destroys approved contour behavior; bilinear on pixel art destroys it equally.
- **Mipmaps** default off for 2D UI and gameplay sprites; enabling them changes appearance at distance and needs a runtime validation pass.
- **Compression** that is lossy changes approved pixels. If a budget forces lossy compression, that is a decision for the owner, and the affected assets need re-validation at runtime.

## Atlas packing

Atlas membership is a runtime decision, not a tidiness decision.

Group by:

- **draw order** — assets drawn in the same pass belong together; that is what reduces draw calls,
- **lifetime** — assets loaded and unloaded together belong together,
- **scene locality** — a menu atlas that is resident during gameplay is wasted memory,
- **update frequency** — animated frames that change every tick do not belong with static UI.

Do not group by category name alone. "All the icons" is a filing decision, not a rendering decision.

Decide membership, then run the packer. Placement, dimensions, padding, and hashing are arithmetic:

```bash
python3 skills/game-engine-integrator/scripts/pack_atlas.py \
    --project-root . --atlas-id FAM-GATE \
    --member AST-GATE-CLOSED --member AST-GATE-TRANSITION --member AST-GATE-OPEN
```

It refuses any member whose QC report does not promote, or whose QC report evaluated a different `content_hash` than the file on disk — an atlas built from assets QC never described is an atlas of unverified pixels. It emits `atlas-manifest.yaml` with each member's placement rect and source `content_hash`, so a changed asset invalidates the atlas that contains it.

Padding defaults to 2 px and should not go below it: under bilinear filtering at non-integer scale, neighbouring members bleed. This is the single most common atlas defect.

Dimensions are packed tight by default. Pass `--power-of-two` only when the target needs it — compressed texture formats and older GL do; a modern 2D web target does not, and rounding up can more than double the sheet.

**The atlas is what is resident at runtime, not the loose sprites.** Pack before measuring: `budget_check.py` counts an atlased member as part of its atlas rather than charging for both, and reports `max_atlas_dimension` as `INSUFFICIENT_EVIDENCE` when no atlas has been packed. It does not substitute the largest sprite dimension for an atlas dimension — that reads green for a reason unrelated to the risk.

## Sprite sheets

A clip packs like any atlas, and the manifest gains a `clips` block: ordered frames with their rects, `fps`, `loop`, `hold_frames`, and total `duration_ms`. That is the difference between an atlas and a sprite sheet an engine can play — the region rects alone do not say which rect is frame 0.

Pack every frame of a clip into one sheet. The packer refuses a partial clip rather than emitting a frame map that indexes frames the sheet does not contain.

## Budgets

Budgets live in `project.yaml`:

```yaml
budgets:
  max_atlas_dimension: 2048
  max_texture_memory_mb: 64
  max_total_asset_bytes: 12000000
  max_single_asset_bytes: 512000
```

`scripts/budget_check.py` measures against exactly these. The estimated texture memory figure is `width * height * 4` per asset — the honest uncompressed RGBA8 ceiling. When the target compresses, record the format in `import-settings.yaml` and treat the figure as a ceiling rather than a prediction. Never report a compressed figure the script did not measure.

Use `references/budget-policy.md` for how to choose budgets and what to do when one is exceeded.

## Failure routing

Root ownership follows `references/routing.yaml`. The classes this stage owns:

- `BUDGET_VIOLATION` — a measured budget is exceeded,
- `IMPORT_SETTING_DEFECT` — wrong pivot mapping, filter mode, compression, or pixels-per-unit.

The classes that look like this stage's but are not:

- a budget that cannot be met without changing asset content → `DECOMPOSITION_DEFECT` or `REPRESENTATION_STRATEGY_DEFECT`, owner `game-asset-planner`,
- a pivot that is wrong in the normalization record itself → `MECHANICAL_PROCESSING_DEFECT`, owner `game-asset-normalizer`,
- an asset that looks wrong once imported correctly → `game-asset-qc` or `runtime-visual-validator` depending on whether scene context is involved.

External rework handoffs serialize through `references/rework-handoff-contract.yaml`.

## Status

- `integration_ready`
- `integration_ready_with_minor_findings`
- `integration_rework_required`
- `integration_blocked`

Only the first two promote to `INTEGRATION_READY`. An undeclared budget produces `integration_blocked`, never a silent pass.

## Outputs

```text
engine-integration/<target-id>/integration-plan.yaml
engine-integration/<target-id>/import-settings.yaml
engine-integration/<target-id>/budget-report.yaml
engine-integration/<atlas-id>/atlas-manifest.yaml   # when atlases are produced
```

Resolve actual paths through `project.yaml`. `budget-report.yaml` must validate against `references/schemas/budget-report.schema.json`.

## Version lineage

Every integration artifact records the `content_hash` of each asset it consumed. A changed normalized output invalidates the atlas and import settings that referenced it, and the dependent runtime approval with them. An import-setting change alone invalidates only dependent runtime contexts — generation, normalization, and QC stay valid.

## Completion criteria

Integration is complete for a target only when every required asset has import settings derived from its recorded geometry, atlas membership is justified by draw order and lifetime, `budget_check.py` reports no `FAIL` against declared budgets, every consumed asset is pinned by `content_hash`, and any unmet budget has been routed to its root owner rather than absorbed by re-encoding approved pixels.
