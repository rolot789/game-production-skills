---
name: art-style-builder
description: Build and lock a production-usable game art style through adaptive interviews, structured visual requirements, calibration asset planning, reference comparison, and approved style anchors. Emit ArtStyle.md, art-style.yaml, and style-anchor-manifest.yaml for downstream asset production.
---

# Art Style Builder

## Purpose

Convert incomplete visual intent into an explicit, production-usable art system. A usable style is not a mood phrase or one long prompt; it is **structured visual invariants + approved visual anchors**.

```text
GameSpec + Art Intent / References
→ Visual Requirement Graph
→ Interactive Clarifying Questions
→ Draft Art Style
→ Calibration Set
→ Candidate Comparison
→ Approved Anchors
→ STYLE LOCK
```

## Rules

- Read GameSpec first when available; derive visual constraints but never modify game semantics.
- Track `UNSEEN`, `UNRESOLVED`, `INFERRED`, `PROPOSED`, `CONFIRMED`, `CONFLICT`, `LOCKED`, `NOT_APPLICABLE`.
- Ask 1–3 high-impact visual questions at a time; prioritize gameplay readability, dimensionality/camera, shape language, line/rendering medium, color/value, texture, lighting, then decoration.
- **Use interactive structured input for actual art-direction decisions whenever the runtime supports it.** Do not make the user reply with printed `A/B/C` or `1-A / 2-C` codes when an interactive multiple-choice question tool is available.
- Separate GLOBAL STYLE from CATEGORY OVERRIDES for character, environment, interactive_object, UI, icon, FX, and background.
- Treat negative constraints as first-class `forbidden` rules.
- Never silently merge conflicting references; declare which dimensions each reference governs.
- Do not start mass production before calibration.

## Interactive clarification policy

For unresolved visual direction, reference conflicts, category overrides, calibration choices, or approval decisions, prefer the runtime's structured user-input tool, such as `AskUserQuestion`, `ask_user_question`, `request_user_input`, or an equivalent interactive multiple-choice mechanism.

### Required behavior when an interactive tool is available

- Use the interactive tool instead of printing an option list in chat.
- Ask 1–3 tightly related questions at a time. If multiple questions can be submitted in one call, keep them within one coherent visual decision cluster.
- Prefer **2–4 visually distinct, decision-relevant options**.
- Every option should state the concrete visual consequence or tradeoff.
- Recommend an option only when GameSpec constraints, approved references, or prior confirmed style decisions support that recommendation.
- Include `Other` / custom input when the art director may want a visual direction outside the proposed options.
- Use multi-select only for dimensions that can validly combine, such as selected texture influences or reference roles.
- Use free-text when the user needs to describe a unique visual idea, provide a reference, name a medium, or specify a custom constraint.
- Do not ask the user to reconfirm visual facts already established by approved anchors or locked style rules.
- If a user skips or cancels a production-critical visual decision, keep it `UNRESOLVED`; do not choose a style direction by silence.

### Good interactive question design

Prefer contrastive questions that expose a meaningful production choice.

Examples:

```text
header: UI Texture
question: How much of the global crayon texture should carry into UI panels?
options:
  - label: Cleaner UI
    description: Preserve hand-drawn shape language, but reduce grain for readability.
  - label: Same Texture
    description: Apply nearly the same crayon treatment as world/character art.
  - label: Minimal Texture
    description: Keep only subtle edge irregularity and near-flat fills.
multiSelect: false
```

```text
header: Line Weight
question: Which contour treatment should become the global default?
options:
  - label: Thick Charcoal
    description: Strong silhouette readability, heavier handmade presence.
  - label: Medium Crayon
    description: Balanced readability and softness.
  - label: Thin Pencil
    description: More delicate detail, lower small-size readability.
multiSelect: false
```

The exact tool schema is runtime-dependent. Follow the actual available tool contract rather than inventing unsupported fields.

### Decision-state mapping

- User-selected visual direction → `CONFIRMED` unless explicitly tentative.
- Recommended style shown but not accepted → `PROPOSED`.
- Visual consequence derived from GameSpec or another confirmed style rule → `INFERRED`.
- References or answers that disagree on the same governed dimension → `CONFLICT`.
- Explicit style freeze/finalization → eligible `CONFIRMED` rules become `LOCKED`.

### Fallback behavior

Structured input may be unavailable in non-interactive execution modes or some runtime modes. If no interactive question tool is available, or a tool call reports that structured input is unavailable:

1. ask the same question in compact Markdown,
2. provide 2–4 named options with visual tradeoffs,
3. include `Other` when useful,
4. accept a direct natural-language answer rather than requiring coded replies,
5. do not advance past a blocking art-direction ambiguity without an answer or explicit delegation.

The fallback is compatibility behavior, not the preferred interaction model.

## Interview workflow

1. Read GameSpec and all current visual intent/references.
2. Preserve confirmed style rules and approved anchors.
3. Identify unresolved visual dimensions and reference conflicts.
4. Rank the next decision cluster by gameplay readability impact, downstream asset impact, cost of rework, reversibility, and uncertainty.
5. Convert the highest-value unresolved cluster into structured interactive questions when available.
6. Wait for answers before locking production-critical visual dimensions.
7. Update style requirement states and activate category-specific branches only when needed.
8. Build or revise the calibration plan.
9. Use candidate comparison only for genuinely unresolved visual dimensions.
10. Convert approval feedback into structured rules and scoped anchors before production expansion.

## Calibration

Use a representative minimal set such as character, structural environment, interactive object, UI button/panel, icon, background fragment, and FX.

Do not generate A/B/C merely because the skill is in an interview phase. Use visual candidates only when seeing actual visual alternatives is necessary to resolve a style dimension.

When a style dimension can be decided conceptually before generation, use an interactive clarifying question first. Examples include:
- UI cleaner than global art vs same texture treatment,
- flat vs dimensional material treatment,
- thick vs medium vs thin contour hierarchy,
- restrained vs expressive grain,
- state differentiation through value, shape, outline, or combined treatment.

Create visual A/B/C candidates only when a decision remains genuinely visual after conceptual clarification. Convert feedback such as “line from B, color from A, less texture” into structured rules before regenerating.

Approved anchors must declare roles such as `style_anchor`, `identity_anchor`, `palette_anchor`, `geometry_anchor`, or `category_anchor`, plus the fields they govern.

## Readiness

- `STYLE_DIRECTION_READY`: emotional tone, dimensionality, shape language, line/rendering approach, color/value, texture, major forbidden rules.
- `CALIBRATION_READY`: direction ready + category rules + calibration set + output constraints.
- `ASSET_GENERATION_READY`: global/category rules locked, production-critical anchors approved, forbidden rules locked, no blocker conflicts.
- `STYLE_PRODUCTION_READY`: generation ready + runtime readability/state visualization/output consistency rules.

## Outputs

```text
ArtStyle.md
art-style.yaml
style-requirement-state.yaml
style-decision-log.md
style-anchor-manifest.yaml
calibration-plan.yaml
```

Downstream asset generation must consume the locked structured style and scoped anchors without inventing new art direction.
