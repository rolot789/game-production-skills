# Failure Routing Policy

## Goal

Route QC failures to the stage that owns the root cause, not the stage where the symptom is easiest to see.

## Primary owner classes

### game-asset-generator
Use when the production contract was valid but the candidate visually failed to implement it.

Examples:
- style drift,
- identity drift,
- wrong state appearance,
- invented visual detail,
- scoped anchor violation,
- negative constraint violation,
- derivative variant no longer matches canonical family identity.

### game-asset-normalizer
Use when generation content was acceptable before processing but normalization created the defect.

Examples:
- clipping,
- unintended trim,
- wrong canvas,
- alpha halo,
- scale/export mismatch,
- anchor/pivot offset introduced during processing.

### game-asset-planner
Use when the requested asset contract itself is missing, contradictory, or structurally wrong.

Examples:
- missing state variant,
- wrong family relationship,
- conflicting runtime dimensions,
- unspecified orientation requirement that downstream stages cannot infer.

### art-style-builder
Use when the visual source of truth is insufficient or contradictory.

Examples:
- two locked anchors govern the same dimension incompatibly,
- category override is missing for a production-critical visual distinction,
- negative constraint contradicts a locked positive rule,
- the user deliberately changes approved art direction.

### game-spec-builder
Use when the visual ambiguity originates in unresolved gameplay semantics.

Examples:
- two states have no defined gameplay distinction,
- the asset cannot know which information must be visually communicated,
- direction/state semantics conflict upstream.

## Symptom-to-owner decision procedure

For every MAJOR/BLOCKER finding ask:

1. Was the expected requirement explicit and internally consistent?
   - no → planner/art-style/spec owner depending on requirement type.
2. Did the generated candidate already contain the defect before normalization?
   - yes → generator.
3. Was the candidate correct but normalization introduced the defect?
   - yes → normalizer.
4. Is the requirement itself now rejected by the user rather than incorrectly implemented?
   - yes → art-style-builder or planner/spec; do not blame generator.

## Multi-owner findings

Sometimes one symptom has multiple contributing causes. Record:

- `primary_owner`: stage that must act first,
- `secondary_owner`: only when another stage requires follow-up after primary correction,
- dependency/order between actions.

Example:

```yaml
primary_owner: art-style-builder
secondary_owner: game-asset-generator
reason: two locked texture rules conflict; style truth must be repaired before regeneration.
```

Do not send the same ambiguous ticket to every stage.

## Systemic failures

If the same failure appears across multiple independent assets, test whether the root cause is shared:

- same generation contract compiler issue → generator systemic,
- same normalization policy → normalizer systemic,
- same locked style rule or anchor ambiguity → art-style-builder systemic,
- same AssetSpec template defect → planner systemic.

Systemic failures should produce one root issue plus affected asset list, rather than unrelated local fixes that preserve the faulty source.

## Rework payload

Every routed rework should contain:

```yaml
finding_ids: []
owner:
change_dimensions: []
preserve_dimensions: []
source_contract_ids: []
required_action:
recheck_scope:
```

`preserve_dimensions` is mandatory whenever the asset has meaningful passing dimensions. This prevents rework from causing unrelated drift.
