# Elicitation Policy

## Purpose

An interview is not a questionnaire. The value of this stage is in *which* questions get asked and in what order, because the designer's attention is the scarce resource and most design questions do not need to be answered yet.

This policy covers question ranking, branch activation, conflict handling, and when to stop.

## The objective

> Remove the smallest number of high-impact ambiguities required to make downstream work deterministic enough to proceed.

Not "produce a complete design document." A spec that answers everything about a game nobody has prototyped is mostly fiction. A spec that answers the six things blocking asset planning is production truth.

## Ranking questions

Score each unresolved decision on four axes and ask the highest first.

### Downstream impact

How many later decisions depend on this one? Camera projection is high — it constrains every asset's geometry, the readability rules, and the entire art direction. A menu's button colour is low.

The strongest signal: does an active readiness gate name it? A gate blocker outranks everything else regardless of the other axes.

### Reversibility

What does it cost to change later? Grid-based versus free movement changes level design, collision, animation, and every environment asset. A difficulty curve is a number in a table.

Prefer asking about irreversible decisions early even when they feel premature, and prefer *deferring* reversible ones even when they feel urgent.

### Uncertainty

How confident can you be without asking? If confirmed facts already constrain the answer to one option, that is an `INFER`, not an `ASK`. Do not spend a question re-confirming a deterministic consequence — it reads as not having been paying attention.

### Preference sensitivity

Would two reasonable designers disagree? If yes, it is an `ASK` no matter how confident you feel. Taste is not inferable, and a guessed preference recorded as `CONFIRMED` is the single most damaging thing this stage can do.

### Composite

```text
priority = downstream_impact × uncertainty × irreversibility
```

with preference sensitivity as an override that forces `ASK` regardless of score.

## Branch activation

Requirements are a graph, not a list. Activate a branch only when its parent is confirmed.

```text
grid_based = CONFIRMED true
    ↓ activates
    movement step size
    collision resolution model
    grid dimensions
    tile footprint rules
    ↓ deactivates
    free-movement acceleration curve      → NOT_APPLICABLE
    continuous collision shape            → NOT_APPLICABLE
```

Two rules:

- **Never ask a question from an inactive branch.** It signals that the previous answer was not registered, and it wastes the designer's attention on a world the game is not in.
- **Explicitly close deactivated branches** as `NOT_APPLICABLE` rather than leaving them `UNSEEN`. The difference matters: `UNSEEN` means "we have not got there yet", `NOT_APPLICABLE` means "this game will never need this". A later reader cannot reconstruct which one you meant.

## Question shape

Ask 1–3 tightly related questions per interaction — one coherent decision cluster, never a scattered survey.

For each option, describe the **consequence**, not the label:

```text
Bad:   "Grid-based" / "Free movement"
Good:  "Grid-based — movement snaps to tiles; puzzles can rely on exact
        adjacency; every environment asset gets a fixed footprint"
       "Free movement — analogue positioning; puzzles need tolerance
        ranges; environment assets need edge blending"
```

The designer is choosing between futures, not between words. If the option text does not describe the future, the answer will not survive contact with it.

Mark a recommendation only when the current spec actually supports one. A recommendation offered without grounds is noise, and worse, it biases an answer you then record as `CONFIRMED`.

## Decision states

Keep these strictly distinct — the whole downstream pipeline treats them differently:

| State | Means | Created by |
|---|---|---|
| `UNSEEN` | not reached yet | initial graph |
| `UNRESOLVED` | asked or needed, no answer | a skipped question |
| `INFERRED` | follows deterministically from confirmed facts | logic |
| `PROPOSED` | a default was offered, not accepted | a recommendation |
| `CONFIRMED` | the designer chose it | an explicit answer |
| `CONFLICT` | two confirmed facts disagree | conflict detection |
| `LOCKED` | frozen; downstream may depend on it | explicit freeze |
| `NOT_APPLICABLE` | this game will never need it | branch deactivation |

Three failure modes to avoid absolutely:

- **Silence is not consent.** A skipped question leaves `UNRESOLVED`, never `PROPOSED → CONFIRMED`.
- **`INFERRED` is not `CONFIRMED`.** Inference is a convenience for low-risk consequences. The moment a downstream stage would make an expensive commitment on an inferred value, promote it to a question instead.
- **A default shown is not a default accepted.** `PROPOSED` stays `PROPOSED` until someone says yes.

## Conflict handling

When two confirmed facts disagree, mark both `CONFLICT` and stop — do not pick a winner.

Present the conflict as the decision it actually is:

```text
CONFLICT: real-time reflex play vs turn-based puzzle solving

CONFIRMED (earlier): "the player should feel time pressure"
CONFIRMED (later):   "the player can take as long as they want to plan"

These cannot both hold. Which survives?
  - Time pressure wins  → the planning phase becomes a timed window
  - Planning wins       → pressure moves to resource scarcity instead
  - Both, separated     → timed action phases alternate with untimed planning
```

The third option is the reason not to resolve conflicts silently: the productive answer is frequently a synthesis that neither original statement contained, and it only appears if the designer sees the tension stated plainly.

Do not carry an unresolved `CONFLICT` past a readiness gate that depends on either side.

## Interactive input

Use the runtime's structured question tool when one exists — `AskUserQuestion` or equivalent. Printing a numbered menu and asking someone to type `2-B` is a worse version of the same interaction.

Fall back to compact prose with named options only when structured input is genuinely unavailable, keeping the same 2–4 options and the same consequence descriptions. The fallback is compatibility behaviour, not a style choice.

Use free text — never constrained options — for names, original mechanics, narrative concepts, and numeric constraints. Forcing those into multiple choice distorts exactly the intent you are trying to capture.

## When to stop

Stop asking when the requested readiness gate passes. Not when the design feels complete, and not when the question list is empty.

Each gate has a specific downstream consumer:

- `ART_HANDOFF_READY` — `art-style-builder` can establish visual direction without inventing gameplay meaning.
- `ASSET_PLANNING_READY` — `game-asset-planner` can decompose entities and expand states without guessing what a state means.
- `PRODUCTION_READY` — the full pipeline, including the accessibility baseline that QC will verify.

After each meaningful update, re-evaluate: *can the next consumer proceed?* If yes, stop and hand off. Remaining unknowns stay explicit in `open-questions.md`, where they are visible rather than blocking.

Continuing to interview past a satisfied gate has a real cost beyond the designer's patience: it produces specification detail that has never been tested against anything, and that detail then gets `LOCKED` and inherited by every downstream stage.
