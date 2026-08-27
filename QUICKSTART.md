# Quickstart

## Setup

```bash
npx game-production-skills install
npx game-production-skills init --name "My Game"
```

Both steps matter. `install` copies the skills; `init` writes `project.yaml`, which every skill resolves artifact paths through. Skills installed without it have no path registry, and stages will write where later stages do not look.

For a jam or a small asset set, add `--profile lite`.

```bash
python3 -m pip install pyyaml Pillow   # needed by the validators and image scripts
```

## A. Starting from a new game idea

1. Run `game-spec-builder`. Continue the interview until at least `ART_HANDOFF_READY`.
2. Run `art-style-builder`. Approve calibration anchors until `ASSET_GENERATION_READY`.
3. Run `game-asset-planner`.
4. Generate **one representative family first** — not the whole tier.
5. Normalize it: `python3 .agents/skills/game-asset-normalizer/scripts/normalize.py …`
6. QC it: `python3 .agents/skills/game-asset-qc/scripts/technical_check.py …`
7. Pack and budget-check it with `game-engine-integrator`.
8. Integrate into the game and run `runtime-visual-validator`.
9. Only then expand to the next tier.

Step 4 is the one people skip. A systemic style problem found on the first family costs one regeneration; found on forty assets it costs forty.

## B. Starting from a locked GameSpec and ArtStyle

Start at `game-asset-planner`. Do not rerun the design interviews unless a downstream blocker proves a locked source must be revised — and when it does, the handoff says exactly which surface may change.

## C. Production tiers

```text
Tier 0 — calibration and style anchors
Tier 1 — P0 core gameplay assets
Tier 2 — P0 states and directions
Tier 3 — core UI
Tier 4 — progression and secondary UI
Tier 5 — decoration, FX, polish
```

Do not scale a later tier while a representative earlier tier still shows a systemic problem.

## D. The usual top-level request

> Inspect the current game-art production state, validate the artifacts, and continue from the earliest incomplete valid stage using `game-art-production-orchestrator`.

## E. Checking your work

```bash
npx game-production-skills validate
```

This verifies schemas, checks every recorded `content_hash` against the bytes on disk, confirms QC verdicts are bound to the outputs they claim to have evaluated, and rejects handoffs using non-canonical field names.

Run it after any rework. It is how you find out that an approval is pointing at a file that no longer exists in that form — which is otherwise invisible until something looks wrong in the build.

## F. When something breaks

Do not fix it where you see it. Classify the symptom against `contracts/routing.yaml`, take the root owner and both scopes from the matching row, and route a handoff with `change_scope` and `preserve_scope` filled in.

`preserve_scope` is the field that does the work. "Fix the contrast" invites a palette redesign; "fix the contrast, preserving the hue family" gets you a contrast fix. The worked example in `examples/gate-family` shows exactly that exchange.

## G. Reading the worked example

```bash
python3 scripts/validate_project.py examples/gate-family
cat examples/gate-family/README.md
```

Three gate states, complete from GameSpec to runtime report, with real hashes and real measurements. Faster than reading the policy documents, and it shows what the fields look like when they are filled in correctly.
