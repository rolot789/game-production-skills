# game-spec-builder

Adaptive game specification skill for Codex/agent workflows.

It converts a partial game idea into a structured, progressively locked specification through designer/planner interviews.

```text
Game Idea
   ↓
game-spec-builder
   ↓
Adaptive Questions
   ↓
Requirement Graph
   ↓
Readiness Gate
   ↓
GameSpec.md
game-spec.yaml
```

## Key design

This is **not** a fixed questionnaire.

Answers activate new requirement branches.

Example:

```text
grid_based = true
        ↓
requires:
- movement step
- collision resolution
- grid dimensions
- tile footprint rules
```

## Requirement states

```text
UNSEEN
UNRESOLVED
INFERRED
PROPOSED
CONFIRMED
CONFLICT
LOCKED
NOT_APPLICABLE
```

## Outputs

- `GameSpec.md`
- `game-spec.yaml`
- `requirement-state.yaml`
- `decision-log.md`

## Suggested install

```text
<repo>/.agents/skills/game-spec-builder/
```
