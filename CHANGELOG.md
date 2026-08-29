# Changelog

Versions follow Semantic Versioning. Before 1.0, a minor bump may carry breaking changes.

## Unreleased

An audit of the promotion gates found that the hard half of the lineage model was enforced and the easy half was not: `content_hash` verification was rigorous, and any promotion claim laid on top of it was accepted. Four defects, all reproduced before being fixed, all now covered by executable evals.

### Fixed

- **Two stages disagreed deterministically, and the routing loop did not terminate.** `normalization.padding` is optional and defaults to `0`. At zero padding the normalizer scales content to fill the canvas exactly and exits `0`; `technical_check.py` then failed the same file on `no_edge_clipping`, which routes `MECHANICAL_PROCESSING_DEFECT` back to the normalizer, which reproduces identical bytes. Edge contact is now only evidence of clipping when the AssetSpec reserved padding, and `no_edge_clipping` (content lost to the canvas) is kept distinct from `padding_respected` (padding contract broken, nothing lost). The worked example uses `padding: 8`, so CI never saw this.
- **`INTEGRATION_READY` promotion was never checked.** The lifecycle evidence table mapped it to `None` and the next line skipped it. Deleting `budget-report.yaml` outright and claiming the promotion passed validation. It now requires a promoting budget report, and a promoting integration plan that lists the asset when one exists.
- **`SHIPPABLE` had no validator at all.** It is the one promotion no single report authorizes — it claims every stage the active profile requires agrees about one lineage — and it was absent from the evidence table entirely. It is now checked as a chain.
- **The active profile was never enforced against a project.** `validate_project.py` did not read `contracts/profiles/`; the `profile` field only produced one lite-ceiling warning. A `full` project missing whole stages passed. Required stages and artifacts are now enforced, gated on what each asset has actually reached so a run in progress is never failed for work it has not started.
- **Runtime approval bound to a stale normalized output was accepted.** The QC binding was checked and the runtime one was not, so QC and runtime could each be internally consistent while describing different generations — the mixed-version case `ARCHITECTURE.md` uses as its example.
- **`normalize.py` checked padding on the horizontal axis and the bare canvas on the vertical one,** letting a vertically overflowing placement pass the normalizer and fail QC instead.

### Added

- **`rework_budget`** in `toolkit-contract.yaml`. `generation_budget` bounds the edge that spends image budget; this bounds every other routing edge, which costs nothing per attempt and so has no natural stopping point. Two routes to the same owner for the same `reason_code` on one subject, counted in `assets.<id>.rework_attempts`, then a `BLOCKER` naming both stages. An attempt counts as progress only when the receiving stage produced a new `content_hash`.
- **Five executable lineage evals** (`LIN-007`–`LIN-011`) covering each promotion gate and the rework cap. Eval cases may now carry a list of mutations, and `delete_file` joins the mutation types.
- **`runtime-validation-plan.yaml` and `evidence-manifest.yaml` in the worked example**, which the `full` profile required and the example did not ship — found by the new profile enforcement. Every capture id is now backed by hashed bytes on disk: a headless composite of the runtime asset over a declared background at the intended display size, recorded as such rather than described as a screenshot.
- **`pack_atlas.py`** — the atlas packer the engine-integration stage claimed and never shipped. Membership stays an agent decision (draw order, lifetime, scene locality); the script does the arithmetic: deterministic shelf placement, padding, dimensions, hashing. It refuses a member whose QC report does not promote or evaluated a different `content_hash` than the file on disk. Tight dimensions by default, `--power-of-two` for targets that need it — on the worked example the difference is 97% fill versus 38%. Adds `atlas-manifest.schema.json`, and `validate_project.py` verifies every member against the active normalized output.

- **`retention` in `toolkit-contract.yaml`, and `retain.py`** — the toolkit said provenance is append-only even when artifacts are superseded, and its file layout said otherwise: normalization records, QC reports, and runtime reports live at fixed per-asset paths and were simply overwritten, so what a rework rejected and why was gone. Meanwhile generation candidates accumulated with no policy at all — at the default budget one asset can produce 24 images across its rework transactions. The single active path stays (a versioned filename would make "the current QC report" a search rather than a lookup); append-only provenance is now satisfied by `.pipeline/history/` and its ledger. `retain.py archive` is content-triggered, so rewriting identical bytes supersedes nothing. `retain.py prune` deletes only candidate images that are neither selected nor consumed by a normalization record and fall outside the last two per job — and never the record, which is the provenance. `validate_project.py` verifies archived bytes and rejects a pruned candidate that is still selected or referenced.
- **`import_candidates.py`** — the return half of the external-generation path. The generator could always emit a complete job for an external tool, and nothing could bring the result back, so `external_job: true` was a dead end. Imported images are hashed, bound to the `generation-contract.yaml` they were made from (it refuses to import without one), alpha-screened, and consumable by normalization like any other candidate. It never marks a candidate `selected` and records only the `output` screening dimension — a script filling in `identity: PASS` would be writing a fabricated verdict that QC later trusts.

### Changed

- **README states what the toolkit does not do.** It ships no image generator, the anti-drift machinery is specified but unmeasured, and the deterministic layer is single-frame 2D raster only. All three were true before and inferable only by reading the source.
- **`budget_check.py` measures real atlases.** `max_atlas_dimension` previously held the largest single *sprite* dimension and was compared against the atlas budget — a check that passed for a reason unrelated to the risk it names, which is worse than no check because it reads green. Atlas dimensions now come from packed atlases, an absent atlas reports `INSUFFICIENT_EVIDENCE`, the sprite figure moves to its own honestly-named `max_sprite_dimension`, and texture memory charges an atlased member to its atlas instead of counting it twice. On the worked example `max_atlas_dimension` goes from `256` (a sprite) to `780` (the atlas).

## 0.2.0

Contract **v2 → v3**. Breaking. Existing projects need the migration below.

An audit of all 8 skills (31 documents, 6,716 lines) found 19 defects, 5 of which broke real installs. All 19 are fixed, each with a check that prevents recurrence.

### Fixed — these broke installed projects

- **Installed skills referenced contract files that were never shipped.** Four `SKILL.md` files pointed at `contracts/rework-handoff-contract.yaml` eight times; the installer only copied `skills/`, so every one of those references was dangling in a real install. Contracts and schemas are now mirrored into each skill's `references/` directory.
- **`npx` users could not create `project.yaml`,** which six skills resolve artifact paths through. `bootstrap_project.py` was never in `package.json` `files`. Adds the `init` command.
- **`game-spec-builder` and `art-style-builder` did not know about `project.yaml`** while every downstream stage resolved through it. The pipeline split silently between stages 2 and 3 — the first two stages wrote to repository-root filenames and everything after looked in `spec/` and `art/`.
- **All five `G0`–`G4` escalation levels existed under two incompatible names** — one set in the contract and skill documents, another in the policy file those documents point at.
- **Two policy documents specified non-canonical rework field names** against the contract they were meant to implement.

### Added

- **`contracts/schemas/`** — 11 JSON Schemas, plus `scripts/validate_project.py`, which verifies recorded `content_hash` values against the bytes on disk, binds QC verdicts to the outputs they claim to have evaluated, and rejects specialist-local aliases and unknown reason codes. Uses a dependency-free subset validator, so the npm package keeps zero runtime dependencies.
- **Deterministic scripts** for the three stages whose work is arithmetic: `normalize.py` (geometry, hashing), `technical_check.py` (conformance, contrast, colour-vision separation), `budget_check.py` (texture memory, atlas dimensions, file size).
- **`contracts/routing.yaml`** — single source of truth for failure routing: 20 symptom classes mapped to a root owner, an invalidation scope, and a revalidation scope.
- **`game-engine-integrator`** — an eighth stage between QC and runtime validation, covering atlas packing, import settings derived from recorded pivots, and measured performance budgets.
- **`examples/gate-family`** — a complete run from GameSpec to runtime report. Every hash and measurement is real, and `tools/build_example.py` rebuilds the derived layer byte-deterministically.
- **Lifecycle transitions** — 14 states with a declared, enforceable transition graph; every transition names the evidence that authorizes it.
- **`lite` / `full` profiles.** `lite` runs six stages with three artifacts and a `QC_APPROVED` ceiling; it relaxes file count, never lineage discipline.
- **Generation budget** — candidate, retry, and same-level repeat caps, symmetric with the existing reference-search budget.
- **Accessibility verification** — the baseline GameSpec declares is now checked downstream (contrast, colour-vision separability, non-colour channel) instead of merely stated.
- **`evals/`** — 24 executable cases (routing, handoff, lineage) and 21 specified for a model harness.
- **Reference policies** for the four skills that had none, including MRAU decomposition and geometry semantics.
- **Living-artist boundary policy** for reference anchoring.
- **`scripts/test_install.py`** — installs into a temporary project and resolves every path the installed documents point at. This is the check that would have caught the shipped install defect.

### Changed

- `validate_contracts.py` rewritten. It previously asserted that specific English sentences appeared in specific files — coupling prose to CI while proving nothing, and excluding the exact two skills that had the path-registry defect. It now compares sets and resolves references across 15 check groups.
- Skill descriptions rewritten as trigger conditions (`Use when …`) with explicit boundaries naming the sibling skill that owns the adjacent case.
- `version` and `content_hash` are required rather than "when available"; sha256 and the equivalence rule are defined.
- README, ARCHITECTURE, QUICKSTART, and CONTRIBUTING rewritten.
- `examples/minimal-project` removed, replaced by `examples/gate-family`.

### Migration from 0.1.x

No asset regeneration is required. The changes are to record shape, not to asset content.

**1. Reinstall the skills.** Installed skills now carry their contracts and schemas inside `references/`, so a stale install still has the dangling paths.

```bash
npx game-production-skills install --force
```

**2. Update `project.yaml`.**

```yaml
version: 3                        # was 2

profile: full                     # new, optional; full is the default

paths:
  engine_integration: engine-integration/   # new, required
```

Optionally add the `engine`, `budgets`, and `accessibility` blocks — see `templates/project/project.yaml`. `budgets` is required only if you run the engine integration stage, where an undeclared budget produces `integration_blocked` rather than a silent pass.

**3. Update `.pipeline/game-art-production-state.yaml`.**

```yaml
version: 3                        # was 2

stages:
  # ... after asset_qc, before runtime_validation:
  engine_integration:
    skill: game-engine-integrator
    status: NOT_STARTED
    readiness: null
    artifacts: []
```

**4. Convert lineage fields.** Records that carried `hash:` or the value `unknown` need real digests:

```yaml
# before
asset_spec:
  path: assets/specs/AST-001.yaml
  version: v3
  hash: unknown

# after
asset_spec:
  path: assets/specs/AST-001.yaml
  version: v3
  content_hash: <sha256sum of that exact file>
```

**5. Find everything that still needs attention.**

```bash
npx game-production-skills validate
```

It reports every schema violation, every hash mismatch, and every QC verdict bound to an output that has since changed. Work the list until it passes.

**Two behaviour changes worth knowing about**

- A QC report whose `evaluated.normalized_output.content_hash` does not match the current normalized output no longer counts as an approval for that asset. If a project has been regenerating assets without re-running QC, the validator will now say so.
- A runtime report claiming approval while `build.executable` is `false`, or while a `risk: high` context is untested, is rejected. Both were previously possible to record.

## 0.1.0

Initial release: eight skills, contract v2, prose contracts.
