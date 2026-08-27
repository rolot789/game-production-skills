# Generation Contract Compilation Policy

## Purpose

Compile upstream production truth into a generation job without collapsing structured art direction into an adjective-heavy prompt.

The generator should reason from a structured contract first and serialize that contract into provider/tool-specific instructions only at the final step.

## Precedence

When inputs overlap, use this precedence unless an upstream artifact explicitly defines another relationship:

```text
1. Locked AssetSpec semantic requirements
2. Locked identity / geometry requirements for the asset or family
3. Locked category-specific style overrides
4. Locked scoped anchors for the governed dimension
5. Locked global ArtStyle invariants
6. Locked negative constraints
7. Confirmed but not yet locked production details
8. Non-authoritative reference evidence / discovery hints
9. Generator defaults
```

This order is not a license to ignore global style. It prevents a broad global rule from overwriting a more specific approved rule.

## Scope resolution

Resolve every visual dimension independently when possible.

Example:

```yaml
line:
  source: REF-012
  role: line_anchor
  status: LOCKED

palette:
  source: REF-004
  role: palette_anchor
  status: LOCKED

lighting:
  source: global_art_style
  status: LOCKED

identity:
  source: CHARACTER-ANCHOR-001
  status: LOCKED
```

Do not turn these into:

> Make an image inspired by REF-012, REF-004, and CHARACTER-ANCHOR-001.

That instruction destroys scope.

Instead compile explicit inheritance and non-inheritance rules.

## Recommended generation-contract schema

```yaml
asset:
  id: gate-closed
  family: gate
  semantic_role: blocking field object

identity:
  required: true
  anchors:
    - id: GATE-BASE-001
      governs: [silhouette, proportions, frame_geometry]

style:
  global_rules: []
  category_overrides: []

anchors:
  - id: REF-017
    role: line_anchor
    governs: [line.weight, line.irregularity]
    preserve: []
    do_not_inherit: [lighting, composition]

constraints:
  hard_forbidden: []
  soft_avoid: []
  bounded: []
  anti_reference: []

family:
  canonical_parent: gate-base
  preserve: []
  allowed_delta: []

output:
  medium: raster
  background: transparent
  framing: full_asset
  clipping: forbidden

non_goals: []
```

The exact schema may evolve, but these semantic groups should remain distinct.

## Prompt serialization order

When a target generation capability requires prose, serialize in this order:

1. say what asset is being produced and what gameplay/visual role it serves;
2. state non-negotiable identity, silhouette, camera, and geometry;
3. state global visual invariants that apply;
4. apply category overrides explicitly;
5. describe each scoped anchor only for its governed dimensions;
6. state family/canonical-parent preservation requirements;
7. state the desired positive rendering behavior;
8. compile negative constraints with positive counterparts;
9. state output framing/background/transparency requirements;
10. finish with explicit non-goals or drift guards.

Do not lead with mood prose when geometry or identity is production-critical.

## Avoid adjective soup

Bad:

> Cute whimsical charming hand-drawn indie cozy beautiful crayon storybook game asset, highly polished but handmade, cinematic yet minimal.

Better:

```text
Preserve the approved simple 3-part silhouette and top-view projection.
Use medium charcoal-like contours with small controlled width variation.
Use matte, low-density wax-crayon fill texture; broad calm fills are more important than visible stroke noise.
No rim light, glossy gradient, micro-decoration, or extra costume segmentation.
```

Observable instructions are preferred over mood stacks.

## Reference weighting

Do not invent numerical weights unless the upstream manifest provides them. Use semantic priority instead:

```text
PRIMARY / LOCKED
SECONDARY / SUPPORTING
DISCOVERY_ONLY
ANTI_REFERENCE
```

User-provided references that have been approved for a dimension are primary for that dimension. Search-derived references can become primary only through approval/locking.

## Reference blending

Never blend references globally by default.

Allowed:

```text
REF-A → line
REF-B → palette
REF-C → UI spacing
```

Unsafe:

```text
Blend the overall style of REF-A, REF-B, and REF-C.
```

If two approved references govern the same dimension and conflict, generation is blocked until the relationship is resolved upstream.

## Constraint compilation

For each applicable constraint:

```text
HARD_FORBIDDEN
→ explicit rejection criterion

SOFT_AVOID
→ discourage unless a higher-priority rule requires it

BOUNDED
→ state allowed intensity/range and positive target

ANTI_REFERENCE
→ name the reference dimension that must not transfer
```

Example:

```text
Avoid dense visible crayon scribbling across large fill areas.
Preserve subtle tactile grain and sparse rubbed texture instead.
```

## Provider adaptation

Different generation tools expose different controls, reference-image mechanisms, edit modes, seeds, masks, or style parameters.

Adapt the contract to available capabilities without changing its meaning.

If a required scoped reference cannot be supplied to the provider and cannot be reliably described from verified analysis, record the limitation. Do not claim equivalent grounding.

## Contract stability

When regenerating, reuse the previous passing contract and patch only the failed fields.

Keep a diff such as:

```yaml
revision:
  base_job: v3
  changed_dimensions:
    - texture.density
  preserved_dimensions:
    - identity
    - geometry
    - line
    - palette
    - lighting
```

This is preferred to creating a fresh prompt from memory.
