# Representation Strategy Policy

## Purpose

Decide *how* each planned unit gets produced. The strategy determines what the asset can do at runtime, what it costs to change, and whether the locked art style can survive the trip.

The default failure is treating every visual element as a generated PNG. That is the most expensive option on almost every axis — file size, memory, regeneration cost, and flexibility — and it is frequently the wrong one.

## The options

| Strategy | Use when | Cost to change later |
|---|---|---|
| `generated_raster` | authored texture, contour irregularity, or painterly fill is production-critical | high — regenerate, renormalize, re-QC |
| `generated_vector` | crisp scaling matters and the style is geometric | medium |
| `generated_3d` | the game renders 3D, or 2D frames are baked from a model | high |
| `procedural` | the form follows a rule that code can express | low — change the rule |
| `runtime_primitive` | a rectangle, line, or circle genuinely satisfies the locked style | trivial |
| `runtime_text` | typography is rendered live and no authored lettering is required | trivial |
| `shader_or_particle` | behaviour is continuous and parameterized rather than a fixed image | low |
| `reuse_existing` | an approved asset already satisfies this contract | none |

## Decide against locked style, not against convenience

The binding question is: **which style dimensions materially depend on authored media?**

Work through the locked ArtStyle and constraint ledger for the asset's category and list the dimensions that are production-critical. Then ask whether the candidate strategy can reproduce each one.

```text
locked: "contours carry restrained hand-drawn irregularity"
→ runtime_primitive CANNOT reproduce this. A drawn rectangle is mechanically perfect
  by construction, which is exactly what NEG-LINE-001 forbids.
→ generated_raster or generated_vector with authored path data.

locked: "UI separators are mechanically precise 1px rules"
→ generated_raster is wasteful and will resample badly.
→ runtime_primitive.

locked: "glow intensity responds to charge level"
→ no static image can do this. Baking N frames is a workaround, not a strategy.
→ shader_or_particle.
```

If the chosen strategy cannot satisfy a locked `HARD_FORBIDDEN`, a `BOUNDED` range, an approved anchor, or a category rule, **the plan is invalid**. Revise it before generation rather than discovering it in QC, where the finding routes back here anyway having burned a generation cycle.

## Do not rasterize what the runtime can do

Turning runtime-capable elements into PNGs is the most common planning waste in this pipeline. Each one costs generation, normalization, QC, memory, and download size, and buys nothing.

Reach for the runtime when:

- **Text** is text. Baked lettering cannot be localized, cannot reflow, and blurs at non-integer scales. Bake it only when the style requires authored letterforms that no available font provides — and record that reason.
- **Solid shapes** are solid shapes. A 512×512 PNG of a rounded rectangle is 40 KB of nothing.
- **Colour variants** are tints. One asset plus a runtime multiply replaces N recolours — *unless* colour is the only channel carrying a gameplay distinction, in which case the variants need a second channel anyway and the whole approach is wrong.
- **Mirrored directions** are transforms, when the style permits mirroring. Some do not: asymmetric lighting, handedness, or readable text on the asset all forbid it. Check before assuming.
- **Panels and frames** are nine-slice. A 32×32 corner set replaces every panel size the UI will ever need.
- **Continuous effects** are shaders or particles. Baking a 12-frame glow loop produces 12 assets that must stay coherent, and a family invariant that will drift.

## Do not proceduralize what needs authorship

The inverse error is real too. Reaching for `procedural` or `runtime_primitive` because it is cheaper produces assets that quietly violate the locked style, and the violation is systemic rather than local — every asset made that way is wrong the same way.

The tell is a style rule that describes *irregularity*, *tactility*, or *material*: "hand-drawn", "wax crayon", "torn paper", "brush texture". Those are authored properties. Code can approximate them, but the approximation is a new art direction, and nobody approved it.

## Derivation mode

Strategy pairs with `derivation_mode`, which decides how a family member relates to its parent:

- `independent` — generated from the contract alone. Only for canonical parents and genuinely unrelated assets.
- `parent_derived` — generated with the canonical parent as structural input. The default for states and directions.
- `reference_edit` — the parent image is edited rather than regenerated. Strongest identity preservation; use when identity drift has already occurred once.
- `procedural` — derived by a deterministic transform of the parent.

For any family where identity or geometry must stay stable, `independent` is the wrong mode for derivatives. It is how a gate's three states end up with three different frame widths.

## Cost asymmetry to weigh

Not all strategies are equally expensive to *revise*, and revision is certain:

```text
change a shader parameter          seconds, no revalidation beyond the affected context
change a procedural rule           minutes, regenerate derived assets
change a nine-slice corner         one regeneration, one normalization, one QC
change a generated raster family   N regenerations, N normalizations, N QC passes,
                                   plus family coherence re-verification
```

When two strategies both satisfy the locked style, prefer the one that is cheaper to revise. Art direction changes. Planning for the version that never changes is planning for a project that does not exist.

## Record the rationale

Every non-obvious strategy choice records why:

```yaml
production:
  strategy: generated_raster
  derivation_mode: independent
  strategy_rationale: >-
    NEG-LINE-001 forbids mechanically uniform contours; runtime_primitive cannot
    produce the required irregularity. Vector was rejected because the locked
    texture rule needs raster grain.
```

Without this, a later reviewer sees an expensive choice with no justification and either reverses it — reintroducing the style violation — or preserves it out of caution long after the reason expired.
