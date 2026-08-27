# Style Loop Policy

## Purpose

Prevent expensive full restarts when the user rejects a style result. Preserve validated decisions, diagnose the smallest affected visual surface, reuse existing evidence, and escalate only as far as necessary.

## Core rule

`REJECT` does not mean `RESET`.

A rejection triggers diagnosis:

```text
User dissatisfaction
        ↓
Clarify observable problem
        ↓
Map to affected dimensions/categories
        ↓
Classify root cause
        ↓
Check locked decisions and corpus coverage
        ↓
Choose smallest sufficient loop level
```

## Root-cause classes

Classify a revision before acting:

- `PREFERENCE_DELTA`: the user's taste changed or became more specific,
- `ANCHOR_MISMATCH`: chosen evidence/anchor does not represent the intended dimension,
- `GENERATION_FAILURE`: output violated an otherwise correct locked style,
- `NEGATIVE_PATTERN_VIOLATION`: output contains a known undesirable visual pattern,
- `REFERENCE_GAP`: current corpus lacks evidence for the requested direction,
- `CATEGORY_DRIFT`: one category such as UI/environment drifted while global style remains valid,
- `DIRECTION_REJECTION`: the user rejects the overall art direction itself.

Do not reopen art direction for a `GENERATION_FAILURE` unless repeated evidence shows the underlying style rule is actually wrong.

## Interactive rejection diagnosis

When feedback is vague (`too AI`, `not right`, `too polished`, `doesn't feel handmade`), ask a structured clarification question before searching.

Examples of diagnostic dimensions:
- contour smoothness,
- silhouette genericness,
- texture density,
- gradient/gloss intensity,
- micro-detail clutter,
- lighting/bloom,
- symmetry,
- costume segmentation,
- palette/saturation,
- proportion,
- composition,
- UI readability.

Prefer one primary problem and optional secondary problems rather than asking the user to respecify the entire style.

## Loop levels

### `L0_MICRO`

Use when the direction and anchors are correct but intensity/parameter tuning is wrong.

Examples:
- grain slightly too strong,
- outline 10–20% too thick,
- saturation slightly high,
- glow too visible.

Actions:
- no web search,
- preserve locks,
- adjust bounded values / calibration rule,
- regenerate only affected candidates.

### `L1_RESELECT`

Use when the current anchor is wrong but the existing corpus already contains alternatives.

Actions:
- no new search,
- re-rank relevant corpus candidates,
- present a compact comparison,
- replace only affected anchor roles,
- preserve unrelated locks.

### `L2_DELTA_SEARCH`

Use when the current corpus lacks enough evidence for a specific requested change.

Actions:
- search only affected dimensions/categories,
- carry forward all locked constraints into the query,
- add a small number of candidates to the existing corpus,
- do not discard previous search history,
- update only affected anchors/rules.

Example:

```text
Preserve:
  palette
  shape language
  character proportion

Search only:
  UI treatment with lower texture density and higher readability
```

### `L3_BRANCH_RESET`

Use when one major category/domain is fundamentally wrong while the rest remains valid.

Examples:
- character direction accepted, environment rejected,
- world art accepted, UI art direction rejected,
- global palette retained but FX branch needs replacement.

Actions:
- unlock only that branch and dependent anchors,
- preserve global/invariant locks unless explicitly implicated,
- allow wider category-specific search,
- rebuild calibration for that branch.

### `L4_DIRECTION_RESET`

Use only when:
- the user explicitly rejects the overall style direction,
- a foundational assumption such as handmade vs clean-vector changes,
- locked global dimensions conflict irreconcilably with the new user intent.

Actions:
- summarize what will be invalidated,
- preserve useful provenance/history but mark prior direction superseded,
- reopen major global dimensions,
- perform broad exploration only after the user confirms or clearly requests the reset.

## Invalidation rules

Invalidate descendants, not siblings.

Example:

```text
UI texture rule changes
→ UI texture anchor invalidated
→ UI calibration invalidated
→ UI generation downstream invalidated

Character proportion anchor remains valid.
```

A global line-language change may invalidate several categories; a category override should not invalidate unrelated categories.

## Corpus reuse order

Before searching again, follow this order:

1. current locked rules,
2. active user references,
3. existing approved anchors,
4. current reference corpus,
5. rejected/superseded corpus items that may become relevant under the new delta,
6. search history,
7. new delta search.

## Search budget and stop condition

A loop should stop searching as soon as enough accessible evidence exists to resolve the target decision.

Default delta loop:
- <=2 focused queries,
- <=6–8 new references,
- present <=3–6 curated candidates.

Escalate only if the user cannot make a stable decision or critical evidence remains unavailable.

## Query memory

Store normalized search intent and a semantic fingerprint. Repeating `rough hand-drawn UI low grain` after only a minor wording change should reuse prior results rather than launch a new broad search.

A new search is justified when:
- target dimensions changed,
- source scope changed for a reason,
- previous results are inaccessible,
- user feedback adds a materially new constraint,
- corpus coverage is still insufficient.

## Loop state

Persist `style-loop-state.yaml` with at least:

```yaml
active_revision:
  reason: null
  root_cause: null
  loop_level: null
  affected_dimensions: []
  affected_categories: []
  preserved_locks: []
  invalidated_locks: []
  corpus_reused: []
  delta_search_ids: []
  pending_decision: null

history: []
```

Do not use loop history as hidden rationale only; it is production state used to avoid repeated work and explain invalidation.

## Acceptance behavior

When the user accepts a revision:
- update the positive rules,
- update anchor roles,
- update negative constraints learned from rejected alternatives,
- mark superseded references appropriately,
- close the active loop,
- re-evaluate readiness gates.
