---
name: game-asset-generator
description: Generate game-art candidates from production asset specs and approved style references. Compile prompts without redesigning upstream decisions, resolve scoped reference roles, preserve family invariants, and record generation provenance for deterministic regeneration and downstream normalization.
---

# Game Asset Generator

## Purpose

Execute visual generation from an already compiled AssetSpec. **Compile, do not improvise.** Do not redesign game mechanics, art direction, state semantics, scale rules, or family structure.

```text
AssetSpec + ArtStyle + Approved References
→ Reference Resolution
→ Prompt Compilation
→ Generation Job
→ Candidate(s)
→ Generation Record / Provenance
```

## Reference roles

Resolve references by scope: `identity_anchor`, `style_anchor`, `geometry_anchor`, `palette_anchor`, `state_parent`, `direction_parent`. A character identity anchor does not automatically govern UI geometry.

## Prompt model

Compile `Global Style + Category Override + Asset Spec + Scoped References + Negative Constraints`. Preserve family invariants such as identity, proportions, camera, scale, anchor, palette, and shared geometry. Generate related states/directions from a canonical parent/seed when possible instead of independent generations.

## Provenance

For every candidate record asset ID, job/prompt version, reference versions, generation capability/tool/model when exposed, output path, deviations, and status. If generation is unavailable, emit a truthful `ready_for_external_generation` job rather than claiming an image exists.

## Regeneration

When a candidate fails, change only the failed dimension where possible. Do not rewrite the whole prompt and cause uncontrolled drift.

## Outputs

```text
generation/<asset-id>/
├── job.yaml
├── prompt.md
├── candidates/
├── records/
└── candidate-index.yaml
```
