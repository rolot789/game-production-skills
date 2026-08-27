# MRAU Decomposition Policy

## Purpose

Decide where one asset ends and the next begins. This is the highest-leverage decision in the pipeline and the most expensive to reverse: every generation, normalization, QC report, and runtime approval downstream is a descendant of it. Getting it wrong does not produce a bad asset, it produces a whole family of assets that cannot express what the game needs.

## The test

A Minimum Reusable Asset Unit is something the runtime must be able to independently **place, swap, animate, hide, reuse, or state-control**.

Ask, for each candidate boundary:

1. Does the runtime ever need to move one part without the other?
2. Does one part change state while the other does not?
3. Is one part reused somewhere the other is not?
4. Does one part animate on a different clock?
5. Does one part need a different z-order relative to a third object?
6. Does one part have a different lifetime — loaded, unloaded, or streamed separately?

One clear `yes` means separate units. All `no` means one unit.

The question is always about **runtime responsibility**, never about how the concept art was drawn or how a screenshot happens to crop.

## The two failure modes

Both are expensive, and they fail differently.

### Under-decomposition: one asset that should have been several

The classic case is a door with a lock icon baked into the sprite. The moment the game needs "locked door" and "unlocked door" to be the same door, the asset cannot express it, and the fix is a regeneration of the whole family rather than a runtime toggle.

Symptoms that appear later:

- QC reports state readability failures the generator cannot fix, because the states differ by a detail that should have been a separate overlay,
- runtime asks for a variant that does not exist and someone generates a near-duplicate,
- the asset count grows combinatorially because every combination of two independent properties became its own image.

The combinatorial tell is the strongest signal: if you find yourself planning `door_locked_north`, `door_unlocked_north`, `door_locked_south`, `door_unlocked_south`, the lock is a separate unit and the direction is a variant. Four assets became two.

### Over-decomposition: several assets that should have been one

Splitting a character into head, torso, and limbs when the game never animates them independently produces alignment problems that no single asset has: three pivots that must agree, three normalization records to keep in sync, three QC verdicts, and a family alignment constraint that did not need to exist.

Symptoms:

- normalization needs a shared scale basis for parts that are always drawn together,
- runtime always composites the same set in the same arrangement,
- a change to one part always requires regenerating the others to match.

If the runtime always draws them together in a fixed arrangement, they are one unit.

## Runtime semantics, not screenshot crops

Plan from what the game *does*, not from what a reference image *shows*.

A reference screenshot of a level shows a wall, a torch, and a glow. That is three things visually and may be one, two, or three assets:

- if the torch never moves independently of the wall → the torch is part of the wall asset,
- if the glow pulses on its own clock → the glow is a separate unit, probably a shader or particle rather than an image,
- if torches appear on many wall types → the torch is a separate unit and the wall is a background.

The screenshot cannot answer any of these. The GameSpec can.

## States are units too

Convert game rules into visible states before deciding decomposition. A gate whose rule is "blocks movement until the switch is pressed" needs, at minimum:

```text
closed        traversal blocked
open          traversal permitted
```

and probably a transition, because the player needs feedback that their action worked.

The decomposition question is whether those states are:

- **separate assets in a family** — when the geometry genuinely differs (a gate whose panel slides away),
- **one asset plus a runtime transform** — when the difference is position, rotation, or opacity,
- **one asset plus an overlay unit** — when the difference is an added marker that also appears elsewhere,
- **one asset plus a runtime tint** — when the difference is colour only, and colour is *not* the sole channel carrying the meaning.

Prefer the cheapest option that the locked style permits. Each additional generated state costs a generation, a normalization, a QC pass, and a runtime check, and adds a family invariant that can drift.

## Variant expansion without Cartesian products

Expand only combinations the game actually reaches.

```text
states:      closed, open, transition          3
directions:  north, south                      2
                                              ---
naive product                                  6
```

Before accepting 6, ask:

- Is `transition` directional? Often it is not — one transition reads for both.
- Is `south` a mirror of `north`? If the style permits mirroring, it is a runtime transform, not an asset.
- Does the game ever place a south-facing gate? If the level design never does, it is not in scope.

Six can easily be three. Record *why* each combination was dropped, so a later reviewer does not "restore" a variant that was deliberately excluded.

## Family topology follows decomposition

Once the units exist, declare which one is canonical. The canonical parent is the member that carries the most stable identity and geometry with the fewest state-specific distortions — usually the neutral or default state, not the first one someone asked for.

Record for every derivative what may change and what may not:

```yaml
family:
  canonical_parent: AST-GATE-CLOSED
  must_preserve: [outer_frame_geometry, top_view_projection, palette_family, footprint]
  must_change: [panel_position]
  may_vary: [panel_shadow_shape]
  must_not_introduce: [new_ornament, extra_hinge]
```

This block is what makes downstream rework deterministic. Without `must_preserve`, a regeneration of one state is free to drift on every dimension, and QC has no contract to check family coherence against.

## When to block instead of decomposing

Block and route to `game-spec-builder` when:

- two states have no defined gameplay distinction — you cannot decompose meaning that does not exist,
- the asset would have to communicate information the spec never assigned to it,
- direction or orientation semantics contradict between screens.

Guessing here is the most expensive guess in the pipeline, because it is the one every later stage inherits.
