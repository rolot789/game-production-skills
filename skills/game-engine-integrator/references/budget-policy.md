# Budget Policy

## Purpose

A performance budget only works if it is declared before it is needed, measured rather than estimated, and enforced against an owner who can actually change the outcome.

This policy covers how to choose budgets, how to read a violation, and what is forbidden when one is exceeded.

## Declaring budgets

Budgets live in `project.yaml` under `budgets`. Declare them at the point the engine target is chosen, not after the build gets slow.

```yaml
budgets:
  max_atlas_dimension: 2048
  max_texture_memory_mb: 64
  max_total_asset_bytes: 12000000
  max_single_asset_bytes: 512000
  max_draw_calls: 120
```

Choosing starting values:

- **max_atlas_dimension** — the lowest maximum texture size across supported devices, not the highest. 2048 is safe almost everywhere; 4096 excludes older mobile GPUs; 8192 is a desktop-only decision.
- **max_texture_memory_mb** — a fraction of the device budget, not all of it. Textures compete with audio, meshes, and the engine itself. For a 2D web game, 32–64 MB is a realistic ceiling; mobile is tighter than that.
- **max_total_asset_bytes** — driven by acceptable download or install size, which is a product decision, not a technical one. Ask what load time is acceptable on the slowest supported connection and work backwards.
- **max_single_asset_bytes** — catches the one accidental 4096×4096 background that quietly doubles the build.
- **max_draw_calls** — only meaningful when the engine reports it. Leave it undeclared rather than guessing; `INSUFFICIENT_EVIDENCE` is more honest than a made-up number.

An undeclared budget is not a passing budget. `budget_check.py` reports `INSUFFICIENT_EVIDENCE` for each undeclared limit, and a set of budgets that is entirely undeclared produces `integration_blocked`.

## Measuring

Never assert a budget figure that was not measured.

```bash
python3 scripts/budget_check.py --project-root . --target-id web-main
```

The texture memory figure is `width × height × 4` bytes summed across assets: the uncompressed RGBA8 ceiling with no mipmaps. It is deliberately pessimistic.

- If the engine compresses textures, actual residency is lower. Record the compression format in `import-settings.yaml` and describe this figure as a ceiling.
- If the engine generates mipmaps, actual residency is roughly one third higher. Mipmaps on 2D sprites are usually a mistake; if they are enabled deliberately, note the multiplier.
- File size on disk is not texture memory. A 40 KB PNG can be 4 MB resident. Both matter, for different reasons: file size is download cost, texture memory is runtime cost.

## Reading a violation

A `FAIL` names a number, not an owner. Determine the owner before routing.

1. **Is the budget itself wrong?** A budget set without evidence, or set for a different target, is a declaration defect. Fix `project.yaml` with the owner's approval and re-measure. Do not quietly raise a budget to make a check pass — record who approved the change and why.
2. **Is one asset responsible?** `largest_asset_id` usually answers this. A single oversized asset is normally a planning defect: the runtime footprint in its AssetSpec was specified larger than the asset needs to be.
3. **Is the set responsible?** Many correctly sized assets that collectively exceed the budget is a decomposition question — are there variants that should be produced by runtime tinting, a shader, or a transform rather than as separate images?
4. **Is packing responsible?** Poor atlas grouping wastes area on padding and empty regions. That is this stage's defect and this stage's fix.

## Forbidden responses

Do not do any of these to make a budget pass:

- **Re-encode or recompress an approved asset.** The QC verdict is bound to a `content_hash`. Changing the bytes invalidates the approval, and a lossy re-encode changes approved pixels without anyone reviewing the result.
- **Resize a normalized asset.** Scale is a normalization decision bound to the AssetSpec footprint. Changing it here breaks family alignment silently.
- **Drop an asset from the atlas and call the budget met.** The asset still loads; it just loads worse.
- **Report a compressed figure the script did not measure.**
- **Raise the budget without recording who approved it.**

The correct response to a budget that cannot be met with the current asset set is a rework handoff upstream, not a local workaround. `DECOMPOSITION_DEFECT` and `REPRESENTATION_STRATEGY_DEFECT` both exist for exactly this.

## Reduction strategies, in preference order

When the owner asks how to get under budget, prefer changes that do not touch approved pixels:

1. **Better atlas packing** — tighter grouping, fewer half-empty atlases. Free.
2. **Runtime tinting instead of colour variants** — one asset plus a colour multiply replaces N recolours. A planner change, cheap to make.
3. **Nine-slice instead of full-size panels** — a 32×32 corner set replaces a 512×512 panel. A planner change.
4. **Shader or particle instead of baked frames** — for FX especially, this often removes an entire family.
5. **Reduced source resolution in the AssetSpec** — a planner change that requires regeneration and re-QC. Real cost, but honest.
6. **Texture compression** — engine-level, changes appearance subtly, requires a runtime validation pass on affected assets.
7. **Dropping content** — a product decision, never an integration decision.

The first four cost no regeneration. Reach for them before anything that invalidates an approval.

## Budget regression

Re-run `budget_check.py` whenever the asset set changes, not only when something feels slow. A budget check is cheap; discovering the violation after a build is not.

Record the measured figures in each `budget-report.yaml` so the trend is visible across versions. A budget that has been at 95% for three versions is a budget that is about to fail.
