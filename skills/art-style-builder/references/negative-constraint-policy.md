# Negative Constraint Policy

## Purpose

Turn subjective rejection feedback into persistent, observable, scoped production rules instead of one-turn negative prompts.

## Core principle

Vague rejection language is a diagnostic signal, not a final constraint.

Do not stop at:
- `do not look AI-generated`,
- `not generic`,
- `not too polished`,
- `make it less artificial`.

Translate these into visible, reviewable behaviors.

## Constraint model

Each constraint should contain:
- stable ID,
- dimension/category,
- type,
- observable forbidden behavior,
- positive counterpart (`DO INSTEAD`),
- scope,
- origin,
- status,
- verification notes,
- related references/assets when applicable.

Recommended types:

### `HARD_FORBIDDEN`

Presence constitutes a style failure unless the rule is explicitly reopened.

Examples:
- perfectly uniform vector contours in a deliberately handmade character family,
- strong cinematic bloom when the locked lighting model forbids it,
- photoreal material shading in a flat illustrative UI system.

### `SOFT_AVOID`

Normally undesirable but may be contextually acceptable.

Examples:
- highly symmetrical decorative layouts,
- dense surface noise in large background-only elements,
- small ornamental marks with no gameplay or design purpose.

### `BOUNDED`

Allowed only in a controlled amount.

Examples:
- crayon grain: subtle-to-medium only,
- gloss highlight: sparse/local only,
- outline wobble: readable and restrained,
- color variation: low enough to preserve state readability.

### `ANTI_REFERENCE`

A particular reference is accepted for some dimensions but explicitly rejected for another.

Example:

```text
REF-014
  accept: line, palette
  reject: dramatic rim lighting
```

## Positive counterpart requirement

Whenever possible, pair a negative rule with a positive destination.

Bad:

```text
Avoid smooth lines.
```

Better:

```text
AVOID:
perfectly uniform, mechanically smooth vector contours

DO INSTEAD:
use controlled hand-drawn irregularity with stable readable silhouettes
```

This reduces under-specification during generation.

## Diagnostic taxonomy for "AI-looking" results

Use this taxonomy to clarify what the user actually dislikes. It is not itself a negative prompt.

### Line / contour
- mechanically perfect curvature,
- inconsistent line intentionality,
- random wobble without structural purpose,
- overly clean vector edges in a tactile medium,
- over-thick contour hierarchy that flattens internal forms.

### Surface / rendering
- generic glossy gradients,
- plastic-like specular treatment,
- over-rendered highlights,
- ambiguous airbrushed shading,
- excessive soft volumetric rendering on otherwise flat art.

### Texture
- purposeless texture everywhere,
- noisy micro-strokes that reduce silhouette clarity,
- inconsistent medium simulation,
- repeated brush/grain patterns,
- excessive "handmade" noise added as decoration rather than material logic.

### Detail / design density
- micro-detail with no semantic purpose,
- arbitrary costume segmentation,
- excessive tiny accessories,
- decorative motifs that do not follow world/function logic,
- shape complexity inconsistent with target runtime scale.

### Lighting / effects
- default cinematic rim light,
- excessive bloom,
- unnecessary atmospheric glow,
- dramatic vignette or spotlighting not supported by scene logic,
- overuse of floating particles as polish.

### Composition
- generic centered hero composition,
- excessive bilateral symmetry,
- poster-like framing when a gameplay asset is required,
- empty "cinematic" negative space unrelated to UI/gameplay needs.

### Character design
- generic mascot proportions inconsistent with project identity,
- overly polished facial features,
- too many costume/material zones,
- anatomy or silhouette details that exceed the intended simplification level,
- generic expression conventions that erase character identity.

### Color
- fashionable gradient palettes unrelated to style anchors,
- excessive saturation spread,
- too many accent colors,
- value compression that harms readability,
- inconsistent palette temperature across asset families.

## Feedback conversion

When the user says something such as:

> The coloring marks are too strong.

Do not only edit the next prompt. Record a rule such as:

```yaml
id: NEG-TEXTURE-004
category: texture
type: BOUNDED
avoid: dense visible crayon stroke marks that compete with the silhouette
positive_counterpart: preserve subtle tactile grain with mostly calm fills
scope:
  categories: [UI, icon, small_gameplay_asset]
origin:
  type: calibration_feedback
status: CONFIRMED
verification:
  check_at_target_scale: true
```

## Constraint scope

Use narrow scope unless evidence supports a global rule.

Inheritance order:

```text
Global
  ↓
Category
  ↓
Asset Family
  ↓
Asset Override
```

Examples:
- global: avoid generic glossy material rendering,
- character: allow thicker contour hierarchy,
- UI: reduce texture density substantially,
- FX: allow more glow than UI but remain within bounded intensity.

A local complaint about a UI icon should not automatically become a global prohibition.

## Origin tracking

Recommended origins:
- `USER_EXPLICIT`,
- `USER_CALIBRATION_FEEDBACK`,
- `REFERENCE_REJECTION`,
- `GAME_SPEC_DERIVED`,
- `RUNTIME_READABILITY_FINDING`,
- `QC_RECURRING_FAILURE`.

Origin matters when conflicts occur. Direct user intent normally outranks inferred preferences.

## Status lifecycle

Recommended states:
- `PROPOSED`,
- `CONFIRMED`,
- `LOCKED`,
- `SUPERSEDED`,
- `CONFLICT`.

A generated failure may suggest a new constraint, but it should not silently become a locked art rule unless it clearly follows from already locked direction or receives user confirmation when taste is involved.

## Reference interaction

References provide both positive and negative evidence.

Example:

```text
User: I like the line from REF-021, but the lighting feels too cinematic.
```

Record:
- line role → positive anchor evidence,
- lighting role → rejected for this project,
- optional constraint → avoid strong cinematic rim lighting in the affected scope.

Do not mark the entire reference rejected if useful dimensions remain.

## Generation handoff

The generation stage should receive negative constraints in structured form grouped by scope and priority.

Avoid dumping the full ledger indiscriminately into every prompt. Compile only constraints relevant to the asset/category being generated.

Example:

```text
Character generation receives:
- global HARD_FORBIDDEN
- character constraints
- relevant family constraints

UI icon generation receives:
- global HARD_FORBIDDEN
- UI constraints
- icon constraints
```

## QC behavior

Constraints should be verifiable when possible.

QC should be able to classify:
- compliant,
- minor bounded deviation,
- major violation,
- ambiguous / needs human review.

Do not create fake precision for subjective constraints. Use observable language and target-scale evidence instead of arbitrary numeric thresholds unless the project has real measurable values.

## Constraint ledger

Persist in `style-constraint-ledger.yaml`.

Suggested shape:

```yaml
version: 1
constraints:
  NEG-LINE-001:
    category: line
    type: HARD_FORBIDDEN
    avoid: perfectly uniform vector-smooth contour behavior
    positive_counterpart: restrained handmade irregularity with readable silhouettes
    scope:
      global: true
    origin:
      type: USER_EXPLICIT
    status: LOCKED
    verification:
      visual_review: true
      target_scale_required: true
```

## Anti-bloat rule

Do not create a new constraint for every minor comment.

Before adding a ledger entry:
1. check whether an existing constraint already covers the behavior,
2. refine or narrow an existing bounded rule when appropriate,
3. create a new rule only when the feedback represents a distinct persistent behavior,
4. supersede contradictory old rules rather than keeping both active.

The ledger should become more precise over time, not merely longer.
