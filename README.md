# AI-Native Game Production Skills

Composable agent skills for game specification, art direction, asset planning, generation, normalization, quality control, and runtime visual validation.

## Install

### Option 1 — `npx` package installer

Install all skills into the current project:

```bash
npx game-production-skills install
```

Install selected skills only:

```bash
npx game-production-skills install game-spec-builder art-style-builder
```

Replace already-installed copies:

```bash
npx game-production-skills install --force
```

By default skills are installed to:

```text
.agents/skills/
```

A custom output directory is also supported:

```bash
npx game-production-skills install --output .agents/skills
```

### Option 2 — standard Agent Skills CLI

Because this repository exposes each skill under `skills/<skill-name>/SKILL.md`, it can also be consumed directly through the public Agent Skills CLI:

```bash
npx skills add rolot789/tokencat --all
```

Install a specific skill:

```bash
npx skills add rolot789/tokencat --skill game-spec-builder
```

### Option 3 — npm dependency

```bash
npm install --save-dev game-production-skills
npx game-production-skills install
```

## List available skills

```bash
npx game-production-skills list
```

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

## Development

Validate the repository:

```bash
python -m pip install pyyaml
python scripts/doctor.py .
npm run check
npm run pack:check
```

Contribution conventions are documented in [`CONTRIBUTING.md`](CONTRIBUTING.md). Changes should go through pull requests and use Conventional Commits. Squash merge is preferred for `main`.

## npm publishing

The repository includes `.github/workflows/publish-npm.yml`.

A GitHub Release triggers:

```bash
npm publish --access public --provenance
```

The repository owner must configure npm publishing authorization before the first release. The current workflow supports an `NPM_TOKEN` repository secret; npm Trusted Publishing can replace the token flow later.

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

## License

MIT
