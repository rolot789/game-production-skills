# Handoff and Promotion Policy

## Purpose

Define deterministic specialist handoffs and promotion gates so the orchestrator advances only authoritative artifacts with sufficient evidence.

## Handoff contract

A handoff should identify:

- sender and receiver,
- subject type/id,
- authoritative input versions,
- readiness gate/status,
- requested action,
- change scope,
- preserve scope,
- expected outputs,
- downstream revalidation requirements,
- blocker conditions.

Example:

```yaml
handoff_id: HND-0104
from: art-style-builder
to: game-asset-planner
subject:
  type: project
  id: GAME
inputs:
  game_spec: spec/game-spec.yaml@v7
  art_style: art/art-style.yaml@v5
  anchors: art/style-anchor-manifest.yaml@v4
  constraints: art/style-constraint-ledger.yaml@v3
readiness:
  game_spec: ASSET_PLANNING_READY
  art_style: ASSET_GENERATION_READY
request:
  action: compile_asset_manifest_and_specs
change_scope:
  - initial_planning
preserve_scope:
  - locked_gameplay_semantics
  - locked_art_direction
```

## Gate validation

A gate is satisfied by state/evidence, not by file existence.

### Art style to planning/generation

Require relevant locked style rules and, when used:

- approved scoped anchors,
- sufficient reference grounding,
- applicable locked negative constraints,
- no production-blocking reference conflict.

Search results still marked discovery-only must not be treated as anchors.

### Planning to generation

Require:

- planned asset exists in manifest,
- required spec fields are resolved,
- family topology/canonical parent is known where applicable,
- required upstream style authority is available.

### Generation to normalization

Require an actual selected candidate and truthful provenance. `ready_for_external_generation` is not equivalent to `GENERATED`.

### Normalization to QC

Require a runtime candidate plus normalization record for the same candidate version.

### QC to runtime

Require QC status permitted by project policy and ensure the runtime candidate matches the QC-approved version.

### Runtime to shipping

Only these may promote:

- `runtime_approved`
- `runtime_approved_with_minor_findings`

These may not promote:

- `partial_validation_only`
- `runtime_rework_required`
- `runtime_blocked`

## Version matching

Do not combine approval artifacts from different versions.

Invalid example:

```text
generated candidate v6
+ QC report for v5
+ runtime report for v4
→ SHIPPABLE  X
```

Promotion requires a coherent lineage.

## Preserve/change during handoff

Rework handoffs are deltas, not fresh production requests.

The receiver must know which passing dimensions are protected.

Example:

```yaml
request:
  action: regenerate
  change_scope:
    - texture_density
  preserve_scope:
    - identity
    - silhouette
    - palette
    - line_weight
```

If a downstream skill cannot honor the preserve scope, it should report the conflict before performing broad rework.

## Revalidation map

Typical minimum rerun surfaces:

| Changed owner/surface | Preserve | Revalidate |
|---|---|---|
| Generation visual | upstream specs/style | normalization, QC, affected runtime |
| Normalization only | generated visual | QC, affected runtime |
| QC classification only | asset files | runtime/promotion as needed |
| Runtime integration only | generation, normalization, QC | affected runtime contexts |
| AssetSpec visual semantics | GameSpec/style unless changed | generation onward |
| Scoped ArtStyle rule | unrelated categories/families | dependent planning if required, generation onward |

Treat this table as default routing, not a substitute for dependency analysis.

## Family promotion

Do not automatically promote an entire family because one canonical asset passes.

Use staged expansion:

```text
canonical parent approved
→ representative variants approved
→ family expansion
→ family summary
```

A family may be considered production-ready only when required members meet their required lifecycle states.

## Partial production

The orchestrator may mark a subset `SHIPPABLE` while other non-required or later-tier assets remain in progress if the project shipping definition permits it.

Do not claim the entire production pipeline is complete while required subjects remain blocked/rework.

## Human approval boundaries

Require human confirmation when the handoff changes creative authority rather than merely executing a locked contract.

Examples requiring confirmation:

- locking art direction,
- approving calibration anchors,
- broad L4 art-direction reset,
- accepting a systemic runtime fix that changes locked visual hierarchy.

Examples not normally requiring confirmation:

- retrying a failed export,
- rerunning QC after deterministic normalization fix,
- revalidating one runtime scene after z-order correction.

## Handoff history

Preserve enough history to reconstruct why a specialist ran.

Recommended location:

```text
.pipeline/handoffs/
```

or an equivalent append-only section in pipeline state.

Do not depend on chat history as the only record of production routing.
