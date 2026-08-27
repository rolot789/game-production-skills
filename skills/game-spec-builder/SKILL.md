---
name: game-spec-builder
description: Build and lock a production-usable game specification through adaptive interviews with a game designer or planner. Maintain a structured requirement graph, distinguish confirmed/proposed/inferred decisions, detect conflicts, ask high-impact questions first, and emit both human-readable GameSpec.md and machine-readable game-spec.yaml.
---

# Game Spec Builder

## Purpose

Turn an incomplete game concept into a production-usable game specification through structured, adaptive elicitation.

This skill does **not** generate a game design document in one pass from a vague prompt.

It must:

```text
Initial Game Concept
        ↓
Requirement Graph
        ↓
Interactive Clarifying Questions
        ↓
Decision State Updates
        ↓
Conflict / Dependency Checks
        ↓
Readiness Gates
        ↓
LOCKED GameSpec
```

The goal is:

> Remove the smallest number of high-impact ambiguities required to make downstream implementation and asset planning deterministic enough to proceed.

## Core principles

1. **Interview, do not invent.** Never silently convert guesses into confirmed requirements.
2. Track requirement status as `UNSEEN`, `UNRESOLVED`, `INFERRED`, `PROPOSED`, `CONFIRMED`, `CONFLICT`, `LOCKED`, or `NOT_APPLICABLE`.
3. `INFERRED` and `CONFIRMED` are never equivalent.
4. Ask high-impact questions first: downstream impact × uncertainty × implementation cost × reversibility.
5. Use progressive disclosure: normally 1–3 tightly related questions per interaction.
6. Separate `ASK`, `PROPOSE`, and `INFER` decisions.
7. Activate branch-specific requirements only when their parent branch is active.
8. Detect conflicts early and do not silently resolve them.
9. Lock by readiness stage rather than requiring the entire game to be specified before useful work begins.
10. **Use interactive structured input for real design decisions whenever the runtime supports it.** Do not make the user answer printed `1-A / 2-B / 3-C` menus when an interactive question tool is available.

## Interactive clarification policy

For preference-sensitive, branching, approval, or conflict-resolution decisions, prefer the runtime's structured user-input tool, such as `AskUserQuestion`, `ask_user_question`, `request_user_input`, or an equivalent interactive multiple-choice mechanism.

### Required behavior when an interactive tool is available

- Use the interactive tool instead of printing a numbered option menu in normal chat.
- Ask 1–3 tightly related questions per interaction. If the tool supports multiple questions in one call, group only one coherent decision cluster.
- Prefer **2–4 concrete options** per question.
- Options should be mutually exclusive for single-select questions and must describe the meaningful tradeoff, not just a vague label.
- Mark a recommended option only when the current GameSpec provides enough evidence for a recommendation.
- Allow `Other` / custom input when the designer may legitimately want a direction outside the proposed options.
- Use multi-select only when several choices can simultaneously be valid requirements.
- Use free-text input for names, original mechanics, narrative concepts, numeric constraints, or other cases where constrained choices would distort intent.
- Do not ask questions whose answers are already present in the current conversation, GameSpec, repository, or other authoritative project artifacts.
- If the user skips or cancels a material question, keep the requirement `UNRESOLVED`; never infer approval from silence.

### Suggested structured question shape

```text
header: short decision label
question: concrete decision with relevant context
options:
  - label: concise choice
    description: consequence / tradeoff
  - label: concise choice
    description: consequence / tradeoff
multiSelect: false
customAnswer: allowed when useful
```

The exact tool schema is runtime-dependent. Follow the actual available tool contract rather than inventing unsupported fields.

### Decision-state mapping

- Answer selected by the user → record as `CONFIRMED` unless the user explicitly describes it as tentative.
- Recommended default shown but not accepted → `PROPOSED`.
- Logical consequence derived from confirmed facts → `INFERRED`.
- Conflicting interactive answers → `CONFLICT` until resolved.
- Explicit freeze/finalization → eligible `CONFIRMED` requirements become `LOCKED`.

### Fallback behavior

Structured input may be unavailable in non-interactive execution modes or some runtime modes. If no interactive question tool is available, or a tool call explicitly reports that structured input is unavailable:

1. fall back to a compact Markdown question,
2. show the same 2–4 option labels and tradeoffs,
3. include `Other` when useful,
4. ask for a direct answer,
5. do not proceed past a blocking ambiguity until the user answers or explicitly delegates the choice.

The fallback is compatibility behavior, not the preferred interview UX.

## Requirement domains

Base taxonomy: vision, gameplay, controls, camera, world, level_design, ui_ux, audio, and technical. Extend only when the concept requires it.

## Interview workflow

1. Parse all current information and preserve confirmed content.
2. Identify active unresolved branches; do not ask irrelevant branches.
3. Rank the next questions by readiness blocker, conflict, downstream impact, cost, reversibility, and uncertainty.
4. Convert the highest-value unresolved decision cluster into interactive structured questions when the runtime supports them.
5. Wait for the user's answers before advancing through blocking decisions.
6. Update values/statuses, activate dependencies, close irrelevant branches, detect conflicts, and record decisions.
7. Propose defaults only when a sensible default exists; keep them `PROPOSED` until accepted.
8. Evaluate readiness after meaningful updates.
9. When explicitly frozen/finalized, convert eligible `CONFIRMED` values to `LOCKED` and keep non-blocking unknowns explicit.

## ASK / PROPOSE / INFER

### ASK

Use for high-impact, preference-sensitive, hard-to-reverse decisions. When structured user input is available, ASK decisions should normally be delivered through the interactive question tool.

### PROPOSE

Use when a sensible default exists. Present the recommendation and alternatives through structured input when approval materially affects downstream work. A recommendation remains `PROPOSED` until selected or otherwise explicitly accepted.

### INFER

Use only for low-risk consequences that follow directly from confirmed information. Do not invoke an interactive question merely to reconfirm a trivial deterministic consequence.

## Readiness gates

- `VISION_READY`: premise, player fantasy, target experience, core loop, design pillars.
- `PROTOTYPE_READY`: core verbs/rules, controls, camera, completion logic, minimal level structure, platform.
- `ART_HANDOFF_READY`: camera/projection, gameplay readability constraints, major entity categories, environment structure, UI screen classes, target display context.
- `ASSET_PLANNING_READY`: visible entities, gameplay states, orientation/direction, screen flow, UI states, semantic animation requirements, runtime footprint rules.
- `PRODUCTION_READY`: prototype requirements plus progression, persistence, onboarding, accessibility baseline, technical constraints, production-facing state definitions, no blocker conflict.

## Outputs

Primary outputs:

```text
GameSpec.md
game-spec.yaml
requirement-state.yaml
decision-log.md
```

Optional outputs: `open-questions.md`, `conflicts.md`.

`game-spec.yaml` is the machine-readable source of truth with stable IDs. `GameSpec.md` is the human-readable view. Never hide inferred, unresolved, or conflicting values.

## Completion criteria

Complete a requested game-spec phase only when the requested readiness gate passes, all blockers/conflicts affecting it are resolved, outputs are internally consistent, and downstream skills can consume `game-spec.yaml` without guessing core behavior.
