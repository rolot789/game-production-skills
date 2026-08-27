# Gate Family — GameSpec (slice)

Human-readable view of `spec/game-spec.yaml`. The YAML is the source of truth; this document exists so a person can read the decisions without parsing a schema.

This is a **slice**: it covers only what the gate asset family depends on. A real GameSpec covers the whole game.

## Premise

A top-down puzzle game. The player routes power through a facility; gates open when their adjacent switch is powered.

## Camera and display

| Decision | Value | State |
|---|---|---|
| Projection | orthographic top-down | LOCKED |
| Tile size | 64 px | LOCKED |
| Target context | desktop browser, 1280×720 minimum | LOCKED |

Tile size is why every gate asset declares a 64×64 intended display size, and why readability is judged there rather than at the 256 px source canvas.

## The gate

Blocks a corridor until its adjacent switch is powered. Footprint 1×1 tile. The player never interacts with it directly — state is driven entirely by the switch.

### States

All three are **decision-critical**: the player decides whether to route power here before committing to walking down the corridor, so each state must be readable from across the room.

| State | Meaning | Encoded by |
|---|---|---|
| `closed` | traversal blocked | shape, value |
| `transition` | changing; traversal not yet permitted | shape, motion |
| `open` | traversal permitted | shape, value |

The encoding column is a requirement, not a description. Hue is deliberately absent from all three: the accessibility baseline below forbids carrying a decision-critical distinction on colour alone.

### Orientation — NOT_APPLICABLE

The level grammar places gates on one axis only, so a vertical variant would be an asset no level can reach.

Recorded as `NOT_APPLICABLE` rather than left unanswered. The difference matters: `UNRESOLVED` means "we have not decided", `NOT_APPLICABLE` means "this game will never need it". A later reader cannot reconstruct which was meant from silence.

## Backgrounds

| Surface | Value |
|---|---|
| Corridor floor | `#1B1F24` |
| Chamber floor | `#3A4149` |

Both are declared because both are backgrounds a gate is drawn against, and contrast is measured against the worst of them.

## Accessibility baseline — LOCKED

```yaml
min_contrast_ratio: 3.0
color_vision_modes: [protanopia, deuteranopia, tritanopia]
require_non_color_channel: true
```

Gate state drives a movement decision. A distinction carried by hue alone would fail for roughly one player in twelve.

This baseline is not a statement of intent — it is verified downstream. `game-asset-qc` measures all three checks via `technical_check.py`, and a failure routes to whichever upstream contract is deficient. That is exactly what happened here: see `.pipeline/handoffs/HND-0001.yaml`.

## Readiness

| Gate | Status |
|---|---|
| VISION_READY | PASSED |
| PROTOTYPE_READY | PASSED |
| ART_HANDOFF_READY | PASSED |
| ASSET_PLANNING_READY | PASSED |
| PRODUCTION_READY | PASSED |

## Open questions

**OQ-001** — does a locked gate need a distinct "permanently sealed" state? `UNRESOLVED`, non-blocking. Confirming it would add a fourth family member.

Left explicit rather than resolved, because it does not block the current milestone and guessing it would create an asset nobody asked for.
