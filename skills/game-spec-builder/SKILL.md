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
Adaptive Questions
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
5. Use progressive disclosure: normally 1–3 tightly related questions per turn.
6. Separate `ASK`, `PROPOSE`, and `INFER` decisions.
7. Activate branch-specific requirements only when their parent branch is active.
8. Detect conflicts early and do not silently resolve them.
9. Lock by readiness stage rather than requiring the entire game to be specified before useful work begins.

## Requirement domains

Base taxonomy: vision, gameplay, controls, camera, world, level_design, ui_ux, audio, and technical. Extend only when the concept requires it.

## Interview workflow

1. Parse all current information and preserve confirmed content.
2. Identify active unresolved branches; do not ask irrelevant branches.
3. Rank the next questions by readiness blocker, conflict, downstream impact, cost, reversibility, and uncertainty.
4. Ask concise concrete behavior questions.
5. Update values/statuses, activate dependencies, close irrelevant branches, detect conflicts, and record decisions.
6. Propose defaults only when a sensible default exists; keep them `PROPOSED` until accepted.
7. Evaluate readiness after meaningful updates.
8. When explicitly frozen/finalized, convert eligible `CONFIRMED` values to `LOCKED` and keep non-blocking unknowns explicit.

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
