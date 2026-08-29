---
name: game-art-production-orchestrator
description: Use when the question spans the whole asset pipeline rather than one stage — "continue production", "what should we do next", "what's blocking us", "where did this break", "is this ready to ship" — or when a failure must be routed to its root owner. Enforces readiness gates, legal lifecycle transitions, version lineage, and dependency-aware invalidation across all eight stages. Does not perform any specialist's work itself — it decides who acts next, with which inputs, and what exactly may change.
---

# Game Art Production Orchestrator

## Purpose

Coordinate routing, gates, handoffs, lifecycle state, rework scope, invalidation, and promotion without duplicating specialist work.

```text
game-spec-builder
→ art-style-builder
→ game-asset-planner
→ game-asset-generator
→ game-asset-normalizer
→ game-asset-qc
→ game-engine-integrator
→ runtime-visual-validator
```

The orchestrator does not redesign art, write provider prompts, normalize pixels, perform QC, pack atlases, or visually approve scenes. It determines which specialist acts next, with which authoritative inputs, and what exact surface may change.

## Authoritative references

Read these rather than restating them from memory. They are mirrored into this skill so they resolve from any install location.

- `references/toolkit-contract.yaml` — stage order, enums, **legal lifecycle transitions**, lineage rules, generation budget, accessibility checks.
- `references/routing-index.yaml` — the compact lookup: decision procedure, then symptom class to root owner, invalidation scope, and revalidation scope. Read this first. `references/routing.yaml` is the full table and stays authoritative; open it when a row needs its description or note, when two classes look equally applicable, or when scope escalation, multi-owner, or `qc_escape` is involved.
- `references/rework-handoff-contract.yaml` — the canonical handoff envelope.

When this document and a contract disagree, the contract wins and the document is a bug.

## Profiles

`project.yaml` may declare `profile: lite` or `profile: full` (default `full`). The profile decides which stages are required and what the promotion ceiling is — see `contracts/profiles/`.

Under `lite`, `engine_integration` and `runtime_validation` are optional and the ceiling is `QC_APPROVED`. Do not route to an optional stage that the project has not asked for, and do not promote past the ceiling. `RUNTIME_APPROVED` still requires executable runtime evidence under either profile; a lite project that wants it runs the optional stage.

## Project path resolution

If `project.yaml` exists, its `paths` registry is the canonical artifact path map. Contract paths such as `specs/<asset-id>.yaml` are logical patterns. The orchestrator must resolve logical names through the registry before creating handoffs and must carry resolved paths in `authoritative_inputs` / `expected_outputs`.

## Core principles

1. Advance artifacts, not assumptions.
2. Preserve validated truth.
3. Search-derived references are evidence until explicitly approved as scoped anchors.
4. Rework uses canonical `change_scope / preserve_scope` from `references/rework-handoff-contract.yaml`.
5. Symptom location, root ownership, invalidation scope, and revalidation scope are separate decisions.
6. Invalidate the smallest descendant surface that can no longer be trusted.
7. `partial_validation_only` never promotes runtime readiness.
8. Provenance/history is append-only even when artifacts are superseded — which the *active* path cannot provide, because exactly one version of each derived artifact lives where the registry resolves it. Archive to `.pipeline/history/` with `scripts/retain.py` **before** overwriting, and prune candidate images with the same tool; see `references/toolkit-contract.yaml` → `retention`.
9. Descendant approvals cannot survive changed upstream identity unless effective input equivalence is proven.

## Source-of-truth hierarchy

1. LOCKED GameSpec
2. LOCKED ArtStyle
3. approved scoped Style Anchors
4. locked applicable Style Constraint Ledger
5. Asset Manifest / Asset Specs
6. Generation Contract + candidate/generation records
7. Normalization records / output hashes
8. QC reports / family summaries
9. Runtime reports / evidence / approved baselines

`reference-corpus.yaml` is evidence; `style-anchor-manifest.yaml` defines reference authority.

## Pipeline state

Maintain `.pipeline/game-art-production-state.yaml` as canonical orchestration state.

Stage states:

`NOT_STARTED`, `IN_PROGRESS`, `READY`, `BLOCKED`, `FAILED`, `INVALIDATED`, `COMPLETE`.

Asset lifecycle happy path:

```text
PLANNED
→ READY_FOR_GENERATION
→ GENERATED
→ NORMALIZED
→ QC_APPROVED
→ INTEGRATION_READY
→ RUNTIME_APPROVED
→ SHIPPABLE
```

Rework/failure states:

`GENERATION_REWORK`, `NORMALIZATION_BLOCKED`, `QC_REWORK`, `INTEGRATION_REWORK`, `RUNTIME_REWORK`, `INVALIDATED`.

### Transitions are enforced, not suggested

`references/toolkit-contract.yaml` → `lifecycle_transitions` lists, for every state, the states it may move to and the evidence that authorizes each move.

**Reject any transition not in that table.** A state change without its listed evidence is illegal even when the target state is listed — for example, `NORMALIZED → QC_APPROVED` requires a QC report whose status is in `stages.asset_qc.promotion_status` *and* whose `evaluated.normalized_output.content_hash` equals the active normalized output. A promoting status bound to a stale hash is not evidence for this asset.

This is what makes the orchestrator deterministic rather than merely opinionated: routing decisions come from a table, not from reconstructing intent out of chat history.

Track active version lineage for each asset/family:

```yaml
active_versions:
  asset_spec:            { version: v3, content_hash: <sha256> }
  generation_candidate:  { id: v6-c2,   content_hash: <sha256> }
  normalization_output:  { version: v6, content_hash: <sha256> }
  qc_report:             { version: v6, content_hash: <sha256> }
  integration_plan:      { version: v2, content_hash: <sha256> }
  runtime_report:        { version: v6, content_hash: <sha256> }
```

Version plus `content_hash`, never one or the other. A version string alone cannot prove a file did not change; a hash alone cannot express ordering. Both are required by `references/schemas/`, and `validate_project.py` verifies each recorded hash against the bytes on disk.

## Canonical handoff envelope

Every external specialist transition follows `references/rework-handoff-contract.yaml` when rework is involved. Normal forward handoffs should use the same authority/version discipline.

```yaml
handoff_id: HND-0042
from: game-asset-qc
to: game-asset-generator
subject:
  type: asset
  id: AST-001
root_owner: game-asset-generator
reason_codes:
  - NEGATIVE_CONSTRAINT_VIOLATION

authoritative_inputs: []

change_scope:
  dimensions:
    - texture_density
  artifacts: []
  runtime_properties: []

preserve_scope:
  dimensions:
    - identity
    - silhouette
    - palette
  artifacts:
    - assets/specs/AST-001.yaml
  upstream_truth:
    - game_spec
    - art_style
    - approved_anchors

expected_outputs: []
invalidation_scope: LOCAL_ASSET
revalidation_scope:
  - normalization
  - asset_qc
  - affected_runtime_contexts
next_action: regenerate scoped dimension
```

Specialist-local aliases such as `change_dimensions`, `preserve_dimensions`, `change`, or `preserve` may appear inside specialist reports. Before routing, normalize them into canonical scope fields.

## Readiness / promotion

### GameSpec
Require the relevant readiness gate. Never promote inferred semantics as confirmed production truth.

### ArtStyle
Before mass generation require applicable locked rules, reference grounding, approved production-critical anchors, applicable negative constraints, and representative calibration approval.

### Generation
Require complete AssetSpec/style authority/family inputs. `generation-contract.yaml` is authoritative; `prompt.md` is serialized output.

### Normalization
Require exact candidate/spec lineage and mechanical policy. A normalization result applies only to the exact effective input it records.

### QC
Only normalized outputs with coherent generation/normalization lineage enter QC. `approved` / policy-allowed `approved_with_minor_findings` promote to `QC_APPROVED` — but only when the report's `evaluated.normalized_output.content_hash` matches the active output.

### Engine integration
Require QC-approved assets whose hashes still match, a declared engine target, and declared budgets. `integration_ready` / `integration_ready_with_minor_findings` promote. An undeclared budget produces `integration_blocked`, never a silent pass. Skip this stage only when the active profile makes it optional.

### Runtime
Only executable rendered-context evidence may produce runtime approval. `partial_validation_only`, `runtime_rework_required`, and `runtime_blocked` never promote. A report claiming approval while `build.executable` is false, or while a `risk: high` context is untested, is malformed.

### SHIPPABLE
Require coherent current lineage across every stage the active profile requires, from AssetSpec through runtime approval. Mixed versions never promote:

```text
generated candidate v6 + QC report for v5 + runtime report for v4  →  SHIPPABLE   ✗
```

## Failure routing

`references/routing.yaml` is the single source of truth. Do not carry a routing table in this document — that duplication is what let the pipeline's own vocabulary drift apart in the first place.

Procedure:

1. classify the symptom using `decision_procedure` in `routing.yaml`, in order, stopping at the first row that resolves;
2. take `root_owner`, `invalidation_scope`, and `revalidation_scope` from that row rather than deciding them independently;
3. when `root_owner` is `null` (`CONTEXT_SENSITIVE_ASSET_FAILURE`, `ACCESSIBILITY_FAILURE`), do not auto-route — determine which upstream contract is deficient first;
4. when ambiguous, request the smallest diagnostic step capable of separating the candidate causes.

Never widen `invalidation_scope` on a single observation. `systemic_escalation` in `routing.yaml` requires a shared-cause hypothesis tested against one representative dependent subject before the scope grows.

## Dependency-aware invalidation

Preserve unaffected locked truth by default. Invalidate descendants of changed authoritative input.

### Generator-local change

Correct behavior:

```text
new generation candidate
→ old normalization output/record becomes non-authoritative
→ old QC approval becomes non-authoritative
→ dependent runtime approval becomes non-authoritative
→ rerun normalization
→ rerun QC
→ rerun affected runtime contexts
```

Do **not** preserve an old normalization record for a changed candidate unless exact effective input equivalence is proven via hash/version and reuse is policy-permitted.

### Normalization-only change

```text
preserve generation candidate
→ invalidate normalization output/record
→ invalidate dependent QC/runtime
→ normalize → QC → affected runtime
```

### Runtime-integration-only change

```text
preserve generation / normalization / QC
→ change runtime integration
→ invalidate affected runtime contexts only
→ revalidate affected contexts
```

### Scoped ArtStyle change

```text
changed locked UI texture rule/anchor
→ invalidate only AssetSpecs/generation descendants governed by that changed authority
→ preserve unrelated categories/families
```

A reference merely added to `reference-corpus.yaml` causes no invalidation until production authority changes.

Record trigger artifact/version, root owner, changed truth, invalidated descendants, preserved siblings, and revalidation scope.

## Art-style loop orchestration

Respect:

- `L0_MICRO`
- `L1_RESELECT`
- `L2_DELTA_SEARCH`
- `L3_BRANCH_RESET`
- `L4_DIRECTION_RESET`

Do not escalate when a narrower loop is sufficient. Broad direction resets require explicit user intent.

## Generation rework orchestration

Respect:

- `G0_SAME_CONTRACT_RETRY`
- `G1_LOCAL_DIMENSION_DELTA`
- `G2_REDERIVE_FROM_CANONICAL_PARENT`
- `G3_CHANGE_GENERATION_STRATEGY`
- `G4_ESCALATE_UPSTREAM`

`G4` means contract insufficiency/contradiction, not generator permission to redesign ArtStyle.

## Rework budget on the edges that cost nothing

`generation_budget` bounds the edge that spends image budget. Every other routing edge spends nothing per attempt, which is exactly why it needs a bound: a routing loop there is free, so nothing stops it.

`references/toolkit-contract.yaml` → `rework_budget` caps repeats at **2 routes to the same root owner for the same `reason_code` on one subject**. Count an attempt as progress only when the receiving stage produced an output with a *new* `content_hash`; an identical output is a repeat however the receiver described its work. Record the count in `assets.<id>.rework_attempts` so the cap survives a context reset.

On the third route, stop and emit a `BLOCKER` naming both stages, the disputed check, and the subject. Two stages that return different verdicts for identical bytes is a contract defect — neither of them owns it, and sending the ticket back to either one produces the same bytes and the same disagreement.

## Family/batch orchestration

Separate the work that costs image budget from the work that does not, and do all of the cheap work first.

```text
all AssetSpecs                          planner, one pass
→ all generation contracts              generator, one pass, no image budget
→ review the contract set as a set      systemic errors are visible here and nowhere else
→ canonical parent                      first image spent
→ representative derivatives
→ representative QC
→ representative runtime validation
→ remaining family
```

Two rules make this ordering worth enforcing rather than merely suggesting:

- **Do not let a specialist interleave contract compilation with generation.** Contracts are deterministic derivations of locked truth; compiling them per-asset as generation proceeds hides set-level contradictions until image budget is already being spent on them.
- **Bulk compilation never authorizes bulk generation.** A contract set is unproven until an image made from one has been screened and approved. Routing straight from step 2 to the full batch is the single most expensive routing mistake available here — it converts one systemic style error into N regenerations.

Canonical/systemic failure blocks dependent variants. Local derivative failure preserves passing siblings unless evidence shows family-wide cause.

Batch order:

- Tier 0 calibration/anchors
- Tier 1 P0 core gameplay
- Tier 2 P0 variants
- Tier 3 core UI
- Tier 4 secondary/progression
- Tier 5 decoration/FX/polish

Do not scale later tiers while representative earlier tiers expose systemic problems.

## Human checkpoints

Require explicit human approval for GameSpec lock, ArtStyle direction lock, calibration anchor approval, first P0 canonical family approval, broad L4 direction reset, and systemic runtime fixes that reopen locked upstream truth.

Do not interrupt for deterministic routine routing when contracts already determine the next action.

## Policy references

Use when needed:

- `references/orchestration-state-policy.md`
- `references/invalidation-routing-policy.md`
- `references/handoff-promotion-policy.md`
- `references/rework-handoff-contract.yaml`

## Completion

Production is complete only when required GameSpec/ArtStyle truth is locked, reference authority is approved, planned assets have authoritative generation and normalization versions, QC passes on those exact versions, executable runtime contexts pass for the integrated lineage, required assets are `SHIPPABLE`, and orchestration state points to the exact shipping versions with no unresolved blocker/systemic rework.
