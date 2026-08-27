---
name: game-asset-generator
description: Generate game-art candidates from locked AssetSpec and ArtStyle artifacts without redesigning upstream decisions. Compile scoped approved anchors, reference evidence, category overrides, persistent negative constraints, family invariants, and provenance into generation jobs; detect style drift and regenerate only affected dimensions.
---

# Game Asset Generator

## Purpose

Execute visual generation from already-approved production inputs. **Compile, do not improvise.**

This skill is not an art director. It must not silently invent a new style, reinterpret gameplay semantics, broaden an approved reference, or compensate for missing upstream decisions with generic image-generation taste.

```text
AssetSpec
+ Locked ArtStyle
+ Style Anchor Manifest
+ Reference Corpus
+ Style Constraint Ledger
+ Category Overrides
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
        ↓
Selected Candidate → Normalization / QC
```

The primary objective is:

> Preserve the approved art system while changing only the asset-specific content required by the AssetSpec.

## Core principles

1. **Upstream truth wins.** Locked GameSpec, AssetSpec, ArtStyle, approved anchors, and locked constraints are authoritative.
2. **Reference scope is explicit.** A reference may govern line, palette, geometry, identity, texture, lighting, composition, UI treatment, or another declared dimension; it never governs unspecified dimensions by implication.
3. **User-provided and approved anchors outrank generic model priors.** Do not dilute them with generic aesthetic language.
4. **Negative constraints are executable production rules, not decorative prompt suffixes.** Pair them with positive counterparts where available.
5. **Category overrides modify only their declared dimensions.** Global style remains inherited elsewhere.
6. **Family coherence is planned, not hoped for.** Related states, directions, frames, icons, or character poses should derive from a canonical parent when possible.
7. **A candidate that is attractive but violates identity, style, state semantics, or family invariants is a failure.**
8. **Regenerate the smallest failing surface.** Do not rewrite the complete generation contract after a local failure.
9. **Record provenance truthfully.** Never fabricate model IDs, seeds, timestamps, reference downloads, or tool capabilities.
10. **Generation availability is not assumed.** If the runtime cannot generate the required media, emit a complete external-generation job instead of pretending an output exists.

## Required inputs

At minimum:

```text
asset-manifest.yaml
specs/<asset-id>.yaml
art-style.yaml
style-anchor-manifest.yaml
```

When produced by `art-style-builder` v2, also consume:

```text
reference-corpus.yaml
style-constraint-ledger.yaml
style-loop-state.yaml          # when relevant to current revisions
```

Do not require absent optional artifacts when equivalent locked information is already represented elsewhere, but never ignore them when present and applicable.

## Readiness checks

Before generating, verify:

- the target AssetSpec is `READY_FOR_GENERATION` or equivalent;
- required semantic states/directions are defined;
- the relevant ArtStyle readiness gate permits asset generation;
- production-critical anchor dimensions are resolved;
- required references are visually accessible when their role requires visual grounding;
- no `HARD_FORBIDDEN` constraint conflicts with the AssetSpec;
- category overrides are unambiguous;
- family/canonical-parent requirements are known.

If a blocker belongs upstream, stop and route it back. Do not solve an art-direction ambiguity inside this skill.

## Reference grounding

References are consumed through declared roles and governed dimensions.

Supported roles include, but are not limited to:

```text
identity_anchor
style_anchor
geometry_anchor
palette_anchor
line_anchor
texture_anchor
lighting_anchor
composition_anchor
ui_anchor
category_anchor
state_parent
direction_parent
animation_parent
```

For every resolved reference, compile:

```yaml
reference_id: REF-017
role: line_anchor
governs:
  - line.weight
  - line.irregularity
preserve:
  - restrained hand-drawn contour variation
do_not_inherit:
  - cinematic lighting
  - background composition
```

### Accessibility rule

A discovered URL is not automatically usable as a generation anchor.

- `PREVIEWABLE` / visually accessible references may be used when the generator can actually inspect or pass them to the generation capability.
- `LINK_ONLY`, `BLOCKED`, or `UNAVAILABLE` references may remain provenance/evidence records but must not be treated as unseen visual truth.
- Never claim a visual characteristic was verified from an inaccessible image.

## Generation contract

Compile a structured generation contract before writing any free-form prompt.

Recommended order:

```text
1. Asset identity and semantic purpose
2. Required geometry / silhouette / composition
3. Locked global style invariants
4. Applicable category overrides
5. Scoped approved anchors
6. Family / parent invariants
7. Positive rendering instructions
8. Negative constraints + positive counterparts
9. Output / transparency / framing requirements
10. Explicit non-goals and forbidden drift
```

The free-form prompt is a serialization of this contract, not the source of truth itself.

Read `references/generation-compilation-policy.md` when compiling jobs.

## Constraint compilation

Consume `style-constraint-ledger.yaml` by scope and severity.

### `HARD_FORBIDDEN`

A candidate exhibiting the pattern is not acceptable.

### `SOFT_AVOID`

Discourage unless another locked requirement requires it.

### `BOUNDED`

Preserve the feature within the declared range rather than eliminating it.

### `ANTI_REFERENCE`

Explicitly do not inherit a rejected dimension from a named reference.

Where possible, compile:

```text
AVOID <observable failure pattern>
PRESERVE / DO INSTEAD <approved positive behavior>
```

Do not reduce the ledger to vague phrases such as `not AI-looking`, `not generic`, or `make it professional`.

## Anti-generic / anti-AI-drift behavior

Treat generic image-model aesthetics as drift symptoms only when they conflict with locked style evidence.

Common diagnostics include:

- excessive glossy gradients on materials defined as matte;
- default cinematic rim lighting not present in approved anchors;
- purposeless micro-detail or ornamental segmentation;
- over-smoothed vector-like contours when handmade irregularity is locked;
- excessive bloom, glow, volumetric haze, or depth effects;
- generic mascot proportions overriding an identity anchor;
- arbitrary asymmetry or decorative noise introduced without style evidence;
- highly rendered surface detail that destroys small-size gameplay readability.

Do not blindly ban these patterns globally. Apply only constraints supported by the current ArtStyle / ledger.

## Family-first generation

When generating a family, determine a canonical parent first.

Examples:

```text
character neutral pose
→ directional variants
→ action poses

closed gate
→ transition frame
→ open gate

base icon
→ active
→ disabled
→ hover
```

Preserve family invariants such as:

- identity;
- proportions;
- camera/projection;
- silhouette logic;
- line hierarchy;
- palette family;
- material treatment;
- local scale and canvas footprint;
- state-specific geometry that should remain unchanged.

Prefer reference edit / parent-derived generation over independent redraws when the available generation capability supports it.

Read `references/family-coherence-policy.md` for family topology and acceptance rules.

## Candidate screening before downstream handoff

Generation is not full QC, but obviously invalid candidates should not be promoted merely because a file exists.

Screen for:

```text
semantic mismatch
identity drift
anchor-scope violation
hard negative-constraint violation
major family inconsistency
missing state differentiation
wrong camera/orientation
wrong required transparency/background
obvious composition/canvas failure
```

Record rejected candidates and reasons. Do not silently discard failed generations if provenance matters for later diagnosis.

## Regeneration / anti-drift loop

When a candidate fails, classify the failure before regeneration.

```text
CONTENT_ERROR
IDENTITY_DRIFT
STYLE_DIMENSION_DRIFT
CONSTRAINT_VIOLATION
FAMILY_DRIFT
STATE_READABILITY_FAILURE
OUTPUT_TECHNICAL_FAILURE
UPSTREAM_SPEC_AMBIGUITY
```

Then preserve every dimension that already passed.

Example:

```text
line            PASS
palette         PASS
identity        PASS
texture         FAIL: too dense
lighting        PASS

→ regenerate texture treatment only
→ preserve line/palette/identity/lighting contracts
```

Do not respond to a single failed dimension by replacing the whole prompt with a new artistic description.

Read `references/anti-drift-regeneration-policy.md` for failure ownership, delta contracts, and escalation rules.

## Prompt/version discipline

Every generation attempt should have stable versioned inputs.

Record at least:

```text
asset_id
job_version
asset_spec_version/hash when available
art_style_version/hash when available
anchor IDs + governed dimensions
constraint IDs + scopes
canonical parent / family lineage
compiled prompt version
runtime generation tool/capability when exposed
model identifier when exposed
seed when exposed
candidate path/reference
deviations
screening result
```

If the provider does not expose a field, store `unknown` / `not_exposed` rather than inventing it.

## Outputs

```text
generation/<asset-id>/
├── job.yaml
├── generation-contract.yaml
├── prompt.md
├── candidates/
├── records/
└── candidate-index.yaml
```

For families, optionally include:

```text
generation/<family-id>/
├── family-contract.yaml
├── parent-lineage.yaml
└── family-candidate-index.yaml
```

`generation-contract.yaml` is the structured source used to compile `prompt.md`.

## Completion criteria

A generation batch is ready for normalization/QC when:

- required candidates exist or an honest external-generation job is emitted;
- candidates preserve production-critical locked anchors;
- no known `HARD_FORBIDDEN` violation remains in the selected candidate;
- family invariants required at generation time are preserved;
- generation provenance is complete enough to reproduce or diagnose the attempt;
- unresolved failures are routed to their correct owner rather than hidden.
