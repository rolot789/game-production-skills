---
name: game-asset-qc
description: Evaluate normalized game assets against production contracts, scoped visual anchors, persistent style constraints, family lineage, and runtime-readability requirements. Produce evidence-backed findings, pass/fail status, and precise upstream ownership without modifying assets.
---

# Game Asset QC

## Purpose

Judge whether a normalized asset satisfies the production contract it was supposed to implement. Do not judge isolated attractiveness and do not redesign the asset during QC.

```text
Normalized Asset
+ AssetSpec
+ Generation Contract / Record
+ Locked ArtStyle
+ Scoped Anchors
+ Style Constraint Ledger
+ Family / State Context
        ↓
Contract Resolution
        ↓
Technical + Visual Verification
        ↓
Finding Classification
        ↓
Root-owner Routing
        ↓
APPROVED / REWORK_REQUIRED / BLOCKED
```

The primary question is:

> Did this asset faithfully implement the approved semantic, technical, visual, and family contracts at its intended game-use scale?

## Required inputs

Consume the strongest available evidence. Prefer explicit artifacts over reconstructed assumptions.

Required when applicable:

- normalized runtime asset,
- normalization record,
- AssetSpec,
- `generation-contract.yaml`,
- selected candidate generation record,
- locked `art-style.yaml`,
- `style-anchor-manifest.yaml`,
- `style-constraint-ledger.yaml`,
- canonical family parent and sibling variants,
- gameplay/state semantics from GameSpec or AssetSpec.

If a production-critical contract is missing or contradictory, do not invent it. Emit a blocked finding and route to the upstream owner.

## Core rules

1. **Contract first, taste second.** Personal aesthetic preference is not a failure unless it conflicts with an approved contract or gameplay requirement.
2. Verify scoped anchors only on dimensions they govern. A palette anchor cannot fail an asset for geometry.
3. Enforce locked negative constraints as real QC rules, not prompt suggestions.
4. Inspect assets both at source/zoom scale and intended runtime display scale.
5. Family assets are evaluated comparatively; states/directions must read as the same identity under controlled variation.
6. Preserve symptom vs root cause. The visible defect location does not determine ownership.
7. Do not modify, repaint, crop, normalize, or regenerate assets. QC only records evidence and routes remediation.
8. Do not downgrade a repeated systemic failure to MINOR because each individual asset is superficially usable.

## Contract Compliance Matrix

Build an internal compliance matrix before deciding status. Evaluate only dimensions applicable to the asset.

### A. Technical conformance

- expected file exists and is readable,
- format/color/alpha mode,
- canvas dimensions,
- transparent-background requirements,
- bounds/clipping/edge contamination,
- naming/export contract,
- normalization metadata,
- anchor/pivot consistency when verifiable.

### B. Semantic conformance

- correct asset identity,
- correct object/category,
- correct state/direction/pose,
- required gameplay-significant feature present,
- no invented semantic feature that changes interpretation,
- intended state remains distinguishable.

### C. Positive style conformance

Resolve applicable global and category rules from ArtStyle. Check shape language, line behavior, palette/value, texture, lighting, material treatment, composition, detail density, readability, and category overrides.

### D. Scoped anchor conformance

For each applicable anchor, record:

```text
anchor_id
role
governed_dimensions
applicable_to_asset
result: PASS | FAIL | NOT_APPLICABLE | INSUFFICIENT_EVIDENCE
```

Do not compare unrelated dimensions.

### E. Negative constraint conformance

Read active constraints from `style-constraint-ledger.yaml` using scope inheritance:

```text
Global
→ Category
→ Family
→ Asset Override
```

Evaluate `HARD_FORBIDDEN`, `SOFT_AVOID`, `BOUNDED`, and `ANTI_REFERENCE` according to their defined severity/scope. Vague labels such as `looks AI-generated` are not findings; translate them into observable violations such as excessive glossy gradients, purposeless micro-detail, mechanically smooth contours, generic symmetry, unintended bloom, or over-dense texture.

### F. Family coherence

Compare against canonical parent and siblings for applicable invariants:

- identity,
- silhouette/proportion,
- camera/projection,
- relative scale,
- palette/material family,
- line/texture treatment,
- shared geometry,
- controlled state difference,
- direction consistency.

A family member should look like the same asset transformed by the intended state/direction, not a new independent design.

### G. Gameplay readability

At intended runtime size verify:

- silhouette recognition,
- state differentiation,
- important feature visibility,
- value/contrast hierarchy,
- clutter/noise level,
- distinction from neighboring gameplay categories when required.

Runtime scene composition itself belongs to `runtime-visual-validator`, but an asset that is intrinsically unreadable at its specified runtime footprint can fail here.

## Evidence policy

Every `BLOCKER` or `MAJOR` finding must contain concrete evidence. Prefer measurable or directly observable statements.

Bad:

```text
The asset feels too AI-generated.
```

Good:

```text
NEG-TEXTURE-004 is violated: dense high-contrast crayon marks cover the full fill area,
while the locked rule bounds UI texture to subtle edge/fill grain. At intended 48 px display,
those marks compete with the state icon.
```

For each finding record:

```yaml
id:
severity:
dimension:
contract_source:
expected:
observed:
evidence:
root_cause_class:
owner:
required_action:
preserve_dimensions:
```

`preserve_dimensions` should list already-passing dimensions that regeneration/normalization must not disturb.

## Severity

- `BLOCKER`: unusable, wrong semantic identity/state, missing critical contract, hard forbidden violation with production impact, corrupted/invalid runtime asset, or contradiction that prevents valid evaluation.
- `MAJOR`: clearly violates a locked production requirement, anchor, family invariant, bounded constraint, or gameplay-readability requirement; rework required.
- `MINOR`: localized defect that does not materially break identity, style system, state readability, or runtime use; may ship only if project policy allows.
- `NOTE`: observation or non-blocking recommendation outside locked requirements.

Do not use severity to express aesthetic preference intensity.

## Asset QC status

- `approved`: no unresolved BLOCKER/MAJOR; no project-disallowed MINOR.
- `approved_with_minor_findings`: only accepted MINOR/NOTE findings remain.
- `rework_required`: one or more MAJOR findings, or project policy requires fixing MINOR findings.
- `blocked`: evaluation cannot validly complete because of BLOCKER conditions or missing/contradictory production truth.

## Root-cause routing

Route according to the source of the defect, not where it was observed.

- `game-asset-generator`: style drift, identity drift, wrong state visuals, invented details, anchor violation, negative-pattern violation, family visual incoherence originating in generation.
- `game-asset-normalizer`: clipping, canvas, alpha, trim/padding, runtime scale processing, anchor/pivot/export errors caused during normalization.
- `game-asset-planner`: missing/incorrect asset variant, contradictory AssetSpec, wrong state inventory, undefined runtime footprint or family relation.
- `art-style-builder`: insufficient, contradictory, or incorrectly scoped locked style/anchor/constraint truth; user direction changed and requires deliberate style unlock.
- `game-spec-builder`: underlying gameplay/state semantics are contradictory or insufficient to know what the asset must communicate.
- `runtime-visual-validator`: do not route isolated QC findings here. Runtime validator owns context/scene integration failures after asset QC approval.

See `references/failure-routing-policy.md` for ambiguous and multi-owner cases.

## Rework handoff

A rework request must be delta-oriented. Do not say `regenerate better`.

Example:

```yaml
owner: game-asset-generator
change_dimensions:
  - texture_density
  - highlight_treatment
preserve_dimensions:
  - identity
  - silhouette
  - palette
  - line_weight
violations:
  - NEG-TEXTURE-004
  - NEG-LIGHT-002
```

This allows generator v2 to perform scoped regeneration without reopening passing dimensions.

## Family and batch policy

For a family, QC should normally verify:

1. canonical parent first,
2. representative state/direction variants,
3. remaining family members with comparative checks.

If the canonical parent fails identity/style invariants, block derivative approvals until the parent is corrected. If only one derivative fails a local state/direction dimension, keep passing siblings valid.

See `references/contract-verification-policy.md` and `references/family-batch-qc-policy.md`.

## Outputs

```text
qc/<asset-id>/
├── qc-report.yaml
└── evidence/            # optional references/crops/measurements when tooling supports them
```

A family or batch may additionally emit:

```text
qc/<family-id>/family-qc-summary.yaml
```

The report must include evaluated contract versions so a later upstream change can invalidate only affected approvals.

## Completion criteria

QC is complete only when:

- applicable contracts have been resolved,
- technical and visual checks are complete at intended scale,
- all findings have evidence and severity,
- BLOCKER/MAJOR findings have root owners and required actions,
- passing dimensions are recorded for preservation,
- final status is explicit,
- evaluated upstream versions/IDs are recorded.
