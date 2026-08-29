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
game-asset-generator       → image candidates        [scripts/check_alpha.py, import_candidates.py]
   ↓
game-asset-normalizer      → engine-ready geometry     [scripts/normalize.py]
   ↓
game-asset-qc              → contract conformance      [scripts/technical_check.py]
   ↓
game-engine-integrator     → atlases, imports, budgets [scripts/pack_atlas.py, budget_check.py]
   ↓
runtime-visual-validator   → does it work in the game
```

`game-art-production-orchestrator` coordinates all of it and never does any of it.

## What makes this different from a prompt library

**Deterministic work runs in code, not prose.** Trimming, scaling, canvas placement, hashing, contrast measurement, colour-vision simulation, atlas packing, and budget accounting are arithmetic. Four stages ship scripts that do them; the agent reads the output and makes the judgment calls the script cannot.

**Identity is computed, not asserted.** Every record names its inputs by `content_hash`. `validate_project.py` verifies each one against the bytes on disk, so a QC approval bound to a file that has since changed is *detected* rather than quietly trusted. Without that, dependency-aware invalidation is a slogan.

**Symptom location and root ownership are separate decisions.** `contracts/routing.yaml` maps 20 symptom classes to a root owner, an invalidation scope, and a revalidation scope. It is the single source of truth — the routing table used to be restated in five documents, and they drifted.

**Rejection becomes durable knowledge.** "This looks too AI-generated" is a diagnostic trigger, not a rule. It gets decomposed into observable constraints with positive counterparts, which persist in a ledger instead of evaporating into one prompt.

**Partial evidence never promotes.** Supplied screenshots are not runtime approval. A high-risk untested context forces `partial_validation_only`. The validator enforces both mechanically.

## What this does not do

**It ships no image generator.** There is no provider integration here, and there is no plan to hide that behind one. `game-asset-generator` compiles a `generation-contract.yaml` and a provider-facing `prompt.md`; the image itself comes from whatever image capability the runtime has, or from a tool you run yourself.

That second path is a first-class one, not a fallback with a dead end at the far side:

```bash
npx game-production-skills install                # contracts and prompts
# ... produce the images with your own tool ...
python3 skills/game-asset-generator/scripts/import_candidates.py \
    --project-root . --asset-id AST-GATE-CLOSED --image ~/out/gate_a.png \
    --capability external-tool --model "<what actually ran>" --seed not_exposed
```

The imported candidate is hashed, bound to the contract it was made from, alpha-screened, and consumable by normalization like any other. It is *not* marked selected and its visual dimensions are *not* scored, because those are judgments.

So the honest description is that this is a production-management and failure-routing system for game art. It makes a good image model's output traceable, verifiable, and reworkable without collateral regeneration. It will not, by itself, draw anything.

**The anti-drift machinery is specified but not yet measured.** Scoped anchors, the negative-constraint ledger, and the `G0`–`G4` escalation levels are the reason to use this over a prompt file, and they are the part with no executable evidence behind them. `evals/` runs 30 deterministic cases; 23 more are written and need a model harness. See ARCHITECTURE.md §10.

**Coverage is 2D raster.** The deterministic layer reads and writes PNG. Animation clips are modelled and checked (ordered families, frame continuity, sprite sheets with frame maps), but runtime validation of a clip still needs frame-sequence evidence that the evidence model does not yet carry. `generated_vector`, `generated_3d`, `procedural`, and `shader_or_particle` are valid planning strategies with no downstream tooling, and there is no tileset or nine-slice model. Specification, art direction, planning, and failure routing are genre-neutral; the executable layer is narrower.

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
python3 scripts/run_evals.py             # routing, handoff, lineage, harness self-test
python3 scripts/run_model_evals.py       # triggering and gates; needs a model backend
```

Requires Python 3 with `pyyaml`; the image scripts also need `Pillow`. The npm package itself has no runtime dependencies.

## Upgrading from 0.1.x

`0.2.0` moves the contract from v2 to v3 and is a breaking change. No asset regeneration is required — the changes are to record shape, not to asset content.

```bash
npx game-production-skills install --force   # installed skills now carry their own contracts
npx game-production-skills validate          # reports everything that still needs updating
```

`CHANGELOG.md` has the full migration: the `version` bumps, the new `engine_integration` path key and stage, and converting `hash: unknown` lineage fields to real `content_hash` digests.

Two behaviour changes are worth knowing about before you run the validator, because a project that was previously "green" may not be:

- A QC report bound to a `content_hash` that is no longer the active normalized output does not count as an approval for that asset.
- A runtime report claiming approval while the build was not executable, or while a high-risk context went untested, is rejected.

Both were previously possible to record.

## Contributing

`CONTRIBUTING.md` covers the rules that keep this consistent — chiefly that contracts live in `contracts/` and are referenced rather than restated, and that any relative path a skill document names must resolve inside the installed skill directory.

## License

MIT
