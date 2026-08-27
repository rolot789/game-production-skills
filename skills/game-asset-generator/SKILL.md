---
name: game-asset-generator
description: Generate game-art candidates from locked AssetSpec and ArtStyle artifacts without redesigning upstream decisions. Compile scoped approved anchors, reference evidence, category overrides, persistent negative constraints, family invariants, provenance, and canonical rework scopes into generation jobs; detect style drift and regenerate only affected dimensions.
---

# Game Asset Generator

## Purpose

Execute visual generation from approved production inputs. **Compile, do not improvise.** The generator is not an art director and must not silently reinterpret gameplay semantics, broaden approved references, or replace missing upstream truth with generic image-model taste.

```text
AssetSpec
+ Locked ArtStyle
+ Style Anchor Manifest
+ Reference Corpus
+ Style Constraint Ledger
+ Category Overrides
+ Optional Rework Scope
        ↓
Input Validation
        ↓
Scoped Reference Resolution
        ↓
Generation Contract Compilation
        ↓
Generation Job
        ↓
Candidate(s)
        ↓
Drift / Constraint Screening
        ↓
Generation Record + Provenance
```

## Project path resolution

If `project.yaml` exists, use its `paths` registry as the canonical mapping for logical artifacts. Do not hard-code root paths that contradict the project registry.

## Core rules

1. Locked GameSpec, AssetSpec, ArtStyle, approved scoped anchors, and locked constraints are authoritative.
2. A reference governs only declared dimensions.
3. User-provided/approved anchors outrank generic model priors.
4. Negative constraints are executable rules, not prompt decoration.
5. Category overrides change only declared dimensions.
6. Families should derive from canonical parents when identity/geometry continuity matters.
7. Attractive but contract-violating candidates fail.
8. Regenerate the smallest failing surface.
9. Record provenance truthfully; never invent seed/model/timestamp/tool access.
10. If generation capability is unavailable, emit a complete external-generation job rather than pretending output exists.

## Required inputs

At minimum:

```text
asset-manifest.yaml
specs/<asset-id>.yaml
art-style.yaml
style-anchor-manifest.yaml
```

When present/applicable:

```text
reference-corpus.yaml
style-constraint-ledger.yaml
style-loop-state.yaml
project.yaml
```

For rework, consume the canonical handoff envelope defined by `contracts/rework-handoff-contract.yaml`:

```yaml
change_scope:
  dimensions: []
  artifacts: []
  runtime_properties: []

preserve_scope:
  dimensions: []
  artifacts: []
  upstream_truth: []
```

The generator may derive internal fields such as `change_dimensions`, but external handoffs remain canonical `change_scope / preserve_scope`.

## Readiness checks

Before generating, verify:

- AssetSpec is ready for generation,
- semantic states/directions are defined,
- ArtStyle gate permits generation,
- production-critical anchors are resolved,
- required references are actually accessible when visual grounding is necessary,
- no hard constraint conflicts with AssetSpec,
- category overrides are unambiguous,
- canonical parent/family rules are known,
- requested change scope does not contradict preserved upstream truth.

Route blockers upstream rather than solving art direction inside generation.

## Scoped reference grounding

References may act as:

`identity_anchor`, `style_anchor`, `geometry_anchor`, `palette_anchor`, `line_anchor`, `texture_anchor`, `lighting_anchor`, `composition_anchor`, `ui_anchor`, `category_anchor`, `state_parent`, `direction_parent`, or `animation_parent`.

Compile each reference with its governed and excluded dimensions. `LINK_ONLY`, `BLOCKED`, and `UNAVAILABLE` references may remain provenance/evidence but cannot be treated as visually verified truth.

## Generation contract

Compile `generation-contract.yaml` before any free-form prompt. Recommended order:

1. asset identity and semantic purpose,
2. geometry/silhouette/composition,
3. global style invariants,
4. category overrides,
5. scoped anchors,
6. family/parent invariants,
7. positive rendering rules,
8. negative constraints + positive counterparts,
9. output/transparency/framing,
10. explicit non-goals,
11. rework `change_scope / preserve_scope` when applicable.

`prompt.md` is a provider-facing serialization of the contract, not the source of truth.

Use `references/generation-compilation-policy.md` when compiling jobs.

## Constraint compilation

Consume `style-constraint-ledger.yaml` by scope and severity:

- `HARD_FORBIDDEN`: any occurrence is unacceptable when applicable,
- `SOFT_AVOID`: discourage unless another locked rule requires it,
- `BOUNDED`: retain only within approved range,
- `ANTI_REFERENCE`: do not inherit the rejected dimension from the named reference.

Prefer `AVOID <observable failure> / DO INSTEAD <approved behavior>` pairs. Do not use vague final rules such as `not AI-looking`.

## Family-first generation

Prefer canonical-parent derivation for related states/directions/poses. Preserve identity, proportions, projection, silhouette logic, line hierarchy, palette/material family, scale/canvas footprint, and state-invariant geometry.

Use `references/family-coherence-policy.md` for topology and acceptance rules.

## Candidate screening

Before downstream handoff, reject obvious failures involving:

- semantic mismatch,
- identity drift,
- anchor-scope violation,
- hard negative-constraint violation,
- major family inconsistency,
- missing state differentiation,
- wrong camera/orientation,
- wrong transparency/background,
- major composition/canvas failure.

Generation screening is not a substitute for QC.

## Delta regeneration

Classify failures before retry:

`CONTENT_ERROR`, `IDENTITY_DRIFT`, `STYLE_DIMENSION_DRIFT`, `CONSTRAINT_VIOLATION`, `FAMILY_DRIFT`, `STATE_READABILITY_FAILURE`, `OUTPUT_TECHNICAL_FAILURE`, `UPSTREAM_SPEC_AMBIGUITY`.

Preserve every already-passing dimension.

Escalation levels:

- `G0_SAME_CONTRACT_RETRY`
- `G1_LOCAL_DIMENSION_DELTA`
- `G2_REDERIVE_FROM_CANONICAL_PARENT`
- `G3_CHANGE_GENERATION_STRATEGY`
- `G4_ESCALATE_UPSTREAM`

`G4` does not grant permission to redesign ArtStyle. Use `references/anti-drift-regeneration-policy.md`.

## Version lineage

Every generation attempt should record, when available:

```text
asset_id
job_version
asset_spec version/hash
art_style version/hash
anchor IDs + governed dimensions
constraint IDs + scopes
canonical parent/family lineage
change_scope / preserve_scope
compiled prompt version
generation capability/model/seed when exposed
candidate path/id/hash
screening result
```

Unavailable fields remain `unknown` / `not_exposed`.

## Outputs

Logical outputs:

```text
generation/<asset-id>/
├── job.yaml
├── generation-contract.yaml
├── prompt.md
├── candidates/
├── records/
└── candidate-index.yaml
```

Family outputs may additionally include `family-contract.yaml`, `parent-lineage.yaml`, and `family-candidate-index.yaml`. Resolve actual paths through `project.yaml` when present.

## Rework output contract

If generation hands rework onward or escalates upstream, external routing data must serialize through `contracts/rework-handoff-contract.yaml`. Specialist-local aliases are allowed only inside internal reports.

## Completion criteria

A batch is ready for normalization/QC only when required candidates exist (or an honest external job exists), critical anchors are preserved, no known hard violation remains, family invariants are respected, provenance/version lineage is sufficient for diagnosis, and unresolved failures are routed to the correct owner.
