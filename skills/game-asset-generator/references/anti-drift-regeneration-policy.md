# Anti-Drift Regeneration Policy

## Purpose

Regenerate failed candidates without erasing dimensions that already match the approved art system.

The default response to failure is not `rewrite the prompt`. It is:

```text
observe failure
→ classify failure
→ identify affected dimensions
→ preserve passing dimensions
→ patch generation contract
→ regenerate smallest useful surface
→ compare against previous passing evidence
```

## Failure classes

### `CONTENT_ERROR`

Wrong object, missing required component, incorrect semantic feature, or invented content.

Owner is usually generator when AssetSpec was clear. Route upstream when semantics were ambiguous.

### `IDENTITY_DRIFT`

Character/object identity, proportions, signature geometry, or defining features changed.

Preserve style dimensions; reassert identity/geometry anchors and use reference edit or canonical parent where possible.

### `STYLE_DIMENSION_DRIFT`

One or more style dimensions moved away from approved anchors, such as line, palette, texture, lighting, material, or composition.

Patch only the affected dimensions.

### `CONSTRAINT_VIOLATION`

Candidate exhibits a `HARD_FORBIDDEN`, exceeds a `BOUNDED` rule, or inherits an `ANTI_REFERENCE` feature.

Make the violated rule explicit in the next delta contract and preserve unrelated dimensions.

### `FAMILY_DRIFT`

A state/direction/frame no longer belongs visually to the approved family.

Return to canonical parent/family lineage rather than independently redesigning the failed member.

### `STATE_READABILITY_FAILURE`

The state exists but is visually ambiguous or too similar/different relative to siblings.

If the state visualization rule is already defined, generator owns the fix. If the rule itself is undefined, route to planner/art-style owner.

### `OUTPUT_TECHNICAL_FAILURE`

Wrong background, crop, framing, resolution, transparency, or unsupported file-mode artifact attributable to generation.

Preserve visual content and patch output constraints. Do not unnecessarily restyle.

### `UPSTREAM_SPEC_AMBIGUITY`

The generator cannot determine correct output without inventing semantics or art direction.

Stop and route upstream. Repeated guessing is not regeneration.

## Delta contract

For every regeneration after a non-trivial failure, record:

```yaml
delta:
  failure_class: STYLE_DIMENSION_DRIFT
  failed_dimensions:
    - texture.density
  preserve_dimensions:
    - identity
    - geometry
    - line
    - palette
    - lighting
  constraint_changes:
    - reinforce: NEG-TEXTURE-004
  parent_candidate: candidate-v2
```

A delta contract should be understandable without reading the entire conversation history.

## Regeneration escalation

Use the smallest level that can plausibly solve the failure.

### `G0_REPEAT_WITH_SAME_CONTRACT`

Use when the provider is stochastic and the contract itself is correct. Do not mutate style rules.

### `G1_LOCAL_DELTA`

Patch one or a few explicit dimensions while preserving the rest.

Examples:

- reduce texture density;
- remove extra rim light;
- restore one missing costume element;
- correct transparent background;
- strengthen state indicator while preserving geometry.

This is the default regeneration level.

### `G2_PARENT_REDERIVE`

Use when one member has drifted too far from a family or identity anchor.

Re-derive from canonical parent / reference edit / previous accepted member rather than patching an unrelated independent generation.

### `G3_GENERATION_STRATEGY_CHANGE`

Use when the current provider capability or topology repeatedly fails the same locked requirement.

Examples:

- independent text-to-image cannot preserve identity → switch to reference-edit topology;
- separate state generation cannot preserve geometry → generate canonical parent then edit states;
- provider cannot preserve transparency → change generation/export strategy.

The style contract stays fixed; only generation strategy changes.

### `G4_UPSTREAM_ESCALATION`

Use only when the requested visual behavior is internally conflicting, unspecified, or impossible under current locked sources.

Route to the correct upstream owner rather than silently changing ArtStyle or AssetSpec.

## When not to regenerate

Do not regenerate merely because another candidate might be prettier.

If a candidate satisfies the production contract, stylistic preference changes should be recorded as an explicit revision request. This prevents endless aesthetic sampling from replacing production decisions.

## Preservation ledger

After each screened candidate, keep a compact pass/fail view by critical dimension.

Example:

```yaml
screening:
  identity: PASS
  geometry: PASS
  line: PASS
  palette: PASS
  texture: FAIL
  lighting: PASS
  state_readability: PASS
  output: PASS
```

The next attempt should preserve every `PASS` dimension unless the user or upstream artifact explicitly unlocks it.

## Repeated failure policy

Repeated failure on the same dimension is diagnostic evidence.

```text
same failure once
→ local delta

same failure repeatedly under correct contract
→ inspect provider/topology

same failure across providers/topologies
→ inspect upstream feasibility or conflicting constraints
```

Do not keep appending increasingly aggressive negative phrases to a prompt indefinitely.

## User feedback mapping

When feedback is vague, do not automatically rewrite the generation contract.

Examples:

```text
"too AI-looking"
→ identify observable symptom before patching

"doesn't feel like the reference"
→ identify which governed dimension drifted

"make it more handmade"
→ determine whether line, fill texture, shape imperfection, material, or another dimension is meant
```

If an interactive user-input mechanism is available and the distinction matters, request clarification through it.

## Provenance across loops

Every candidate should retain lineage:

```text
candidate-v1
  ↓ G1 texture delta
candidate-v2
  ↓ G2 parent rederive
candidate-v3
```

Record why each transition happened. Never overwrite failed candidates or records in a way that destroys diagnosis history.
