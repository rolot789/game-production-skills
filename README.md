# AI-Native Game Production Skills

Composable agent skills for running a game art pipeline — from game specification and art direction through asset generation, normalization, QC, engine integration, and runtime validation.

The pipeline's premise is that an asset is not a file. It is a specification, its references, its provenance, its runtime metadata, and the evidence that it works — and that when something breaks, the stage where you *see* it is rarely the stage that *owns* it.

## Install

```bash
npx game-production-skills install
npx game-production-skills init --name "My Game"
```

The first command copies the skills into `.agents/skills/`. The second writes `project.yaml` and `.pipeline/`, which every skill resolves artifact paths through — without it the skills have no path registry.

```bash
npx game-production-skills list                              # available skills
npx game-production-skills install game-spec-builder         # selected skills only
npx game-production-skills install --output .claude/skills   # different target
npx game-production-skills init --name "Jam Game" --profile lite
npx game-production-skills validate                          # check your project
```

Also installable with the Agent Skills CLI:

```bash
npx skills add rolot789/game-production-skills --all
npx skills add rolot789/game-production-skills --skill game-spec-builder
```

## Skills

| Skill | Use when |
|---|---|
| `game-spec-builder` | a concept must become a specification others can build from |
| `art-style-builder` | visual direction must be defined, locked, or revised |
| `game-asset-planner` | locked spec and style must become a concrete asset list |
| `game-asset-generator` | asset specs must become image candidates |
| `game-asset-normalizer` | candidates must become engine-ready files with predictable geometry |
| `game-asset-qc` | an asset must be judged against its production contract |
| `game-engine-integrator` | assets must be packed and configured for a specific engine |
| `runtime-visual-validator` | assets must be checked inside the running game |
| `game-art-production-orchestrator` | the question spans the whole pipeline, or a failure must be routed |

## Pipeline

```text
Game Idea
   ↓
game-spec-builder          → what the game means
   ↓
art-style-builder          → what it looks like
   ↓
game-asset-planner         → which assets exist
   ↓
game-asset-generator       → image candidates
   ↓
game-asset-normalizer      → engine-ready geometry     [scripts/normalize.py]
   ↓
game-asset-qc              → contract conformance      [scripts/technical_check.py]
   ↓
game-engine-integrator     → atlases, imports, budgets [scripts/budget_check.py]
   ↓
runtime-visual-validator   → does it work in the game
```

`game-art-production-orchestrator` coordinates all of it and never does any of it.

## What makes this different from a prompt library

**Deterministic work runs in code, not prose.** Trimming, scaling, canvas placement, hashing, contrast measurement, colour-vision simulation, and budget accounting are arithmetic. Three stages ship scripts that do them; the agent reads the output and makes the judgment calls the script cannot.

**Identity is computed, not asserted.** Every record names its inputs by `content_hash`. `validate_project.py` verifies each one against the bytes on disk, so a QC approval bound to a file that has since changed is *detected* rather than quietly trusted. Without that, dependency-aware invalidation is a slogan.

**Symptom location and root ownership are separate decisions.** `contracts/routing.yaml` maps 20 symptom classes to a root owner, an invalidation scope, and a revalidation scope. It is the single source of truth — the routing table used to be restated in five documents, and they drifted.

**Rejection becomes durable knowledge.** "This looks too AI-generated" is a diagnostic trigger, not a rule. It gets decomposed into observable constraints with positive counterparts, which persist in a ledger instead of evaporating into one prompt.

**Partial evidence never promotes.** Supplied screenshots are not runtime approval. A high-risk untested context forces `partial_validation_only`. The validator enforces both mechanically.

## Profiles

`full` is the default: every stage, full lineage discipline, ceiling `SHIPPABLE`.

`lite` exists because eight stages is the wrong answer for a game jam or a six-icon UI set — three artifacts, ceiling `QC_APPROVED`, engine integration and runtime validation optional. It relaxes file count, never the locked-versus-inferred distinction, scoped anchors, or hash lineage. See `contracts/profiles/`.

## Worked example

```bash
python3 scripts/validate_project.py examples/gate-family
```

A complete run for a three-state gate family. Every hash is real, every measurement was produced by the actual tools, and `tools/build_example.py` regenerates the whole derived layer byte-for-byte.

It is worth reading for one thing in particular: a QC contrast failure that routes to `art-style-builder` rather than to the generator, because the candidates implemented the locked palette faithfully and the palette was the defect. That routing decision, and the `preserve_scope` that kept the fix from redesigning the palette, is what the toolkit is for.

## Verifying

```bash
python3 scripts/doctor.py .              # skills are well formed
python3 scripts/sync_contracts.py --check # mirrored contracts are current
python3 scripts/validate_contracts.py    # the toolkit agrees with itself
python3 scripts/test_install.py          # a real install resolves every documented path
python3 scripts/validate_project.py DIR  # your project is consistent
python3 scripts/run_evals.py             # routing, handoff, and lineage evals
```

Requires Python 3 with `pyyaml`; the image scripts also need `Pillow`. The npm package itself has no runtime dependencies.

## License

MIT
