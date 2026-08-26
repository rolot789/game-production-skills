# AI-Native Game Production Toolkit

A repository-ready skill pack for turning a game idea into runtime-validated game art assets.

## Pipeline

```text
Game Idea / Existing Design
        ↓
game-spec-builder
        ↓
LOCKED GameSpec
        ↓
art-style-builder
        ↓
LOCKED ArtStyle + Approved Style Anchors
        ↓
game-asset-planner
        ↓
Asset Manifest + Production Specs
        ↓
game-asset-generator
        ↓
Generated Candidates + Provenance
        ↓
game-asset-normalizer
        ↓
Engine-ready Runtime Candidates
        ↓
game-asset-qc
        ↓
QC-approved Assets
        ↓
runtime-visual-validator
        ↓
RUNTIME_APPROVED / SHIPPABLE
```

`game-art-production-orchestrator` sits above the chain and controls readiness gates, handoffs, failure routing, invalidation, and lifecycle promotion.

## Included skills

| Stage | Skill | Main responsibility |
|---|---|---|
| Game design | `game-spec-builder` | Adaptive requirements interview and locked game specification |
| Art direction | `art-style-builder` | Adaptive art direction, calibration, style anchors, style lock |
| Asset planning | `game-asset-planner` | Semantic asset inventory, MRAU decomposition, variants, production specs |
| Generation | `game-asset-generator` | Prompt/job compilation, reference resolution, provenance-aware generation |
| Normalization | `game-asset-normalizer` | Deterministic canvas/scale/alpha/anchor/pivot/export processing |
| Asset QC | `game-asset-qc` | Technical, semantic, style, family, and gameplay-readability QC |
| Runtime QC | `runtime-visual-validator` | Scene-level visual validation using real runtime evidence |
| Orchestration | `game-art-production-orchestrator` | Pipeline state, handoffs, gates, failure routing, invalidation |

## Install into a repository

```bash
python scripts/install_toolkit.py /path/to/your/repo
```

This installs skills under:

```text
<repo>/.agents/skills/
```

Then bootstrap production folders:

```bash
python scripts/bootstrap_project.py /path/to/your/repo --name "My Game"
```

## Validate the toolkit

```bash
python scripts/doctor.py .
```

## Production state

The orchestrator uses:

```text
.pipeline/game-art-production-state.yaml
```

Asset lifecycle:

```text
PLANNED
→ READY_FOR_GENERATION
→ GENERATED
→ NORMALIZED
→ QC_APPROVED
→ RUNTIME_APPROVED
→ SHIPPABLE
```

## Source-of-truth policy

1. Locked Game Spec
2. Locked Art Style
3. Approved Style Anchors
4. Asset Manifest / per-asset specs
5. Generation records
6. Normalization records
7. Asset QC reports
8. Runtime validation reports

Downstream stages do not silently rewrite upstream decisions.
