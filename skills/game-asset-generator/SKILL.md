---
name: game-asset-generator
description: Use when planned asset specs must become actual image candidates — "generate the sprites", "make this asset", "produce the icon set" — or when a rework handoff routes visual content back for regeneration. Compiles scoped anchors, negative constraints, and family invariants into a generation contract, screens candidates for drift, and regenerates only the failing dimension. Does not invent art direction or gameplay meaning; routes those upstream instead of guessing.
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

For rework, consume the canonical handoff envelope defined by `references/rework-handoff-contract.yaml`:

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

## Transparent background is the default

Game assets are cut out unless something says otherwise. `runtime.background_policy` defaults to `transparent`, so an AssetSpec that omits it wants a transparent background — do not read the omission as "unspecified" and do not ask.

Compile that into the generation contract as an explicit output requirement and use the target's transparency option directly. Do not rely on the phrase "transparent background" in prose to do the work: it also describes stock cutouts and editor screenshots, so a target that reads it as a *description* will paint a white background or a checkerboard and hand back a file that is technically RGBA and completely unusable.

Screen for it immediately, before anything downstream touches the candidate:

```bash
python3 skills/game-asset-generator/scripts/check_alpha.py \
    --candidate generation/AST-GATE-CLOSED/candidates/v1-c1.png
```

Four boolean tests over the alpha channel — channel present, some pixel fully transparent, all four corners transparent, transparent area above a floor. The corner test is the one that matters: it catches a painted-on background that the first two tests pass.

The value is in *when* this runs, not in how clever it is. The same defect is also caught by QC's `has_transparency`, but that is two stages downstream — after normalization has already processed a candidate that was never going to pass.

**A transparency failure is `G3_CHANGE_GENERATION_STRATEGY`, not `G1`.** Re-rolling the prompt is the trap here: a target that drew a background will draw one again, and the retry budget is gone before anyone questions the approach. Change how transparency is requested, or change the output strategy.

## Candidate screening

Run `check_alpha.py` first — it is deterministic and costs nothing. Then reject obvious failures involving:

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

## Generation budget

The expensive side of this pipeline is bounded like the cheap side. Defaults from `toolkit-contract.yaml` `generation_budget`:

```text
candidates per job                  <= 4     stop as soon as one passes every critical dimension
regeneration attempts per asset     <= 6     counted across all G-levels within one rework transaction
G0_SAME_CONTRACT_RETRY repeats      <= 2     a third identical retry blames the sampler for a contract defect
```

Two consecutive failures on the same dimension at one level escalate to the next level rather than repeat. Exhausting the attempt budget escalates to `G4_ESCALATE_UPSTREAM` and stops.

Stop generating when a candidate satisfies the production contract. "It might be prettier" is not a reason to spend another attempt — record a stylistic preference as an explicit revision request instead, so endless aesthetic sampling does not quietly replace a production decision.

## Version lineage

Every generation record must validate against `references/schemas/generation-record.schema.json` and record:

```text
asset_id
job_version                       vN
asset_spec        path + version + content_hash    (required)
art_style         path + version + content_hash    (required)
anchor IDs + governed dimensions
constraint IDs + scopes
canonical parent/family lineage
change_scope / preserve_scope
candidate id (vN-cM) + path + content_hash         (required)
screening result per critical dimension
provenance: capability, model, seed
```

Compute the candidate hash from the exact bytes written:

```bash
sha256sum generation/AST-GATE-CLOSED/candidates/v1-c2.png
```

Two rules that are not softened by circumstance:

- **Hashes and versions are required.** If one cannot be produced, emit a blocker rather than an unverifiable record. Every downstream invalidation decision rests on being able to prove whether an input changed.
- **Provenance is never invented.** `capability`, `model`, and `seed` record what actually happened. A provider that does not expose a seed gets `not_exposed`, never a plausible-looking number. If no generation capability was available at all, set `provenance.external_job: true` and emit a complete job for an external tool — do not describe a candidate that does not exist.

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

If generation hands rework onward or escalates upstream, external routing data must serialize through `references/rework-handoff-contract.yaml`, and `reason_codes` must resolve against `references/routing.yaml`. Specialist-local aliases such as `change_dimensions` are allowed only inside internal reports, never in a routed handoff.

Root ownership follows `references/routing.yaml`. Do not restate the routing table from memory; the classes this stage owns are `CONTENT_ERROR`, `IDENTITY_DRIFT`, `STYLE_DIMENSION_DRIFT`, `NEGATIVE_CONSTRAINT_VIOLATION`, `FAMILY_DRIFT`, and `STATE_READABILITY_FAILURE`.

## Completion criteria

A batch is ready for normalization/QC only when required candidates exist (or an honest external job exists), critical anchors are preserved, no known hard violation remains, family invariants are respected, provenance/version lineage is sufficient for diagnosis, and unresolved failures are routed to the correct owner.
