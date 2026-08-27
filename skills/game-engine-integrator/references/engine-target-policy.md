# Engine Target Policy

## Purpose

The same normalized PNG imports differently into Unity, Godot, Unreal, and a web canvas. This policy records what each target needs from the pipeline so import settings are derived rather than guessed, and so a limitation is recorded rather than silently absorbed.

## What every target needs

Regardless of engine, an import contract must resolve four things, and all four come from recorded upstream truth:

| Setting | Source | Never |
|---|---|---|
| pivot | `normalization-record.yaml` → `geometry.runtime_pivot` | re-decided here |
| scale basis | `project.yaml` → `engine.pixels_per_unit` | inferred from image size |
| filter mode | locked ArtStyle rendering rules | defaulted per engine |
| colour space | `project.yaml` → `engine.color_space` | left implicit |

If a target cannot express one of these, record the limitation in `integration-plan.yaml` and route it. Do not round a pivot to the nearest value the engine likes and move on — a half-pixel pivot error shows up as jitter during animation, and it will be diagnosed as a normalizer defect that does not exist.

## Unity

- **Pivot** maps to `SpriteRenderer` custom pivot in normalized 0–1 coordinates, matching `runtime_pivot` directly. Unity's Y axis runs bottom-up while the normalization record uses top-down image coordinates: `unity_pivot_y = 1.0 - runtime_pivot_y`. Record the conversion explicitly in `import-settings.yaml`; an unrecorded axis flip is the most common integration bug in this pipeline.
- **Pixels Per Unit** must be identical across a family, or family members render at different world sizes despite sharing a canvas.
- **Filter Mode** — `Point (no filter)` for pixel art, `Bilinear` otherwise. `Trilinear` implies mipmaps.
- **Compression** — `None` preserves approved pixels. Any other setting is a lossy change to a QC-approved asset and needs a runtime validation pass.
- **Sprite Mode** — `Single` for one asset per file, `Multiple` only when the pipeline produced a sheet.
- **Mesh Type** — `Full Rect` for UI and nine-slice; `Tight` saves fill rate but can crop glow that the approved asset depends on.

## Godot

- **Pivot** is the `offset` on `Sprite2D`, expressed in pixels rather than normalized coordinates: `offset = -(runtime_pivot * canvas_size)`. Record the pixel value alongside the normalized one.
- **Filter** is set per-texture via the import dock (`Filter` off for pixel art) and can also be overridden per-node; declare which layer owns the decision so the two do not disagree.
- **Texture region and atlas** — Godot's `AtlasTexture` needs the region rect for each member, which the atlas manifest already records.
- **Import presets** should be committed with the project so the settings survive a re-import; an uncommitted `.import` file means the contract exists only on one machine.

## Unreal

- 2D sprites go through Paper2D; pivot maps to the sprite's `PivotMode` with `Custom` plus the pixel position.
- **Texture Group** matters more than individual compression settings; `UI` disables mipmaps and sets appropriate compression.
- **sRGB** must be on for colour textures and off for masks and data textures. Getting this wrong changes every value in the asset and reads as an art-direction failure.

## Web canvas / DOM

- There is no import step, so the contract lives in the loader: record the pivot and scale as data the runtime reads, not as engine metadata.
- **Device pixel ratio** is the equivalent of pixels-per-unit. An asset normalized for 1× that renders on a 2× display either upscales blurrily or needs a 2× source; decide which at planning time, not integration time.
- **`image-rendering: pixelated`** is the CSS equivalent of point filtering and must match the locked art style.
- Atlases are usually a single sprite sheet plus a JSON frame map; the atlas manifest is that map.

## Recording limitations

When a target cannot honor a pipeline decision, `integration-plan.yaml` records it explicitly:

```yaml
limitations:
  - asset: AST-GATE-OPEN
    requested: runtime_pivot [0.5, 0.83]
    achievable: [0.5, 0.8]
    reason: target quantizes pivot to 0.05 increments
    impact: up to 2 px vertical offset at 128 px display size
    routed_to: game-asset-normalizer
    reason_code: IMPORT_SETTING_DEFECT
```

An unrecorded limitation becomes an unexplained runtime finding three stages later. Recording it costs four lines and saves a full diagnosis cycle.

## Cross-target projects

When one project ships to more than one target, produce one `engine-integration/<target-id>/` directory per target rather than a merged one. Budgets, filter modes, and atlas dimensions differ per target, and a merged plan hides which target a violation belongs to.

Shared truth stays upstream: the same normalized assets and the same QC approvals feed every target. Only the integration layer forks.
