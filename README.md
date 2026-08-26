# AI-Native Game Production Skills

Composable agent skills for building a game production pipeline from game specification and art direction through asset generation, QC, and runtime validation.

## Install

### Install all skills

```bash
npx game-production-skills install
```

Skills are installed to:

```text
.agents/skills/
```

### Install selected skills

```bash
npx game-production-skills install game-spec-builder art-style-builder
```

### List available skills

```bash
npx game-production-skills list
```

### Reinstall existing skills

```bash
npx game-production-skills install --force
```

### Agent Skills CLI

The repository can also be installed directly with the Agent Skills CLI:

```bash
npx skills add rolot789/game-production-skills --all
```

Or install one skill:

```bash
npx skills add rolot789/game-production-skills --skill game-spec-builder
```

## Skills

| Skill | Purpose |
|---|---|
| `game-spec-builder` | Builds and locks a structured game specification through adaptive design interviews. |
| `art-style-builder` | Defines and locks art direction, calibration rules, and approved visual anchors. |
| `game-asset-planner` | Converts GameSpec + ArtStyle into semantic asset inventories and production specs. |
| `game-asset-generator` | Compiles asset specs and references into reproducible generation jobs and candidates. |
| `game-asset-normalizer` | Normalizes generated assets for predictable runtime scale, canvas, alpha, anchor, and pivot behavior. |
| `game-asset-qc` | Validates technical quality, style consistency, family consistency, and gameplay readability. |
| `runtime-visual-validator` | Validates approved assets inside real game scenes and detects runtime visual regressions. |
| `game-art-production-orchestrator` | Coordinates the complete pipeline, readiness gates, handoffs, failure routing, and invalidation. |

## Pipeline

```mermaid
flowchart TD
    A[Game Idea / Existing Design] --> B[game-spec-builder]
    B --> C[LOCKED GameSpec]
    C --> D[art-style-builder]
    D --> E[LOCKED ArtStyle + Approved Style Anchors]
    E --> F[game-asset-planner]
    F --> G[Asset Manifest + Asset Specs]
    G --> H[game-asset-generator]
    H --> I[Generated Candidates + Provenance]
    I --> J[game-asset-normalizer]
    J --> K[Engine-ready Runtime Candidates]
    K --> L[game-asset-qc]
    L --> M[QC-approved Assets]
    M --> N[runtime-visual-validator]
    N --> O[RUNTIME_APPROVED / SHIPPABLE]

    P[game-art-production-orchestrator] -. gates / handoffs / invalidation .-> B
    P -.-> D
    P -.-> F
    P -.-> H
    P -.-> J
    P -.-> L
    P -.-> N
```

## Asset Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PLANNED
    PLANNED --> READY_FOR_GENERATION
    READY_FOR_GENERATION --> GENERATED
    GENERATED --> NORMALIZED
    NORMALIZED --> QC_APPROVED
    QC_APPROVED --> RUNTIME_APPROVED
    RUNTIME_APPROVED --> SHIPPABLE
    SHIPPABLE --> [*]

    READY_FOR_GENERATION --> GENERATION_REWORK
    GENERATION_REWORK --> READY_FOR_GENERATION

    GENERATED --> NORMALIZATION_BLOCKED
    NORMALIZATION_BLOCKED --> GENERATED

    NORMALIZED --> QC_REWORK
    QC_REWORK --> READY_FOR_GENERATION

    QC_APPROVED --> RUNTIME_REWORK
    RUNTIME_REWORK --> READY_FOR_GENERATION

    PLANNED --> INVALIDATED
    READY_FOR_GENERATION --> INVALIDATED
    GENERATED --> INVALIDATED
    NORMALIZED --> INVALIDATED
    QC_APPROVED --> INVALIDATED
    RUNTIME_APPROVED --> INVALIDATED
```

## License

MIT
