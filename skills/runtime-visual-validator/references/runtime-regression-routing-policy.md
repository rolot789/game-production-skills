# Runtime Regression and Failure Routing Policy

## Purpose

Runtime symptoms frequently originate outside the runtime layer. This policy prevents two common mistakes:

1. treating every visible runtime defect as an integration bug,
2. invalidating too much of the production pipeline when only one local context failed.

The validator must separate **symptom location**, **root owner**, and **invalidation scope**.

## Failure classes

### `INTEGRATION_LOCAL`

The asset and upstream contracts are valid, but one runtime context applies them incorrectly.

Examples:

- wrong z-order,
- scene-specific transform,
- layout overlap,
- local mask/clipping,
- one viewport-specific UI collision,
- local shader/post-process configuration.

Default owner: `runtime_integration`.

Default invalidation: affected runtime context only.

### `INTEGRATION_SYSTEMIC`

A shared runtime rule breaks multiple contexts.

Examples:

- global bloom makes all active-state indicators unreadable,
- shared UI container clips all chapter cards,
- common camera scale causes several gameplay objects to render below readable size.

Default owner: `runtime_integration`.

Default invalidation: dependent runtime contexts that use the shared rule.

Do not invalidate generation/normalization unless their outputs are themselves wrong.

### `NORMALIZATION_RUNTIME_MECHANICAL`

The source visual is correct, but runtime-ready mechanical preparation is wrong.

Examples:

- pivot produces repeated animation jitter,
- trim removes required transparent padding,
- family canvas dimensions cause state popping,
- export bounds clip glow required by the approved asset.

Default owner: `game-asset-normalizer`.

Invalidate:

```text
NORMALIZED
→ QC approval for affected normalized outputs
→ runtime approval for affected descendants
```

Preserve the generated source candidate when its content is valid.

### `CONTENT_QC_ESCAPE`

Runtime evidence reveals a visual-content defect that should have been observable in isolated QC.

Examples:

- generated identity drift,
- wrong state iconography,
- malformed silhouette,
- art-style violation visible without scene context.

Rework owner: normally `game-asset-generator`.

Process-quality owner: `game-asset-qc` as an escaped defect.

Invalidate affected generation descendants only, not unrelated family members unless the defect is systemic.

### `CONTEXT_SENSITIVE_ASSET_FAILURE`

The asset passes transparent-background inspection but fails under legitimate required contexts, and the failure cannot be fixed through ordinary runtime treatment without violating other locked requirements.

Examples:

- approved palette cannot preserve required state contrast across required backgrounds,
- line hierarchy is inherently unreadable at required camera scale,
- a state marker is semantically too subtle at production display size.

Possible owner:

- `art-style-builder` if the style/category rules are inadequate,
- `game-asset-planner` if the state representation/decomposition is wrong,
- `game-asset-generator` if the current asset failed to implement a valid rule.

Do not route automatically. Determine which upstream contract is deficient.

### `SEMANTIC_UNDEFINED`

The validator cannot determine what the visual state is supposed to communicate.

Examples:

- `current` and `available` semantics conflict between screens,
- interaction feedback timing is unspecified,
- the game spec does not define which object should dominate hierarchy.

Owner: `game-spec-builder` or planner/art-style depending on the missing truth.

Status is usually `runtime_blocked` until the expectation is resolved.

## Root-cause decision order

When a failure appears, ask in this order:

1. **Is the expected player-visible behavior defined?**
   - no → specification/planning/style owner.
2. **Does the QC-approved asset satisfy its isolated contract?**
   - no → generation/normalization/QC escape.
3. **Does the same asset work in another valid context?**
   - yes → likely runtime-context issue.
4. **Does the failure correlate with a shared runtime rule?**
   - yes → systemic runtime integration.
5. **Would fixing runtime integration require violating locked asset/style behavior?**
   - yes → upstream contract may be context-inadequate.
6. **Is the defect local or family/systemic?**
   - use this to set invalidation scope.

## Regression model

A visual change is not automatically a regression.

Classify differences as:

### `INTENTIONAL_CHANGE`

The current result differs because an approved upstream/runtime decision changed.

Action:

- validate against the new truth,
- update baseline after approval,
- do not file regression finding solely for the difference.

### `SEMANTIC_REGRESSION`

Player-visible meaning or production requirement degraded unexpectedly.

Examples:

- selected state no longer reads selected,
- goal visibility dropped,
- label now overlaps a control,
- camera change hides a puzzle-critical object,
- animation feedback is too brief to perceive.

Action: file evidence-backed finding and route root owner.

### `COSMETIC_DELTA`

The image differs but no required semantic/style/runtime behavior is harmed.

Examples:

- minor antialiasing change,
- harmless subpixel texture difference,
- background noise variation within allowed bounds.

Action: normally no failure. Record only if useful.

### `BASELINE_STALE`

The baseline represents obsolete approved truth.

Action:

- do not force current implementation to match stale evidence,
- identify the approved decision that superseded it,
- replace baseline after current approval.

## Semantic regression checklist

Compare current vs baseline on relevant dimensions:

```text
identity
state meaning
visual hierarchy
actual-scale readability
placement/alignment
occlusion
UI/world separation
transition clarity
family continuity
critical style-in-context constraints
```

Do not require all dimensions for every context.

## Invalidation policy

Use dependency-aware invalidation.

### Runtime integration-only change

Example: z-index fix.

Invalidate:

```text
affected runtime report/context
```

Preserve:

```text
QC approval
normalized asset
generated candidate
art style
```

### Normalization change

Example: pivot fix.

Invalidate:

```text
affected normalized output
QC for that output
runtime validation descendants
```

Preserve generated visual content when unchanged.

### Generation content change

Example: current-state silhouette regenerated.

Invalidate:

```text
generated affected asset/derivatives
normalization
QC
runtime validation
```

Preserve unrelated family members unless shared source truth changed.

### Planner/state-contract change

Example: locked state is split into a new overlay asset.

Invalidate all descendants of the changed asset/family specification, not the entire project.

### ArtStyle/category-rule change

Invalidate assets and runtime contexts that depend on the changed style dimension/category.

Example:

```text
UI texture density rule changes
→ UI-dependent assets invalidate
→ character/world assets remain valid unless they inherit the same rule
```

### GameSpec semantic change

Invalidate planning/art/runtime descendants whose expected gameplay meaning changed.

## Preserve/change contract

Each rework finding should include both:

```yaml
change:
  - <smallest necessary surface>

preserve:
  - <passing decisions / assets / context>
```

Example:

```yaml
change:
  - runtime.scene.stage_select.postprocess.bloom

preserve:
  - stage-star-current normalized asset
  - stage-star-available normalized asset
  - approved palette relationship
  - node geometry
  - camera framing
```

This prevents runtime fixes from triggering arbitrary asset regeneration.

## QC escape handling

If runtime validation finds an isolated defect that QC should have caught:

1. route visual rework to the true production owner,
2. record `qc_escape: true`,
3. identify the missed QC dimension/check,
4. improve QC coverage if the failure pattern is reusable,
5. do not route the asset itself to QC as though QC can edit it.

Example:

```yaml
root_owner: game-asset-generator
qc_escape: true
missed_qc_dimension: state_readability
```

## Local vs systemic evidence

Do not label a problem systemic after one observation without a shared-cause hypothesis.

Suggested sequence:

```text
Failure in CTX-A
→ identify candidate shared cause
→ test one representative dependent context CTX-B
→ if same cause reproduces, expand invalidation scope
→ otherwise keep failure local
```

This minimizes unnecessary revalidation.

## Reapproval after fix

Revalidate:

- the failing context,
- a representative neighboring context if the fix changes a shared rule,
- any previously passing context that could plausibly regress because of the fix.

Do not automatically rerun the entire validation suite after a local fix.

## Final routing rule

The runtime validator should answer three separate questions for every major failure:

```text
Where is the symptom visible?
Who owns the root cause?
What is the smallest dependency scope that must be invalidated?
```

Never collapse those into one field.
