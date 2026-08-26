---
name: game-asset-qc
description: Evaluate normalized game assets before runtime integration. Check technical conformance, art-style adherence, family consistency, state readability, gameplay readability, and production readiness; produce structured pass/fail results and route failures to the correct upstream owner.
---

# Game Asset QC

## Purpose

Judge assets as production game assets, not isolated illustrations. Evaluate against AssetSpec, locked ArtStyle, normalization record, runtime file, approved anchors, canonical family reference, and sibling variants where applicable.

## QC dimensions

- Technical Conformance
- Semantic Correctness
- Art Style Adherence
- Identity Preservation
- Family Consistency
- State Readability
- Gameplay Readability
- Production Cleanliness

Use deterministic checks for file existence/format/dimensions/alpha/bounds/naming/canvas/metadata. Use visual judgment for style, silhouette, identity, state separation, hierarchy, excessive detail/noise, and generation artifacts.

Always inspect gameplay-critical assets at intended runtime display size, not only zoomed generation size. Family states must look like the same asset changing state, not unrelated generations.

## Severity / status

Severity: `BLOCKER`, `MAJOR`, `MINOR`, `NOTE`.

Status:
- `approved`
- `approved_with_minor_findings`
- `rework_required`
- `blocked`

Any BLOCKER blocks; MAJOR requires rework; MINOR may be approved with findings according to project policy.

## Failure ownership

- undefined/contradictory asset requirement → planner
- wrong visual/style/identity/state → generator
- dimensions/clipping/alpha/anchor/pivot processing → normalizer
- insufficient/contradictory locked style → art-style-builder/spec

QC does not modify the image. It produces evidence-backed findings, severity, root owner, and required action.
