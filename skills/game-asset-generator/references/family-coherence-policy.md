# Family Coherence Policy

## Purpose

Generate related assets as a coherent family instead of treating every state, direction, pose, icon, or frame as an unrelated image request.

The family model exists to reduce identity drift, geometry drift, scale drift, and state inconsistency.

## Family topology

Determine the topology before generation.

Common patterns:

### `CANONICAL_PARENT_TO_STATES`

```text
base object
├── inactive
├── active
├── locked
└── disabled
```

### `CANONICAL_PARENT_TO_DIRECTIONS`

```text
front / canonical
├── left
├── right
└── back
```

### `PARENT_TO_ANIMATION`

```text
neutral pose
→ anticipation
→ action
→ recovery
```

### `STATE_TO_TRANSITION`

```text
closed
→ transition
→ open
```

### `INDEPENDENT_BUT_SHARED_STYLE`

Use only when members do not require shared identity/geometry beyond category-level style.

## Canonical parent selection

Choose the member that exposes the most stable identity and geometry with the fewest state-specific distortions.

A good canonical parent:

- shows the full silhouette clearly;
- contains all identity-critical features;
- uses the default camera/projection;
- avoids transient effects;
- has neutral or baseline state semantics;
- can be reused as a visual edit source when supported.

Do not automatically choose the first requested state.

## Family contract

Record invariants separately from allowed deltas.

```yaml
family:
  id: gate
  canonical_parent: gate-closed

  preserve:
    - outer_frame_geometry
    - top_view_projection
    - line_weight_family
    - palette_family
    - footprint

  allowed_delta_by_state:
    gate-open:
      - door_panel_position
      - opening_readability

    gate-transition:
      - door_panel_position
```

Without an explicit allowed delta, do not invent major structural differences between siblings.

## Identity and geometry preservation

For identity-sensitive families, prioritize in this order when capabilities allow:

```text
reference edit / image-to-image from canonical parent
> controlled variant generation from parent
> shared seed / shared structured job
> independent generation with repeated anchors
```

The exact provider mechanism may differ. The policy goal is to maximize shared visual evidence.

## Directional families

Direction variants must distinguish true rotation/orientation from independent redesign.

Preserve where applicable:

- body/head proportions;
- costume topology;
- accessory count;
- material/color assignment;
- camera elevation;
- ground footprint;
- line/texture treatment.

Allow only orientation-dependent visibility changes that follow geometry.

If an unseen side requires invention, mark the invented region and ensure it does not contradict known identity. For production-critical hidden geometry, route upstream if approval is required.

## State families

State differences should communicate semantics with the smallest sufficient visual delta.

Examples:

```text
locked vs available
→ lock treatment / value / approved state indicator
not a completely different asset style

closed vs open gate
→ geometry/state change
not unrelated decorations
```

If ArtStyle or AssetSpec defines the state-encoding channel, preserve it consistently across the family.

## UI and icon families

UI families often require tighter geometry consistency than illustration assets.

Preserve:

- bounding footprint;
- optical alignment;
- base plate geometry where shared;
- icon stroke hierarchy;
- state transition logic;
- runtime text separation when text is not baked into the asset.

Avoid regenerating each hover/disabled/selected state independently when the state can be produced deterministically from a parent or runtime treatment.

## Calibration before expansion

For a large family:

```text
canonical parent
→ one representative derived member
→ compare / screen
→ approve family contract
→ expand remaining members
```

Do not mass-generate 12 directions/states before proving the parent-to-child relationship works.

## Family screening matrix

Before promoting a family batch, compare siblings on at least:

```text
identity
proportions
projection/camera
silhouette family
line treatment
palette assignment
texture/material treatment
footprint/scale
state readability
forbidden extra details
```

Example:

```yaml
family_screening:
  gate-open:
    identity: PASS
    geometry_family: PASS
    palette: PASS
    state_readability: PASS

  gate-transition:
    identity: PASS
    geometry_family: FAIL
    palette: PASS
    state_readability: PASS
```

Regenerate only the failing member/dimension.

## Drift prevention

Do not accept the following merely because individual assets look polished:

- sibling states with different contour language;
- direction variants with changed costume/accessory topology;
- arbitrary color reassignment;
- different camera elevation or perspective;
- changing proportions between animation frames;
- extra decoration appearing only in one state without semantic reason;
- texture density changing randomly across family members.

## Family lineage

Record lineage explicitly.

```yaml
member: gate-open
parent: gate-closed
strategy: reference_edit
contract_version: 3
preserved_from_parent:
  - frame_geometry
  - line
  - palette
changed:
  - panel_position
```

Lineage is part of provenance and should survive normalization and QC where useful.

## Escalation

If a family cannot remain coherent through independent generation, do not keep sampling independently.

Escalate generation topology:

```text
independent generation
→ parent-derived generation
→ reference edit / deterministic transformation
→ upstream asset decomposition review
```

Sometimes the correct answer is that a variant should be produced procedurally or by runtime transformation rather than generated as another image.
