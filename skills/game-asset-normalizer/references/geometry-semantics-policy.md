# Geometry Semantics Policy

## Purpose

Three points get collapsed into one whenever someone is in a hurry, and the resulting bugs are diagnosed as art problems for weeks. This policy keeps them separate and says how each is chosen.

## The three points

### `visual_anchor`

Where the content *appears* to be centered. A perceptual reference, derived from the alpha bounding box after placement.

Used for: aligning family members so state switching does not visually jump, and for deciding whether padding is balanced.

Not used for: runtime transforms. Nothing in the engine should read this.

### `runtime_pivot`

The origin the engine uses for position, rotation, and scale. Expressed in normalized canvas coordinates.

Used for: everything the engine does with the transform.

This is the one that causes jitter when it is wrong. A character whose pivot sits at the canvas center rather than at the feet will slide vertically whenever the sprite's height changes between animation frames, and the bug reads as "the animation is bad" rather than "the pivot is wrong".

### `collision_origin`

Where gameplay physics considers the object to be. Often *not* the same as either of the above.

A tree sprite is 256 px tall, its visual anchor is in the canopy, its runtime pivot is at the trunk base, and its collision origin is a small circle at the trunk base — but the collision shape does not have to be centered on the pivot at all.

Only define this when the project separates it. If gameplay uses the pivot as the collision origin, record that they coincide deliberately rather than leaving the field empty; the two statements mean different things to the next reader.

## Why collapsing them costs weeks

```text
symptom:    the character shifts down when the walk cycle starts
diagnosed:  animation frames are misaligned → routed to game-asset-generator
actual:     idle and walk have different content heights, and the pivot is
            content_center rather than bottom_center, so the "center" moves
            when the content changes
owner:      game-asset-normalizer
```

The generator regenerates the walk cycle. The jitter persists, because the frames were never the problem. That is two wasted cycles, and it happens because one number was asked to mean two things.

## Choosing `pivot_policy`

Pick from the semantics of the object, not from what looks tidy on the canvas.

| Object behaves like | `pivot_policy` | Why |
|---|---|---|
| a character or prop standing on ground | `bottom_center` | ground contact stays fixed as height varies |
| a projectile or particle | `center` | rotation about the visual middle |
| a UI element in a layout | `center`, or a corner the layout anchors from | matches the layout system's own origin |
| a rotating part (a wheel, a turret) | explicit point at the axis | the axis is not the center |
| a family where members differ in height | `bottom_center` | the only choice that survives varying content |

The most common mistake is `center` on a standing character. It looks correct on the canvas and breaks the moment two states have different heights.

## Choosing `anchor_policy`

`anchor_policy` decides where content sits on the canvas; `pivot_policy` decides where the engine grabs it. They are independent.

- `content_center` — content is centered in the canvas. Fine for symmetric objects and most UI.
- `content_bottom_center` — content sits on the canvas bottom edge (inside padding). Correct for ground-standing objects, and it makes `bottom_center` pivots exact rather than approximate.
- `canvas_center` — geometric center of the canvas regardless of content bounds. Use when the canvas itself is meaningful, such as a fixed-size tile.

## Family alignment

Family members must share a **canvas basis** and a **scale basis**, or they will not switch cleanly at runtime.

The failure looks like this. Three gate states are normalized independently, each maximizing its own content within the canvas:

```text
closed      content 240 px tall → scaled to fill 240 px
transition  content 200 px tall → scaled to fill 240 px    ← 20% larger than it should be
open        content 160 px tall → scaled to fill 240 px    ← 50% larger than it should be
```

Each asset is individually correct and the family is broken. The gate appears to grow as it opens.

The fix is a shared scale basis, chosen from the family member with the largest content, and applied to every member:

```bash
# 1. measure the canonical parent
python3 scripts/normalize.py --candidate ... --spec ... --out ... --dry-run

# 2. apply its scale factor to every member
python3 scripts/normalize.py --candidate ... --spec ... --out ... --shared-scale 0.83
```

Record the shared basis in `family_lineage.shared_scale_basis` so a later re-normalization of one member does not silently revert to `fit_content`.

### Which basis to share

- **Scale basis** — always shared within a family whose members swap in place.
- **Canvas** — always shared. Different canvas sizes shift the pivot's meaning even when the pivot value is identical.
- **Baseline** — shared for anything ground-standing.
- **Pixel density** — shared, or the same asset reads as two different art styles.

A family that genuinely does not swap in place (icons used in unrelated screens) does not need a shared scale, but does still need a shared canvas if they share a layout slot.

## What the normalizer must not do about geometry

If the correct geometry cannot be achieved mechanically, that is a routing decision, not a permission to improvise:

- content does not fit the canvas at any scale that keeps it readable → the runtime footprint is wrong → `DECOMPOSITION_DEFECT`, owner `game-asset-planner`,
- required content is outside the alpha bounds → the candidate is incomplete → `CONTENT_ERROR`, owner `game-asset-generator`,
- the spec does not define pivot semantics for an object whose behaviour needs them → `DECOMPOSITION_DEFECT`, owner `game-asset-planner`,
- the pivot the engine can express differs from the one recorded → `IMPORT_SETTING_DEFECT`, owner `game-engine-integrator`.

Cropping content to make it fit, or nudging a pivot until it looks right, converts a diagnosable upstream defect into an undiagnosable downstream one.

## Recording

Every normalization record carries the geometry it produced:

```yaml
geometry:
  source_size: [1024, 1024]
  alpha_bbox: [112, 96, 916, 948]
  scale_factor: 0.293
  visual_anchor: [0.5, 0.472]
  runtime_pivot: [0.5, 1.0]
  collision_origin: null      # null means "not separately defined", not "unknown"
```

`normalize.py` computes all of these. Do not hand-write them: a recorded pivot that does not match the file is exactly the kind of quiet inconsistency the hash discipline exists to prevent.
