# Gate Family — ArtStyle (slice)

Human-readable view of `art/art-style.yaml`, currently at **v2**. The YAML is the source of truth.

## Global rules — all LOCKED

| Dimension | Rule |
|---|---|
| Dimensionality | 2D orthographic top-down |
| Shape language | blocky, few large forms, no ornament below 4 px at display size |
| Line | no outline; forms separate by value contrast at their edges |
| Palette | desaturated earth tones, warm mid-value structures on cool dark floors |
| Texture | restrained per-pixel value grain, bounded to ±8 of the base value |
| Lighting | flat — no directional shading, no rim light, no bloom |

## Palette — v2

| Role | v1 | v2 |
|---|---|---|
| frame | `#6D5E4E` | `#A89070` |
| frame shadow | `#4E4237` | `#7E6A52` |
| panel | `#B08458` | `#D8B085` |
| panel edge | `#8B6642` | `#B08A62` |
| bolt | `#D0BEA0` | `#F0E4CC` |

### Why v2 exists

v1 measured **2.41:1** against the chamber floor, below the 3.0 baseline the GameSpec declares.

QC found it, and routed it here rather than to the generator. That routing decision is the point: the candidates had implemented the v1 palette faithfully, so no amount of regeneration could have fixed it. The palette was the defect.

The rework handoff (`HND-0001`) constrained the fix tightly — `change_scope` was `palette.value_structure` alone, with `palette.hue_family` in `preserve_scope`. So v2 is brighter, not different. The warm earth family the project had already approved survived a contrast fix, which is not what happens when "fix the contrast" arrives without a preserve scope.

Measured at v2: 4.28, 3.86, 3.32 across the three states.

## Category override: `interactive_object`

| Rule | Value |
|---|---|
| Detail density | readable at 64 px; secondary cues must survive downscale |
| State encoding | state changes must alter silhouette, not only hue |

The state-encoding override exists because the GameSpec marks every gate state decision-critical and the project declares a colour-vision baseline. It is the reason the three gates differ by panel geometry rather than by colour.

## Negative constraints

Four, each with a positive counterpart — see `style-constraint-ledger.yaml`.

| ID | Type | Avoid | Do instead |
|---|---|---|---|
| NEG-LIGHTING-001 | HARD_FORBIDDEN | directional shading, rim light, bloom, glow | flat surfaces; separate forms by edge value contrast |
| NEG-TEXTURE-002 | BOUNDED | grain that competes with the silhouette at 64 px | value jitter within ±8 |
| NEG-DETAIL-003 | SOFT_AVOID | ornament that vanishes below 4 px | detail only on cues that survive downscale |
| NEG-STATE-004 | HARD_FORBIDDEN | hue-only encoding of a decision-critical state | change the panel silhouette; hue may reinforce, never carry |

Every one names an **observable** behaviour. "Don't make it look AI-generated" is not a constraint — it is a symptom report that has to be diagnosed into one of these before it can be verified by anyone.

## Anchors

Two, both project-owned, both scoped by dimension:

- **ANCH-GATE-GEOMETRY-001** governs frame proportion, thickness ratio, and opening aspect. Explicitly excluded from palette, texture density, and lighting.
- **ANCH-PALETTE-001** governs hue family and value structure. Explicitly excluded from shape language and detail density.

The exclusions carry as much weight as the grants. An anchor without stated exclusions tends to quietly govern everything it happens to depict.

No third-party reference was promoted to an anchor in this example. Had one been, the living-artist boundary in `reference-search-policy.md` would apply: name the source, prefer technique over signature, never encode a person's name as a prompt token, and record the decision here.

## Readiness

| Gate | Status |
|---|---|
| STYLE_DIRECTION_READY | PASSED |
| REFERENCE_GROUNDED | PASSED |
| CALIBRATION_READY | PASSED |
| ASSET_GENERATION_READY | PASSED |
