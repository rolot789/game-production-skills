# Quickstart

## A. Starting from a new game idea

1. Run `game-spec-builder`.
2. Continue the adaptive interview until at least `ART_HANDOFF_READY`.
3. Run `art-style-builder`.
4. Approve calibration anchors until `ASSET_GENERATION_READY`.
5. Run `game-asset-planner`.
6. Generate only a representative P0 family first.
7. Normalize.
8. Run asset QC.
9. Integrate into the game.
10. Run runtime visual validation.
11. Expand to the next asset tier only after the representative batch passes.

## B. Starting from already locked GameSpec + ArtStyle

Start at:

```text
game-asset-planner
```

Do not rerun design interviews unless a downstream blocker proves that a locked source must be revised.

## C. Recommended production tiers

```text
Tier 0 — calibration/style anchors
Tier 1 — P0 core gameplay assets
Tier 2 — P0 states/directions
Tier 3 — core UI
Tier 4 — progression/secondary UI
Tier 5 — decoration/FX/polish
```

## D. Primary orchestration command concept

When the toolkit is installed, the normal top-level request is:

> Inspect current game-art production state, validate artifacts, and continue from the earliest incomplete valid stage using `game-art-production-orchestrator`.
