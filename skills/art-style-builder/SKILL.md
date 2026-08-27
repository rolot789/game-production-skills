---
name: art-style-builder
description: Use when a game's visual direction must be defined, locked, or revised — "what should this game look like", "find art references", "this looks too AI-generated", "make it feel more handmade" — or when generation keeps drifting off-style. Runs reference research, scoped anchor locking, calibration, and negative-constraint learning, emitting art-style.yaml plus anchor and constraint ledgers. Does not decide which assets exist (use game-asset-planner) or produce images (use game-asset-generator).
---

# Art Style Builder

## Purpose

Convert incomplete visual intent into an explicit, production-usable art system.

A usable art style is not a mood phrase, one long generation prompt, or a pile of reference images. It is:

```text
Positive Style Rules
+ Approved Scoped Visual Anchors
+ Persistent Negative Constraints
+ Provenance / Search Evidence
```

The skill should progressively reduce ambiguity while preserving decisions the user already likes.

```text
GameSpec + Art Intent + Optional User References
        ↓
Reference Mode Detection
        ↓
Interactive Clarification
        ↓
Style Intent Model
        ↓
Weighted Reference Search
        ↓
Reference Corpus + Accessibility Resolution
        ↓
Curated Reference Presentation
        ↓
Interactive Selection / Refinement
        ↓
Progressive Scoped Anchor Locking
        ↓
Calibration
        ↓
User Review
   ┌────┴─────┐
 Accept     Revise
   ↓           ↓
STYLE LOCK   Feedback Diagnosis
              ↓
          Delta Loop
```

## Project path resolution

If `project.yaml` exists, treat its `paths` registry as canonical. Every output named in this skill is a **logical name**, not a repository-root filename: `art-style.yaml` resolves through `paths.art_style`, `style-anchor-manifest.yaml` through `paths.style_anchors`, `style-constraint-ledger.yaml` through `paths.style_constraint_ledger`, and so on.

Downstream skills resolve the same registry. Writing to the repository root when the registry maps these into `art/` breaks the handoff silently.

When no project registry exists, use a consistent convention and record the resolved output paths in the handoff.

## Non-negotiable principles

1. **User intent outranks search results.** Search provides evidence; it does not get to redefine the art direction.
2. **User-provided references outrank discovered references for the dimensions they clearly govern.** Search should refine or fill gaps, not overpower them.
3. **Search result != usable visual anchor.** A reference becomes lock-eligible only after its visual content is sufficiently accessible and its governed dimensions are understood.
4. **Do not restart art direction on rejection.** Diagnose the delta, preserve validated decisions, reuse accumulated evidence, and change the smallest affected surface.
5. **A rejection becomes persistent visual knowledge.** Do not let repeated user corrections disappear as one-turn negative prompts.
6. **Lock by dimension and category, not by whole image.** A reference may govern line but be explicitly forbidden from governing palette or lighting.
7. **Interactive clarification first.** Use structured user-input tools for production-significant decisions whenever available.
8. **Calibration before mass production.** Do not expand an unresolved style into a large asset batch.
9. **Do not silently merge conflicting references.** Conflicts must be scoped, explained, and resolved.
10. **Do not equate `INFERRED` with `CONFIRMED`.**

## Requirement states

Track visual decisions as:

`UNSEEN`, `UNRESOLVED`, `INFERRED`, `PROPOSED`, `CONFIRMED`, `CONFLICT`, `LOCKED`, `NOT_APPLICABLE`.

## Reference modes

Determine one primary mode at the beginning of a style session.

### `REFERENCE_ANCHORED`

Use when the user provides one or more meaningful visual references.

Rules:
- Treat user references as primary evidence for the visual dimensions they clearly communicate.
- First analyze what each user reference actually governs: line, shape, palette, texture, lighting, composition, character proportion, UI treatment, material, etc.
- Identify dimensions that are strong, ambiguous, missing, or internally conflicting.
- Search primarily to **explain, reinforce, or fill those gaps**.
- Do not drift toward a discovered style merely because it is more polished, popular, or easier to search.
- If the user says a reference is identity-critical or must be followed faithfully, preserve that status explicitly in the anchor manifest.

### `EXPLORATORY`

Use when the user provides no usable visual reference.

Rules:
- Do not immediately generate images from vague adjectives.
- Convert interview answers into a structured `Style Intent Model` first.
- Use that model to form targeted search hypotheses.
- Present a small, diverse, high-relevance reference set to help the user sharpen direction.
- Continue narrowing until production-critical visual dimensions can be scoped and locked.

## Interactive clarification policy

For unresolved art-direction decisions, reference conflicts, category overrides, search refinement, calibration choices, rejection diagnosis, or approval decisions, prefer the runtime's structured user-input mechanism such as `AskUserQuestion`, `ask_user_question`, `request_user_input`, or an equivalent interactive multiple-choice tool.

When structured input is available:
- ask 1–3 tightly related questions at a time,
- prefer 2–4 concrete, visually distinct options,
- state the production consequence or tradeoff of each option,
- include `Other` / custom input when useful,
- use multi-select only when choices can validly combine,
- do not force coded replies such as `1-A, 2-C`,
- do not re-ask facts already established by locked rules or approved anchors,
- if a blocking decision is skipped, keep it `UNRESOLVED`.

Map explicit user selections to `CONFIRMED` unless the user marks them tentative. Convert eligible `CONFIRMED` values to `LOCKED` only at explicit or policy-defined freeze points.

If structured input is unavailable, use a compact natural-language fallback with named options and accept normal prose answers.

## Style Intent Model

Normalize the current direction into explicit visual dimensions before searching or generating.

Typical dimensions:
- dimensionality / projection,
- shape language,
- silhouette complexity,
- line behavior and hierarchy,
- rendering medium,
- palette / saturation / value structure,
- texture type and density,
- lighting model,
- material response,
- composition / framing,
- character proportions and facial simplification,
- environment density,
- UI readability and texture reduction,
- icon treatment,
- FX treatment,
- background treatment,
- state readability,
- runtime scale/readability constraints.

Separate global rules from category overrides for `character`, `environment`, `interactive_object`, `UI`, `icon`, `FX`, and `background`.

## Weighted reference search

Search is a controlled research stage, not free browsing.

Before searching:
1. identify the unresolved dimensions,
2. inspect current corpus coverage,
3. reuse prior search results when they already cover the decision,
4. search only for evidence that can materially improve a pending decision.

Use the detailed policy in `references/reference-search-policy.md`.

Default source preference:
- highest weight: user-provided references, official developer/publisher/artist sources, official game pages/press material, professional artist portfolios with attributable provenance,
- high contextual weight: GDC / art-direction talks and production breakdowns,
- medium-high discovery weight: ArtStation and Behance portfolios/projects,
- medium contextual/discovery weight: 80 Level interviews, Steam and itch.io developer/store pages, developer blogs/devlogs,
- low weight: general aggregators and repost-heavy sources,
- discovery-only by default: Pinterest-like collections, unattributed reposts, low-resolution collages, provenance-unclear image boards.

Do not use a low-provenance source as a production-critical locked anchor when a better attributable source can be found.

## Reference corpus and accessibility

Persist discovered evidence in `reference-corpus.yaml` instead of discarding it after one turn.

Each reference should track at least:
- stable reference ID,
- canonical source page / domain,
- whether it was user-provided or discovered,
- source tier / provenance confidence,
- search query or origin,
- accessibility status,
- dimension relevance scores or qualitative relevance,
- accepted roles,
- rejected dimensions,
- user feedback,
- current state (`CANDIDATE`, `ACTIVE`, `REJECTED`, `SUPERSEDED`, `BLOCKED`),
- lock eligibility.

Accessibility statuses:
- `PREVIEWABLE`: visual content can be shown/inspected in the current environment,
- `DOWNLOADABLE`: bytes can be lawfully/technically retrieved when needed,
- `LINK_ONLY`: source page exists but reliable visual ingestion is unavailable,
- `BLOCKED`: access is prevented by login, anti-hotlinking, permissions, or provider restrictions,
- `UNAVAILABLE`: deleted, expired, or otherwise unreachable.

Never claim a blocked or link-only reference was visually verified when it was not.

A production-critical visual anchor should normally require actual visual accessibility to the agent. A `LINK_ONLY` item may remain a discovery hint but is not sufficient by itself for deterministic visual grounding. If the user can access a critical reference that the agent cannot, ask the user to provide an accessible copy when necessary rather than pretending the image was inspected.

Do not bypass access controls, scrape around restrictions, or persist third-party reference image files into the game project merely because they were discoverable. Prefer metadata/provenance in the project and temporary runtime previews when available.

## Living-artist boundary

This skill's core action is to find a reference, lock the dimensions it governs, and compile those into a generation contract that produces commercial assets. When the reference is an identifiable living artist's portfolio, that is style imitation at production scale, and it is a decision the user must make knowingly.

Before locking any anchor whose source is an individual artist's portfolio:

1. say whose work it is and that the anchor will govern named dimensions in generated production assets,
2. prefer an anchor that captures the **technique** (contour behavior, palette structure, texture logic) over one that captures a **signature** (a recognizable character design, a distinctive motif, a personal visual trademark),
3. never encode an artist's name in a prompt, contract, or constraint as a style shorthand — compile the observable properties instead,
4. record the decision in `style-decision-log.md` so it is visible later rather than buried in an anchor manifest.

Attributable technique references from studios, press kits, and production breakdowns carry none of this weight and are preferred for that reason as well as for provenance. Use `references/reference-search-policy.md` for the full policy.

## Reference presentation

Do not dump large search-result lists on the user.

Curate a small **Reference Board** for the current unresolved dimension cluster. Prefer 3–6 candidates unless the decision genuinely needs more.

For each candidate, show when the runtime supports it:
- preview/thumbnail,
- reference ID,
- source/domain,
- why it was selected,
- which dimensions it is strong for,
- any known dimensions that should **not** be copied,
- accessibility caveat when relevant.

If visual preview cannot be rendered, present the canonical source link plus a concise evidence summary and clearly label that visual verification is limited. Never substitute a textual description for actual visual inspection without disclosing the limitation.

Use interactive selection to capture feedback such as:
- prefer REF-003 overall,
- line from REF-003 + texture from REF-011,
- all are too polished,
- keep current palette but search for a rougher line system,
- none of these; revise direction.

## Structured anchor locking

Do not lock whole reference images as undifferentiated style sources.

Lock **dimensions and roles**.

Example concept:

```text
REF-017
├─ line                 → LOCKED
├─ texture              → LOCKED
├─ palette              → DO NOT USE
├─ lighting             → DO NOT USE
└─ character proportion → N/A
```

Supported anchor roles may include:
- `style_anchor`,
- `identity_anchor`,
- `palette_anchor`,
- `geometry_anchor`,
- `category_anchor`,
- `line_anchor`,
- `texture_anchor`,
- `lighting_anchor`,
- `composition_anchor`,
- `ui_anchor`.

`style-anchor-manifest.yaml` must state exactly which fields/dimensions each anchor governs and any excluded dimensions.

Prefer **progressive style lock**. Lock validated dimensions while leaving unrelated uncertain dimensions open. A later UI revision must not automatically invalidate a locked character line system.

## Calibration

Use a representative minimal set such as:
- character,
- structural environment,
- interactive gameplay object,
- UI button/panel,
- icon,
- background fragment,
- FX.

Do not generate A/B/C merely because a decision is unresolved. Use conceptual interactive clarification first when the choice can be meaningfully described.

Create visual alternatives only when the remaining ambiguity is genuinely visual and cannot be resolved reliably through words/references alone.

Convert feedback such as `line from B, color from A, less texture` into structured rules, anchor changes, and/or negative constraints **before** regenerating.

## Feedback diagnosis and delta loop

A user rejection is not an instruction to restart research.

When the user is dissatisfied:
1. diagnose what is wrong,
2. identify affected dimensions/categories,
3. classify whether the issue is a preference change, anchor mismatch, generation failure, or negative-pattern violation,
4. preserve unaffected locked dimensions,
5. inspect existing corpus coverage,
6. choose the smallest sufficient loop level,
7. only search again when current evidence is insufficient.

Loop levels:
- `L0_MICRO`: parameter/intensity adjustment; no search; preserve anchors,
- `L1_RESELECT`: choose/re-rank existing corpus evidence; no new search,
- `L2_DELTA_SEARCH`: targeted search for missing evidence in specific dimensions,
- `L3_BRANCH_RESET`: reopen one category/domain such as environment or UI while preserving unrelated locks,
- `L4_DIRECTION_RESET`: broad art-direction restart only when the user rejects the overall direction or explicitly requests it.

Use `references/style-loop-policy.md` for escalation, search budgets, corpus coverage, invalidation, and query-memory rules.

## Negative style constraints

Do not rely on vague constraints such as `do not look AI-generated`, `not generic`, or `not too polished` as final production rules. Diagnose them into observable visual symptoms.

Represent negative constraints as persistent structured rules with a positive counterpart.

Supported types:
- `HARD_FORBIDDEN`: presence is a style failure,
- `SOFT_AVOID`: undesirable unless context justifies it,
- `BOUNDED`: allowed only within a controlled range/intensity,
- `ANTI_REFERENCE`: explicitly reject a dimension from a particular reference.

Every meaningful negative constraint should record:
- ID,
- category/dimension,
- type/severity,
- observable forbidden behavior,
- `DO INSTEAD` positive counterpart,
- scope (`global`, category, family, asset),
- origin (`user`, reference analysis, calibration feedback, runtime finding),
- status,
- verification guidance.

Example:

```text
AVOID: perfectly uniform vector-smooth contours
DO INSTEAD: use restrained hand-drawn contour irregularity with readable silhouettes
```

Treat statements such as `this feels AI-generated` as **diagnostic triggers**, not final rules. Clarify whether the symptom is over-polished gradients, purposeless micro-detail, generic symmetry, arbitrary decoration, default cinematic rim light, excessive glow, incoherent texture, generic mascot proportions, or another observable cause.

When the user rejects part of a reference (`I like the line, not the lighting`), preserve the accepted dimension as positive evidence and convert the rejected dimension into negative evidence when useful.

Use `references/negative-constraint-policy.md` for detailed taxonomy and ledger behavior.

## Anti-drift generation handoff

Downstream generation must consume:

```text
Locked Positive Rules
+ Scoped Approved Anchors
+ Negative Constraint Ledger
+ Category Overrides
+ Runtime Readability Constraints
```

Generation must not introduce a new art direction merely to make an asset look more polished or visually impressive.

If generation repeatedly violates a locked style rule, route the problem to generation/QC rather than reopening the art direction without evidence that the style itself is wrong.

## Readiness gates

- `STYLE_DIRECTION_READY`: emotional tone, dimensionality, shape language, line/rendering approach, color/value, texture, major negative constraints, and no blocking reference conflict.
- `REFERENCE_GROUNDED`: production-critical style dimensions have sufficient accessible evidence or explicit user-approved non-reference rules; critical references have scoped roles and provenance.
- `CALIBRATION_READY`: direction ready + reference grounded + category rules + calibration set + output constraints.
- `ASSET_GENERATION_READY`: global/category rules locked, production-critical anchors approved, constraint ledger locked enough for generation, no blocker conflicts.
- `STYLE_PRODUCTION_READY`: generation ready + runtime readability/state visualization/output consistency rules validated.

## Outputs

Primary outputs:

```text
ArtStyle.md
art-style.yaml
style-requirement-state.yaml
style-decision-log.md
style-anchor-manifest.yaml
calibration-plan.yaml
reference-corpus.yaml
reference-search-history.yaml
style-constraint-ledger.yaml
style-loop-state.yaml
```

The machine-readable artifacts are the production source of truth. `ArtStyle.md` is the human-readable view.

## Completion criteria

A style phase is complete only when:
- the requested readiness gate passes,
- blocking reference/accessibility conflicts are resolved or explicitly accepted,
- production-critical visual dimensions are confirmed/locked,
- negative constraints are specific enough to verify,
- approved anchors have scoped roles,
- unresolved dimensions are explicit,
- downstream generation can proceed without inventing missing art direction.
